import sys

from eppy.modeleditor import IDF
import os,shutil,re
from multiprocessing.pool import Pool
from .utils import *

def make_eplaunch_options(idf,**kwargs):
    """Make options for run, so that it runs like EPLaunch on Windows"""
    idfversion = idf.idfobjects['version'][0].Version_Identifier.split('.')
    idfversion.extend([0] * (3 - len(idfversion)))
    idfversionstr = '-'.join([str(item) for item in idfversion])
    fname = idf.idfname
    options = {
        # 'ep_version':idfversionstr, # runIDFs needs the version number
            # idf.run does not need the above arg
            # you can leave it there and it will be fine :-)

        'output_prefix':os.path.basename(fname).split('.')[0],
        'output_suffix':'C',
        'output_directory':os.path.dirname(fname),
        'readvars':True,
        'expandobjects':True,
        #'verbose': 'v'  # allow all stdout
        #'verbose':'q' # ban the stdout but allow stderr
        #'verbose':'s'  # ban both the stdout and stderr
        }
    for key in kwargs.keys():
        options[key]=kwargs[key]
    return options

def error_callback(error):
    print(f'****Process Error: {error}')

def return_callback(msg):
    print(msg)

def simulate_file(idf_path:str,epw:str,idd:str=None,overwrite=False,verbose='q',**kwargs):
    def _processing(idf_path:str,epw:str,idd:str=None,overwrite=False,**kwargs):
        if not check_installation(idf_path):
           return f'Energyplus Ver.{get_version(idf_path)} is not yet installed.'
        if idd is None:
            idd = get_idd(idf_path)
        IDF.setiddname(idd)
        print(f'Case Start:{idf_path}')
        new_idf_path = os.path.join(idf_path[:-4],os.path.basename(epw))+'.idf'
        if os.path.exists(idf_path[:-4]):
            if overwrite:
                shutil.rmtree(idf_path[:-4])
                os.mkdir(idf_path[:-4])
            elif os.path.exists(new_idf_path[:-4]+'.sql'):
                return f'**********Result Already Exist. Skip:{new_idf_path}'
        else:
            os.mkdir(idf_path[:-4])
        print(f'Case Move to:{new_idf_path}')
        shutil.copy(idf_path,new_idf_path)
        idf = IDF(new_idf_path,epw=epw)
        if len(idf.idfobjects['Output:SQLite'])==0:
            sql=idf.newidfobject('Output:SQLite')
            sql.Option_Type='Simple'
        theoptions = make_eplaunch_options(idf,**kwargs)
        idf.run(**theoptions)
        return f'Case Done:{new_idf_path}'
    kwargs['verbose'] = verbose
    if os.path.isfile(idf_path) and os.path.exists(idf_path):
        if verbose == 's':
            with hiddenPrint() as log:
                new_idf_path= _processing(idf_path, epw, idd,overwrite, ** kwargs)
                log.dump(new_idf_path[:-4] + '.log')
                msg=''
        else:
            msg = _processing(idf_path, epw, idd, overwrite, **kwargs)
        return msg
    else:
        return f'IDF not found: {idf_path}'

def simulate_local(idf_path:str,epw:str,idd:str=None,overwrite=False,stdout = sys.stdout , verbose='q',prs_count=4,**kwargs):
    sys.stdout = stdout
    if os.path.isfile(idf_path):
        return simulate_file(idf_path,epw,idd,overwrite)
    elif isinstance(idf_path,IDF):
        return simulate_file(idf_path.idfabsname, epw, idd, overwrite)
    elif os.path.isdir(idf_path):
        prs_pool=Pool(prs_count)
        for file in os.listdir(idf_path):
            file = os.path.join(idf_path,file)
            prs_pool.apply_async(func=simulate_file,
                                 args=(file,epw,idd,overwrite,verbose,),
                                 callback=return_callback,
                                 error_callback=error_callback,**kwargs)
        prs_pool.close()
        prs_pool.join()
        print('**********ALL DONE**********')
        return 1

def find_sql(idf_dir:str):
    file_package=os.walk(idf_dir)
    sql={}
    for dirpath,dirnames,filenames in file_package:
        for file in filenames:
            if re.search('\.sql',file,re.IGNORECASE)!=None:
                case=os.path.normpath(dirpath).split(os.sep)[-1]
                sql[case]=os.path.join(dirpath,file)
    return sql

if __name__=='__main__':
    msg=simulate_file(
        r'test\baseline_0.idf',
        epw=r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Beijing.Beijing.545110_SWERA.epw'
    )
    print(msg)
