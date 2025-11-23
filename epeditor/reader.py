import numpy as np
from .db_eplusout_reader import Variable, get_results, exceptions
from .utils import Hourly, Daily, Monthly, Annually, generate_code, bar
from datetime import datetime
import os, shutil

Working_Dir = r'.\_epeditortemp'
if not os.path.exists(Working_Dir):
    os.mkdir(Working_Dir)

class IDFResult:
    __slots__ = ['variables', 'frequency', 'dump', '__cache', 'sql_list', 'metaData']

    def __init__(self, variables, frequency, data, sql_list):
        """
        Initialize the object with variables, frequency, data, and SQL list.
        
        Parameters
        ----------
        variables : list
            List of variable names corresponding to the data columns.
        frequency : str
            String indicating the frequency of the data (e.g., 'D' for daily, 'M' for monthly).
        data : str or array-like
            If a string, it should be a file path to load data from; if array-like, it should be a 2D array 
            with shape matching the number of variables. If the size exceeds 100,000 elements, data is saved automatically.
        sql_list : list
            List of SQL commands or strings associated with the data.
        
        Returns
        -------
        None
        """
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
        """
        Property that returns the processed data from either a saved dump or an internal cache.
        
        Returns
        -------
        numpy.ndarray
            The loaded data array with the first column removed if loading from `dump`, 
            otherwise returns the cached data stored in `__cache`.
        """
        if self.dump is not None:
            return np.load(self.dump)[:, 1:]
        else:
            return self.__cache

    @classmethod
    def from_npy(cls, path):
        """
        Create an instance of the class from .npy files containing data and variable names.
        
        Parameters
        ----------
        path : str
            Path to the .npy file containing the data. The corresponding variables are loaded 
            from a file with '_variables.npy' appended to the base filename (excluding the .npy extension).
        
        Returns
        -------
        cls
            An instance of the class initialized with the loaded variables, inferred frequency, and path.
        """
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
        """
        Save the current state of the object to a file.
        
        Parameters
        ----------
        path : str, optional
            The file path where the object's state will be saved. 
            Defaults to a randomly generated .npy file in the working directory.
        
        Returns
        -------
        None
        """
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
        """
        Write data to a CSV file in a formatted string sequence.
        
        Parameters
        ----------
        path : str
            The file path where the CSV will be saved.
        seq : str, optional
            The delimiter sequence used to separate values in the CSV. Default is ','.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        streams = []
        if len(np.array(self.data).shape) == 2:
            streamData = np.array(self.__cache).T
            streams += [seq.join(['directory'] + [v.__repr__() for v in self.variables])]
            streams += [seq.join(np.append([os.path.dirname(file)], line.astype(str))) for line, file in
                        zip(streamData, self.sql_list)]
        if len(np.array(self.data).shape) == 3:
            for i, v in enumerate(self.variables):
                streams += [v.__repr__()]
                streams += [seq.join([os.path.dirname(file).split('\\')[-1] for file in self.sql_list])]
                streams += [seq.join(line.astype(str)) for line in np.array(self.__cache[i])]
        with open(path, 'w+') as f:
            f.write('\n'.join(streams))

    def load(self):
        """
        Load and cache data from a dump file.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the `load` method. It is expected to have
            a `__cache` attribute for storing cached data and a `dump` attribute specifying
            the file path to load data from using `np.load`.
        
        Returns
        -------
        __cache : numpy.ndarray or None
            The cached data loaded from the dump file as a NumPy array, or None if no dump file is specified.
        """
        if self.__cache is None and self.dump is not None:
            self.__cache = np.load(self.dump)
            self.dump = None
        return self.__cache


def get_group_result(sql_list: list, variables: Variable, calculator, frequency=Monthly,
                     alike=False, start_date=None, end_date=None, dump_path=None):
    """
    Compute aggregated results for a list of SQL files and variables using a specified calculator function.
    
    Parameters
    ----------
    sql_list : list of str
        List of file paths to SQL files from which data will be retrieved.
    variables : Variable or list of Variable
        One or more Variable objects specifying the data variables to extract and process.
    calculator : callable
        A function that takes a data series (array-like) and returns a computed scalar or array value.
    frequency : type, optional
        The temporal frequency/resolution of the data (e.g., Monthly). Default is Monthly.
    alike : bool, optional
        If True, allows approximate matching of variable data. Default is False.
    start_date : str or datetime-like, optional
        Start date for filtering the time range of data. Default is None.
    end_date : str or datetime-like, optional
        End date for filtering the time range of data. Default is None.
    dump_path : str, optional
        If provided, the resulting group data will be saved to this file path in .npy format.
        Also saves associated variables. Returns the path string instead of IDFResult if used. Default is None.
    
    Returns
    -------
    IDFResult or str
        An IDFResult object containing variables, frequency, computed group results, and valid SQL file paths.
        If dump_path is specified and valid, returns the dump_path string after saving the results.
    """
    group_result = []
    if isinstance(variables, Variable):
        variables = [variables]
    for variable in variables:
        print('Group_result:', variable)
        if variable.key == 'None':
            variable = Variable(None, variable.type, variable.units)
            # print(variable)
        _result = []
        validSql = []
        # print(sql_list)
        for i in range(len(sql_list)):
            sql = os.path.normpath(sql_list[i])
            try:
                # print()
                # print(sql, variable, frequency)
                # print(get_results(sql, variable, frequency, alike=True))
                # print()
                _result.append(get_results(sql, variable, frequency, alike, start_date, end_date).first_array)
                validSql.append(sql)
            except Exception as e:
                print(e)
            bar(i, len(sql_list), 1)
        maxLenth = 0
        for res in _result:
            maxLenth = max(len(res), maxLenth)
        for i in range(len(_result)):
            if len(_result[i]) < maxLenth:
                _result[i] = np.reshape(-999, maxLenth)
        group_result.append(np.array([calculator(data_series) for data_series in np.array(_result).T]))
        print()

    group_result = np.array(group_result)
    if dump_path is not None and os.path.isfile(dump_path):
        np.save(dump_path, group_result)
        np.save(dump_path[:-4] + '_variables.npy', variables)
        group_result = dump_path
    return IDFResult(variables, frequency, group_result, validSql)

def get_group_summary(sql_list: list, variables: Variable, calculator, frequency=Monthly,
                     alike=False, start_date=None, end_date=None, dump_path=None):
    """
    Summarize group results from multiple SQL case files using specified variables and a calculator function.
    
    Parameters
    ----------
    sql_list : list
        List of file paths (strings) to SQL files to process.
    variables : Variable or list of Variable
        Variable or list of Variables specifying the data to extract from each SQL file.
    calculator : callable
        Function that takes a time series data array and computes a summary value (e.g., mean, sum).
    frequency : type, optional
        Frequency object (e.g., Monthly) defining the time frequency for result aggregation. Default is Monthly.
    alike : bool, optional
        If True, allows approximate matching of cases. Default is False.
    start_date : str or datetime-like, optional
        Start date for filtering the data. Default is None (no filtering).
    end_date : str or datetime-like, optional
        End date for filtering the data. Default is None (no filtering).
    dump_path : str, optional
        File path to save the output as a .npy file. If provided, `group_result` is saved and returned as path. 
        Default is None (no saving).
    
    Returns
    -------
    IDFResult
        An object containing the variables, frequency, grouped results (shape: variables × frequency × cases), 
        and list of valid SQL file paths that were successfully processed.
    """
    group_result,validSql = [],[]
    if isinstance(variables, Variable):
        variables = [variables]
    for i in range(len(sql_list)):

        sql = os.path.normpath(sql_list[i])
        try:
            _result = get_case_result(sql, variables, frequency, alike, start_date, end_date)
            validSql.append(sql)
            _result = np.array([calculator(data_series) for data_series in np.array(_result.data).T])
            group_result.append(_result)
        except Exception as e:
            print(e)
            continue
        bar(i, len(sql_list), 1)
        print('Case Summary:', sql,end='')

    print()
    group_result = np.array(group_result)
    if len(group_result.shape)==3:
        # case * freq * variables
        newGR = []
        for i in range(group_result.shape[2]):
            newGR.append(group_result[:, :, i].reshape(group_result.shape[0], group_result.shape[1]).T)
        # variables * freq * case
        group_result = np.array(newGR)
    else:
        # case * freq => freq * case
        group_result = np.array(group_result).T
        variables = [str(i) for i in range(group_result.shape[0])]

    if dump_path is not None and os.path.isfile(dump_path):
        np.save(dump_path, group_result)
        np.save(dump_path[:-4] + '_variables.npy', variables)
        group_result = dump_path
    return IDFResult(variables, frequency, group_result, validSql)
def get_case_result(sql: str, variables: Variable, frequency=Monthly,
                    alike=False, start_date=None, end_date=None, dump_path=None):
    """
    Retrieve simulation results for a given SQL query and variable, optionally saving to disk.
    
    Parameters
    ----------
    sql : str
        Path to the SQL file containing simulation output.
    variables : Variable
        The variable(s) to extract from the SQL result. If a single Variable is provided,
        it will be converted to a list.
    frequency : type, optional
        Time frequency of the data (e.g., Monthly, Hourly). Default is Monthly.
    alike : bool, optional
        If True, allows approximate matches for variable names. Default is False.
    start_date : str or datetime, optional
        Start date for filtering results. Default is None.
    end_date : str or datetime, optional
        End date for filtering results. Default is None.
    dump_path : str, optional
        If provided, saves the result array and variables to the specified .npy file path.
        The result returned will be the path string. Default is None.
    
    Returns
    -------
    IDFResult or str or None
        An IDFResult object containing the variables, frequency, and result data if successful.
        If no results are found, returns None. If dump_path is specified and file is saved,
        returns the dump_path as a string.
    """
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
    return IDFResult(variables, frequency, result,[sql])


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
