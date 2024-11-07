import numpy as np
from .db_eplusout_reader import Variable, get_results, exceptions
from .utils import Hourly, Daily, Monthly, Annually, generate_code, bar
from datetime import datetime
import os, shutil

Working_Dir = r'.\_epeditortemp'


class IDFResult:
    __slots__ = ['variables', 'frequency', 'dump', '__cache','sql_list','metaData']

    def __init__(self, variables, frequency, data,sql_list):
        self.variables = variables
        self.frequency = frequency
        self.dump = None
        self.__cache = None
        self.metaData = {}
        self.sql_list = sql_list
        if isinstance(data, str):
            if os.path.isfile(data):
                self.dump = data
        else:
            if len(variables) != len(data):
                raise Exception('Illegal variables or data: they should have the same len')
            self.__cache = data

        if self.__cache.shape[0] * self.__cache.shape[1] > 100000:
            self.save()

    @property
    def data(self):
        if self.dump is not None:
            return np.load(self.dump)[:, 1:]
        else:
            return self.__cache

    @classmethod
    def from_npy(cls, path):
        data = np.load(path)
        variables = [eval(var) for var in np.load(path[:-4]) + '_variables.npy']
        frequency = len(data[0])
        if frequency <= 1:
            frequency = Annually
        elif frequency <= 12:
            frequency = Monthly
        elif frequency <= 365:
            frequency = Daily
        else:
            frequency = Daily
        del data
        res = cls(variables, frequency, path)
        return res

    def save(self, path: str = os.path.join(Working_Dir, generate_code(6) + '.npy')):
        if self.__cache is None and self.dump is not None:
            if path != self.dump:
                shutil.copy(self.dump, path)
            self.dump = path
        elif self.__cache is not None:
            np.save(path, self.__cache)
            np.save(path[:-4] + '_variables.npy', self.variables)
            self.dump = path
            self.__cache = None

    def to_csv(self, path: str, seq: str = ','):
        streams = []
        if len(np.array(self.data).shape) == 2:
            streams += [seq.join(['directory']+[v.__repr__() for v in self.variables])]
            streams += [seq.join([os.path.dirname(file)]+line.astype(str).tolist()) for line, file in zip(np.array(self.__cache).T,self.sql_list)]
        if len(np.array(self.data).shape) == 3:
            for i,v in enumerate(self.variables):
                streams += [v.__repr__()]
                streams += [seq.join([os.path.dirname(file) for file in self.sql_list])]
                streams += [seq.join(line.astype(str)) for line in np.array(self.__cache[i])]
        with open(path, 'w+') as f:
            f.write('\n'.join(streams))

    def load(self):
        if self.__cache is None and self.dump is not None:
            self.__cache = np.load(self.dump)
            self.dump = None
        return self.__cache


def get_group_result(sql_list: list, variables: Variable, calculator, frequency=Monthly,
                     alike=False, start_date=None, end_date=None, dump_path=None):
    group_result = []
    if isinstance(variables, Variable):
        variables = [variables]
    for variable in variables:
        print('Group_result:', variable.key, variable.type)
        _result = []
        for i in range(len(sql_list)):
            sql = sql_list[i]
            try:
                _result.append(get_results(sql, variable, frequency, alike, start_date, end_date).first_array)
            except exceptions.NoResults:
                print('**********Variable not found. continue')
                continue
            bar(i, len(sql_list), 1)
        group_result.append(np.array([calculator(data_series) for data_series in np.array(_result).T]))
        print()
    group_result = np.array(group_result)
    if dump_path is not None and os.path.isfile(dump_path):
        np.save(dump_path, group_result)
        np.save(dump_path[:-4] + '_variables.npy', variables)
        group_result = dump_path
    return IDFResult(variables, frequency, group_result[:, 1:],sql_list)


def get_case_result(sql: str, variables: Variable, frequency=Monthly,
                    alike=False, start_date=None, end_date=None, dump_path=None):
    if isinstance(variables, Variable):
        variables = [variables]
    try:
        result = get_results(sql, variables, frequency, alike, start_date, end_date).arrays
    except exceptions.NoResults:
        print('**********Variable not found. Return None')
        return None

    result = np.array(result)
    if dump_path is not None and os.path.isfile(dump_path):
        np.save(dump_path, result)
        np.save(dump_path[:-4] + '_variables.npy', variables)
        result = dump_path
    return IDFResult(variables, frequency, result)


if __name__ == '__main__':
    # res= get_results(
    #    r'C:\Users\Umiko\PycharmProjects\IDFprocessing\test\baseline_0\CHN_Beijing.sql',
    #    [Variable(None,None,None)],
    #    frequency=H,
    #    alike=True
    # )
    # print(res.variables)

    v = Variable(key='BLOCK10:ZONE1', type='Lights Total Heating Rate', units='W')
    # res=get_case_result(r'C:\Users\Umiko\PycharmProjects\IDFprocessing\test\baseline_0\CHN_Beijing.sql',v)
    # res.save()
    res = IDFResult.from_npy('test/.0xbe505f.npy')
    print(res.variables)