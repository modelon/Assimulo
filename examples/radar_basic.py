# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 14:03:12 2012
@author: tony
"""
from  __future__  import division
from  scipy       import *
from matplotlib.pyplot import *

from copy import copy, deepcopy

from assimulo.problem import Delay_Explicit_Problem
from assimulo.solvers import radar5

class Simple(Delay_Explicit_Problem):
    def __init__(self):
        Delay_Explicit_Problem.__init__(self)
      
        self.ntimelags = 1          # The number of different time lags
    
        self.lagcompmap = [[1]]     # Delay 0 affects component 1 (Note that 1 = 0 here)
        
        self.nrdens = 1             # There is 1 component that needs dense output
        self.ipast = array([1,0])     # Component 1 needs dense output (Note that 1=1 here)
#        self.ngrid = 0
            
            
    def arglag(self, i, t, y):
        return t - 1.0    # Only one constant time lag, -1
        
    def rhs(self, t, y, ydelay):
        ytm1 = ydelay[0][0] # y(t-1)

        return -y + ytm1
       
#    def jac(self, t, y, ydelay):
#        return J

    def phi(self, i, t):    # History function for $t \in [-1,0]$
        return sin(pi*t)


if __name__ == '__main__':
    ITOL = 1
    RTOL = 1.e-6
    ATOL = 1e-6
    H = 1.e-3
    mxst=1000


	# First solve
    p = Simple()
    p.grid = array([1.0, 0.0])
    p.ngrid = len(p.grid)-1
    p.y0 = 0    # sin(pi*0) = 0, so consistent with history function

    t0 = 0
    tf = 5.0
    #tf = 1.1
    
    s = radar5.Radar5ODE(p)
    s.rtol = RTOL
    s.atol = ATOL
    s.mxst = mxst
    s.inith = H
    s.maxsteps = 1000
    t,y = s.simulate(tf)
    print s.statistics
    
    y1 = array(deepcopy(s.y_sol)).reshape(-1)
    t1 = copy(s.t_sol)
    
    past1 = deepcopy(s.past)
    
    #del s
    #reload(radar5)
    #from assimulo.solvers import radar5

    
    
    #s = radar5.Radar5ODE(p)
    #s.rtol = RTOL
    #s.atol = ATOL
    #s.mxst = mxst
    #s.inith = H
    #s.maxsteps = 1000
    #t,y = s.simulate(tf)
    #print s.statistics
    
    #y2 = array(deepcopy(s.y_sol)).reshape(-1)
    #t2 = copy(s.t_sol)
    
    #past2 = deepcopy(s.past)
    
    #s2 = radar5.Radar5ODE(p)
    #s2.rtol = RTOL
    #s2.atol = ATOL
    #s2.mxst = mxst
    #s2.inith = H
    #s2.maxsteps = 1000
    #t,y = s2.simulate(tf)
    
    #y3 = array(deepcopy(s2.y_sol)).reshape(-1)
    #t3 = copy(s2.t_sol)
    #print s2.statistics
    
    #p2 = Simple()
    #p2.grid = array([1.0, 0.0])
    #p2.ngrid = len(p.grid)-1
    #p2.y0 = 0    # sin(pi*0) = 0, so consistent with history function
    
    #s3 = radar5.Radar5ODE(p2)
    #s3.rtol = RTOL
    #s3.atol = ATOL
    #s3.mxst = mxst
    #s3.inith = H
    #s3.maxsteps = 1000
    #t,y = s3.simulate(tf)
    
    #y4 = array(deepcopy(s3.y_sol)).reshape(-1)
    #t4 = copy(s3.t_sol)
    #print s3.statistics
    
    #print len(y1)
    #print len(y2)
    #print len(y3)
    #print len(y4)
    
    #plot(t,y)
    #show()

    #s.reset()
    #t,y = s.simulate(tf)
    #y2 = array(s.y_sol).copy().reshape(-1)
    #t2 = copy(s.t_sol)
    #plot(t, y1-y2)
    #t,y = s.simulate(tf, 1000)
