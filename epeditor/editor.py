from __future__ import annotations

import sys

import eppy
import numpy as np
import os,re,inspect
from .generator import Generator, original,enumerate
from eppy.modeleditor import IDF
from .simulator import simulate_local, find_sql
from .reader import Working_Dir, Variable, get_results, get_group_result, get_case_result
from .utils import *


class IDFsearchresult:
    '''
        不能自动读取class和name，太气人了
        用于打包搜索结果，也是IDFEditor的基类
        obj: idfobj
        idfclass: idf类型，可被自动读取
        name: 对象名称，可被自动读取
        field: 搜索/修改的field名称，可为空; 定义为IDFEditor时必须填写
    '''

    __slots__ = ['obj', 'idfclass', 'name', 'field', 'value']

    def __init__(self, obj: eppy.bunch_subclass.EpBunch, idfclass: str = None, name: str = None, field=None):
        if idfclass is None:
            idfclass = obj.fieldvalues[0]
        if name is None:
            name = obj.fieldvalues[1]
        self.name = name
        self.idfclass = idfclass
        self.obj = obj
        if field is not None:
            self.field = field
            self.value = self.obj[self.field]
        else:
            self.field = ''
            self.value = ''

    def __repr__(self):
        res = '\n'+self.__class__.__name__
        res += '\n|\tClass: ' + self.idfclass
        res += ',\tName: ' + self.name
        res += '\n|\tField: ' + self.field
        res += ',\tValue: ' + str(self.value)
        return res

    def referred_object(self,field,obj=False):
        if isinstance(field,int):
            field = self.obj.fieldnames[field]
        ref_obj = self.obj.get_referenced_object(field)
        if ref_obj:
            if obj:
                return IDFsearchresult(ref_obj)
            else:
                return '>'.join([ref_obj.fieldvalues[0],ref_obj.fieldvalues[1]])
        else:
            return None

    def referred_list(self,obj=False):
        ref_list=[]
        for i in range(2,len(self.obj.fieldnames)):
            field = self.obj.fieldnames[i]
            if 'type' in self.obj.getfieldidd(field):
                if self.obj.getfieldidd(field)['type']==['object-list']:
                    ref_result = self.referred_object(field,obj)
                    if ref_result and (ref_result not in ref_list):
                        ref_list.append(ref_result)
        return ref_list

    def equal(self,others):
        if self.idfclass == others.idfclass and self.name == others.name and self.field == others.field:
            return True
        else:
            return False


class IDFEditor(IDFsearchresult):
    '''
        默认每次调参都建立在search之上
        sampler: 调参方法，限定为generator类型； 所有sampler被归档于sampler
        args: sampler用到的函数args
        params: 采样出来的参数
    '''
    __slots__ = ['sampler', 'args', 'params']

    def __init__(self, object, field=None, _sampler: Generator = original, args: list = None):
        searchresult=object
        if isinstance(searchresult,eppy.bunch_subclass.EpBunch):
            searchresult=IDFsearchresult(searchresult,field=field)
        if searchresult.field is None or searchresult.field == '':
            if field is None:
                raise NotFoundError('IDFEditor(): Field is empty')
            elif field not in searchresult.obj.fieldnames:
                raise NotFoundError(f'IDFEditor(): Field not found in {searchresult.idfclass} {searchresult.name}')
        if field is not None:
                searchresult.field = field
        super(IDFEditor, self).__init__(searchresult.obj, idfclass=searchresult.idfclass, name=searchresult.name,
                                        field=searchresult.field)
        self.sampler = _sampler
        if args is None:
            args = [self.value,1]
        self.args = args
        self.params = []
        self.generate()

    @classmethod
    def from_idfobject(cls, obj: eppy.bunch_subclass.EpBunch, field: str, _sampler: Generator = original,
                       args: list = None):
        editor = IDFsearchresult(obj, field=field)
        editor = cls(editor, _sampler=_sampler, args=args)
        return editor

    @classmethod
    def eval(cls,model, editorstr:str,_sampler: Generator = original,args: list = None):
        editorstr=editorstr.split('>')
        editor = model.eval(editorstr[0],editorstr[1],editorstr[2])
        editor = cls(editor, _sampler=_sampler, args=args)
        return editor

    @classmethod
    def load(cls,model,editorpath:str):
        with open(editorpath,'r') as f:
            text = [line.strip('\n') for line in f.readlines()]
            editorstr = text[0]
            sampler = Generator.from_py(os.path.join(os.path.dirname(editorpath),text[1]))
            args = eval(text[2])
            return cls.eval(model,editorstr,sampler,args)

    def save(self,editorpath:str):
        sampler_path='smp_'+generate_code(6)+'.py'
        self.sampler.run_to_py(os.path.join(os.path.dirname(editorpath),sampler_path))
        editorstr = '>'.join([self.idfclass,self.name,self.field])
        args = str(self.args)
        with open(editorpath,'w+') as f:
            f.write(editorstr + '\n')
            f.write(sampler_path + '\n')
            f.write(args + '\n')



    def generate(self):
        self.params = []
        for param in self.sampler.run(*self.args):
            try:
                if self.obj.getrange(self.field)['maximum'] is not None or self.obj.getrange(self.field)['minimum'] is not None:
                    if param < self.obj.getrange(self.field)['minimum'] or param < self.obj.getrange(self.field)['maximum']:
                        print(f'**********Warning: parameters out of range: {self.idfclass}=>{self.name}=>{self.field},value={param}')
                        continue
            except:
                print(f'**********Warning: parameters maybe not valid: {self.idfclass}=>{self.name}=>{self.field},value={param}')
            self.params.append(param)

    def apply_generator(self, _sampler: Generator, args: list):
        self.sampler = _sampler
        self.args = args
        self.generate()

    def __str__(self):
        res = super(IDFEditor, self).__repr__()
        res += '\n|\tGenerator: ' + self.sampler.name
        res += ',\targs: ' + str(self.args)
        res += '\n|\tparams: ' + str(self.params)
        return res

    def __repr__(self):
        res = self.__class__.__name__
        res += ' : Class:' + self.idfclass
        res += ' > Name:' + self.name
        res += ' > Field:' + self.field
        return res


class IDFGroupEditor:
    '''
        由单个或多个IDFEditor组成，单个GroupEditor内参数为一对一关系，!!按照params最短者处理!!
        IDFGroupEditor之间在导出时会交叉(cross product),例如：
        IDFGroupEditor[0]有30组params，IDFGroupEditor[1]有40组params，则会生成1200个idf文件！
    '''
    __slots__ = ['editors', 'params_num','name']

    def __init__(self, *editors: IDFEditor):
        for edit in editors:
            edit.generate()
        min_params = np.min([len(edit.params) for edit in editors])
        for edit in editors:
            edit.params = edit.params[:min_params]
        self.editors=editors
        self.params_num = min_params
        self.name = generate_code(4)

    @classmethod
    def group(cls, *editors):
        cross_mode = False
        for edit in editors:
            if not isinstance(edit,IDFEditor):
                cross_mode = True

        if cross_mode:
            geditor=[]
            for i in range(len(editors)):
                if isinstance(editors[i], IDFEditor):
                    geditor.append(cls(editors[i]))
                elif isinstance(editors[i],list):
                    geditor.append(cls(*editors[i]))
                elif isinstance(editors[i],IDFGroupEditor):
                    geditor.append(editors[i])
            for i in range(1,len(geditor)):
                geditor[0]=cls.cross(geditor[0],geditor[i])
            return geditor[0]
        else:
            return cls(*editors)

    @classmethod
    def cross(cls,geditor1,geidtor2):
        for edit in geditor1.editors:
            edit.params = np.repeat([edit.params], geidtor2.params_num, axis=0).flatten()
        for edit in geidtor2.editors:
            edit.params = np.repeat(edit.params, geditor1.params_num)
        geditor1.editors += geidtor2.editors
        geditor1.params_num *= geidtor2.params_num
        return geditor1

    @classmethod
    def merge(cls,geditor1,geditor2):
        if isinstance(geditor1,IDFEditor):
            geditor1=IDFGroupEditor(geditor1)
        if isinstance(geditor2,IDFEditor):
            geditor2=IDFGroupEditor(geditor2)
        geditor = cls(*(list(geditor1.editors) + list(geditor2.editors)))
        return geditor

    def drop(self,*editorStr):
        delId=[]
        for _str in editorStr:
            _str = _str.split('>')
            for i in range(len(self.editors)):
                edit = self.editors[i]
                if edit.idfclass == _str[0] and edit.name == _str[1] and edit.field == _str[2]:
                    delId.append(i)
                    break
        self.editors = np.delete(self.editors,delId).tolist()


    def editorSeries(self):
        return [' > '.join([edit.idfclass,edit.name,edit.field]) for edit in self.editors]

    def __repr__(self):
        return self.__class__.__name__ + '\tEditors: ' + str(len(self.editors)) + '\tParamters: ' + str(self.params_num)

    def __str__(self):
        return '\n'.join(
            ['_' * 20] + [self.__class__.__name__ + '\tParamters: ' + str(self.params_num)] + [edit.__str__() for edit
                                                                                               in self.editors] + [
                '_' * 20])



    def to_csv(self, csv_path):
        cols = np.array(
            [['>'.join([edit.idfclass,edit.name,edit.field])] + [str(para) for para in edit.params] for edit in self.editors])
        rows = [','.join(row) for row in cols.T]
        with open(csv_path, 'w+') as f:
            f.write('\n'.join(rows))

    def to_npy(self, npy_path):
        cols = np.array(
            [['>'.join([edit.idfclass,edit.name,edit.field])] + [str(para) for para in edit.params] for edit in self.editors])
        np.save(npy_path, cols.T)

    def to_numpy(self):
        return np.array(
            [['>'.join([edit.idfclass, edit.name, edit.field])] + [str(para) for para in edit.params] for edit in
             self.editors]).T

    @classmethod
    def load(cls, model, geditorpath:str):
        sheet=[]
        if geditorpath[-4:]=='.csv' or geditorpath[-4:]=='ged':
            with open (geditorpath,'r') as f:
                sheet=np.array([line.strip('\n').split(',') for line in f.readlines()]).T
        elif geditorpath[-4:]=='.npy':
            sheet=np.load(geditorpath).T
        editors=[]
        for _var in sheet:
            edit = IDFEditor.eval(model,_var[0])
            edit.apply_generator(enumerate,[_var[1:]])
            editors.append(edit)
        return cls(*editors)

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
    __slots__ = ['objectdict','references', 'file_name', 'idd', 'folder', 'sql', 'variables']

    def __init__(self, idf_file=None, epw=None, idd=None, folder=None):
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
            self.variables:dict | None = None
        if idf_file is None:
            return
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
        res = self.file_name + '\n'
        res += 'BASELINE VERSION:' + str(self.idfobjects['VERSION'][0]['Version_Identifier'])
        return res

    def __str__(self):
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

    def changeValue(self,idfclass,name,field,value):
        obj=None
        for objNum in range(len(self.idfobjects[idfclass])):
            if name == self.idfobjects[idfclass][objNum].fieldvalues[1]:
                self.idfobjects[idfclass][objNum][field] = value
                obj = self.idfobjects[idfclass][objNum]
                break
        if obj:
            try:
                if not obj.checkrange(field):
                    print(f'*********RangeError:{idfclass}=>{name}=>{field},value = {value}')
                    return 2 # exceed
            except:
                pass
            return 1 # success
        else:
            print(f'*********NotFoundError:{idfclass}=>{name}=>{field},value = {value}')
            return 0 # notfound
    def search_object(self, search_name: list, searchresult: list):
        for _name in search_name:
            for key in self.objectdict.keys():
                for i in range(len(self.objectdict[key])):
                    if re.search(normal_pattern(_name), self.objectdict[key][i], re.IGNORECASE) is not None:
                        searchresult.append(IDFsearchresult(self.idfobjects[key][i], key, self.objectdict[key][i]))
        searchresult = np.array(searchresult)[np.argsort([len(item.name) for item in searchresult])]
        return searchresult.tolist()

    def search_class(self, search_name: list, searchresult: list):
        for _name in search_name:
            for key in self.objectdict.keys():
                if re.search(normal_pattern(_name), key, re.IGNORECASE) is not None:
                    for i in range(len(self.objectdict[key])):
                        searchresult.append(IDFsearchresult(self.idfobjects[key][i], key, self.objectdict[key][i]))
        searchresult = np.array(searchresult)[np.argsort([len(item.idfclass) for item in searchresult])]
        return searchresult.tolist()

    def search_field(self, search_name: list, searchresult: list):
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

    def eval(self, idfclass: str = None, idfname: str = None, field: str = None, strict:bool = True):
        searchresult=[]
        if strict:
            if not idfclass:
                return searchresult
            if(len(self.idfobjects[idfclass]))==0:
                raise NotFoundError(f'eval(): Class not found:{idfclass}')
            if not idfname:
                return [IDFsearchresult(obj) for obj in self.idfobjects[idfclass]]
            searchresult =[IDFsearchresult(epbunch) for epbunch in self.idfobjects[idfclass] if re.fullmatch(normal_pattern(idfname),IDFsearchresult(epbunch).name,re.IGNORECASE)]
            if(len(searchresult))==0:
                raise NotFoundError(f'eval(): Object not found:{idfclass} {idfname}')
            searchresult=searchresult[0]
            if field:
                field=re.sub(' ','_',field)
                if field not in searchresult.obj.fieldnames:
                    raise NotFoundError(f'eval(): Field not found:{idfclass} {idfname} {field}')
                return IDFsearchresult(searchresult.obj,field=field)
            else:
                return searchresult
        else:
            if idfclass:
                searchresult = self.search_class([idfclass],[])
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

    def write(self, group_editor, folder: str = None):
        if type(group_editor) == IDFEditor:
            group_editor = IDFGroupEditor(group_editor)
        if type(group_editor) == list:
            for i in range(1, len(group_editor)):
                group_editor[0] = IDFGroupEditor.cross(group_editor[0],group_editor[i])
            group_editor = group_editor[0]

        if folder is None:
            folder = self.file_name[:-4]
        self.folder = folder
        if not os.path.exists(folder):
            os.mkdir(folder)
        for pNum in range(group_editor.params_num):
            success=1
            for edit in group_editor.editors:
                # edit.obj[edit.field] = edit.params[i]
                # self.eval(edit.idfclass, edit.name).obj= edit.params[i]
                success *= self.changeValue(edit.idfclass, edit.name,edit.field, edit.params[pNum])
            if success == 0:
                continue
            if success == 2:
                print(f'******Warring raised on case {pNum}')
            idf_path = os.path.basename(self.file_name)[:-4] + '_' + str(pNum) + '.idf'
            self.save(os.path.join(folder, idf_path))
            print(f'\rWriting idf: remained tasks....{group_editor.params_num - pNum - 1}',end='')

    def simulation(self, epw, overwrite=True, process_count=4,stdout=sys.stdout, **kwargs):
        if self.folder is None:
            raise Exception('You should play IDFModel.write() first before simulation')
        else:
            simulate_local(self.folder,
                           epw=epw,
                           idd=self.idd,
                           overwrite=overwrite,
                           prs_count=process_count,
                           stdout=stdout,
                           **kwargs)
        self.read_folder()

    def read_folder(self, folder: str = None):
        if folder is not None:
            self.folder = folder
        self.sql = find_sql(self.folder)
        Working_Dir = os.path.join(self.folder, 'result')
        if not os.path.exists(Working_Dir):
            os.mkdir(Working_Dir)
        self.variables = get_variables(list(self.sql.values())[0])

    def group_result(self, variable: Variable, calculator, frequency=Monthly, cases=None,
                     alike=False, start_date=None, end_date=None):
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
        return get_group_result(sql_list, variable, calculator, frequency, alike, start_date,
                                end_date)

    def case_result(self, variable: Variable, case: int, frequency=Monthly,
                    alike=False, start_date=None, end_date=None):
        all_result=[]
        if not isinstance(case,list):
            case=[case]
        for _case in case:
            if isinstance(_case,int):
                _case = os.path.basename(self.file_name)[:-4] + '_' + str(_case)
            all_result.append(get_case_result(self.sql[_case], variable, frequency, alike, start_date, end_date))
        return all_result

    def variables_to_file(self,file_path:str):
        strr = ''
        for key in self.variables:
            strr += key +'\n'
            for item in self.variables[key]:
                strr += item  +'\n'
        with open(file_path, 'w+') as f:
            f.write(strr)

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
