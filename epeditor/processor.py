from __future__ import annotations

import eppy
import numpy as np
from .generator import Generator, original,enumerate
from .utils import *
import re


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
        """
        Initialize an object with EpBunch data and optional class, name, and field attributes.
        
        Parameters
        ----------
        obj : eppy.bunch_subclass.EpBunch
            The EpBunch object containing the underlying data.
        idfclass : str, optional
            The IDF class name; if not provided, defaults to the first value in obj.fieldvalues.
        name : str, optional
            The name of the object; if not provided, defaults to the second value in obj.fieldvalues.
        field : str, optional
            The field name to extract a value from the object; if not provided, field and value are set to empty strings.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
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
        """
        Return a string representation of the object with class name, IDf class, name, field, and value.
        
        Parameters
        ----------
        self : object
            The instance of the class being represented. Contains attributes `idfclass`, `name`, `field`, and `value`.
        
        Returns
        -------
        str
            A formatted string containing the class name, idfclass, name, field, and value of the object.
        """
        res = '\n'+self.__class__.__name__
        res += '\n|\tClass: ' + self.idfclass
        res += ',\tName: ' + self.name
        res += '\n|\tField: ' + self.field
        res += ',\tValue: ' + str(self.value)
        return res

    def referred_object(self,field,obj=False):
        """
        Return the referenced object or its identifier based on a field.
        
        Parameters
        ----------
        field : int or str
            The field index or name referencing the object.
        obj : bool, optional
            If True, return an IDFsearchresult instance; otherwise, return a string 
            representation of the referenced object's first two field values joined by '>'.
            Default is False.
        
        Returns
        -------
        IDFsearchresult or str or None
            If a referenced object exists and `obj` is True, returns an IDFsearchresult 
            instance. If `obj` is False, returns a string formed by joining the first two 
            field values of the referenced object with '>'. Returns None if no referenced 
            object is found.
        """
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
        """
        Return a list of referenced objects from object-list fields.
        
        Parameters
        ----------
        obj : bool, optional
            If True, return detailed object information; otherwise, return only the reference names.
            Default is False.
        
        Returns
        -------
        list
            A list of unique referenced objects or their identifiers, based on the 'object-list' 
            field types in the object's fieldnames. Returns an empty list if no references are found.
        """
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
        """
        Check if two objects are equal based on idfclass, name, and field attributes.
        
        Parameters
        ----------
        others : object
            Another object to compare with. Must have attributes `idfclass`, `name`, and `field`.
        
        Returns
        -------
        bool
            True if all compared attributes (idfclass, name, field) are equal, otherwise False.
        """
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
        """
        Initialize the IDFEditor object with an object and optional field, sampler, and arguments.
        
        Parameters
        ----------
        object : object
            The input object to be edited, which can be an EpBunch instance or another compatible type.
        field : str, optional
            The specific field within the object to edit. If not provided, must be specified in the object or will raise an error.
        _sampler : Generator, default=original
            The random number generator or sampling method used for value generation.
        args : list, optional
            A list of arguments passed to the generator function. Defaults to [self.value, 1] if not provided.
        
        Returns
        -------
        None
            This constructor does not return a value; it initializes the instance attributes.
        """
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
        """
        Create an editor instance from an IDF object using a specified field and sampler.
        
        Parameters
        ----------
        obj : eppy.bunch_subclass.EpBunch
            The IDF object (EpBunch) to be searched and edited.
        field : str
            The field name within the IDF object to target for editing.
        _sampler : Generator, optional
            A generator function used for sampling values; defaults to `original`.
        args : list, optional
            Additional arguments passed to the editor constructor; defaults to None.
        
        Returns
        -------
        editor : cls
            An instance of the class initialized with the IDF search result and provided options.
        """
        editor = IDFsearchresult(obj, field=field)
        editor = cls(editor, _sampler=_sampler, args=args)
        return editor

    @classmethod
    def eval(cls,model, editorstr:str,_sampler: Generator = original,args: list = None):
        """
        Evaluate and return an editor object based on the provided model and string specification.
        
        Parameters
        ----------
        cls : type
            The class calling this method, used for creating an instance of the class.
        model : object
            The model used to evaluate the initial editor configuration. Must have an `eval` method.
        editorstr : str
            A string containing three parts separated by '>', which are passed to the model's `eval` method.
        _sampler : numpy.random.Generator, optional
            Random number generator to be used internally. Defaults to `original`.
        args : list, optional
            Additional arguments to be passed to the editor constructor. Defaults to None.
        
        Returns
        -------
        object
            An instance of the class initialized with the evaluated editor, sampler, and arguments.
        """
        editorstr=editorstr.split('>')
        editor = model.eval(editorstr[0],editorstr[1],editorstr[2])
        editor = cls(editor, _sampler=_sampler, args=args)
        return editor

    @classmethod
    def load(cls,model,editorpath:str):
        """
        Load a generator from a saved configuration file.
        
        Parameters
        ----------
        cls : type
            The class calling this method (used for constructing instances).
        model : object
            The model used in evaluation for generating the instance.
        editorpath : str
            Path to the file containing the editor string, sampler filename, and arguments.
        
        Returns
        -------
        object
            An instance created by evaluating the model with the loaded editor string, sampler, and arguments.
        """
        with open(editorpath,'r') as f:
            text = [line.strip('\n') for line in f.readlines()]
            editorstr = text[0]
            sampler = Generator.from_py(os.path.join(os.path.dirname(editorpath),text[1]))
            args = eval(text[2])
            return cls.eval(model,editorstr,sampler,args)

    def save(self,editorpath:str):
        """
        Save the current object state to a file.
        
        Parameters
        ----------
        editorpath : str
            The file path where the editor data will be saved.
        
        Returns
        -------
        None
        """
        sampler_path='smp_'+generate_code(6)+'.py'
        self.sampler.run_to_py(os.path.join(os.path.dirname(editorpath),sampler_path))
        editorstr = '>'.join([self.idfclass,self.name,self.field])
        args = str(self.args)
        with open(editorpath,'w+') as f:
            f.write(editorstr + '\n')
            f.write(sampler_path + '\n')
            f.write(args + '\n')



    def generate(self):
        """
        Generate a list of sampled parameters with optional range validation.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the method. Must have attributes `sampler`, `args`, `obj`, `field`, `idfclass`, `name`, and `params`.
            `sampler` should have a `run` method that yields parameter values.
            `obj.getrange(field)` should return a dictionary with 'minimum' and 'maximum' keys defining valid parameter bounds.
        
        Returns
        -------
        None
            The generated parameters are stored in `self.params` as a list. Invalid or out-of-range parameters are skipped with a warning message.
        """
        self.params = []
        for param in self.sampler.run(*self.args):
            try:
                if self.obj.getrange(self.field)['maximum'] is not None or self.obj.getrange(self.field)['minimum'] is not None:
                    if param < self.obj.getrange(self.field)['minimum'] or param < self.obj.getrange(self.field)['maximum']:
                        print(f'**********Warning: parameters out of range: {self.idfclass}=>{self.name}=>{self.field},value={param}')
                        continue
            except:
                pass
                # print(f'**********Warning: parameters maybe not valid: {self.idfclass}=>{self.name}=>{self.field},value={param}')
            self.params.append(param)

    def apply_generator(self, _sampler: Generator, args: list):
        """
        Apply a generator function with given arguments.
        
        Parameters
        ----------
        _sampler : Generator
            A generator object to be applied.
        args : list
            A list of arguments to pass to the generator.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.sampler = _sampler
        self.args = args
        self.generate()

    def __str__(self):
        """
        Return a string representation of the IDFEditor object.
        
        Parameters
        ----------
        self : IDFEditor
            The instance of the IDFEditor class.
        
        Returns
        -------
        str
            A formatted string containing the object's representation, generator name, arguments, and parameters.
        """
        res = super(IDFEditor, self).__repr__()
        res += '\n|\tGenerator: ' + self.sampler.name
        res += ',\targs: ' + str(self.args)
        res += '\n|\tparams: ' + str(self.params)
        return res

    def __repr__(self):
        """Return a string representation of the IDFGroupEditor instance.
        
        Parameters
        ----------
        self : IDFGroupEditor
            The instance of IDFGroupEditor to represent as a string.
            It must have attributes `idfclass`, `name`, and `field`.
        
        Returns
        -------
        str
            A string representation containing the class name, idfclass, name, and field attributes.
        """
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
        """
        Initialize a collection of IDFEditor instances with synchronized parameters.
        
        Parameters
        ----------
        editors : *IDFEditor
            Variable number of IDFEditor instances. Each editor's `generate` method is called,
            and their parameter lists are truncated to the length of the shortest parameter list.
        
        Returns
        -------
        None
        """
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
        """
        Create a grouped IDFEditor or IDFGroupEditor from multiple editors.
        
        Parameters
        ----------
        editors : *IDFEditor, list of IDFEditor, or IDFGroupEditor
            Variable length argument list of IDFEditor instances, lists of IDFEditor instances, 
            or IDFGroupEditor instances to be grouped together. If any input is not an IDFEditor, 
            cross_mode is activated to handle mixed types.
        
        Returns
        -------
        IDFGroupEditor
            A single IDFGroupEditor instance representing the combination of all provided editors. 
            If cross_mode is True, the editors are combined using the cross operation; otherwise, 
            they are grouped directly.
        """
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
        """
        Cross product of two GEditor instances.
        
        Parameters
        ----------
        geditor1 : GEditor
            The first GEditor instance whose editors and parameters are to be expanded and updated.
        geidtor2 : GEditor
            The second GEditor instance whose editors are repeated and appended to geditor1.
        
        Returns
        -------
        GEditor
            A modified version of geditor1 with updated parameters and combined editors from both inputs.
        """
        for edit in geditor1.editors:
            edit.params = np.repeat([edit.params], geidtor2.params_num, axis=0).flatten()
        for edit in geidtor2.editors:
            edit.params = np.repeat(edit.params, geditor1.params_num)
        geditor1.editors += geidtor2.editors
        geditor1.params_num *= geidtor2.params_num
        return geditor1

    @classmethod
    def merge(cls,geditor1,geditor2):
        """
        Merge two IDFEditor or IDFGroupEditor instances into a new IDFGroupEditor.
        
        Parameters
        ----------
        cls : class
            The class constructor, used to create the new merged instance.
        geditor1 : IDFEditor or IDFGroupEditor
            The first editor instance to merge. If it is an IDFEditor, it will be converted to an IDFGroupEditor.
        geditor2 : IDFEditor or IDFGroupEditor
            The second editor instance to merge. If it is an IDFEditor, it will be converted to an IDFGroupEditor.
        
        Returns
        -------
        IDFGroupEditor
            A new IDFGroupEditor instance containing the combined editors from both input instances.
        """
        if isinstance(geditor1,IDFEditor):
            geditor1=IDFGroupEditor(geditor1)
        if isinstance(geditor2,IDFEditor):
            geditor2=IDFGroupEditor(geditor2)
        geditor = cls(*(list(geditor1.editors) + list(geditor2.editors)))
        return geditor

    def drop(self,*editorStr):
        """
        Remove editors from the instance based on matching class, name, and field.
        
        Parameters
        ----------
        editorStr : str
            Variable number of strings in the format 'class>name>field' that specify 
            the editors to remove. Each string is split by '>' to extract the idfclass, 
            name, and field for matching.
        
        Returns
        -------
        None
            This method modifies the `editors` attribute in place and does not return a value.
        """
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
        """
        Return a list of formatted strings representing editor series.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the `editors` attribute. Each element in `self.editors`
            is expected to have `idfclass`, `name`, and `field` attributes.
        
        Returns
        -------
        list of str
            A list of strings where each string is formatted as 'idfclass > name > field' for each editor.
        """
        return [' > '.join([edit.idfclass,edit.name,edit.field]) for edit in self.editors]

    def __repr__(self):
        """
        Return a string representation of the object with class name, number of editors, and parameter count.
        
        Parameters
        ----------
        self : object
            The instance of the class.
        
        Returns
        -------
        str
            A formatted string containing the class name, number of editors, and number of parameters.
        """
        return self.__class__.__name__ + '\tEditors: ' + str(len(self.editors)) + '\tParamters: ' + str(self.params_num)

    def __str__(self):
        """
        Return a string representation of the object, including class name, parameter count, and editor details.
        
        Parameters
        ----------
        self : object
            The instance of the class being represented as a string. Contains `params_num` and `editors` attributes.
        
        Returns
        -------
        str
            A formatted string containing the class name, parameter count, and string representations of all editors, separated by newlines and surrounded by separator lines.
        """
        return '\n'.join(
            ['_' * 20] + [self.__class__.__name__ + '\tParamters: ' + str(self.params_num)] + [edit.__str__() for edit
                                                                                               in self.editors] + [
                '_' * 20])



    def to_csv(self, csv_path):
        """
        Write editor data to a CSV file.
        
        Parameters
        ----------
        self : object
            The instance containing the `editors` attribute, which is a list of editor objects.
            Each editor has attributes `idfclass`, `name`, `field`, and `params`.
        csv_path : str
            Path to the output CSV file.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        cols = np.array(
            [['>'.join([edit.idfclass,edit.name,edit.field])] + [str(para) for para in edit.params] for edit in self.editors])
        rows = [','.join(row) for row in cols.T]
        with open(csv_path, 'w+') as f:
            f.write('\n'.join(rows))

    def to_npy(self, npy_path):
        """
        Save editor parameters to a .npy file in transposed column format.
        
        Parameters
        ----------
        npy_path : str
            Path to the output .npy file where the array will be saved.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        cols = np.array(
            [['>'.join([edit.idfclass,edit.name,edit.field])] + [str(para) for para in edit.params] for edit in self.editors])
        np.save(npy_path, cols.T)

    def to_numpy(self):
        """
        Convert the editor data to a NumPy array.
        
        Parameters
        ----------
        self : object
            The instance containing the `editors` attribute, which is an iterable of editor objects.
            Each editor has attributes `idfclass`, `name`, `field`, and `params`.
        
        Returns
        -------
        numpy.ndarray
            A transposed 2D NumPy array where each row represents a field path (joined as 'idfclass>name>field')
            followed by string representations of the parameters.
        """
        return np.array(
            [['>'.join([edit.idfclass, edit.name, edit.field])] + [str(para) for para in edit.params] for edit in
             self.editors]).T

    @classmethod
    def load(cls, model, geditorpath:str,returnFileNames = False):
        """
        Load editors and optionally file names from a given file path.
        
        Parameters
        ----------
        model : object
            The model object used to evaluate and create IDFEditor instances.
        geditorpath : str
            Path to the input file, which can be a .csv, .ged, or .npy file containing editor data.
        returnFileNames : bool, optional
            If True, returns both the created editor instance and a list of file names extracted from the data. Default is False.
        
        Returns
        -------
        out : tuple or object
            If returnFileNames is True, returns a tuple where the first element is an instance of the class initialized with the created editors, 
            and the second element is a list of IDF file names. Otherwise, returns only the class instance with the applied editors.
        """
        sheet=[]
        fileNames = None
        if geditorpath[-4:]=='.csv' or geditorpath[-4:]=='ged':
            with open (geditorpath,'r') as f:
                sheet=np.array([line.strip('\n').split(',') for line in f.readlines()]).T
        elif geditorpath[-4:]=='.npy':
            sheet=np.load(geditorpath).T
        editors=[]
        for _var in sheet:
            if re.search('idf_name',_var[0],re.IGNORECASE) is not None or re.search('idf_names',_var[0],re.IGNORECASE) is not None:
                fileNames = [fn if fn.endswith('.idf') else fn+'.idf' for fn in _var[1:]]
            else:
                edit = IDFEditor.eval(model,_var[0])
                edit.apply_generator(enumerate,[_var[1:]])
                editors.append(edit)
        if returnFileNames:
            return cls(*editors),fileNames
        else:
            return cls(*editors)
