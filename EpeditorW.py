import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import sys




if __name__ == '__main__':
    #获取UIC窗口操作权限
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    from ui import main, event
    MainWindow = QtWidgets.QMainWindow()
    #调自定义的界面（即刚转换的.py对象）
    app = QtWidgets.QApplication(sys.argv)
    Ui = event.Window(MainWindow)

    #显示窗口并释放资源
    MainWindow.show()
    sys.exit(app.exec_())