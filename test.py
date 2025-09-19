import os,sys
path_to_add = os.path.abspath('.')
sys.path.insert(0, path_to_add)
import epeditor as ed

# model =ed.IDFModel(r'D:\works\trainStation\model\C.idf')
# ged = ed.IDFGroupEditor.load(model,r'D:\works\trainStation\model\ged0x228f.csv')
# model.write(ged,'test')
#

ed.simulate_local('test',r'C:\EnergyPlusV24-1-0\WeatherData\USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw')