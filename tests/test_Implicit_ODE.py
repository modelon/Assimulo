import nose
from Assimulo.Implicit_ODE import *
from Assimulo.Problem import Implicit_Problem


class Test_Implicit_ODE:
    
    def test_init(self):
        """
        This tests the functionality of the method __init__.
        """
        class prob(Implicit_Problem):
            def f(self, t, y, yd):
                pass
        res = prob()
        
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, res, 1, 'test')
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, res, 1, 1, 'test')
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, res, 'test', 'test', 'test')
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, res, [1.0 , 1.0], [1.0, 'test'])
        nose.tools.assert_raises(Implicit_ODE_Exception, Implicit_ODE, None, [1.0 , 1.0, 1.0], [1.0, 1, 1])
        
        
        simulator = Implicit_ODE(res, [1 , 1.0], [2, 2.0], 1)
        assert simulator.t[0] == 1.0
        assert simulator.y[0][0] == 1.0
        assert simulator.yd[0][0] == 2.0
        
        
    def test_call(self):
        """
        This tests the functionality of the method __call__.
        """
        y0 = [0.0]
        yd0 = [1.0]
        class prob(Implicit_Problem):
            f = lambda self,t,x,xd: x
        ida = prob()

        simulator = IDA(ida,y0,yd0)
        nose.tools.assert_raises(Implicit_ODE_Exception, simulator, -1.0)
        nose.tools.assert_raises(Implicit_ODE_Exception, simulator, 'test')
        
        [t,y,yd] = simulator(1.0,10)
        
        assert len(t) == 11 #11 Due to t0 is counted as well
        
    
class Test_IDA:
    
    def setUp(self):
        """
        This function sets up the test case.
        """
        class Prob(Implicit_Problem):
            f = 'Test function'
        res = Prob()
        y0 = [1.0]
        yd0 = [1.0]

        self.simulator = IDA(res, y0, yd0)
        
        
    def test_init(self):
        """
        This tests the functionality of the method __init__.
        """
        
        assert self.simulator.res_fcn == 'Test function'
        assert self.simulator.suppress_alg == False
        assert self.simulator.algvar == [1.0]
        assert self.simulator.switches == None
        assert self.simulator.maxsteps == 10000
        assert self.simulator.verbosity == self.simulator.NORMAL
        assert self.simulator.y[0][0] == 1.0
        
        nose.tools.assert_raises(Implicit_ODE_Exception, IDA, 'Test function', 'test', [1.0])
        nose.tools.assert_raises(Implicit_ODE_Exception, IDA, 'Test function', [1.0], [1.0], switches0='Error')
        
        class Prob(Implicit_Problem):
            f = 'Test function'
            event_fcn = lambda self,t,x,xd,sw: x
        res = Prob()
        y0 = [1.0, 1.0, 1]
        yd0 = [1, 1, 1]
        
        switches = [True, False]

        simulator = IDA(res,y0,yd0, switches0=switches)
        
        assert simulator.res_fcn == res.f
        assert simulator.switches == switches
        assert simulator.yd[0][0] == 1.0
        assert simulator.problem_spec[0] == res.f
        assert simulator.problem_spec[1] == simulator.event_fcn
        assert simulator.problem_spec[2] == switches
    
    def test_max_order(self):
        """
        This tests the functionality of the property maxord.
        """
        
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_max_ord, "Test")
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_max_ord, 1.0)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_max_ord, -1.0)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_max_ord, [1,1])
        
        
        self.simulator.maxord = -1
        assert self.simulator.maxord == 1
        self.simulator.maxord = 2
        assert self.simulator.maxord == 2
        self.simulator.maxord = 6
        assert self.simulator.maxord == 5

    def test_tout1(self):
        """
        This tests the functionality of the property tout1.
        """
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_calcIC_tout1, 'Test')
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_calcIC_tout1, [1,1])
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_calcIC_tout1, 'Test')
        
        assert self.simulator.tout1 == 0.001
        self.simulator.tout1 = -0.001
        assert self.simulator.tout1 == -0.001
        self.simulator.tout1 = 1
        assert self.simulator.tout1 == 1.0
        
    def test_lsoff(self):
        """
        This tests the functionality of the property lsoff.
        """
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_lsoff, 'Test')
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_lsoff, 1.0)
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_lsoff, 0.0)
        nose.tools.assert_raises(Implicit_ODE_Exception, self.simulator._set_lsoff, [1,1])
        
        assert self.simulator.lsoff == False
        self.simulator.lsoff = True
        assert self.simulator.lsoff == True
        self.simulator.lsoff = False
        assert self.simulator.lsoff == False
        
        
    def test_algvar(self):
        """
        This tests the functionality of the property algvar.
        """
        
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, 1)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, [1,1,1])
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, {'Test':'case'})
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, -1)
        
        self.simulator.Integrator.dim = 3
        
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, [1.0,1.0])
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_algvar, [3.0, 1.0, 1.0])
        
        vector = [1.0,0.0,1.0]
        
        self.simulator.algvar = vector
        nose.tools.assert_equal(self.simulator.algvar[0], vector[0])
        nose.tools.assert_equal(self.simulator.algvar[1], vector[1])
        nose.tools.assert_equal(self.simulator.algvar[2], vector[2])
        
        
    def test_suppress_alg(self):
        """
        This tests the functionality of the property suppress_alg.
        """
        
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, "Test")
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, [1,2])
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, {'Test':'case'})
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, 3)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, 0)
        nose.tools.assert_raises(Sundials_Exception, self.simulator._set_suppress_alg, 0.1)
        
        self.simulator.suppress_alg = True
        assert self.simulator.suppress_alg == True
        self.simulator.suppress_alg = False
        assert self.simulator.suppress_alg == False
        
    def test_make_consistency(self):
        """
        This tests the functionality of the method make_consistency.
        """
        class Prob(Implicit_Problem):
            def f(self,t,y,yd):
                res_1 = y[0] + y[1]+1.0
                res_2 = y[1]
                return [res_1, res_2]
        res = Prob()
        
        y0 = [2.0, 2.0]
        yd0 = [1.0 , 0.0]
        simulator = IDA(res, y0, yd0)
        
        [y, yd] = simulator.make_consistency('IDA_Y_INIT')
        
        nose.tools.assert_almost_equal(y[1], 0.00000)
        nose.tools.assert_almost_equal(y[0], -1.0000)
        nose.tools.assert_almost_equal(yd[0], 1.0000)
        nose.tools.assert_almost_equal(yd[1], 0.0000)
     
    def test_is_disc(self):
        """
        This tests the functionality of the property is_disc.
        """
        class Prob_IDA(Implicit_Problem):
            f = lambda self,t,y,yd,sw: [y[0]-1.0]
            event_fcn = lambda self,t,y,yd,sw: [t-1.0, t]
            y0 = [1.0]
            yd0 = [1.0]
        switches = [False,True]
        res = Prob_IDA()
        simulator = IDA(res, switches0=switches)
        simulator(2.)
        
        #assert simulator.t[-1] == 1.0 #For now, this error serves as prof of discontinuities
        #assert simulator.is_disc == True
