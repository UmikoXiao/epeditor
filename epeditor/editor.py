from __future__ import annotations

import eppy
import numpy as np
import os, re, inspect

from eppy.modeleditor import IDF
from .simulator import simulate_local, find_sql,simulate_cloud
from .reader import Variable, get_group_result, get_case_result,get_group_summary
from .processor import IDFEditor, IDFGroupEditor, IDFsearchresult
from .utils import *



class IDFModel(IDF):
    '''
        方便Baseline管理的增强IDF类型，提供更方便的idfobject管理
        objectdict:增强idfobjects方法，方便根据name查阅object
        file_name:记录baseline地址
        folder: 记录导出路径
        sql: 记录结果sql路径
        variables: 记录结果所有的variables

        classmethod:
        get_objectdict() 获取所有idfobjects的dictionary
        search() 增强idfobjects方法，所有search的标准化入口，调用下属三个函数：
        search_object() 增强idfobjects方法，方便直接根据name获取object
        search_class() 增强idfobjects方法，方便直接根据关键词搜索class带该名字的
        search_filed() 增强idfobjects方法，方便直接根据name获取带关键词的field

    '''
    __slots__ = ['objectdict', 'references', 'file_name', 'idd', 'folder', 'sql', 'variables']

    def __init__(self, idf_file=None, epw=None, idd=None, folder=None):
        """
        Initialize an IDFModel instance with optional input files and folder.
        
        Parameters
        ----------
        idf_file : str, optional
            Path to the IDF file. If not provided, the instance will be initialized without an IDF file.
        epw : str, optional
            Path to the EPW weather file. Used for simulations requiring weather data.
        idd : str, optional
            Path to the IDD file. If not provided, it will be determined automatically from the IDF file.
        folder : str, optional
            Path to a folder containing an IDF file. If provided, the first file with a '.idf' extension
            in the folder will be used as the `idf_file`, and the folder will be processed.
        
        Returns
        -------
        None
        """

        if folder is not None:
            for dirpath, dirnames, filenames in os.walk(folder):
                for file in filenames:
                    if file[-4:] == '.idf':
                        idf_file = os.path.join(file)
                        break
            self.read_folder(folder)
        else:
            self.folder = None
            self.sql = None
            self.variables: dict | None = None
        if idf_file is None:
            return

        # process utf-8 incompatible issues
        remove_chinese_characters(idf_file)

        self.file_name = os.path.normpath(idf_file)
        self.objectdict = {}
        self.references = {}

        if idd is None:
            idd = get_idd(idf_file)

        self.idd = idd
        IDF.setiddname(idd)
        super(IDFModel, self).__init__(idf_file, epw=epw)
        self.get_objectdict()  # 获取obj列表，方便查询

    def __repr__(self):
        """
        Return a string representation of the object including file name and baseline version.
        
        Parameters
        ----------
        self : object
            The instance of the class containing `file_name` and `idfobjects` attributes. 
            `file_name` is expected to be a string representing the file name, and 
            `idfobjects` should be a dictionary containing at least a 'VERSION' key with 
            a list of objects, each having a 'Version_Identifier' field.
        
        Returns
        -------
        str
            A formatted string containing the file name followed by the baseline version identifier.
        """
        res = self.file_name + '\n'
        res += 'BASELINE VERSION:' + str(self.idfobjects['VERSION'][0]['Version_Identifier'])
        return res

    def __str__(self):
        """
        Return a string representation of the object with details on file, version, and associated data.
        
        Parameters
        ----------
        self : object
            The instance of the class containing attributes such as file_name, idfobjects, idd, folder, sql, and variables.
        
        Returns
        -------
        str
            A formatted string containing the file name, baseline version identifier, IDD version, 
            optional folder path, SQL connection info (if available), and variable names (if present).
        """
        res = self.file_name + '\n'
        res += 'BASELINE VERSION:' + str(self.idfobjects['VERSION'][0]['Version_Identifier']) + '\n'
        res += 'idd:' + self.idd + '\n'
        if self.folder:
            res += 'folder:' + self.folder + '\n'
            res += 'sql:'
        if self.sql:
            res += str(list(self.sql.keys())[0]) + ':' + str(list(self.sql.values())[0]) + '...'
        if self.variables:
            res += '\nvariables:'
            res += list(self.variables.keys())[0].__repr__() + '...'
        return res

    def get_objectdict(self):
        """
        Build a dictionary of object identifiers from IDF objects.
        
        Parameters
        ----------
        self : object
            The instance of the class containing `idfobjects` and `objectdict` attributes.
            `idfobjects` is expected to be a dictionary where keys are class strings and
            values are lists of objects with dictionary-like values. The method modifies
            `self.objectdict` in place and returns it.
        
        Returns
        -------
        dict
            A dictionary mapping IDF class names (e.g., 'ZONE', 'MATERIAL') to lists of 
            string identifiers extracted from the second element of the first value in 
            each object's data, except for 'OUTPUT:VARIABLE' objects, which use the third 
            element. Only objects with more than one entry in the first value are included.
        """
        self.objectdict = {}
        for idfclass in self.idfobjects.keys():
            objs = [obj for obj in self.idfobjects[idfclass] if len(list(obj.values())[0]) > 1]
            if len(objs) > 0:
                if idfclass != 'OUTPUT:VARIABLE':
                    self.objectdict[idfclass] = [str(list(obj.values())[0][1]) for obj in objs]
                else:
                    self.objectdict[idfclass] = [str(list(obj.values())[0][2]) for obj in objs]
        return self.objectdict

    def search(self, searchname: str, strict=True, searchlist=None, searchtype=ANYTHING):
        """
        Search for items by name with optional strictness and filtering by type.
        
        Parameters
        ----------
        searchname : str
            The name or names to search for. If `strict` is True, treated as a single name.
            Otherwise, split into multiple names on whitespace.
        strict : bool, optional
            If True, perform exact match on the entire `searchname` string (default is True).
            If False, split `searchname` by spaces and search for each part independently.
        searchlist : list, optional
            A pre-existing list of items to search within. If None, search across all available items
            based on `searchtype` (default is None).
        searchtype : int, optional
            Specifies the type of items to search for. Valid values are ANYTHING, CLASS, OBJECT, or FIELD
            (default is ANYTHING).
        
        Returns
        -------
        list
            A list of items matching the search criteria. If `searchlist` is provided, returns matches
            within that list; otherwise, returns results from searching internal collections.
        """
        if strict:
            searchname = [searchname]
        else:
            searchname = searchname.split(' ')

        if searchlist is None:
            searchlist = []
            if searchtype == ANYTHING or searchtype == CLASS:
                searchlist = self.search_class(searchname, searchlist)
            if searchtype == ANYTHING or searchtype == OBJECT:
                searchlist = self.search_object(searchname, searchlist)
            if searchtype == ANYTHING or searchtype == FIELD:
                searchlist = self.search_field(searchname, searchlist)
        else:
            searchlist = self.search_in_result(searchname, list(searchlist), searchtype)
        return searchlist

    def eval(self, idfclass: str = None, idfname: str = None, field: str = None, strict: bool = True):
        """
        Evaluate and retrieve objects or fields from IDF data based on specified criteria.
        
        Parameters
        ----------
        idfclass : str, optional
            The class name of the IDF object to search for. If not provided and `strict` is True, returns empty list.
        idfname : str, optional
            The name of the specific IDF object to match. Uses case-insensitive regex matching when `strict` is True.
        field : str, optional
            The field name within the IDF object to retrieve. If provided, checks if the field exists in the object.
        strict : bool, default True
            If True, performs strict matching requiring exact class and object existence with error raising on failure.
            If False, performs flexible searching using internal search methods without raising errors for missing items.
        
        Returns
        -------
        list or IDFsearchresult
            If `strict` is True: returns an IDFsearchresult instance (or its subset by field), or raises NotFoundError.
            If `strict` is False: returns a list of matching results from non-strict searches, possibly empty.
        """
        searchresult = []
        if strict:
            if not idfclass:
                return searchresult
            if (len(self.idfobjects[idfclass])) == 0:
                raise NotFoundError(f'eval(): Class not found:{idfclass}')
            if not idfname:
                return [IDFsearchresult(obj) for obj in self.idfobjects[idfclass]]
            searchresult = [IDFsearchresult(epbunch) for epbunch in self.idfobjects[idfclass] if
                            re.fullmatch(normal_pattern(idfname), IDFsearchresult(epbunch).name, re.IGNORECASE)]
            if (len(searchresult)) == 0:
                raise NotFoundError(f'eval(): Object not found:{idfclass} {idfname}')
            searchresult = searchresult[0]
            if field:
                field = re.sub(' ', '_', field)
                if field not in searchresult.obj.fieldnames:
                    raise NotFoundError(f'eval(): Field not found:{idfclass} {idfname} {field}')
                return IDFsearchresult(searchresult.obj, field=field)
            else:
                return searchresult
        else:
            if idfclass:
                searchresult = self.search_class([idfclass], [])
                if idfname:
                    searchresult = self.search_in_result([idfname], searchresult, OBJECT)
                if field:
                    searchresult = self.search_in_result([field], searchresult, FIELD)
            else:
                if idfname:
                    searchresult = self.search_field([idfname], [])
                    if field:
                        searchresult = self.search_in_result([field], searchresult, FIELD)
                else:
                    if field:
                        searchresult = self.search_field([field], [])
        return searchresult

    def changeValue(self, idfclass, name, field, value):
        """
        Change the value of a specified field in an IDF object.
        
        Parameters
        ----------
        idfclass : str
            The class name of the IDF object to be modified.
        name : str
            The name of the object within the specified class to be matched.
        field : int or str
            The field index or name where the value should be updated.
        value : any
            The new value to assign to the specified field.
        
        Returns
        -------
        int
            1 if the value was successfully changed and within range,
            2 if the value is out of valid range (RangeError),
            0 if the object was not found (NotFoundError).
        """
        obj = None
        for objNum in range(len(self.idfobjects[idfclass])):
            if name == self.idfobjects[idfclass][objNum].fieldvalues[1]:
                self.idfobjects[idfclass][objNum][field] = value
                obj = self.idfobjects[idfclass][objNum]
                break
        if obj:
            try:
                if not obj.checkrange(field):
                    print(f'*********RangeError:{idfclass}=>{name}=>{field},value = {value}')
                    return 2  # exceed
            except:
                pass
            return 1  # success
        else:
            print(f'*********NotFoundError:{idfclass}=>{name}=>{field},value = {value}')
            return 0  # notfound

    def search_object(self, search_name: list, searchresult: list):
        """
        Search for objects matching given names within the object dictionary.
        
        Parameters
        ----------
        search_name : list of str
            List of strings representing the names to search for. Each name is used as a pattern in a regular expression search.
        searchresult : list
            List that accumulates the results of the search. It will be populated with `IDFsearchresult` objects during the search process.
        
        Returns
        -------
        list of IDFsearchresult
            A list of `IDFsearchresult` objects sorted by the length of their `name` attribute in ascending order.
        """
        for _name in search_name:
            for key in self.objectdict.keys():
                for i in range(len(self.objectdict[key])):
                    if re.search(normal_pattern(_name), self.objectdict[key][i], re.IGNORECASE) is not None:
                        searchresult.append(IDFsearchresult(self.idfobjects[key][i], key, self.objectdict[key][i]))
        searchresult = np.array(searchresult)[np.argsort([len(item.name) for item in searchresult])]
        return searchresult.tolist()

    def search_class(self, search_name: list, searchresult: list):
        """
        Search for IDF objects matching given names and return sorted results.
        
        Parameters
        ----------
        search_name : list of str
            List of strings representing the names to search for. Each name is used
            as a pattern to match against keys in `self.objectdict` using case-insensitive
            regular expression matching.
        searchresult : list
            List to which found `IDFsearchresult` objects are appended during the search.
            This list is modified in place before being converted to a numpy array and sorted.
        
        Returns
        -------
        list of IDFsearchresult
            A list of `IDFsearchresult` instances corresponding to matched IDF objects,
            sorted by the length of their `idfclass` attribute in ascending order.
        """
        for _name in search_name:
            for key in self.objectdict.keys():
                if re.search(normal_pattern(_name), key, re.IGNORECASE) is not None:
                    for i in range(len(self.objectdict[key])):
                        searchresult.append(IDFsearchresult(self.idfobjects[key][i], key, self.objectdict[key][i]))
        searchresult = np.array(searchresult)[np.argsort([len(item.idfclass) for item in searchresult])]
        return searchresult.tolist()

    def search_field(self, search_name: list, searchresult: list):
        """
        Search for fields in IDF objects matching given names.
        
        Parameters
        ----------
        search_name : list of str
            List of field names to search for; spaces are replaced with underscores.
        searchresult : list
            List to append found IDF search results to; modified in place.
        
        Returns
        -------
        list of IDFsearchresult
            List of IDFsearchresult objects sorted by the length of their field attribute.
        """
        for _name in search_name:
            _name = re.sub(' ', '_', _name)
            for key in self.objectdict.keys():
                for i in range(len(self.objectdict[key])):
                    for field in self.idfobjects[key][i].objls:
                        if re.search(normal_pattern(_name), field, re.IGNORECASE) is not None:
                            searchresult.append(
                                IDFsearchresult(self.idfobjects[key][i], key, self.objectdict[key][i], field=field))
        searchresult = np.array(searchresult)[np.argsort([len(item.field) for item in searchresult])]
        return searchresult.tolist()

    def search_in_result(self, search_name: list, searchresult: list, searchtype):
        """
        Search through a list of results based on specified names and search type.
        
        Parameters
        ----------
        search_name : list
            List of strings to search for; used to match against class, object name, or field.
        searchresult : list
            List of search results, typically containing EpBunch objects or IDFsearchresult instances.
        searchtype : str
            Type of search to perform; expected values are ANYTHING, CLASS, OBJECT, or FIELD, which determine the attribute to match against.
        
        Returns
        -------
        list
            A list of filtered IDFsearchresult objects that match the search criteria. If searching by FIELD, multiple entries per object may be returned.
        """
        searchresult_new = []
        for _result in searchresult:
            if type(_result) == eppy.bunch_subclass.EpBunch:
                _result = IDFsearchresult(_result)
            for _name in search_name:
                if searchtype == ANYTHING or searchtype == CLASS:
                    if re.search(normal_pattern(_name), _result.idfclass, re.IGNORECASE) is not None:
                        searchresult_new.append(_result)
                        break
                if searchtype == ANYTHING or searchtype == OBJECT:
                    if re.search(normal_pattern(_name), _result.name, re.IGNORECASE) is not None:
                        searchresult_new.append(_result)
                        break
                if searchtype == ANYTHING or searchtype == FIELD:
                    _name = re.sub(' ', '_', _name)
                    find = False
                    for field in _result.obj.objls:
                        if re.search(normal_pattern(_name), field, re.IGNORECASE) is not None:
                            _result2 = IDFsearchresult(_result.obj, field=field)
                            searchresult_new.append(_result2)
                            find = True
                    if find: break
        return searchresult_new

    def write(self, group_editor, folder: str = None, file_names=None):
        """
        Write IDF files based on parameter variations defined in a group editor.
        
        Parameters
        ----------
        group_editor : IDFEditor or list of IDFEditor or IDFGroupEditor
            An editor or list of editors defining the parameter changes. If a list is provided,
            cross-product of parameters is computed. If a single IDFEditor is passed, it is
            converted to an IDFGroupEditor.
        folder : str, optional
            Directory path where the generated IDF files will be saved. If not provided,
            defaults to the base name of the current file (without extension).
        file_names : list of str, optional
            List of filenames for the output IDF files. Must match the number of parameter
            combinations. If not provided or incorrect length, default naming is used.
        
        Returns
        -------
        None
            This function does not return any value. It writes IDF files to the specified folder.
        """
        if type(group_editor) == IDFEditor:
            group_editor = IDFGroupEditor(group_editor)
        if type(group_editor) == list:
            for i in range(1, len(group_editor)):
                group_editor[0] = IDFGroupEditor.cross(group_editor[0], group_editor[i])
            group_editor = group_editor[0]

        if folder is None:
            folder = self.file_name[:-4]
        self.folder = folder
        if not os.path.exists(folder):
            os.mkdir(folder)
        if file_names is None:
            file_names = [os.path.basename(self.file_name)[:-4] + '_' + str(pNum) + '.idf' for pNum in
                          range(group_editor.params_num)]
        elif len(file_names) != group_editor.params_num:
            print(f'******Warring not enough file names, renamed default.')
        for pNum in range(group_editor.params_num):
            success = 1
            for edit in group_editor.editors:
                # edit.obj[edit.field] = edit.params[i]
                # self.eval(edit.idfclass, edit.name).obj= edit.params[i]
                success *= self.changeValue(edit.idfclass, edit.name, edit.field, edit.params[pNum])
            if success == 0:
                continue
            if success == 2:
                print(f'******Warring raised on case {pNum}')
            idf_path = file_names[pNum]
            self.save(os.path.join(folder, idf_path))
            print(f'\rWriting idf: remained tasks....{group_editor.params_num - pNum - 1}', end='')

    def simulation(self, epw, overwrite=True,local=True, process_count=4, stdout=sys.stdout,forceCPU=False, **kwargs):
        """
        Run an EnergyPlus simulation either locally or in the cloud.
        
        Parameters
        ----------
        epw : str
            Path to the EPW weather file to be used for the simulation.
        overwrite : bool, optional
            If True, overwrites existing simulation output files. Default is True.
        local : bool, optional
            If True, runs the simulation locally; otherwise, runs it in the cloud. Default is True.
        process_count : int, optional
            Number of processes to use for local simulation. Default is 4.
        stdout : file-like object, optional
            Output stream for logging simulation progress. Default is sys.stdout.
        forceCPU : bool, optional
            If True, forces the simulation to run on CPU even if GPU is available (applies only to local simulation). Default is False.
        **kwargs : dict
            Additional keyword arguments passed to the simulation function.
        
        Returns
        -------
        None
            This function does not return any value. It updates the internal state by reading simulation results from the output folder.
        """
        if self.folder is None:
            raise Exception('You should play IDFModel.write() first before simulation')
        else:
            if local:
                simulate_local(self.folder,
                               epw=epw,
                               idd=self.idd,
                               overwrite=overwrite,
                               prs_count=process_count,
                               stdout=stdout,
                               forceCPU = forceCPU,
                               **kwargs)
            else:
                simulate_cloud(self.folder,
                               epw=epw,
                               overwrite=overwrite,
                               **kwargs)
        self.read_folder()

    def read_folder(self, folder: str = None):
        """
        Read and process SQL files from a specified folder.
        
        Parameters
        ----------
        folder : str, optional
            Path to the folder containing SQL files. If not provided, uses the previously set folder attribute.
        
        Returns
        -------
        None
            This function does not return any value. It updates the instance attributes `folder`, `sql`, and `variables`.
        """
        if folder is not None:
            self.folder = folder
        self.sql = find_sql(self.folder)
        Working_Dir = os.path.join(self.folder, 'result')
        if not os.path.exists(Working_Dir):
            os.mkdir(Working_Dir)
        self.variables = get_variables(list(self.sql.values())[0])

    def group_result(self, variable: Variable, calculator, frequency=Monthly, cases=None,
                     alike=False, start_date=None, end_date=None,x='variables'):
        """
        Group calculation results based on specified cases and parameters.
        
        Parameters
        ----------
        variable : Variable
            The variable object for which the result is calculated.
        calculator : object
            The calculator used to compute results, typically containing computation logic.
        frequency : type, optional
            The frequency of the result grouping (e.g., Monthly). Default is Monthly.
        cases : int, str, list of int/str, or None, optional
            Specific case identifiers to include in the grouping. If None, all cases are used.
            Can be a single int or string, or a list of ints/strings. Default is None.
        alike : bool, optional
            If True, groups results with similar characteristics. Default is False.
        start_date : str or datetime-like, optional
            The start date for filtering results. Default is None.
        end_date : str or datetime-like, optional
            The end date for filtering results. Default is None.
        x : str, optional
            Determines the type of grouping: if 'variables', returns detailed group results;
            otherwise, returns summary statistics. Default is 'variables'.
        
        Returns
        -------
        result : pandas.DataFrame or similar
            The grouped result data, either as detailed results or summary depending on `x`.
        """
        if cases is not None:
            sql_list = []
            if isinstance(cases, int) or isinstance(cases, str):
                cases = [cases]
            for case in cases:
                if type(case) == int:
                    case = os.path.basename(self.file_name)[:-4] + '_' + str(case)
                try:
                    sql_list.append(self.sql[case])
                except:
                    print(f'**********Cases: {case} Not Found')
        else:
            sql_list = list(self.sql.values())
        if x == 'variables':
            return get_group_result(sql_list, variable, calculator, frequency, alike, start_date,
                                    end_date)
        else:
            return get_group_summary(sql_list, variable, calculator, frequency, alike, start_date,
                                    end_date)

    def case_result(self, variable: Variable, case: int, frequency=Monthly,
                    alike=False, start_date=None, end_date=None):
        """
        Retrieve simulation results for specified cases and a given variable.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the method. Expected to have `file_name` and `sql` attributes.
        variable : Variable
            The variable object for which results are to be retrieved.
        case : int or list of int
            The case identifier(s) for which to fetch results. If an integer is provided, it is converted to a single-element list.
            Each case is used to construct a key by appending the case number to the base filename.
        frequency : optional
            The temporal frequency of the data (e.g., Monthly). Default is Monthly.
        alike : bool, optional
            If True, retrieves results with similar characteristics. Default is False.
        start_date : str or datetime-like, optional
            The start date for filtering the results. Default is None.
        end_date : str or datetime-like, optional
            The end date for filtering the results. Default is None.
        
        Returns
        -------
        list
            A list of results corresponding to each case, where each element is the result of `get_case_result` for the given parameters.
        """
        all_result = []
        if not isinstance(case, list):
            case = [case]
        for _case in case:
            if isinstance(_case, int):
                _case = os.path.basename(self.file_name)[:-4] + '_' + str(_case)
            all_result.append(get_case_result(self.sql[_case], variable, frequency, alike, start_date, end_date))
        return all_result

    def variables_to_file(self, file_path: str):
        """
        Save variables to a specified file.
        
        Parameters
        ----------
        file_path : str
            Path to the file where variables will be written.
        
        Returns
        -------
        None
        """
        strr = ''
        for key in self.variables:
            strr += key + '\n'
            for item in self.variables[key]:
                strr += item + '\n'
        with open(file_path, 'w+') as f:
            f.write(strr)

    def diff(self, model: IDFModel):
        """
        Compare IDF objects between two models and return differences.
        
        Parameters
        ----------
        model : IDFModel
            The second IDF model to compare against the current instance. 
            It should have an `idfobjects` attribute containing the objects to compare.
        
        Returns
        -------
        list of IDFsearchresult
            A list of IDFsearchresult objects representing the differences found 
            between corresponding IDF objects in the two models. Each entry includes 
            information about the differing object, class, name, and field.
        """
        searchresult = []
        for idfclass in self.idfobjects.keys():
            if (not str(idfclass).startswith('OUTPUT')) and (idfclass in model.idfobjects.keys()):
                objls1 = [obj for obj in self.idfobjects[idfclass] if len(obj.fieldvalues) > 2]
                objls2 = [obj for obj in model.idfobjects[idfclass] if len(obj.fieldvalues) > 2]
                if len(objls1) * len(objls2) > 0 and len(objls1) == len(objls2):  # same num of obj
                    for i, target_obj in enumerate(self.idfobjects[idfclass]):
                        idfName = str(target_obj.fieldvalues[1])
                        # print(f"{idfclass}>{idfName}")
                        for fNum, field in enumerate(target_obj.objls):
                            if fNum < len(model.idfobjects[idfclass][i].fieldvalues):
                                if target_obj.fieldvalues[fNum] != model.idfobjects[idfclass][i].fieldvalues[fNum]:
                                    searchresult.append(
                                        IDFsearchresult(self.idfobjects[idfclass][i], idfclass, idfName, field=field)
                                    )
                elif len(objls1) * len(objls2) > 0:
                    for i, target_obj in enumerate(self.idfobjects[idfclass]):
                        idfName = str(target_obj.fieldvalues[1])
                        print(f"{idfclass}>{idfName},Different Num of objs.")
                        for j, diff_obj in enumerate(model.idfobjects[idfclass]):
                            if re.match(normal_pattern(idfName), str(diff_obj.fieldvalues[1]),
                                        re.IGNORECASE) is not None:
                                for field in target_obj.objls:
                                    if target_obj[field] != diff_obj[field]:
                                        searchresult.append(
                                            IDFsearchresult(self.idfobjects[idfclass][i], idfclass, idfName,
                                                            field=field)
                                        )
                                break
        return searchresult


if __name__ == '__main__':
    model = IDFModel(r'project\baseline.idf',
                     epw=r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Beijing.Beijing.545110_SWERA.epw')
    result = model.search('area', searchtype=FIELD)
    # editor1 = IDFEditor(result[0], _sampler=sampler['random'], args=[100, 200, 10])
    # editor2 = IDFEditor.from_idfobject(model.idfobjects['ZONE'][1], 'Floor_Area', _sampler=sampler['random'],
    #                                   args=[110, 230, 8])
    # editor3 = IDFEditor.from_idfobject(model.idfobjects['ZONE'][0], 'Volume', sampler=sampler['random'],
    #                                   args=[110, 230, 12])
    # editor4 = IDFEditor.from_idfobject(model.idfobjects['ZONE'][1], 'Volume', sampler=sampler['random'],
    #                                   args=[110, 230, 8])
    # geditor=IDFGroupEditor(editor1 , editor2).cross(IDFGroupEditor(editor3, editor4))
    # geditor = IDFGroupEditor(editor1, editor2)
    # geditor.to_csv('test.csv')
    # model.write(geditor, r'test')
    model.simulation(epw=r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Beijing.Beijing.545110_SWERA.epw')
    model.group_result(Variable("Cumulative", "Electricity:Facility", "J"), np.mean)
    model.case_result(Variable("Cumulative", "Electricity:Facility", "J"), 0)
