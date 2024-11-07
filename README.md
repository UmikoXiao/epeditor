# epeditor：EnergyPlus批量调参、模拟、结果读取
该模块基于[eppy](https://eppy.readthedocs.io/en/latest/Main_Tutorial.html)与[db_eplusout_reader](https://github.com/DesignBuilderSoftware/db-eplusout-reader)模块开发，为**课题组内部工具**。模块的主要功能包括：
1. 自动读取.idf文件作为baseline，匹配对应版本解释文件.idd；
2. 兼容eppy模块的所有功能，对baseline进行基本的参数修改；
3. 可基于关键词搜索或者eppy的idfobjects方法建立批量修改参数的editor；
4. 应用editors批量生成指定版本的idf文件；
5. 通过多种方式云端（未实现）/本地对idf进行并行批量模拟，并对结果进行归档；
6. 兼容db_eplusout_reader的所有功能，对不同cases结果进行横向与纵向统计；
7. 将模拟结果发送至课题组数据库（未实现）
<br />
<br />**样板文件请见test.py**
<br />

---

##  🔧 安装流程
请对应版本安装eppy与db_eplusout_reader，三个whl都已提供在本zip中，放置于***setup文件夹***内。本模块需大量调用numpy，同时numpy提供很丰富又很快速的数据处理功能，测试可用版本为1.26.3。此外非常推荐安装两个energyplus版本[22.2.0（本模块支持的最新稳定版本）](https://github.com/NREL/EnergyPlus/releases/tag/v22.2.0)与[8.9.0（DesignBuilder使用的稳定版本）](https://github.com/NREL/EnergyPlus/releases/tag/v8.9.0)
```console
cd .\setup
pip install eppy-0.5.63-py2.py3-none-any.whl
pip install db_eplusout_reader-0.3.1-py2.py3-none-any.whl
pip install numpy==1.26.3
pip install epeditor-0.1.0-py3-none-any.whl
```

---

## 👀 基本工作流程

### 三个最主要的类型的定义以及用法
- [EpBunch](#EpBunch) -- 一个idfobject对象。idf文件是基于类的数据库，每一项模拟设定都是一个idfobject对象，属于某个类型(idfclass)，并拥有独立的名称(idfname)。他每一项可被修改的参数称为该idfobject的field：
<br>*#一个典型的zone类型的EpBunch，他的idfname==Block1:Zone1，有诸如Type,Volume,Floor_Area等field*


      >>>model.idfobjects['Zone'][0]
      Zone,
        Block1:Zone1,             !- Name
        0,                        !- Direction of Relative North
        0,                        !- X Origin
        0,                        !- Y Origin
        0,                        !- Z Origin
        1,                        !- Type
        1,                        !- Multiplier
        ,                         !- Ceiling Height
        1106.9178,                !- Volume
        316.2622,                 !- Floor Area
        TARP,                     !- Zone Inside Convection Algorithm
        ,                         !- Zone Outside Convection Algorithm
        Yes;                      !- Part of Total Floor Area

- [IDFEditor](#IDFEditor) -- 一个Editor对应一个被调整的模拟参数(field)，以及该模拟参数的多个目标取值(params)

```python
      >>>editor=ed.IDFEditor(model.idfobjects['Zone'][0],field='Floor_Area')
      >>>editor.apply_generator(ed.generator.arange,[100,110,2])
      >>>print(editor)
      IDFEditor
      |	Class: Zone,	Name: Block1:Zone1
      |	Field: Floor_Area,	Value: 316.2622
      |	Generator: _arange,	args: [100, 110, 2]
      |	params: [100, 102, 104, 106, 108]
```

- [IDFGroupEditor](#IDFGroupEditor) -- 将几个Editor进行打包，从而同时调整多个模拟参数(field)

```python
    >>>geditor=ed.IDFGroupEditor.group([editor1,editor2],[editor4,editor5])
    >>>print(geditor)
    ____________________
    IDFGroupEditor	Paramters: 64
    IDFEditor
    |	Class: ZONE,	Name: Block1:Zone1
    |	Field: Floor_Area,	Value: 316.2622
    |	Generator: _arange,	args: [100, 200, 10]
    |	params: [100 110 120 130 ...]
    IDFEditor
    |	Class: Zone,	Name: Block2:Zone1
    |	Field: Floor_Area,	Value: 316.2622
    |	Generator: _random,	args: [110, 230, 8]
    |	params: [158.19996359 188.800937 218.21130432 156.57865731  ...]
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1
    |	Field: Thickness,	Value: 0.1
    |	Generator: _uniform,	args: [0.1, 0.3, 8]
    |	params: [0.11579802 0.11579802 0.11579802 0.11579802 ...]
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1
    |	Field: Conductivity,	Value: 0.51
    |	Generator: _enumerate,	args: [[0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]]
    |	params: [0.4  0.4  0.4  0.4  ...]
    ____________________
```

### 通过print查看具体信息
IDFModel -- baseline的路径和版本信息,以及其结果路径和结果条目([variables](#Variable))数量等

    >>>print(model)
    project\baseline.idf
    BASELINE VERSION:22.2
    idd:C:\Users\Umiko\PycharmProjects\IDFprocessing\epeditor\idd\V22-2-0-Energy+.idd
    folder:d:\test
    sql:
    variables:

[EpBunch](#EpBunch) -- 单个idf对象，打印内容为该对象的field

      >>>model.idfobjects['Zone'][0]
      Zone,
        Block1:Zone1,             !- Name
        0,                        !- Direction of Relative North
        0,                        !- X Origin
        0,                        !- Y Origin
        0,                        !- Z Origin
        1,                        !- Type
        1,                        !- Multiplier
        ,                         !- Ceiling Height
        1106.9178,                !- Volume
        316.2622,                 !- Floor Area
        TARP,                     !- Zone Inside Convection Algorithm
        ,                         !- Zone Outside Convection Algorithm
        Yes;                      !- Part of Total Floor Area

[IDFSearchResult](#IDFSearchResult) -- 对象或field的搜索结果，打印内容为其idfclass与名称，含有field时则包括其field和value


    >>>print(result1)
    IDFsearchresult
    |	Class: Zone,	Name: Block2:Zone1
    |	Field: Floor_Area,	Value: 316.2622

[IDFEditor](#IDFEditor) -- 对某个idf对象的某个field的调参，可打印其原始数值、参数生成器([Generator](#Generator))以及生成的模拟参数等


    >>>print(editor2)
    IDFEditor
    |	Class: Zone,	Name: Block2:Zone1
    |	Field: Floor_Area,	Value: 316.2622
    |	Generator: _random,	args: [110, 230, 8]
    |	params: [180.93822712889147, 126.26729225784902, 118.68167701264017, 181.2467989209593, 203.15066281134813, 181.27183372272788, 187.39091696051247, 178.86552281046121]

[IDFGroupEditor](#IDFGroupEditor) -- Editor的编组，同编组内的Editor模拟参数个数相同，生成idf文件时一一匹配

    >>>geditor = ed.IDFGroupEditor(editor2,editor3)    
    >>>print(geditor)
    ____________________
    IDFGroupEditor	Paramters: 8
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Thickness
    |	Value: 0.1
    |	Generator: _linspace,	args: [0.1, 0.3, 8]
    |	params: [0.1, 0.1285714285714286, 0.15714285714285714, 0.18571428571428572, 0.2142857142857143, 0.24285714285714285, 0.27142857142857146, 0.3]
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Conductivity
    |	Value: 0.51
    |	Generator: _enumerate,	args: [[0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]]
    |	params: [0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]
    ____________________

### 简易的工作流程
1. 读取baseline idf文件，建议先升级为22.2版本，或者安装对应版本的energyplus
   ```console
   model = ed.IDFModel(r'project\baseline.idf')
   ```
2. 寻找需要修改的field.该步骤也可使用[关键词搜索](#instruction_search)进行
   ```console
    # 匹配Zone类型对象：‘Block2:zone1’的Floor_Area,class和name的词条忽略大小写,但Field名称要注意大小写
   result1 = model.eval('Zone','Block2:zone1','Floor_Area')
   print(result1)
   
    # 匹配material类型对象：'Concrete Block (Medium)_O.1'的Thickness和Conductivity
   result2 = model.eval('material','Concrete Block (Medium)_O.1','Thickness')
   result3 = model.eval('material','Concrete Block (Medium)_O.1','Conductivity')
   
    # 匹配WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM类型对象：'Simple 1001'的UFactor和SHGC
   result4 = model.eval('WindowMaterial:SimpleGlazingSystem','Simple 1001','UFactor')
   result5 = model.eval('WindowMaterial:SimpleGlazingSystem','Simple 1001','Solar Heat Gain Coefficient') #带空格或下划线都可以
   ```
3. 使用[IDFEditor](#IDFEditor)对baseline进行批量调参
   ```console
    # 修改result1，使用arange方法生成10个params
   editor1 = ed.IDFEditor(result1, _sampler=ed.generator.arange, args=[100, 200, 10])
   
    # 修改result2，使用uniform采样方法生成8个params
   editor2 = ed.IDFEditor(result2, _sampler=ed.generator.uniform,args=[0.1, 0.3, 8])
   
    # 修改修改result3，使用enumerate采样方法生成8个params,即直接输入参数
   conduct_params=[0.40, 0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.54]
   editor3 = ed.IDFEditor(result3, _sampler=ed.generator.enumerate,args=[conduct_params]) #需要[conduct_params]
   
    # 同样修改4,5，都采用高斯采样生成6个params
   editor4 = ed.IDFEditor(result4, _sampler=ed.generator.gaussian,args=[1.8, 2.2, 6])
   editor5 = ed.IDFEditor(result5, _sampler=ed.generator.gaussian,args=[0.3, 0.5, 6])
   ```
4. 使用[GroupEditor](#IDFGroupEditor)对editor进行打包。
<br>在同一个*GroupEditor*中所有params按位匹配。即8个params的editor1,editor2,editor3会生成8个idf。当editor的参数个数不等时，按照最少的取值<br />
<br>在不同*GroupEditor*中所有params交叉匹配。即8个params的GroupEditor1与6个params的GroupEditor2生成8*6=48个idf文件<br />
   ```console
    # GroupEditor的参数表可导出为csv，方便做case的记录
   geditor=ed.IDFGroupEditor.group([editor1, editor2, editor3],[editor4,editor5])
   geditor.to_csv('test.csv')
   ```
5. 将模型写入folder，生成一系列idf文件。文件的数量为*GroupEditor*的params_num
   ```console
   model.write(geditor, r'test')
   ```
6. 模拟。默认为本地模拟
   ```console
   model.simulation(epw=r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Beijing.Beijing.545110_SWERA.epw')
   ``` 
   若已有模拟结果，只希望重读结果，也可以带folder参数初始化IDFModel:
    ```console
   model = ed.IDFModel(r'project\baseline.idf',folder=r'.\test')
   ``` 
7. 读取模拟结果，有两种方法：\*Variables参数详见[Variables](#Variable),返回类型为[IDFResult](#IDFResult)
   ```console
   result1 = model.group_result(ed.Variable("Cumulative", "Electricity:Facility", "J"), 
                                     calculator = np.mean, frequency=ed.Monthly)
   result2 = model.case_result(ed.Variable("Cumulative", "Electricity:Facility", "J"),
                                     case = 0,frequency=ed.Monthly)
   ```
8. 调用IDFResult.save()/IDFResult.to_csv()保存为npy二进制格式或者csv可读格式
   ```console
   result1.to_csv(r'result1.csv')
   result2.save(r'result2.npy')
   ```
<br >

### <a id='instruction_search'></a>关键词搜索([IDFModel.search()](#search))
#### 方法一：使用[model.eval()](#eval)方法强制匹配

    >>>model.eval('material','Concrete Block (Medium)_O.1','Conductivity')
    IDFsearchresult
    |	Class: Material,	Name: Concrete Block (Medium)_O.1
    |	Field: Conductivity,	Value: 0.51
也可以直接用上级方法[IDFEditor.eval()](#IDFEditor.eval)打包为IDFEditor

    >>>editor = ed.IDFEditor.eval( model, 'material>Concrete Block (Medium)_O.1>Conductivity')
    >>>editor.apply_generator(ed.generator.uniform,[0.4, 0.6, 8])
    >>>print(editor)
    IDFEditor
    |	Class: Material,	Name: Concrete Block (Medium)_O.1
    |	Field: Conductivity,	Value: 0.51
    |	Generator: _uniform,	args: [0.4, 0.6, 8]
    |	params: [0.4542428970176472, 0.43462444181106613, 0.40781635968392793, 0.4125632388517584, 0.4500160035426242, 0.4474714608002809, 0.44085745570614454, 0.5968550821740386]
    
#### 方法二：调用[IDFModel.search()](#search)方法:
该方法有很多种灵活的用法：(更详细的说明请见[IDFModel.search()](#search))
<br>*field的名称中带有‘area’的object*
    
    >>>model.search('area', searchtype=ed.FIELD,strict=False)[0]
    IDFsearchresult
    |	Class: ZONE,	Name: Block1:Zone1
    |	Field: Floor_Area,	Value: 316.2622
<br>*选取名字带 ‘Block2:zone1’,类型为zone 的第一个object*

    >>>model.search('Block2:zone1', searchlist=model.idfobjects['ZONE'], searchtype=ed.OBJECT)[0]
    IDFsearchresult
    |	Class: Zone,	Name: Block2:Zone1
    |	Field: ,	Value: 
<br>*在任何信息带'material'的搜索结果中，搜索带'Concrete Block (Medium)_O.1'的object*

    >>>model.search('Concrete Block', searchlist=model.search('Material'))
    [IDFsearchresult
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1
    |	Field: ,	Value: ]

### 各种数据管理的办法
1. IDFGroupEditor存取：
<br>IDFGroupEditor作为baseline调参的最终结果是可以存取的，通过[to_csv()](#IDFGroupEditor.to_csv())/[to_npy()](#IDFGroupEditor.to_npy()))与[load()](#IDFGroupEditor.load())方法实现
    ```console
   geditor=ed.IDFGroupEditor.group([editor1,editor2],[editor4],[editor5])
   geditor.to_csv('parameters_record.csv')
   
   geditor=ed.IDFGroupEditor.load('parameters_record.csv')
   ```
2. IDFModel的存取：
<br>若不希望每次都进行模拟，对于已经进行过模拟的IDFModel可以直接通过folder初始化，就可以直接进行结果的读取。
    ```console
   model = ed.IDFModel(r'project\baseline.idf',folder=r'.\test')
   ```
3. 模拟中断与各种设定：
<br>只需要在[IDFModel.simulation()](#simulation)中设定overwrite=False就可‘断点续传’，同时还带有诸如禁止打印/改变输出名称等多种功能
4. IDFResult的存取：
<br>由于群组模拟的结果很大，IDFResult自带缓存与IO功能[IDFResult.to_csv()](#IDFResult.to_csv())，就算程序崩了也可以找回来:)
---

## 🤗 CERTIFICATION
**由于工具在不远的将来将内置网络功能，本工具暂时仅限课题组内使用。若项目源码不慎泄露至外网上，将极易导致课题组服务器遭受攻击，进而失去各位辛辛苦苦积攒的数据....但清华内网就无所谓了**
<br>p.s.任何bug或者使用上的问题 Please do not hesitate to reach me: junx026@gmail.com

---

## 📖 DOCUMENT
### CLASS
#### <a id='IDFModel'>IDFModel(IDF)</a>
方便Baseline管理的增强IDF类型，提供更方便的idfobject([EpBunch](#EpBunch))管理。大部分操作都基于本类型进行。在epeditor中，所有的操作都不会作用于baseline文件，调参都通过 [IDFEditor](#IDFEditor) 和 [IDFGroupEditor](#IDFGroupEditor) 进行；但由于IDFModel继承了eppy.IDF并兼容其一切属性,您仍可调用IDF类中的任何方法对baseline进行修改或查询。虽然我真的不建议这么做......

    >>>model
    project\baseline.idf
    BASELINE VERSION:22.2
    >>>print(model)
    project\baseline.idf
    BASELINE VERSION:22.2
    idd:C:\Users\Lenovo\PycharmProjects\IDFprocessing\epeditor\idd\V22-2-0-Energy+.idd
    folder:test
    sql:
    variables:
##### properties
###### objectdict:dict
增强idfobjects方法，由[get_objectdict()](#objectdict)方法产生，方便根据name查阅object<br />*objectdict={idfclass:[idfname1,idfname2...]}*

    >>>model.objectdict
    {'VERSION': ['22.2'], 'SIMULATIONCONTROL': ['Yes'], 'BUILDING': ['Building'], ....}
###### file_name:str(path)
记录baseline地址
###### folder: str(path)
记录导出路径
###### sql:dict {str:str(path)}
记录结果sql路径<br />
*sql={casename:sqlpath}*
###### <a id='IDFModel.variables'>variables: list\<Variable></a>
记录结果所有的variables，详见[Variables](#Variable)
###### <a id='idfobjects'> idfojbects</a>: dict {str: [list \<eppy.EpBunch>](#EpBunch)} (inherit: eppy.modeleditor.IDF)
含有指定idfclass的dict，可以精确查询需要的object，性能比[search(searchtype=ed.CLASS)](#search)要好

    >>>model.idfobjects['Zone']
    [
    Zone,
    Block1:Zone1,             !- Name
    0,                        !- Direction of Relative North
    0,                        !- X Origin
    0,                        !- Y Origin
    0,                        !- Z Origin
    1,                        !- Type
    1,                        !- Multiplier
    ,                         !- Ceiling Height
    1106.9178,                !- Volume
    170,                      !- Floor Area
    TARP,                     !- Zone Inside Convection Algorithm
    ,                         !- Zone Outside Convection Algorithm
    Yes;                      !- Part of Total Floor Area
    , 
    Zone,
    Block2:Zone1,             !- Name
    ...]
##### classmethod
>  __init__(idf_file=None, epw=None, idd=None, folder=None) 🔧constructive

baseline模型的构造函数,可以不指定epw文件与idd文件：idd文件将自动读取，而epw文件可在模拟时传入。 <br>
Parameters
- idf_file: str -- *idf文件路径* (default:None)
- epw: str -- *epw文件路径* (default:None) 
- idd: str -- *idd文件路径,函数内部提供自动识别* (default:None)
- folder: str -- *结果储存的路径* (default:None)<br>

Returns: 
- None
> <a id="objectdict">get_objectdict() </a> 

获取所有idfobject([EpBunch](#EpBunch))的dictionary，***仅限可接受修改的主要object*** <br>
<br>Example:<br>

    >>>model.get_objectdict()
    {'VERSION': ['22.2'], 'SIMULATIONCONTROL': ['Yes'], 'BUILDING': ['Building'], ....}
Parameters:
- None

Returns:
- objects_dictionary: dict -- *以{idfClass1:[Name1,Name2...]...}为结构的dict，包括所有含有名字的idfobject([EpBunch](#EpBunch))*

> <a id='eval'> eval(idfclass: str , idfname: str , field: str ) </a>

增强idfobjects方法，通过名字强制匹配某物体某词条。由于匹配条件很严格，只会返回一个结果
<br>Parameters:
- idfclass: str -- *类型名称，忽略大小写*
- idfname: str -- *idfobject([EpBunch](#EpBunch))的名称，忽略大小写*
- field: str -- *field的名称，忽略大小写，可为下划线或空格*

Returns:
- eval_result: [IDFSearchResult](#IDFSearchResult)

Examples:
*#寻找idfClass == Zone, name == Block1:Zone1, field == Floor_Area的匹配结果*

    >>>model.eval('Zone' , 'Block1:Zone1' , 'Floor_Area')
    IDFsearchresult
    |	Class: Zone,	Name: Block1:Zone1
    |	Field: Floor_Area,	Value: 170

> <a id='search'>search(searchname: str, strict=True, searchlist=None, searchtype=ANYTHING) </a>

增强idfobjects方法，所有search的标准化入口，searchname与searclist接受多种混合输入，提供可打包为[IDFEditor](#IDFEditor)的返回值。此为搜索方法，将返回多个搜索结果。若寻求精确的匹配方法，请使用[IDFModel.eval()](#eval)
<br>Parameters:
- searchname: str or list \<str> -- *搜索的关键词，可用空格键隔开或者传入list*
- strict: bool  --  *为True时无视空格键，将整个关键词放入比较 **待改善：做不到完全精确匹配*** (default:True)
- searchlist: [list \<IDFSearchResult>](#IDFSearchResult) or [list \<eppy.EpBunch>](#EpBunch) -- *为空时搜索整个文件，不为空时只在列表内搜索* (default:None)
- searchtype: enum [ ANYTHING==0 , CLASS==1 , OBJECT==2 , FILED==3 ] (default:0)

Returns:
- search_result: [list \<IDFSearchResult>](#IDFSearchResult)

<br>Example:<br>
*#搜索一切名字带有'material'的*

    >>>model.search('Material')
    [IDFsearchresult
    |	Class: MATERIAL,	Name: Brickwork Outer_O.1	
    |   Field: , 	Value: , 
    IDFsearchresult
    |	Class: MATERIAL,	Name: XPS Extruded Polystyrene  - CO2 Blowing_O.O795 
    |   Field: ,	Value: , 
    IDFsearchresult 
    ...]
*#在一切名字带有'material'的结果中，搜索名字带有'Cast Concrete'的*

    >>>model.search('Cast Concrete',searchlist=model.search('Material'))
    [IDFsearchresult
    |	Class: MATERIAL,	Name: Cast Concrete (Dense)_O.1
    |	Field: ,	Value: ]
*#在一切名字带有'material'的结果中，搜索名字带有'Cast' 或 'Concrete'的*

    model.search('Cast Concrete',searchlist=model.search('Material'),strict=False)
    [IDFsearchresult
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,
    |   Field: ,	Value: , 
    IDFsearchresult    
    |	Class: MATERIAL,	Name: Cast Concrete (Dense)_O.1,	
    |   Field: ,	Value: ]
*#搜索一切在**idfClass中带有Zone**的*

    >>>model.search('Zone',searchtype=ed.CLASS)
    [IDFsearchresult
    |	Class: ZONECAPACITANCEMULTIPLIER:RESEARCHSPECIAL,	Name: All	
    |   Field: ,	Value: , 
    IDFsearchresult
    |	Class: ZONE,	Name: Block1:Zone1, 
    |   Field: ,	Value: , 
    IDFsearchresult
    |	Class: ZONE,	Name: Block2:Zone1,	
    |   Field: ,	Value: , 
    IDFsearchresult
    ...]

*#在**idfClass中带有Zone**的所有结果中，搜索名字带Block1:Zone1的*

    >>>model.search('Block1:Zone1',searchtype=ed.OBJECT,searchlist=model.search('Zone',searchtype=ed.CLASS))
    [IDFsearchresult
    |	Class: ZONE,	Name: Block1:Zone1
    |   Field: ,	Value: , IDFsearchresult
    |	Class: ZONEINFILTRATION:DESIGNFLOWRATE,	Name: Block1:Zone1 Infiltration 
    |	Field:	Value: , 
    IDFsearchresult
    ...]
*#通过[idfobjects](#idfobjects)属性，在**idfClass==Zone**的所有结果中，搜索名字带Block1:Zone1的*

    >>>model.search('Block1:Zone1',searchtype=ed.OBJECT,searchlist=model.idfobjects['Zone'])
    [IDFsearchresult
    |	Class: Zone,	Name: Block1:Zone1
    |   Field: 	Value: ]
*#在idfClass==Zone、name中带有Block1:Zone1的结果中，搜索含有的Floor_Area的field*

    >>>model.search('Floor_Area',searchlist=model.search('Block1:Zone1', searchtype=ed.OBJECT, searchlist=model.idfobjects['Zone']))
    [IDFsearchresult
    |	Class: Zone,	Name: Block1:Zone1
    |   Field: Floor_Area	Value: 170, 
    IDFsearchresult
    |	Class: Zone,	Name: Block1:Zone1,	
    |   Field: Part_of_Total_Floor_Area,	Value: Yes]
> search_object(search_name: list, searchresult: list)

更为轻量的search方法，针对全文件搜索name属性中带有search_name的idfobject([EpBunch](#EpBunch))，并追加至searchresult
<br>Parameters:
- search_name: list\<str> -- *只要含有其中一个search_name，就会被纳入结果*
- searchresult: [list\<IDFSearchResult>](#IDFSearchResult) -- *结果将基于这个list继续追加*

Returns:
- searchresult: [list\<IDFSearchResult>](#IDFSearchResult)
> search_class(earch_name: list, searchresult: list)

更为轻量的search方法，针对全文件搜索idfClass中带有search_name的idfobject([EpBunch](#EpBunch))，并追加至searchresult
<br>Parameters:
- search_name: list\<str> -- *只要含有其中一个search_name，就会被纳入结果*
- searchresult: [list\<IDFSearchResult>](#IDFSearchResult) -- *结果将基于这个list继续追加*

Returns:
- searchresult: [list\<IDFSearchResult>](#IDFSearchResult)
> search_filed(search_name: list, searchresult: list)

更为轻量的search方法，针对全文件搜索field中带有search_name的idfobject([EpBunch](#EpBunch))，并将对应Object和field追加至searchresult
<br>Parameters:
- search_name: list\<str> -- *只要含有其中一个search_name，就会被纳入结果*
- searchresult: [list\<IDFSearchResult>](#IDFSearchResult) -- *结果将基于这个list继续追加*

Returns:
- searchresult: [list\<IDFSearchResult>](#IDFSearchResult)
> search_in_result(search_name: list, searchresult: list, searchtype)

更为轻量的search方法，针对searchresult搜索field/Name/Class中带有search_name的idfobject([EpBunch](#EpBunch))
<br>Parameters:
- search_name: list\<str> -- *只要含有其中一个search_name，就会被纳入结果*
- searchresult: [list\<IDFSearchResult>](#IDFSearchResult) -- *将在此list中进行搜索*
- searchtype: enum [ ANYTHING==0 , CLASS==1 , OBJECT==2 , FILED==3 ] 

Returns:
- searchresult: [list\<IDFSearchResult>](#IDFSearchResult)

> <a id = 'write'> write(group_editor, folder: str = None) </a>

将IDFModel写入某个文件夹，idf文件数量将等于group_editor.params_num，第 *i* 个idf文件的参数取值将依次序 *i* 选取每一个editor的第 *i* 个params
<br>Examples:<br>

    #editor1/2修改第一种material(Brickwork Outer_O.1)的厚度与K值，共10组参数
    #editor3修改第一个房间的面积，共100-150五组参数
    editor1 = IDFEditor(model.search('material')[0],'Thickness',ed.generator.linespace,[0.1,0.4,10])
    editor2 = IDFEditor(model.search('material')[0],'Conductivity',ed.generator.linespace,[0.8,1.0,10])
    editor3 = IDFEditor.fromobject(model.idfobjects['Zone'][0],'Floor_Area',ed.generator.arange,[100,150,10])
    geditor1 = GroupEditor(editor1,editor2)
    geditor2 = GroupEditor(editor3)
    model.write([geditor1,geditor2], r'.\test')
Parameters:
- group_editor: [list \<IDFGroupEditor>](#IDFGroupEditor) or [\<IDFGroupEditor>](#IDFGroupEditor) or [\<IDFEditor>](#IDFEditor)
- folder: str(path) *保存路径，None时保存在baseline的文件夹* (default:None)

Returns:
- None

> <a id='simulation'>simulation</a>(epw=None, overwrite=True, process_count=4,**kwargs) (inherit: [eppy.modeleditor.IDF.run()](https://eppy.readthedocs.io/en/latest/eppy.html#eppy.modeleditor.IDF.run))

对运行过[IDFmodel.write()](#write)的模型进行并行模拟。完成后将自动整理结果文件夹运行[self.read_folder()](#read_folder)
<br>Parameters:
- epw: str(path) or list\<str>(path) -- *模拟时采用的epw文件;，可以是多个epw文件。但不建议在此处进行批量epw赋予，因为结果不容易处理，并且location和groundtemperature信息不会随之改变* (default:None)
- overwirite: bool -- *是否覆盖原有结果。可以传入false实现断点续传，以防突发的模拟中断* (default:True)
- process_count: int -- *并行模拟进程，建议不要超过CPU允许的进程，否则Ep性能会大幅下降，很容易出现模拟错误* (default:4)

Returns:
- None

kwargs: (inherit: [eppy.modeleditor.IDF.run()](https://eppy.readthedocs.io/en/latest/eppy.html#eppy.modeleditor.IDF.run))
- 'verbose': enum [ 'v' , 'q' , 's' ] -- v：*模拟时打印模拟过程 q：只打印报错 s：静默模拟* (default: 'q')
- output_directory : str, optional -- *不要修改！* 
- annual : bool, optional -- *If True then force annual simulation* (default: False)
- design_day : bool, optional -- *Force design-day-only simulation* (default: False)
- idd : str, optional -- *Input data dictionary* (default: Energy+.idd in EnergyPlus directory)
- epmacro : str, optional -- *Run EPMacro prior to simulation* (default: False).
- expandobjects : bool, optional -- *Run ExpandObjects prior to simulation* (default: False)
- readvars : bool, optional -- *Run ReadVarsESO after simulation* (default: False)
- output_prefix : str, optional -- *Prefix for output file names* (default: eplus)
- output_suffix : str, optional -- *Suffix style for output file names* (default: L)
  - L: Legacy (e.g., eplustbl.csv)
  - C: Capital (e.g., eplusTable.csv)
  - D: Dash (e.g., eplus-table.csv)
- version : bool, optional -- *Display version information* (default: False)

> <a id='read_folder'>read_folder(folder: str = None)</a>

读取folder的模拟结果。此方法不需要与baseline对应，可应用于空IDFModel对象上，以提供结果处理的接口
<br> Examples:

    >>>model = IDFModel()
    >>>model.read_folder(r'.\test')
    >>>result1 = model.group_result(ed.Variable("Cumulative", "Electricity:Facility", "J"), 
                                     calculator = np.mean, frequency=ed.Monthly)
    >>>result2 = model.case_result(ed.Variable("Cumulative", "Electricity:Facility", "J"),
                                     case = 0,frequency=ed.Monthly)
Paramters:
- folder: str(path) -- *结果存取的目录。只要是存储结果的上级目录即可，但尽可能不要离结果太远，否则将增加遍历时间,默认调用存储位置，即[write()](#write)时输入的folder* (default:None)

Returns:
- None

> <a id='group_result'>group_result</a>(variable: Variable, calculator, frequency=Monthly, cases=None, alike=False, start_date=None, end_date=None)

包装了reader.get_group_result方法，根据不同[Variable](#Variable)与不同的统计方法、统计频率等获得某些cases的结果。在[Variable](#Variable)词条中，本文档记录了常用的各种variable列表
<br>Parameters:
- variable: [Variable](#Variable) or [list\<Variable>](#Variable) -- *以Variable定义的搜索关键词*
- calculator: method -- *统计用的计算函数，请不要输入()，以调用方法本身（见Example)*
- frequency: enum [ Hourly , Daily , Monthly , Annually ] -- *取结果的频率，逐日数据/逐月数据/全年总和等* (default:Monthly)
- cases: int or list\<int> or str or list\<str> -- *接受多种输入的cases名称或者编号，定义需要统计的cases，None时统计全部* (default:None)
- alike: bool -- *模糊搜索，为True时所有擦边结果都会纳入，False时只有全部对应才行。若要查询所有可严格匹配的variables，可查看[IDFModel.variables](#IDFModel.variables)属性* (default:False)
- start_date -- 查询开始日期 (default:None)
- end_date -- 查询结束日期 (default:None)

Returns:
- summarized_result: [IDFResult](#IDFResult)

Examples:<br>
*#查询全空间累计的逐月电耗，统计所有cases的总合*

    import numpy as np
    model = ed.IDFModel(folder = r'.\test')
    var = ed.Variable(None, "Electricity:Facility", "J")
    result = model.group_result(var,calculator = np.sum)
*#查询全空间累计的逐日灯光能耗与设备能耗，统计所有cases的方差*

    import numpy as np
    model = ed.IDFModel(folder = r'.\test')
    var1 = ed.Variable(None, "InteriorLights:Electricity", "J")
    var2 = ed.Variable(None, "InteriorEquipment:Electricity", "J")
    result = model.group_result(var,calculator = np.var)

*#查询全空间累计的逐日灯光能耗与设备能耗，**不统计,直接存储所有cases \(caculator=np.array)***

    import numpy as np
    model = ed.IDFModel(folder = r'.\test')
    var1 = ed.Variable(None, "InteriorLights:Electricity", "J")
    var2 = ed.Variable(None, "InteriorEquipment:Electricity", "J")
    result = model.group_result(var,calculator = np.array)
*#查询全空间累计的逐日灯光能耗与设备能耗，取cases \[0,1,3,5...] 并统计所有cases的方差*

    import numpy as np
    model = ed.IDFModel(folder = r'.\test')
    var1 = ed.Variable(None, "InteriorLights:Electricity", "J")
    var2 = ed.Variable(None, "InteriorEquipment:Electricity", "J")
    cases = np.arange(0,len(model.sql.values()),2)
    result = model.group_result(var,calculator = np.var,cases=cases)
> <a id='case_result'>case_result</a>(variable: Variable, case:int, frequency=Monthly,alike=False, start_date=None, end_date=None)

包装了reader.get_case_result方法，根据不同[Variable](#Variable)与不同的统计方法、统计频率等获得单个cases的结果。在[Variable](#varexample)中记录了常用的各种variable列表
<br>Parameters:
- variable: [Variable](#Variable) or [list\<Variable>](#Variable) -- *以Variable定义的搜索关键词*
- frequency: enum [ Hourly , Daily , Monthly , Annually ] -- *取结果的频率，逐日数据/逐月数据/全年总和等* (default:Monthly)
- cases: int or list\<int> or str or list\<str> -- *接受多种输入的cases名称或者编号，定义需要统计的cases，None时统计全部* (default:None)
- alike: bool -- *模糊搜索，为True时所有擦边结果都会纳入，False时只有全部对应才行。若要查询所有可严格匹配的variables，可查看[IDFModel.variables](#IDFModel.variables)属性* (default:False)
- start_date -- *查询开始日期* (default:None)
- end_date -- *查询结束日期* (default:None)

Returns:
- summarized_result: [IDFResult](#IDFResult) or [list\<IDFResult>](#IDFResult) -- *若查询了多个cases，将按顺序给出IDFResult \(不过分开几次调用不好吗为啥一定要夹在一起.....)*

---

#### <a id = 'EpBunch'> eppy.EpBunch </a> (inherit [eppy.bunch_subclass.EpBunch](https://eppy.readthedocs.io/en/latest/eppy.html#eppy.bunch_subclass.EpBunch))
<br>Fields, values, and descriptions of fields in an EnergyPlus IDF object stored in a bunch which is a dict extended to allow access to dict fields as attributes as well as by keys.
##### properties
###### fieldnames 
Friendly name for objls.
###### fieldvalues  
Friendly name for obj.
> checkrange(fieldname)

Check if the value for a field is within the allowed range.
<br>Parameters:
- fieldnames -- Friendly name for objls.

Returns:
- result: bool

> get_referenced_object(fieldname)

<br> Get an object referred to by a field in another object.
<br> For example an object of type Construction has fields for each layer, each of which refers to a Material. This functions allows the object representing a Material to be fetched using the name of the layer.
<br> Returns the first item found since if there is more than one matching item, it is a malformed IDF.  
<br> Parameters:
- fieldnames: str -- The name of the field in the referring object which contains the reference to another object.

Returns:
- reference_object: EpBunch

> get_retaincase(fieldname)

check if the field should retain case
<br>Parameters:
- fieldnames -- Friendly name for objls.

Returns:
- result: bool

> getfieldidd(fieldname)

get the idd dict for this field Will return {} if the fieldname does not exist
<br>Parameters:
- fieldnames -- Friendly name for objls.

Returns:
- result: dict -- idd description of the IDF version

> <a id='getrange'>getrange(fieldname)</a>

Get the allowed range of values for a field.
<br>Parameters:
- fieldnames -- Friendly name for objls.

Returns:
- result: list\<> 

> getreferingobjs(iddgroups=None, fields=None)

Get a list of objects that refer to this object
<br>Parameters:
- fields -- Friendly name for objls.

Returns:
- result: list\<EpBunch> 
---

#### <a id = 'IDFSearchResult'> IDFSearchResult</a>
IDFModel.search()系列方法的返回值，[IDFEditor](#IDFEditor)的父类。扩展的EpBunch类，因为直接修改EpBunch将影响IDF本体，因此做了个索引类的接口。IDFSearchResult与idfobject([EpBunch](#EpBunch))是多对一关系
##### properties
###### obj: [eppy.EpBunch](#EpBunch)
存储idfobject([EpBunch](#EpBunch))本体。
###### idfclass: str
idfobject([EpBunch](#EpBunch))的第一条属性，为该idfobject([EpBunch](#EpBunch))的CLASS
###### name: str
idfobject([EpBunch](#EpBunch))的第二条属性(通常情况下) 部分unique的类name即是他的取值，例如Version或SimulationPeriod
###### field: str
这个IDFSearchResult的field，可为空。
###### value: object
当field不为空时该field的数值
##### classmethod
> __init__(obj: eppy.bunch_subclass.EpBunch, idfclass: str = None, name: str = None, field=None) 🔧constructive

根据指向的idfobject([EpBunch](#EpBunch))进行初始化，不输入class与name时自动识别。一般情况下不需要构造IDFSearchResult
<br> Parameters:
- obj: [eppy.bunch_subclass.EpBunch](#EpBunch)
- idfclass: str -- *类型名称* (default: None)
- name: str -- *对象名称* (default: None)
- field: str -- *field名称* (default: None)

Returns:
- None

---

#### <a id = 'IDFEditor'> IDFEditor(IDFsearchresult)</a>
用于对idf文件进行调参，包含某个field的搜索结果以及该field生成参数的方法、生成的参数等。
<br> 如下是一个用于对idf中'Concrete Block'材质K值进行调参的Editor,直接传入list进行采样。此为最常用且最朴实的方法

    >>>searchresult = model.search('Concrete Block', searchlist=model.search('Material'))[0]
    >>>conduct_params = [0.40, 0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.54]
    >>>editor = ed.IDFEditor(searchresult, field='Conductivity', _sampler=ed.generator.enumerate,args=[conduct_params])
    >>>print(editor)
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Conductivity
    |	Value: 0.51
    |	Generator: _enumerate,	args: [[0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]]
    |	params: [0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]
<br> 如下是一个用于对idf中'Concrete Block'材质厚度进行调参的Editor：使用了均匀采样的方法，在 [ 0.1 , 0.3 ] 的范围内进行了8次均匀采样，得到8个参数假如使用这个Editor批量生成idf文件，将会产生8个文件。

    >>>editor2 = ed.IDFEditor(searchresult, field='Thickness', _sampler=ed.generator.uniform,args=[0.1, 0.3, 8])
    >>>print(editor2)
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Thickness
    |	Value: 0.2775968892673033
    |	Generator: _uniform,	args: [0.1, 0.3, 8]
    |	params: [0.23653308807702936, 0.27015122279696446, 0.26021691781725276, 0.2956364025826844, 0.22458860243634488, 0.21587202354876933, 0.1731319291948782, 0.12423114708252805]

##### properties
###### sampler: [Generator](#Generator)
用于批量生成模拟参数采样的方法。
###### args: list \<object>
用于sampler的函数参数。
###### params: list \<object>
生成的模拟参数，在批量模拟中会应用在idf模型里，通过self.generate()更新
###### obj: [eppy.EpBunch](#EpBunch) (inherit: [IDFSearchResult](#IDFSearchResult))
存储idfobject([EpBunch](#EpBunch))本体。
###### idfclass: str (inherit: [IDFSearchResult](#IDFSearchResult))
idfobject([EpBunch](#EpBunch))的第一条属性，为该idfobject([EpBunch](#EpBunch))的CLASS
###### name: str (inherit: [IDFSearchResult](#IDFSearchResult))
idfobject([EpBunch](#EpBunch))的第二条属性(通常情况下) 部分unique的类name即是他的取值，例如Version或SimulationPeriod
###### field: str (inherit: [IDFSearchResult](#IDFSearchResult))
这个IDFSearchResult的field，可为空。
###### value: object (inherit: [IDFSearchResult](#IDFSearchResult))
当field不为空时该field的数值
##### classmethod
> __init__(self, object, field=None, _sampler: Generator = original, args: list = None) 🔧constructive

通过[IDFSearchResult](#IDFSearchResult)或者idfobject([EpBunch](#EpBunch))产生IDFEditor。方法最后会自动更新params
<br>Parameters:
- object: [IDFSearchResult](#IDFSearchResult) or [eppy.EpBunch](#EpBunch)
- field: str -- *需要调参的field，若object传入的是idfobject([EpBunch](#EpBunch))或者不带Field的[IDFSearchResult](#IDFSearchResult),此项不能为空* (default: None)
- _sampler: [Generator](#Generator) -- *注意函数参数名有下划线...见property定义* (default: None)
- args: list \<object> -- *见property定义* (default: [ self.value ] )

Returns:
- None

Examples:
想要使用用户设计的函数func，只需要改为Generator(func)包装就行。如下包装了np.array()来实现枚举类型，但务必注意args只有一个list参数

    >>>editor = ed.IDFEditor(result3, field='Thickness', _sampler=ed.Generator(np.array),args=[[0.1, 0.2, 0.3]])
    >>>print(editor)
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Thickness
    |	Value: 0.2775968892673033
    |	Generator: array,	args: [[0.1, 0.2, 0.3]]
    |	params: [0.1, 0.2, 0.3]

> <a id='IDFEditor.eval'>eval</a>( model, editorstr: str, _sampler: Generator = original,args: list = None)🔧constructive

读取字符串构造Editor.根据'>'进行分割，链接至[IDFModel.eval()](#eval)，格式请参考example

<br>Parameters:
- model: IDFModel -- *用于检查合法性与批量调参的baseline model*
- editorstr: str -- *根据','分割的idfclass/idfname/field*
- _sampler: [Generator](#Generator) -- *注意函数参数名有下划线...见property定义* (default: None)
- args: list \<object> -- *见property定义* (default: [ self.value ] )

Returns:
- None

Examples:

    >>>editor = ed.IDFEditor.eval( model, 'Zone>Block1:Zone1>Floor_Area')
    >>>print(editor)
    IDFEditor
    |	Class: Zone,	Name: Block1:Zone1,	Field: Floor_Area
    |	Value: 316.2622
    |	Generator: _original,	args: [316.2622]
    |	params: [316.2622]

> generate()

运行self.sampler(self.args)，更新模拟参数(self.params) 内部对参数的合法性进行的检查，但不严谨（只能判断数值类参数）
<br>Parameters:
- None

Returns:
- None

> apply_generator(_sampler: Generator, args: list)

想反悔了，可以应用别的generator。完成后会自动更新params
<br>Parameters:
- _sampler: [Generator](#Generator) -- *注意函数参数名有下划线...见properties定义* 
- args: list \<object> -- *见properties定义* 

Returns:
- None

---

#### <a id = 'IDFGroupEditor'> IDFGroupEditor</a>

用于对Editor进行编组。同一个GroupEditor内参数将一一匹配，不同GroupEditor之间将交叉匹配。

##### properties
###### editors: list \<[IDFEditor](#IDFEditor)>
包含的editor,所有GroupEditor的方法为实际引用，将会修改editor的值
###### params_num: int
GroupEditor的模拟参数组的数量
##### classmethod

> __init__( *editors: IDFEditor)🔧constructive

Parameters:
- *editors: IDFEditor -- *不定长参数，可传入多个IDFEditor*

Examples：<br>

    >>>geditor = ed.IDFGroupEditor(editor2,editor3)    
    >>>print(geditor)
    ____________________
    IDFGroupEditor	Paramters: 8
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Thickness
    |	Value: 0.1
    |	Generator: _linspace,	args: [0.1, 0.3, 8]
    |	params: [0.1, 0.1285714285714286, 0.15714285714285714, 0.18571428571428572, 0.2142857142857143, 0.24285714285714285, 0.27142857142857146, 0.3]
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Conductivity
    |	Value: 0.51
    |	Generator: _enumerate,	args: [[0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]]
    |	params: [0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]
    ____________________

> group( *editors )🔧constructive

根据IDFEditor的分组生成GroupEditor
Parameters:
- *editors: IDFEditor or IDFGroupEditor or list \<IDFEditor>

Examples：<br>
- *#Editor1 定义了对Floor_Area的调整，Editor2 定义了对Thickness的调整，Editor3 定义了Conductivity对的调整*

  
    >>>print(editor1)
    IDFEditor
    |	Class: ZONE,	Name: Block1:Zone1,	Field: Floor_Area
    |	Value: 316.2622
    |	Generator: _arange,	args: [100, 200, 10]
    |	params: [100, 110, 120, 130, 140, 150, 160, 170, 180, 190]

    >>>print(editor2)
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Thickness
    |	Value: 0.1
    |	Generator: _linspace,	args: [0.3, 0.1, 8]
    |	params: [0.1, 0.1285714285714286, 0.15714285714285714, 0.18571428571428572, 0.2142857142857143, 0.24285714285714285, 0.27142857142857146, 0.3]

    >>>print(editor3)
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Conductivity
    |	Value: 0.51
    |	Generator: _enumerate,	args: [[0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]]
    |	params: [0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]
- 在批量产生cases时，我们希望editor2与editor3是被同时修改的，即产生类似如下的效果：
<br> case1: Thickness == 0.10, Conductivity == 0.40
<br> case2: Thickness == 0.13, Conductivity == 0.42
<br> case3: Thickness == 0.16, Conductivity == 0.44
<br> case4: Thickness == 0.19, Conductivity == 0.46
<br> ...
<br> 这种情况下，就需要对editor2与editor3打包：


    >>>geditor = ed.IDFGroupEditor.group(editor2,editor3)    
    >>>print(geditor)
    ____________________
    IDFGroupEditor	Paramters: 8
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Thickness
    |	Value: 0.1
    |	Generator: _linspace,	args: [0.1, 0.3, 8]
    |	params: [0.1, 0.1285714285714286, 0.15714285714285714, 0.18571428571428572, 0.2142857142857143, 0.24285714285714285, 0.27142857142857146, 0.3]
    IDFEditor
    |	Class: MATERIAL,	Name: Concrete Block (Medium)_O.1,	Field: Conductivity
    |	Value: 0.51
    |	Generator: _enumerate,	args: [[0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]]
    |	params: [0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54]
    ____________________
- 若我们希望对editor1和上述geditor交叉，产生如下的cases:
<br> case1: Thickness == 0.10, Conductivity == 0.40, Floor_Area == 100
<br> case2: Thickness == 0.13, Conductivity == 0.42, Floor_Area == 100
<br> ...
<br> case8: Thickness == 0.30, Conductivity == 0.54, Floor_Area == 100
<br> case9: Thickness == 0.10, Conductivity == 0.40, Floor_Area == 110
<br> case10: Thickness == 0.13, Conductivity == 0.42, Floor_Area == 110
<br> ...
<br> case80: Thickness == 0.30, Conductivity == 0.54, Floor_Area == 190
<br> 这种情况下，就需要对editor1打包后，与geditor进行cross运算：


    >>>geditor = ed.IDFGroupEditor.group(editor2,editor3)
    >>>geditor.cross(ed.IDFGroupEditor(editor1))
- 也可以简化为如下表达：


    >>>geditor = ed.IDFGroupEditor.group( [ editor2 , editor3 ] , [ editor1 ] )

> cross ( other: IDFGroupEditor )

将其他GroupEditor交叉到本GroupEditor中。将直接修改self
<br> Parameters:
- other: IDFGroupEditor -- *被交叉的另一个GroupEditor*

Returns:
- self: IDFGroupEditor

Examples:

    >>>geditor = ed.IDFGroupEditor.group(editor2,editor3)
    >>>geditor.cross(ed.IDFGroupEditor(editor1))

> <a id='IDFGroupEditor.to_csv()'>to_csv</a>( csvpath: str )

将本groupeditor导出为可读csv格式，以便查阅
<br>Parameters:
- csvpath: str(path) -- *导出路径*

Returns:
- None

> <a id='IDFGroupEditor.to_npy()'>to_npy</a> ( npypath: str )

将本groupeditor导出为二进制npy格式，以便记录，可直接调用load读取生成一样的GroupEditor
<br>Parameters:
- csvpath: str(path) -- *导出路径*

Returns:
- None

> <a id='IDFGroupEditor.load()'>load </a>( model, geditorpath: str )🔧constructive

读取csv或者npy文件构造GroupEditor.根据后缀自动识别，若要读取csv文件，格式请参考example
<br>Parameters:
- model: IDFModel -- *用于检查合法性与批量调参的baseline model*
- geditorpath: str(path) -- *导入文件路径*

Returns:
- None

Examples:
<br>***#test.csv文件示例:***

    ZONE>Block1:Zone1>Floor_Area,   Zone>Block2:Zone1>Floor_Area,   Zone>Block2:Zone1>Volume,   MATERIAL>Concrete Block (Medium)_O.1>Thickness, MATERIAL>Concrete Block (Medium)_O.1>Conductivity
    100,                            126.05937661563902,             138.28256987990844,         0.23985559114742538,                            0.4
    110,                            180.73141712629183,             115.58215798918066,         0.23985559114742538,                            0.4
    120,                             209.70974413186292,            178.15436610989173,         0.23985559114742538,                            0.4
    130,                            130.67673423474824,             214.45392447617894,         0.23985559114742538,                            0.4
    ...

***#load:***
    
    >>>ed.IDFGroupEditor.load(model,'test.csv')
    IDFGroupEditor	Editors: 5	Paramters: 64

---

#### <a id = 'IDFResult'> IDFResult</a>
对结果的存储、展现、IO. 若只希望获取结果，调用IDFResult.data即可
##### properties
###### variables: [list \<Variable>](#Variable)
结果中统计的一个或者多个Variable(s)
###### frequency: enum \[ Hourly , Daily , Monthly , Annually ]
结果记录的频率（逐时、逐日、逐月、逐年）
###### dump: str
结果缓存的路径（或存储的路径）
<br> 由于idf结果，特别是批量案例的结果过于庞大，容易造成内存崩溃，本模块设置了结果大小阈值，超过阈值自动dump
###### data: np.ndarry \<object>
结果的具体内容，内存或本地读取
##### classmethod

> __init__(variables, frequency, data)🔧constructive

超过100000个数据将调用self.save()
Parameters:
- variables: [list \<Variable>](#Variable) -- *结果中统计的一个或者多个Variable(s)*
- frequency: enum \[ Hourly , Daily , Monthly , Annually ] -- *结果记录的频率（逐时、逐日、逐月、逐年）*
- data: np.ndarry \<object> -- *结果的ndarry*

Returns:
- None

> from_npy(path)🔧constructive

从路径载入npy结果,一般情况下直接用np.load()就好了，写完才发现没什么用....
Parameters:
- path: str(path)

Returns:
- self: IDFResult

> save(path: str = os.path.join(Working_Dir, generate_code(6) + '.npy'))

将结果文件以二进制形式存储于某npy文件。将会存储两个文件: [filename].npy, [filename]_variables.npy
Parameters:
- path: str(path) (default: Working_Dir \\ [随机文件名].npy)

Returns:
- None

> <a id='IDFResult.to_csv()'>to_csv</a>(path: str, seq: str = ',')

将结果文件以可读形式存储于某csv文件。
Parameters:
- path: str(path) 
- seq: str -- *csv分隔符* (default: ',')

Returns:
- None

> load()

加载数据到内存中
<br>Parameters:
- None

Returns:
- None


---

#### <a id="Variable">Variable</a> (inherit: [db_epulsout_reader.Variables](https://github.com/DesignBuilderSoftware/db-eplusout-reader))
读取结果时输入的结果关键词，由key,type,unit三部分组成。
##### properties
###### key: str
该结果所属的部位，一般为某Zone的名称，或某Zone的HVAC部件的名称以及 Environment / Whole Building 等。对于某些全建筑的结果会为None
###### type: str
该结果的类型，一般是结果的具体名称，记录在EnergyPlus文档中，例如 DistrictCooling:Facility 等
###### unit: str
结果的单位
##### classmethod
> __init__(key: str, type: str, unit:str)🔧constructive

tips: Variable的保存与打印名称和其构造函数格式是一样的，可以用系统的eval()方法直接构造Variable
<br>Parameters:
- key: str
- type: str
- unit: str

Returns:
- None

##### <a id='varexample'> Example: Variable </a>
下列是常见的idf文件中结果的三个要素。[ZoneName] 指Zone的名称，在DesignBuilder中一般是 Block1:Zone1 的格式。每个idf文件含有的结果不同，这是由DB方面定义的，具体可调用[IDFModel.variables](#IDFModel.variables)查看
<table>
<thead>
<tr><th>KEY</th><th>TYPE</th><th>UNIT</th><th>EVAL</th></tr>
</thead>
<tbody>
<tr><td>None</td><td>Carbon Equivalent:Facility</td><td>kg</td><td>Variable('None','Carbon Equivalent:Facility','kg')</td></tr>
<tr><td>None</td><td>DistrictCooling:Facility</td><td>J</td><td>Variable('None','DistrictCooling:Facility','J')</td></tr>
<tr><td>None</td><td>DistrictHeating:Facility</td><td>J</td><td>Variable('None','DistrictHeating:Facility','J')</td></tr>
<tr><td>None</td><td>Electricity:Facility</td><td>J</td><td>Variable('None','Electricity:Facility','J')</td></tr>
<tr><td>Whole Building</td><td>Facility Total Produced Electricity Energy</td><td>J</td><td>Variable('Whole Building','Facility Total Produced Electricity Energy','J')</td></tr>
<tr><td>None</td><td>InteriorEquipment:Electricity</td><td>J</td><td>Variable('None','InteriorEquipment:Electricity','J')</td></tr>
<tr><td>None</td><td>InteriorLights:Electricity</td><td>J</td><td>Variable('None','InteriorLights:Electricity','J')</td></tr>
<tr><td>[ZoneName]</td><td>Lights Total Heating Rate</td><td>W</td><td>Variable('[ZoneName]','Lights Total Heating Rate','W')</td></tr>
<tr><td>[ZoneName] EQUIPMENT GAIN 1</td><td>Other Equipment Total Heating Rate</td><td>W</td><td>Variable('[ZoneName] EQUIPMENT GAIN 1','Other Equipment Total Heating Rate','W')</td></tr>
<tr><td>Environment</td><td>Site Diffuse Solar Radiation Rate per Area</td><td>W/m2</td><td>Variable('Environment','Site Diffuse Solar Radiation Rate per Area','W/m2')</td></tr>
<tr><td>Environment</td><td>Site Direct Solar Radiation Rate per Area</td><td>W/m2</td><td>Variable('Environment','Site Direct Solar Radiation Rate per Area','W/m2')</td></tr>
<tr><td>Environment</td><td>Site Outdoor Air Barometric Pressure</td><td>Pa</td><td>Variable('Environment','Site Outdoor Air Barometric Pressure','Pa')</td></tr>
<tr><td>Environment</td><td>Site Outdoor Air Dewpoint Temperature</td><td>C</td><td>Variable('Environment','Site Outdoor Air Dewpoint Temperature','C')</td></tr>
<tr><td>Environment</td><td>Site Outdoor Air Drybulb Temperature</td><td>C</td><td>Variable('Environment','Site Outdoor Air Drybulb Temperature','C')</td></tr>
<tr><td>Environment</td><td>Site Solar Altitude Angle</td><td>deg</td><td>Variable('Environment','Site Solar Altitude Angle','deg')</td></tr>
<tr><td>Environment</td><td>Site Solar Azimuth Angle</td><td>deg</td><td>Variable('Environment','Site Solar Azimuth Angle','deg')</td></tr>
<tr><td>Environment</td><td>Site Wind Direction</td><td>deg</td><td>Variable('Environment','Site Wind Direction','deg')</td></tr>
<tr><td>Environment</td><td>Site Wind Speed</td><td>m/s</td><td>Variable('Environment','Site Wind Speed','m/s')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Air Relative Humidity</td><td>%</td><td>Variable('[ZoneName]','Zone Air Relative Humidity','%')</td></tr>
<tr><td>[ZoneName] IDEAL LOADS AIR</td><td>Zone Ideal Loads Heat Recovery Sensible Cooling Rate</td><td>W</td><td>Variable('[ZoneName] IDEAL LOADS AIR','Zone Ideal Loads Heat Recovery Sensible Cooling Rate','W')</td></tr>
<tr><td>[ZoneName] IDEAL LOADS AIR</td><td>Zone Ideal Loads Heat Recovery Total Cooling Rate</td><td>W</td><td>Variable('[ZoneName] IDEAL LOADS AIR','Zone Ideal Loads Heat Recovery Total Cooling Rate','W')</td></tr>
<tr><td>[ZoneName] IDEAL LOADS AIR</td><td>Zone Ideal Loads Supply Air Sensible Cooling Rate</td><td>W</td><td>Variable('[ZoneName] IDEAL LOADS AIR','Zone Ideal Loads Supply Air Sensible Cooling Rate','W')</td></tr>
<tr><td>[ZoneName] IDEAL LOADS AIR</td><td>Zone Ideal Loads Supply Air Total Cooling Rate</td><td>W</td><td>Variable('[ZoneName] IDEAL LOADS AIR','Zone Ideal Loads Supply Air Total Cooling Rate','W')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Infiltration Air Change Rate</td><td>ach</td><td>Variable('[ZoneName]','Zone Infiltration Air Change Rate','ach')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Infiltration Sensible Heat Gain Energy</td><td>J</td><td>Variable('[ZoneName]','Zone Infiltration Sensible Heat Gain Energy','J')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Interior Windows Total Transmitted Beam Solar Radiation Rate</td><td>W</td><td>Variable('[ZoneName]','Zone Interior Windows Total Transmitted Beam Solar Radiation Rate','W')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Lights Electricity Rate</td><td>W</td><td>Variable('[ZoneName]','Zone Lights Electricity Rate','W')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Mean Air Temperature</td><td>C</td><td>Variable('[ZoneName]','Zone Mean Air Temperature','C')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Mean Radiant Temperature</td><td>C</td><td>Variable('[ZoneName]','Zone Mean Radiant Temperature','C')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Mechanical Ventilation Air Changes per Hour</td><td>ach</td><td>Variable('[ZoneName]','Zone Mechanical Ventilation Air Changes per Hour','ach')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Operative Temperature</td><td>C</td><td>Variable('[ZoneName]','Zone Operative Temperature','C')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Other Equipment Total Heating Rate</td><td>W</td><td>Variable('[ZoneName]','Zone Other Equipment Total Heating Rate','W')</td></tr>
<tr><td>[ZoneName]</td><td>Zone People Sensible Heating Rate</td><td>W</td><td>Variable('[ZoneName]','Zone People Sensible Heating Rate','W')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Total Internal Latent Gain Energy</td><td>J</td><td>Variable('[ZoneName]','Zone Total Internal Latent Gain Energy','J')</td></tr>
<tr><td>[ZoneName]</td><td>Zone Windows Total Transmitted Solar Radiation Rate</td><td>W</td><td>Variable('[ZoneName]','Zone Windows Total Transmitted Solar Radiation Rate','W')</td></tr>
</tbody>
</table>


---

#### <a id = 'Generator'> Generator</a>
用于打包调参方法的类型，内部还记录了这些方法所需要的参数，例如:
<br>**包含三个函数参数的伯努利采样**

    >>>print(ed.generator.bernoulli)
    Generator: _bernoulli
    args_count: 3
    times : 单次采样试验次数,即概率P=1时的值
    propety : 事件概率[0,1]
    size : 样本个数
##### properties
###### name: str
方法的名字
###### args_count: int
方法函数的参数个数
###### args_name: list \<str>
方法函数的参数名称
###### args_description: list \<str>
方法函数的参数描述
###### run: method
调用方法本体
##### classmethod
>__init__(self,run_method,descriotion=None)🔧constructive

用户使用该类型时只需要输入方法名就可以
<br>Parameters:
- run_method: method -- *方法本体，不带()传入*
- descriotion: list \<str> -- *方法的描述* (default: None)

Returns:
- None

---

### MEMBER
#### epeditor.utils
##### constants:Hourly,Daily,Monthly,Annually
用于定义结果读取时的频率，详见IDFModel.[group_result](#group_result)与[case_result](#case_result)方法
##### constants:ANYTHING,CLASS,OBJECT,FIELD
用于IDFModel.search()时的搜索对象的定义，详见[IDFModel.search()](#search)
##### get_version(idf_path:str)
从idf文件获得对应版本EnergyPlus
##### method:check_installation(idf_path:str)
从idf文件检查对应版本EnergyPlus是否已安装
##### method:get_idd(idf_path:str)
从idf文件中获得数据库里对应的idd版本解释文件
##### method:normal_pattern(pattern:str)
转义正则表达式的特殊字符
##### error:NotFoundError
当搜索或者匹配找不到相关结果/field不存在时将会报此错误
##### error:VersionError
当idd版本文件不存在或者对应EnergyPlus版本未安装时将出现此错误
##### class:hiddenPrint
使用with()语句调用，可隐藏后续代码的文本输出，并存放在redirect()中.目前无法处理Energyplus的打印文字
##### class:redirect
保存重定向的标准输出(stdout)，并可以dump在某目录.目前无法处理Energyplus的打印文字

---

#### epeditor.generator
##### original
返回原数值的匹配方式。
    
    >>>print(ed.generator.original)
    Generator: _original
    args_count: 1
    value : 原始数值
##### linspace
按照对象数量生成等差数列。

    >>>print(ed.generator.linspace)
    Generator: _linspace
    args_count: 3
    start : 线性采样起点
    end : 线性采样终点
    num : 样本个数
##### arange
按照公差生成等差数列。

    >>>print(ed.generator.arange)
    Generator: _arange
    args_count: 3
    start : 等差数列起点
    end : 等差数列终点
    step : 等差数量的差
##### uniform
在给定数值范围内进行均匀采样。

    >>>print(ed.generator.uniform)
    Generator: _uniform
    args_count: 3
    low : 均匀采样下边界
    high : 均匀采样上边界
    size : 样本个数
##### gaussian
在给定范围内进行高斯采样/普通采样/正态分布采样

    >>>print(ed.generator.gaussian)
    Generator: _gaussian
    args_count: 3
    median : 高斯分布中位数
    scale : 高斯分布标准差
    size : 样本个数
##### bernoulli
在给定数值范围内进行伯努利采样/二项分布采样

    >>>print(ed.generator.bernoulli)
    Generator: _bernoulli
    args_count: 3
    times : 单次采样试验次数,即概率P=1时的值
    propety : 事件概率[0,1]
    size : 样本个数
##### power
在给定数值范围内 [0 , max] 进行指数分布采样

    >>>print(ed.generator.power)
    Generator: _power
    args_count: 3
    max : 采样最大值，结果落在[0,max]
    a : 指数幂,p=ax^(a-1)
    size : 采样个数
##### random
在给定数值范围内进行随机分布采样，结果类似于均匀采样

    >>>print(ed.generator.random)
    Generator: _random
    args_count: 3
    min : 随机采样最小值
    max : 随机采样最大值
    size : 采样个数
##### enumerate
按照输入的数列直接赋值

    >>>print(ed.generator.enumerate)
    Generator: _enumerate
    args_count: 1
    anydata : 所有的取值，为list

---

#### epeditor.idd
##### idd_dir
idd文件夹位置
##### idd_files
idd文件位置

