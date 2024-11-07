import os, shutil
import sys
import time

from .editor import IDFEditor, IDFModel, IDFGroupEditor, IDFsearchresult
from .reader import IDFResult
from .generator import Generator
from .utils import generate_code
import json
# from multiprocessing import Process, Queue
# from multiprocessing import cpu_count


class project:
    __slots__ = ['model', 'editor', 'groupeditor', 'generator', 'result', 'library', 'stdout','tempFolder']

    def __init__(self, model=None, editor=None, groupeditor=None, generator=None, result=None, stdout=sys.stdout):
        if model is None:
            self.model = None
        if editor is None:
            editor = []
        if groupeditor is None:
            groupeditor = []
        if generator is None:
            generator = []
        if result is None:
            result = []
        self.model:IDFModel = model
        self.stdout = stdout
        self.editor = editor
        self.groupeditor = groupeditor
        self.result = result
        self.generator = generator
        self.library = {}
        self.tempFolder=os.path.abspath(r'\_epeditortemp')
        if not os.path.exists(self.tempFolder):
            os.makedirs(self.tempFolder)
        if self.model:
            self.library['object'] = self.model.objectdict
            self.library['folder'] = self.model.folder

    @classmethod
    def load(cls, savepath: str):
        tempFolder = os.path.join(os.path.dirname(savepath), '_epeditortemp')
        tempLoadFolder = os.path.join(os.path.dirname(savepath), '_epeditortemp\load')
        shutil.unpack_archive(savepath, tempLoadFolder, 'zip')
        model = None
        for item in os.listdir(tempLoadFolder):
            if item[-4:] == '.idf':
                model = IDFModel(os.path.join(tempLoadFolder, item))
        if not model:
            raise Exception('*.idf not found. invalid *.zip')
        else:
            prj = cls(model=model)
            for item in os.listdir(tempLoadFolder):
                if item[:3] == 'edt':
                    prj.editor.append(IDFEditor.load(prj.model, os.path.join(tempLoadFolder, item)))
                if item[:3] == 'ged':
                    ged = IDFGroupEditor.load(prj.model, os.path.join(tempLoadFolder, item))
                    ged.name = item.split('_')[1]
                    prj.groupeditor.append(ged)
                if item[:3] == 'gen':
                    prj.generator.append(Generator.from_py(os.path.join(tempLoadFolder, item)))
                if item[:3] == 'res':
                    prj.result.append(IDFResult.from_npy(os.path.join(tempLoadFolder, item)))
                if item[:3] == 'lib':
                    with open(os.path.join(tempLoadFolder, item)) as f:
                        prj.library = json.load(f)
            if 'folder' in prj.library.keys() and prj.library['folder'] and prj.library['folder'] != '':
                prj.model.read_folder(prj.library['folder'])
            else:
                prj.library['folder'] = None
            prj.tempFolder=tempFolder
            return prj

    def save(self, savepath: str):
        saveTempFolder = os.path.join(os.path.dirname(savepath), '_epeditortemp\save')
        tempFolder = os.path.join(os.path.dirname(savepath), '_epeditortemp')
        self.tempFolder = tempFolder
        if os.path.exists(saveTempFolder):
            shutil.rmtree(saveTempFolder)
        if not os.path.exists(tempFolder):
            os.mkdir(tempFolder)
        if not os.path.exists(saveTempFolder):
            os.mkdir(saveTempFolder)

        shutil.copy(self.model.file_name, os.path.join(saveTempFolder, os.path.basename(self.model.file_name)))
        for geditor in self.groupeditor:
            geditor.to_npy(os.path.join(saveTempFolder, f'ged_{geditor.name}_' + generate_code(6) + '.npy'))
        for edit in self.editor:
            edit.save(os.path.join(saveTempFolder, 'edt_' + generate_code(6) + '.edt'))
        for res in self.result:
            if res.dump:
                res.load()
            res.save(os.path.join(saveTempFolder, 'res_' + generate_code(6) + '.npy'))
        for gen in self.generator:
            gen.run_to_py(os.path.join(saveTempFolder, f'gen_' + generate_code(6) + '.py'))
        with open(os.path.join(saveTempFolder, 'lib_' + generate_code(6) + '.json'), 'w+') as f:
            json.dump(self.library, f)
        if os.path.exists(savepath):
            os.remove(savepath)

        shutil.make_archive(savepath, 'zip', saveTempFolder)
        try:
            shutil.rmtree(saveTempFolder)
        except:
            pass
        os.rename(savepath + '.zip', savepath)

    def reference_callback(self, msg):
        self.stdout.write(f'Extract reference finish. Class:{msg[0]} Found:{len(msg[1].values())}')


    def get_references(self, processes=4, stdout=sys.stdout):
        return None
        sys.stdout = stdout
        references = {}
        q = Queue()
        result = []
        process, processing = [], []
        currentprs = 0
        for idfclass in self.model.idfobjects.keys():
            objs = [obj for obj in self.model.idfobjects[idfclass] if len(obj.fieldvalues) > 2]
            if len(objs) > 0:
                if idfclass != 'OUTPUT:VARIABLE':
                    process.append([idfclass, Process(target=_get_references, args=(idfclass, objs, q))])
        res = []
        while len(process) > 0:
            while currentprs < processes and len(process) > 0:
                processing.append(process.pop())
                print(f'Extracting Referencing EpBunch for Class: {processing[-1][0]}')
                currentprs += 1
                processing[-1][1].start()

            while not q.empty():
                res.append(q.get())
            currentprs = len(processing) - len(res)
            time.sleep(1)
            print(f'Waiting......,task: {len(process)}')

        print('Packing......')
        for r in res:
            references[r[0]] = r[1]
        return references

    def node_reference(self, node: IDFsearchresult):
        nodestr = '>'.join([node.idfclass, node.name])
        referenced = self.library['references'][node.idfclass][node.name]
        referenced = [self.model.eval(nodstr) for nodstr in referenced]
        referencing = []
        for idfclass in self.library['references'].keys():
            for idfname in self.library['references'][idfclass].keys():
                if nodestr in self.library['references'][idfclass][idfname]:
                    referencing.append(self.model.eval(idfclass, idfname))
        return referenced, referencing


def _get_references(idfclass, objs, queue):
    ref_dict = {}
    for obj in objs:
        ref_list = IDFsearchresult(obj).referred_list(obj=False)
        if len(ref_list) > 0:
            ref_dict[str(obj.fieldvalues[1])] = ref_list
    # print(f'Class: {idfclass} finish',end='')
    queue.put([idfclass, ref_dict])


def error_callback(error):
    print(f'****Process Error: {error}')
