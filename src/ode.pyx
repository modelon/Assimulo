#!/usr/bin/env python 
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Modelon AB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import numpy as N
cimport numpy as N
import time
import pylab as P

import itertools

from exception import *

include "constants.pxi" #Includes the constants (textual include)

realtype = N.float 

cdef class ODE:
    """
    Base class for all our integrators.
    """
    
    def __init__(self, problem):
        """
        Defines general starting attributes for a simulation
        problem.
        """
        self.options = {"continuous_output":False,"verbosity":NORMAL}
        #self.internal_flags = {"state_events":False,"step_events":False,"time_events":False} #Flags for checking the problem (Does the problem have state events?)
        self.supports = {"state_events":False,"interpolated_output":False,"one_step_mode":False} #Flags for determining what the solver supports
        self.problem_info = {"dim":0,"dimRoot":0,"dimSens":0,"state_events":False,"step_events":False,"time_events":False
                             ,"jac_fcn":False, "sens_fcn":False, "jacv_fcn":False,"switches":False}
        
        #Data object for storing the event data
        self.event_data = []
        
        if problem is None:
            raise ODE_Exception('The problem needs to be a subclass of a Problem.')
        
        #Check Problem for event functions
        if hasattr(problem, 'time_events'):
            self.problem_info["time_events"] = True
        
        if hasattr(problem, 'state_events'):
            self.problem_info["state_events"] = True
        
        if hasattr(problem, 'step_events'):
            self.problem_info["step_events"] = True
        
        if hasattr(problem, 'y0'):
            problem.y0 = N.array(problem.y0,dtype=realtype) if len(N.array(problem.y0,dtype=realtype).shape)>0 else N.array([problem.y0],dtype=realtype)
            self.problem_info["dim"] = len(problem.y0)
        else:
            raise ODE_Exception('y0 must be specified in the problem.')
        
        if hasattr(problem, "p0"):
            problem.p0 = N.array(problem.p0,dtype=realtype) if len(N.array(problem.p0,dtype=realtype).shape)>0 else N.array([problem.p0],dtype=realtype)
            self.problem_info["dimSens"] = len(problem.p0)
            self.p_cur = problem.p0.copy()
        
        if hasattr(problem, "sw0"):
            problem.sw0 = N.array(problem.sw0,dtype=N.bool) if len(N.array(problem.sw0,dtype=N.bool).shape)>0 else N.array([problem.sw0],dtype=N.bool)
            self.problem_info["switches"] = True
            self.sw_cur = problem.sw0.tolist()
        
        if hasattr(problem, 't0'):
            problem.t0 = float(problem.t0)
        else:
            problem.t0 = 0.0
            
        if hasattr(problem, "jac"):
            self.problem_info["jac_fcn"] = True
        if hasattr(problem, "jacv"):
            self.problem_info["jacv_fcn"] = True
        
    def __call__(self, double tfinal, int ncp=0, list cpts=None):
        return simulate(tfinal, ncp, cpts)
        
    cpdef simulate(self, double tfinal, int ncp=0, object ncp_list=None):
        """
        Calls the integrator to perform the simulation over the given time-interval. 
        If a second call to simulate is performed, the simulation starts from the last
        given final time.
        
            Parameters::
            
                tfinal  
                        - Final time for the simulation
                
                        - Should be a float or integer greater than the initial time.
                        
                ncp     
                        - Default '0'. Number of communication points where the 
                          solution is returned. If '0', the integrator will return 
                          at its internal steps.
                          
                        - Should be an integer.
                          
                    Example:
                    
                        __call__(10.0, 100), 10.0 is the final time and 100 is the number
                                             communication points.
                 
        """
        t0 = self.t_cur
        
        #Error checking
        try:
            tfinal = float(tfinal)
        except ValueError:
            raise AssimuloException('Final time must be an integer or float.')
            
        if self.t_cur > tfinal:
            raise AssimuloException('Final time must be greater than start time.')
        
        if not isinstance(ncp, int):
            raise AssimuloException('Number of communication points must be an integer')
        
        if ncp < 0:
            ncp = 0
            self.log_message('Number of communication points must be a positive integer, setting ncp = 0.',WARNING)
        
        #Check solver support against current problem
        if self.problem_info["step_events"] and self.supports["one_step_mode"] is False:
            self.log_message("The current solver does not support step events (completed steps). Disabling step events and continues.", WHISPER)
            self.problem_info["step_events"] = False
        
        if self.supports["one_step_mode"] is False and self.options["continuous_output"]:
            self.log_message("The current solver does not support continuous output. Setting continuous_output to False and continues.", WHISPER)
            self.solver_options["continuous_output"] = False
        
        if (ncp != 0 or ncp_list != None) and (self.options["continuous_output"] or self.problem_info["step_events"]) and self.supports["interpolated_output"] is False:
            self.log_message("The current solver does not support interpolated output. Setting ncp to 0 and ncp_list to None and continues.", WHISPER)
            ncp = 0
            ncp_list = None
            
        #Determine the output list
        if ncp != 0:
            output_list = N.linspace(t0,tfinal,ncp+1)
            output_index = 0
        elif ncp_list != None:
            output_list = N.array(ncp_list, dtype=realtype, ndmin=1)
            output_index = 0
        else:
            output_list = None
            output_index = 0
        
        #Determine if we are using one step mode or normal mode
        if self.problem_info['step_events'] or self.options['continuous_output']:
            ONE_STEP = 1
        else:
            ONE_STEP = 0
        
        #Determine if the output should be interpolated or not
        if output_list == None:
            INTERPOLATE_OUTPUT = 0
        else:
            INTERPOLATE_OUTPUT = 1

        #Time and Step events
        TIME_EVENT = 1 if self.problem_info['time_events'] is True else 0
        STEP_EVENT = 1 if self.problem_info["step_events"] is True else 0

        #Simulation starting, call initialize
        self.problem.initialize(self)
        self.initialize()
        
        #Start of simulation, start the clock
        time_start = time.clock()
        
        #Start the simulation
        self._simulate(t0, tfinal, output_list, ONE_STEP, INTERPOLATE_OUTPUT, TIME_EVENT, STEP_EVENT)
        
        #End of simulation, stop the clock
        time_stop = time.clock()
        
        #Simulation complete, call finalize
        self.finalize()
        self.problem.finalize(self)
        
        #Print the simulation statistics
        self.print_statistics(NORMAL)
        
        #Log elapsed time
        self.log_message('Simulation interval    : ' + str(t0) + ' - ' + str(self.t_cur) + ' seconds.', NORMAL)
        self.log_message('Elapsed simulation time: ' + str(time_stop-time_start) + ' seconds.', NORMAL)
    
    cpdef initialize(self):
        pass
    
    cpdef finalize(self):
        pass
    
    def _set_verbosity(self, verb):
        self.options["verbosity"] = int(verb)
    
    def _get_verbosity(self):
        """
        This determines the level of the output. A smaller value
        means more output.
        
            Parameters::
            
                verb  
                        - Default 30
                    
                        - Should be a integer.

        """
        return self.options["verbosity"]
    
    verbosity = property(_get_verbosity,_set_verbosity)
    
    def _set_continuous_output(self, cont_output):
        self.options["continuous_output"] = bool(cont_output)
    
    def _get_continuous_output(self):
        """
        This options specifies if the solver should use a one step approach. 
        
            Parameters::
            
                cont_output
                  
                        - Default False
                    
                        - Should be a boolean.

        """
        return self.options["continuous_output"]
    
    continuous_output = property(_get_continuous_output,_set_continuous_output)
    
    cpdef log_message(self, message,int level):
        if level >= self.options["verbosity"]:
            print(message)
            
    cpdef log_event(self,double time,object event_info, int level):
        if level >= self.options["verbosity"]:
            self.event_data.append([time,event_info])
            
    cpdef get_options(self):
        """
        Returns the solver options.
        """
        return self.options
    