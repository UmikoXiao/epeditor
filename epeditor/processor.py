from __future__ import annotations

import eppy
import numpy as np
from .generator import Generator, original,enumerate
from .utils import *
import re


class IDFsearchresult:
    """Container for an IDF search hit with class, object name, and field metadata."""
    __slots__ = ['obj', 'idfclass', 'name', 'field', 'value']

    def __init__(self, obj: eppy.bunch_subclass.EpBunch, idfclass: str = None, name: str = None, field=None):
        """
          init  .
        
        Parameters
        ----------
        obj : eppy.bunch_subclass.EpBunch
            Input parameter `obj`.
        
        idfclass : str
            Input parameter `idfclass`.
        
        name : str
            Input parameter `name`.
        
        field : Any
            Input parameter `field`.
        
        Returns
        -------
        None
            Return value from `__init__`.
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
          repr  .
        
        Returns
        -------
        Any
            Return value from `__repr__`.
        """
        res = '\n'+self.__class__.__name__
        res += '\n|\tClass: ' + self.idfclass
        res += ',\tName: ' + self.name
        res += '\n|\tField: ' + self.field
        res += ',\tValue: ' + str(self.value)
        return res

    def referred_object(self,field,obj=False):
        """
        Referred object.
        
        Parameters
        ----------
        field : Any
            Input parameter `field`.
        
        obj : Any
            Input parameter `obj`.
        
        Returns
        -------
        Any
            Return value from `referred_object`.
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
        Referred list.
        
        Parameters
        ----------
        obj : Any
            Input parameter `obj`.
        
        Returns
        -------
        Any
            Return value from `referred_list`.
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
        Equal.
        
        Parameters
        ----------
        others : Any
            Input parameter `others`.
        
        Returns
        -------
        Any
            Return value from `equal`.
        """
        if self.idfclass == others.idfclass and self.name == others.name and self.field == others.field:
            return True
        else:
            return False


class IDFEditor(IDFsearchresult):
    """Parameterized editor that binds a target field to a sampling generator."""
    __slots__ = ['sampler', 'args', 'params']

    def __init__(self, object, field=None, _sampler: Generator = original, args: list = None):
        """
          init  .
        
        Parameters
        ----------
        object : Any
            Input parameter `object`.
        
        field : Any
            Input parameter `field`.
        
        _sampler : Generator
            Input parameter `_sampler`.
        
        args : list
            Input parameter `args`.
        
        Returns
        -------
        None
            Return value from `__init__`.
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
        From idfobject.
        
        Parameters
        ----------
        obj : eppy.bunch_subclass.EpBunch
            Input parameter `obj`.
        
        field : str
            Input parameter `field`.
        
        _sampler : Generator
            Input parameter `_sampler`.
        
        args : list
            Input parameter `args`.
        
        Returns
        -------
        Any
            Return value from `from_idfobject`.
        """
        editor = IDFsearchresult(obj, field=field)
        editor = cls(editor, _sampler=_sampler, args=args)
        return editor

    @classmethod
    def eval(cls,model, editorstr:str,_sampler: Generator = original,args: list = None):
        """
        Eval.
        
        Parameters
        ----------
        model : Any
            Input parameter `model`.
        
        editorstr : str
            Input parameter `editorstr`.
        
        _sampler : Generator
            Input parameter `_sampler`.
        
        args : list
            Input parameter `args`.
        
        Returns
        -------
        Any
            Return value from `eval`.
        """
        editorstr=editorstr.split('>')
        editor = model.eval(editorstr[0],editorstr[1],editorstr[2])
        editor = cls(editor, _sampler=_sampler, args=args)
        return editor

    @classmethod
    def load(cls,model,editorpath:str):
        """
        Load.
        
        Parameters
        ----------
        model : Any
            Input parameter `model`.
        
        editorpath : str
            Input parameter `editorpath`.
        
        Returns
        -------
        Any
            Return value from `load`.
        """
        with open(editorpath,'r') as f:
            text = [line.strip('\n') for line in f.readlines()]
            editorstr = text[0]
            sampler = Generator.from_py(os.path.join(os.path.dirname(editorpath),text[1]))
            args = eval(text[2])
            return cls.eval(model,editorstr,sampler,args)

    def save(self,editorpath:str):
        """
        Save.
        
        Parameters
        ----------
        editorpath : str
            Input parameter `editorpath`.
        
        Returns
        -------
        Any
            Return value from `save`.
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
        Generate.
        
        Returns
        -------
        Any
            Return value from `generate`.
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
        Apply generator.
        
        Parameters
        ----------
        _sampler : Generator
            Input parameter `_sampler`.
        
        args : list
            Input parameter `args`.
        
        Returns
        -------
        Any
            Return value from `apply_generator`.
        """
        self.sampler = _sampler
        self.args = args
        self.generate()

    def __str__(self):
        """
          str  .
        
        Returns
        -------
        Any
            Return value from `__str__`.
        """
        res = super(IDFEditor, self).__repr__()
        res += '\n|\tGenerator: ' + self.sampler.name
        res += ',\targs: ' + str(self.args)
        res += '\n|\tparams: ' + str(self.params)
        return res

    def __repr__(self):
        """
          repr  .
        
        Returns
        -------
        Any
            Return value from `__repr__`.
        """
        res = self.__class__.__name__
        res += ' : Class:' + self.idfclass
        res += ' > Name:' + self.name
        res += ' > Field:' + self.field
        return res


class IDFGroupEditor:
    """Group of IDF editors for combined parameter-set generation."""
    __slots__ = ['editors', 'params_num','name']

    def __init__(self, *editors: IDFEditor):
        """
          init  .
        
        Parameters
        ----------
        *editors : IDFEditor
            Input parameter `*editors`.
        
        Returns
        -------
        None
            Return value from `__init__`.
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
        Group.
        
        Parameters
        ----------
        *editors : Any
            Input parameter `*editors`.
        
        Returns
        -------
        Any
            Return value from `group`.
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
        Cross.
        
        Parameters
        ----------
        geditor1 : Any
            Input parameter `geditor1`.
        
        geidtor2 : Any
            Input parameter `geidtor2`.
        
        Returns
        -------
        Any
            Return value from `cross`.
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
        Merge.
        
        Parameters
        ----------
        geditor1 : Any
            Input parameter `geditor1`.
        
        geditor2 : Any
            Input parameter `geditor2`.
        
        Returns
        -------
        Any
            Return value from `merge`.
        """
        if isinstance(geditor1,IDFEditor):
            geditor1=IDFGroupEditor(geditor1)
        if isinstance(geditor2,IDFEditor):
            geditor2=IDFGroupEditor(geditor2)
        geditor = cls(*(list(geditor1.editors) + list(geditor2.editors)))
        return geditor

    def drop(self,*editorStr):
        """
        Drop.
        
        Parameters
        ----------
        *editorStr : Any
            Input parameter `*editorStr`.
        
        Returns
        -------
        Any
            Return value from `drop`.
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
        Editorseries.
        
        Returns
        -------
        Any
            Return value from `editorSeries`.
        """
        return [' > '.join([edit.idfclass,edit.name,edit.field]) for edit in self.editors]

    def __repr__(self):
        """
          repr  .
        
        Returns
        -------
        Any
            Return value from `__repr__`.
        """
        return self.__class__.__name__ + '\tEditors: ' + str(len(self.editors)) + '\tParamters: ' + str(self.params_num)

    def __str__(self):
        """
          str  .
        
        Returns
        -------
        Any
            Return value from `__str__`.
        """
        return '\n'.join(
            ['_' * 20] + [self.__class__.__name__ + '\tParamters: ' + str(self.params_num)] + [edit.__str__() for edit
                                                                                               in self.editors] + [
                '_' * 20])



    def to_csv(self, csv_path):
        """
        To csv.
        
        Parameters
        ----------
        csv_path : Any
            Input parameter `csv_path`.
        
        Returns
        -------
        Any
            Return value from `to_csv`.
        """
        cols = np.array(
            [['>'.join([edit.idfclass,edit.name,edit.field])] + [str(para) for para in edit.params] for edit in self.editors])
        rows = [','.join(row) for row in cols.T]
        with open(csv_path, 'w+') as f:
            f.write('\n'.join(rows))

    def to_npy(self, npy_path):
        """
        To npy.
        
        Parameters
        ----------
        npy_path : Any
            Input parameter `npy_path`.
        
        Returns
        -------
        Any
            Return value from `to_npy`.
        """
        cols = np.array(
            [['>'.join([edit.idfclass,edit.name,edit.field])] + [str(para) for para in edit.params] for edit in self.editors])
        np.save(npy_path, cols.T)

    def to_numpy(self):
        """
        To numpy.
        
        Returns
        -------
        Any
            Return value from `to_numpy`.
        """
        return np.array(
            [['>'.join([edit.idfclass, edit.name, edit.field])] + [str(para) for para in edit.params] for edit in
             self.editors]).T

    @classmethod
    def load(cls, model, geditorpath:str,returnFileNames = False):
        """
        Load.
        
        Parameters
        ----------
        model : Any
            Input parameter `model`.
        
        geditorpath : str
            Input parameter `geditorpath`.
        
        returnFileNames : Any
            Input parameter `returnFileNames`.
        
        Returns
        -------
        Any
            Return value from `load`.
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
