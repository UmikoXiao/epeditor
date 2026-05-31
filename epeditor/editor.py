from __future__ import annotations

import eppy
import numpy as np
from eppy.modeleditor import IDF
from .processor import IDFEditor, IDFGroupEditor, IDFsearchresult
from .reader import get_group_result, get_case_result, get_group_summary
from .simulator import simulate_local, find_sql, simulate_cloud
from .utils import *


class IDFModel(IDF):
    """Enhanced IDF model wrapper for batch editing and simulation workflows."""
    __slots__ = ['objectdict', 'references', 'file_name', 'idd', 'folder', 'sql', 'variables']

    def __init__(self, idf_file=None, epw=None, idd=None, folder=None):

        """
          init  .
        
        Parameters
        ----------
        idf_file : Any
            Input parameter `idf_file`.
        
        epw : Any
            Input parameter `epw`.
        
        idd : Any
            Input parameter `idd`.
        
        folder : Any
            Input parameter `folder`.
        
        Returns
        -------
        None
            Return value from `__init__`.
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
        remove_chinese_characters(idf_file)

        self.file_name = os.path.normpath(idf_file)
        self.objectdict = {}
        self.references = {}

        if idd is None:
            idd = get_idd(idf_file)

        self.idd = idd
        IDF.setiddname(idd)
        super(IDFModel, self).__init__(idf_file, epw=epw)
        self.get_objectdict()

    def __repr__(self):
        """
          repr  .
        
        Returns
        -------
        Any
            Return value from `__repr__`.
        """
        res = self.file_name + '\n'
        res += 'BASELINE VERSION:' + str(self.idfobjects['VERSION'][0]['Version_Identifier'])
        return res

    def __str__(self):
        """
          str  .
        
        Returns
        -------
        Any
            Return value from `__str__`.
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
        Get objectdict.
        
        Returns
        -------
        Any
            Return value from `get_objectdict`.
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
        Search.
        
        Parameters
        ----------
        searchname : str
            Input parameter `searchname`.
        
        strict : Any
            Input parameter `strict`.
        
        searchlist : Any
            Input parameter `searchlist`.
        
        searchtype : Any
            Input parameter `searchtype`.
        
        Returns
        -------
        Any
            Return value from `search`.
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
        Eval.
        
        Parameters
        ----------
        idfclass : str
            Input parameter `idfclass`.
        
        idfname : str
            Input parameter `idfname`.
        
        field : str
            Input parameter `field`.
        
        strict : bool
            Input parameter `strict`.
        
        Returns
        -------
        Any
            Return value from `eval`.
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
        Changevalue.
        
        Parameters
        ----------
        idfclass : Any
            Input parameter `idfclass`.
        
        name : Any
            Input parameter `name`.
        
        field : Any
            Input parameter `field`.
        
        value : Any
            Input parameter `value`.
        
        Returns
        -------
        Any
            Return value from `changeValue`.
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
                    return 2
            except:
                pass
            return 1
        else:
            print(f'*********NotFoundError:{idfclass}=>{name}=>{field},value = {value}')
            return 0

    def search_object(self, search_name: list, searchresult: list):
        """
        Search object.
        
        Parameters
        ----------
        search_name : list
            Input parameter `search_name`.
        
        searchresult : list
            Input parameter `searchresult`.
        
        Returns
        -------
        Any
            Return value from `search_object`.
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
        Search class.
        
        Parameters
        ----------
        search_name : list
            Input parameter `search_name`.
        
        searchresult : list
            Input parameter `searchresult`.
        
        Returns
        -------
        Any
            Return value from `search_class`.
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
        Search field.
        
        Parameters
        ----------
        search_name : list
            Input parameter `search_name`.
        
        searchresult : list
            Input parameter `searchresult`.
        
        Returns
        -------
        Any
            Return value from `search_field`.
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
        Search in result.
        
        Parameters
        ----------
        search_name : list
            Input parameter `search_name`.
        
        searchresult : list
            Input parameter `searchresult`.
        
        searchtype : Any
            Input parameter `searchtype`.
        
        Returns
        -------
        Any
            Return value from `search_in_result`.
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
        Write.
        
        Parameters
        ----------
        group_editor : Any
            Input parameter `group_editor`.
        
        folder : str
            Input parameter `folder`.
        
        file_names : Any
            Input parameter `file_names`.
        
        Returns
        -------
        Any
            Return value from `write`.
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
                success *= self.changeValue(edit.idfclass, edit.name, edit.field, edit.params[pNum])
            if success == 0:
                continue
            if success == 2:
                print(f'******Warring raised on case {pNum}')
            idf_path = file_names[pNum]
            self.save(os.path.join(folder, idf_path))
            print(f'\rWriting idf: remained tasks....{group_editor.params_num - pNum - 1}', end='')

    def simulation(self, epw, overwrite=True, local=True, process_count=4, stdout=sys.stdout, forceCPU=False, **kwargs):
        """
        Simulation.
        
        Parameters
        ----------
        epw : Any
            Input parameter `epw`.
        
        overwrite : Any
            Input parameter `overwrite`.
        
        local : Any
            Input parameter `local`.
        
        process_count : Any
            Input parameter `process_count`.
        
        stdout : Any
            Input parameter `stdout`.
        
        forceCPU : Any
            Input parameter `forceCPU`.
        
        **kwargs : Any
            Input parameter `**kwargs`.
        
        Returns
        -------
        Any
            Return value from `simulation`.
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
                               forceCPU=forceCPU,
                               **kwargs)
            else:
                simulate_cloud(self.folder,
                               epw=epw,
                               overwrite=overwrite,
                               **kwargs)
        self.read_folder()

    def read_folder(self, folder: str = None):
        """
        Read folder.
        
        Parameters
        ----------
        folder : str
            Input parameter `folder`.
        
        Returns
        -------
        Any
            Return value from `read_folder`.
        """
        if folder is not None:
            self.folder = folder
        self.sql = find_sql(self.folder)
        Working_Dir = os.path.join(self.folder, 'result')
        if not os.path.exists(Working_Dir):
            os.mkdir(Working_Dir)
        self.variables = get_variables(list(self.sql.values())[0])

    def group_result(self, variable: Variable, calculator, frequency=Monthly, cases=None,
                     alike=False, start_date=None, end_date=None, x='variables'):
        """
        Group result.
        
        Parameters
        ----------
        variable : Variable
            Input parameter `variable`.
        
        calculator : Any
            Input parameter `calculator`.
        
        frequency : Any
            Input parameter `frequency`.
        
        cases : Any
            Input parameter `cases`.
        
        alike : Any
            Input parameter `alike`.
        
        start_date : Any
            Input parameter `start_date`.
        
        end_date : Any
            Input parameter `end_date`.
        
        x : Any
            Input parameter `x`.
        
        Returns
        -------
        Any
            Return value from `group_result`.
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
        Case result.
        
        Parameters
        ----------
        variable : Variable
            Input parameter `variable`.
        
        case : int
            Input parameter `case`.
        
        frequency : Any
            Input parameter `frequency`.
        
        alike : Any
            Input parameter `alike`.
        
        start_date : Any
            Input parameter `start_date`.
        
        end_date : Any
            Input parameter `end_date`.
        
        Returns
        -------
        Any
            Return value from `case_result`.
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
        Variables to file.
        
        Parameters
        ----------
        file_path : str
            Input parameter `file_path`.
        
        Returns
        -------
        Any
            Return value from `variables_to_file`.
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
        Diff.
        
        Parameters
        ----------
        model : IDFModel
            Input parameter `model`.
        
        Returns
        -------
        Any
            Return value from `diff`.
        """
        searchresult = []
        for idfclass in self.idfobjects.keys():
            if (not str(idfclass).startswith('OUTPUT')) and (idfclass in model.idfobjects.keys()):
                objls1 = [obj for obj in self.idfobjects[idfclass] if len(obj.fieldvalues) > 2]
                objls2 = [obj for obj in model.idfobjects[idfclass] if len(obj.fieldvalues) > 2]
                if len(objls1) * len(objls2) > 0 and len(objls1) == len(objls2):
                    for i, target_obj in enumerate(self.idfobjects[idfclass]):
                        idfName = str(target_obj.fieldvalues[1])
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
    model.simulation(epw=r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Beijing.Beijing.545110_SWERA.epw')
    model.group_result(Variable("Cumulative", "Electricity:Facility", "J"), np.mean)
    model.case_result(Variable("Cumulative", "Electricity:Facility", "J"), 0)
