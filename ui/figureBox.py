import numpy as np

import os,shutil
from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
import traceback
class FigureDialog(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super(FigureDialog, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle('Figure')
        self.tab = QtWidgets.QTabWidget(self)
        self.Layout=QtWidgets.QVBoxLayout(self)
        self.Layout.addWidget(self.tab)
        self.resize(600, 400)
        self.figures=[]
    def addFigure(self,figurePath,hint):
        figWidget = figureWidget(self,figurePath)
        figWidget.setObjectName(hint)
        self.figures.append(figWidget)
        self.tab.addTab(figWidget,'')
        self.tab.setTabText(self.tab.indexOf(figWidget),hint)
class figureWidget(QtWidgets.QWidget):
    def __init__(self,parent=None,figurePath=None):
        super(figureWidget, self).__init__(parent=parent)
        try:
            self.figurePath = figurePath
            if os.path.exists(self.figurePath):
                pixmap = QtGui.QPixmap(self.figurePath)
                self.Figure = QtWidgets.QLabel(self.figurePath,self)
                pixmap.scaled(min(600 / pixmap.width(), 400 / pixmap.height()) * pixmap.width(),
                              min(600 / pixmap.width(), 400 / pixmap.height()) * pixmap.height())
                self.Figure.setPixmap(pixmap)
                self.VBoxLayout = QtWidgets.QVBoxLayout(self)
                self.VBoxLayout.addWidget(self.Figure)
                self.savebutton = QtWidgets.QPushButton('Save')
                self.savebutton.setText('Save Figure')
                self.savebutton.clicked.connect(self.save)
                self.VBoxLayout.addWidget(self.savebutton)
        except Exception as e:
            print(traceback.format_exc())

    def save(self):
        try:
            filePath, filetype = QtWidgets.QFileDialog.getSaveFileName(self, "Select the saving path", "./",
                                                                       'Png File (*.png)')
            if filePath:
                shutil.copy(self.figurePath,filePath)
                print(f'Figure save to: {filePath}')

        except Exception as e:
            print(traceback.format_exc())

def plotToWindow(methodName,figurePath,Dialog=None):
    if not Dialog:
        Dialog = FigureDialog()
        Dialog.show()
        Dialog.addFigure(figurePath,methodName)
        Dialog.setModal(True)
    else:
        Dialog.addFigure(figurePath,methodName)
    return Dialog

