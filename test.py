import epeditor as ed
import numpy as np

if __name__ == '__main__':

    '''1. 读取baseline idf文件，建议先升级为22.2版本，或者安装对应版本的energyplus'''
    model = ed.IDFModel(r'project\baseline.idf')

    '''2. 寻找需要修改的field.所有搜索忽略大小写'''
    # 匹配Zone类型对象：‘Block2:zone1’的Floor_Area,class和name的词条忽略大小写,但Field名称要注意大小写
    result1 = model.eval(idfclass= 'Zone',idfname= 'Block2:zone1',field= 'Floor_Area')

    # 匹配material类型对象：'Concrete Block (Medium)_O.1'的Thickness和Conductivity
    result2 = model.eval('material', 'Concrete Block (Medium)_O.1', 'Thickness')
    result3 = model.eval('material', 'Concrete Block (Medium)_O.1', 'Conductivity')

    # 匹配WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM类型对象：'Simple 1001'的UFactor和SHGC
    result4 = model.eval('WindowMaterial:SimpleGlazingSystem', 'Simple 1001', 'UFactor')
    result5 = model.eval('WindowMaterial:SimpleGlazingSystem', 'Simple 1001',
                         'Solar Heat Gain Coefficient')  # 带空格或下划线都可以

    ''' 3.对idf文件进行批量调参。例如：当前项目需要对IDF模型中的area进行调参，生成100,110,120....200十一个参数
    
    IDFEditor()用于生成生成需要调整的params:
        field：若搜索类型不是ed.FIELD，此处需要补充field的名称
        _sampler：Generator()的采样方式，具体可在generator.py中增删或寻找。用于生成一系列的params，一般为numpy函数打包而成
        args：_sampler产生params所用的函数参数。
    '''
    # 修改result1，使用arange方法生成10个params
    editor1 = ed.IDFEditor(result1, _sampler=ed.generator.arange, args=[100, 200, 10])

    editor = model.eval('Building', 'Building', 'North_Axis')

    # 修改名为Floor_Area的field，使用random方法生成8个params
    editor2 = ed.IDFEditor(model.idfobjects['ZONE'][1], field='Floor_Area', _sampler=ed.generator.random,
                                       args=[110, 230, 8])
    # 修改result2，使用uniform采样方法生成8个params
    editor3 = ed.IDFEditor(result2, _sampler=ed.generator.uniform, args=[0.1, 0.3, 8])

    # 修改修改result3，使用enumerate采样方法生成8个params,即直接输入参数
    conduct_params = [0.40, 0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.54]
    editor4 = ed.IDFEditor(result3, _sampler=ed.generator.enumerate, args=[conduct_params])
    # 修改名为'Conductivity'的field，区分大小写，使用enumerate采样方法生成8个params
    # 同样修改4,5，都采用高斯采样生成6个params
    editor5 = ed.IDFEditor(result4, _sampler=ed.generator.gaussian, args=[1.8, 2.2, 6])
    editor6 = ed.IDFEditor(result5, _sampler=ed.generator.gaussian, args=[0.3, 0.5, 6])


    '''
        4. 使用GroupEditor()对editor进行打包。
            在同一个GroupEditor中所有params按位匹配。即10个params的editor1,editor2,editor3会生成10个idf。当editor的参数个数不等时，按照最少的取值
            在不同GroupEditor中所有params交叉匹配。即10个params的GroupEditor1与8个params的GroupEditor2生成8*10=80个idf文件
    '''
    geditor=ed.IDFGroupEditor.group([editor1,editor2,editor3],[editor4,editor5,editor6])
    geditor.to_csv('test.csv')

    '''5. 将模型写入folder，生成一系列idf文件。文件的数量为GroupEditor的params数量'''
    model.write(geditor, r'd:\test')

    '''6. 模拟。默认为本地模拟.
        
        IDF.simulation()：
            epw: 使用的 **一个或者多个** epw文件
            prs_count: 并行进程数，默认为4
            verbose: 是否打印模拟过程，v：什么都打印 q：energyplus.exe只报错，不打印 s：什么都不打印
    '''
    model.simulation(epw=r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Beijing.Beijing.545110_SWERA.epw')

    '''7. 读取模拟结果，有两种方法：
        
        IDFModel.group_result() 获取对所有case的模拟输出，并应用某函数对输出进行统计；
            variables: Variable类型（或为Variable的list），包含key，type和unit三个参数，详见技术文档
            calculator: 结果统计方法，一般是numpy的参数，np.mean np.sum等
            frequency: 统计的频率,ed.Hourly,ed.Daily,ed.Monthly,ed.Annually选一个
        
        IDFModel.case_result() 获取单个case的模拟输出；
            variables: Variable类型（或为Variable的list），包含key，type和unit三个参数，详见技术文档
            case: 结果统计方法，一般是numpy的参数，np.mean np.sum等
            frequency: 统计的频率,ed.Hourly,ed.Daily,ed.Monthly,ed.Annually选一个
    '''
    result1 = model.group_result(ed.Variable("Cumulative", "Electricity:Facility", "J"), calculator = np.mean, frequency=ed.utils.Monthly)
    result2 = model.case_result(ed.Variable("Cumulative", "Electricity:Facility", "J"),case = 0,frequency=ed.utils.Monthly)

    '''8.调用IDFResult.save()/IDFResult.to_csv()保存为npy二进制格式或者csv可读格式'''
    result1.to_csv(r'result1.csv')
    result2.save(r'result2.npy')

