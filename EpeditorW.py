import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import os

QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)


path_to_add = os.path.abspath('.')
sys.path.insert(0, path_to_add)

import epeditor
import ui
from ui import main, event



if __name__ == '__main__':
    #获取UIC窗口操作权限

    MainWindow = QtWidgets.QMainWindow()
    #调自定义的界面（即刚转换的.py对象）
    app = QtWidgets.QApplication(sys.argv)
    Ui = event.Window(MainWindow)

    #显示窗口并释放资源
    MainWindow.show()
    sys.exit(app.exec_())