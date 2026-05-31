import numpy as np
import inspect
class Generator:
    """Callable sampler wrapper with argument metadata and persistence helpers."""
    __slots__ = ['name','args_count','args_name','args_description','run']
    def __init__(self,run_method,descriotion=None):
        """
          init  .
        
        Parameters
        ----------
        run_method : Any
            Input parameter `run_method`.
        
        descriotion : Any
            Input parameter `descriotion`.
        
        Returns
        -------
        None
            Return value from `__init__`.
        """
        self.run=run_method
        self.name=run_method.__name__
        try:
            self.args_count=run_method.__code__.co_argcount
            self.args_name = run_method.__code__.co_varnames
        except:
            self.args_count=0
            self.args_name=''
        if descriotion is None:
            descriotion=[]*self.args_count
        self.args_description=descriotion

    def __repr__(self):
        """
          repr  .
        
        Returns
        -------
        Any
            Return value from `__repr__`.
        """
        res = self.__class__.__name__
        res += ': '+self.name
        res += '\nargs_count: '+str(self.args_count)
        for i in range(len(self.args_name)):
            res += '\n' + self.args_name[i] + ' : '+self.args_description[i]
        return res

    def run_to_py(self,path:str):
        """
        Run to py.
        
        Parameters
        ----------
        path : str
            Input parameter `path`.
        
        Returns
        -------
        Any
            Return value from `run_to_py`.
        """
        definition = inspect.getsource(self.run)
        description = ','.join(['\''+des+'\'' for des in self.args_description])
        definition+=f'{self.name[1:]}=Generator({self.name},[{description}])'
        with open(path, 'w+') as f:
            f.write(definition+'\n')
            f.write(self.name[1:])
        return self.name[1:]

    @classmethod
    def from_py(cls,path:str):
        """
        From py.
        
        Parameters
        ----------
        path : str
            Input parameter `path`.
        
        Returns
        -------
        Any
            Return value from `from_py`.
        """
        with open(path, 'r') as f:
            lines=f.readlines()
            exec(''.join(lines[:-1]))
            return eval(lines[-1].strip('\n'))

def _original(value,size=1):
    """
     original.
    
    Parameters
    ----------
    value : Any
        Input parameter `value`.
    
    size : Any
        Input parameter `size`.
    
    Returns
    -------
    Any
        Return value from `_original`.
    """
    return [value]*int(size)
original = Generator(_original, ['original value', 'sample size'])

def _linspace(start,end,num):
    """
     linspace.
    
    Parameters
    ----------
    start : Any
        Input parameter `start`.
    
    end : Any
        Input parameter `end`.
    
    num : Any
        Input parameter `num`.
    
    Returns
    -------
    Any
        Return value from `_linspace`.
    """
    return np.linspace(start,end,num).tolist()
linspace = Generator(_linspace, ['linear start', 'linear end', 'sample size'])

def _arange(start,end,step):
    """
     arange.
    
    Parameters
    ----------
    start : Any
        Input parameter `start`.
    
    end : Any
        Input parameter `end`.
    
    step : Any
        Input parameter `step`.
    
    Returns
    -------
    Any
        Return value from `_arange`.
    """
    return np.arange(start,end,step).tolist()
arange = Generator(_arange, ['sequence start', 'sequence end', 'step'])

def _uniform(low,high,size):
    """
     uniform.
    
    Parameters
    ----------
    low : Any
        Input parameter `low`.
    
    high : Any
        Input parameter `high`.
    
    size : Any
        Input parameter `size`.
    
    Returns
    -------
    Any
        Return value from `_uniform`.
    """
    return np.random.uniform(low,high,size)
uniform = Generator(_uniform, ['uniform low', 'uniform high', 'sample size'])

def _gaussian(median,scale,size):
    """
     gaussian.
    
    Parameters
    ----------
    median : Any
        Input parameter `median`.
    
    scale : Any
        Input parameter `scale`.
    
    size : Any
        Input parameter `size`.
    
    Returns
    -------
    Any
        Return value from `_gaussian`.
    """
    return np.random.normal(median,scale,size)
gaussian = Generator(_gaussian, ['normal mean', 'normal std', 'sample size'])

def _bernoulli(times,propety,size):
    """
     bernoulli.
    
    Parameters
    ----------
    times : Any
        Input parameter `times`.
    
    propety : Any
        Input parameter `propety`.
    
    size : Any
        Input parameter `size`.
    
    Returns
    -------
    Any
        Return value from `_bernoulli`.
    """
    return np.random.binomial(times,propety,size)
bernoulli = Generator(_bernoulli, ['trials per sample', 'event probability [0,1]', 'sample size'])

def _power(max,a,size):
    """
     power.
    
    Parameters
    ----------
    max : Any
        Input parameter `max`.
    
    a : Any
        Input parameter `a`.
    
    size : Any
        Input parameter `size`.
    
    Returns
    -------
    Any
        Return value from `_power`.
    """
    return max*np.random.power(a,size)
power = Generator(_power, ['max value in [0,max]', 'power exponent', 'sample size'])

def _random(min,max,size):
    """
     random.
    
    Parameters
    ----------
    min : Any
        Input parameter `min`.
    
    max : Any
        Input parameter `max`.
    
    size : Any
        Input parameter `size`.
    
    Returns
    -------
    Any
        Return value from `_random`.
    """
    return (max-min)*np.random.random(size)+min
random = Generator(_random, ['random min', 'random max', 'sample size'])

def _enumerate(anydata):
    """
     enumerate.
    
    Parameters
    ----------
    anydata : Any
        Input parameter `anydata`.
    
    Returns
    -------
    Any
        Return value from `_enumerate`.
    """
    if isinstance(anydata,str):
        anydata = anydata.split(',')
    return np.array(anydata)
enumerate = Generator(_enumerate, ['all candidate values as list or comma-separated string'])


