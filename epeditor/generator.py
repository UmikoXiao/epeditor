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
        res = self.__class__.__name__
        res += ': '+self.name
        res += '\nargs_count: '+str(self.args_count)
        for i in range(len(self.args_name)):
            res += '\n' + self.args_name[i] + ' : '+self.args_description[i]
        return res

    def run_to_py(self,path:str):
        definition = inspect.getsource(self.run)
        description = ','.join(['\''+des+'\'' for des in self.args_description])
        definition+=f'{self.name[1:]}=Generator({self.name},[{description}])'
        with open(path, 'w+') as f:
            f.write(definition+'\n')
            f.write(self.name[1:])
        return self.name[1:]

    @classmethod
    def from_py(cls,path:str):
        with open(path, 'r') as f:
            lines=f.readlines()
            exec(''.join(lines[:-1]))
            return eval(lines[-1].strip('\n'))

# 默认，返回原始值
def _original(value,size=1):
    return [value]*int(size)
original=Generator(_original,['原始数值','样本个数'])

# 自定义函数！
# numpy.linspace实现
def _linspace(start,end,num):
    return np.linspace(start,end,num).tolist()
linspace = Generator(_linspace,['线性采样起点','线性采样终点','样本个数'])

# numpy.arange实现
def _arange(start,end,step):
    return np.arange(start,end,step).tolist()
arange = Generator(_arange,['等差数列起点','等差数列终点','等差数量的差'])

# 均匀分布采样
def _uniform(low,high,size):
    return np.random.uniform(low,high,size)
uniform=Generator(_uniform,['均匀采样下边界','均匀采样上边界','样本个数'])

# 高斯分布采样
def _gaussian(median,scale,size):
    return np.random.normal(median,scale,size)
gaussian=Generator(_gaussian,['高斯分布中位数','高斯分布标准差','样本个数'])

# 伯努利分布采样
def _bernoulli(times,propety,size):
    return np.random.binomial(times,propety,size)
bernoulli=Generator(_bernoulli,['单次采样试验次数,即概率P=1时的值','事件概率[0,1]','样本个数'])

# 指数分布采样
def _power(max,a,size):
    return max*np.random.power(a,size)
power=Generator(_power,['采样最大值，结果落在[0,max]','指数幂,p=ax^(a-1)','采样个数'])

# 随机分布采样
def _random(min,max,size):
    return (max-min)*np.random.random(size)+min
random=Generator(_random,['随机采样最小值','随机采样最大值','采样个数'])

# 枚举类型
def _enumerate(anydata):
    if isinstance(anydata,str):
        anydata = anydata.split(',')
    return np.array(anydata)
enumerate=Generator(_enumerate,['所有的取值，为list或者为\',\'分割的字符串'])

