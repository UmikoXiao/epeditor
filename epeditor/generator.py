import numpy as np
import inspect
class Generator:
    '''
        name: 采样方法的名称
        args_count: 该函数的参数个数，list
        args_name: 该函数的参数名称，list
        agrs_description: 不摆烂就会有的参数说明
        run: 函数本体
    '''
    __slots__ = ['name','args_count','args_name','args_description','run']
    def __init__(self,run_method,descriotion=None):
        """
        Initialize a callable object wrapper with metadata about the given function.
        
        Parameters
        ----------
        run_method : callable
            The function to be wrapped, from which metadata such as name, argument count, and argument names are extracted.
        descriotion : list of str, optional
            A list of descriptions corresponding to each argument of `run_method`. If None, defaults to an empty list multiplied by the number of arguments.
        
        Returns
        -------
        None
            This constructor does not return a value.
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
        Return a string representation of the object with class name, name, args_count, and argument details.
        
        Parameters
        ----------
        self : object
            The instance of the class being represented. Expected to have attributes: `name` (str),
            `args_count` (int), `args_name` (list of str), and `args_description` (list of str).
        
        Returns
        -------
        str
            A formatted string containing the class name, instance name, argument count, and 
            descriptions of each argument.
        """
        res = self.__class__.__name__
        res += ': '+self.name
        res += '\nargs_count: '+str(self.args_count)
        for i in range(len(self.args_name)):
            res += '\n' + self.args_name[i] + ' : '+self.args_description[i]
        return res

    def run_to_py(self,path:str):
        """
        Write the source code of the `run` method and a generator instantiation to a Python file.
        
        Parameters
        ----------
        path : str
            The file path where the generated Python code will be written.
        
        Returns
        -------
        str
            The name of the generator instance, derived from `self.name[1:]`.
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
        Create an instance from a Python script file.
        
        Parameters
        ----------
        path : str
            Path to the Python script file to be read and executed.
        
        Returns
        -------
        object
            The value returned by evaluating the last line of the script, typically an instance of the class.
        """
        with open(path, 'r') as f:
            lines=f.readlines()
            exec(''.join(lines[:-1]))
            return eval(lines[-1].strip('\n'))

# 默认，返回原始值
def _original(value,size=1):
    """
    Generate a list of repeated values.
    
    Parameters
    ----------
    value : any
        The value to be repeated in the list.
    size : int, optional
        The number of times to repeat the value. Default is 1.
    
    Returns
    -------
    list
        A list containing the repeated value.
    """
    return [value]*int(size)
original=Generator(_original,['原始数值','样本个数'])

# 自定义函数！
# numpy.linspace实现
def _linspace(start,end,num):
    """Generate a list of evenly spaced values over a specified interval.
    
        Parameters
        ----------
        start : float
            The starting value of the sequence.
        end : float
            The end value of the sequence.
        num : int
            Number of samples to generate.
    
        Returns
        -------
        list
            A list of `num` evenly spaced samples between `start` and `end`.
    """
    return np.linspace(start,end,num).tolist()
linspace = Generator(_linspace,['线性采样起点','线性采样终点','样本个数'])

# numpy.arange实现
def _arange(start,end,step):
    """
    Generate a list of evenly spaced values within a given interval.
    
    Parameters
    ----------
    start : float
        The starting value of the sequence.
    end : float
        The end value of the sequence (exclusive).
    step : float
        The step size between consecutive values.
    
    Returns
    -------
    list
        A list of evenly spaced numbers from start to end, not including end.
    """
    return np.arange(start,end,step).tolist()
arange = Generator(_arange,['等差数列起点','等差数列终点','等差数量的差'])

# 均匀分布采样
def _uniform(low,high,size):
    """
    Uniform sampling from a given range.
    
    Parameters
    ----------
    low : float
        Lower boundary of the uniform distribution.
    high : float
        Upper boundary of the uniform distribution.
    size : int or tuple of ints
        Number of samples to draw or shape of the output array.
    
    Returns
    -------
    ndarray
        Drawn samples from the uniform distribution.
    """
    return np.random.uniform(low,high,size)
uniform=Generator(_uniform,['均匀采样下边界','均匀采样上边界','样本个数'])

# 高斯分布采样
def _gaussian(median,scale,size):
    """
    Generate samples from a Gaussian (normal) distribution.
    
    Parameters
    ----------
    median : float
        The median (also the mean) of the Gaussian distribution.
    scale : float
        The standard deviation (scale) of the Gaussian distribution.
    size : int or tuple of ints
        The number of samples to generate, or the shape of the output array.
    
    Returns
    -------
    ndarray
        Array of samples drawn from the Gaussian distribution with specified median and scale.
    """
    return np.random.normal(median,scale,size)
gaussian=Generator(_gaussian,['高斯分布中位数','高斯分布标准差','样本个数'])

# 伯努利分布采样
def _bernoulli(times,propety,size):
    """Draw samples from a Bernoulli distribution.
    
    Parameters
    ----------
    times : int
        Number of trials in a single Bernoulli experiment (value when probability P=1).
    propety : float
        Probability of success in each trial, must be in the interval [0, 1].
    size : int or tuple of ints
        Number of samples to draw.
    
    Returns
    -------
    ndarray
        Array of drawn samples from the Bernoulli distribution, where each sample is 0 or 1.
    """
    return np.random.binomial(times,propety,size)
bernoulli=Generator(_bernoulli,['单次采样试验次数,即概率P=1时的值','事件概率[0,1]','样本个数'])

# 指数分布采样
def _power(max,a,size):
    """
    Draw random samples from a power distribution with a specified maximum, exponent, and sample size.
    
    Parameters
    ----------
    max : float
        The maximum value of the distribution. Samples will be in the range [0, max].
    a : float
        The power exponent parameter, where the probability density function is proportional to x^(a-1).
    size : int or tuple of ints
        The number of samples to draw or the shape of the output array.
    
    Returns
    -------
    ndarray
        An array of random samples drawn from the power distribution with the specified parameters.
    """
    return max*np.random.power(a,size)
power=Generator(_power,['采样最大值，结果落在[0,max]','指数幂,p=ax^(a-1)','采样个数'])

# 随机分布采样
def _random(min,max,size):
    """
    Randomly sample numbers from a uniform distribution.
    
    Parameters
    ----------
    min : float or int
        The minimum value of the sampling range.
    max : float or int
        The maximum value of the sampling range.
    size : int or tuple of ints
        The number of samples to generate or the shape of the output array.
    
    Returns
    -------
    ndarray
        Array of randomly sampled values in the range [min, max) with specified size.
    """
    return (max-min)*np.random.random(size)+min
random=Generator(_random,['随机采样最小值','随机采样最大值','采样个数'])

# 枚举类型
def _enumerate(anydata):
    """
    Enumerate input data by converting it into a numpy array.
    
    Parameters
    ----------
    anydata : str or list
        The input data to be enumerated. If a string, it is expected to be a comma-separated 
        sequence of values which will be split into a list. If a list, it is directly converted 
        to a numpy array.
    
    Returns
    -------
    numpy.ndarray
        A numpy array containing the elements from the input data.
    """
    if isinstance(anydata,str):
        anydata = anydata.split(',')
    return np.array(anydata)
enumerate=Generator(_enumerate,['所有的取值，为list或者为\',\'分割的字符串'])

