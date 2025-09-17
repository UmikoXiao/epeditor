import numpy as np
import sys

import re
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QTextCursor, QPainter, QPalette, QColor
from .style import *
from .figureBox import plotToWindow
# from openpyxl.styles import stylesheet

import os
from epeditor import *
from epeditor import generator

import traceback

app = QtWidgets.QApplication(sys.argv)

samplerList = [
    generator.original,
    generator.linspace,
    generator.arange,
    generator.random,
    generator.gaussian,
    generator.uniform,
    generator.bernoulli,
    generator.power,
    generator.enumerate
]

defaultArgsList = [
    [0],
    [0, 10, 10],
    [0, 10, 1],
    [0, 10, 10],
    [5, 1, 10],
    [0, 10, 10],
    [10, 0.5, 10],
    [10, 2, 10],
    ['0,1,2,3,4,5']
]


class emptyBox(QtWidgets.QLabel):
    def __init__(self, parent, i, j, itemheight=rowHight*2):
        super(emptyBox, self).__init__(parent=parent)
        self.i, self.j = i, j
        self.itemheight = itemheight
        self.setMinimumHeight(self.itemheight)
        self.setAcceptDrops(True)
        self.setStyleSheet(emptyBoxStyleSheet)

    def dragEnterEvent(self, event) -> None:
        self.setStyleSheet(emptyBoxStyleSheetHover)
        self.setText('DROP HERE!')
        event.setDropAction(Qt.MoveAction)
        event.accept()

    def dragLeaveEvent(self, a0: QtGui.QDragLeaveEvent) -> None:
        self.setStyleSheet(emptyBoxStyleSheet)
        self.setText('')

    def dropEvent(self, a0: QtGui.QDropEvent) -> None:
        self.parent().addBox(self.i, self.j)


class IDFSearchResultBox(QtWidgets.QCheckBox):
    def __init__(self, parent=None, item: IDFsearchresult = None, rect=None,prj=None):
        super(IDFSearchResultBox, self).__init__(parent)
        if rect is None:
            rect = QtCore.QRect(0, 0, 220, rowHight*2)
        self.prj=prj
        self.showed = False
        self.setGeometry(rect)
        self.setText('                          ')
        self.girdLayout = QtWidgets.QGridLayout(self)
        self.girdLayout.setContentsMargins(20, 5, 5, 5)
        self.girdLayout.setObjectName("girdLayout")
        self.item = item
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.longPressEvent)
        if item:
            idfclass = QtWidgets.QLabel(item.idfclass)
            idfclass.setStyleSheet(titlestylesheet)
            self.girdLayout.addWidget(idfclass, 0, 0, 1, 2)
            if len(str(item.field)) == 0:
                itemname = item.name if len(str(item.name)) <= 30 else item.name[:30] + '...'
                self.girdLayout.addWidget(QtWidgets.QLabel(str(itemname)), 1, 0, 1, 2)
            else:
                itemname = item.name if len(str(item.name)) <= 15 else item.name[:15] + '...'
                itemfield = item.field if len(str(item.field)) <= 15 else item.field[:15] + '...'
                self.girdLayout.addWidget(QtWidgets.QLabel(str(itemname)), 1, 0)
                self.girdLayout.addWidget(QtWidgets.QLabel(str(itemfield)), 1, 1)
            self.setToolTip(self.item.obj.__repr__())

    def mousePressEvent(self, event):
        super(IDFSearchResultBox, self).mousePressEvent(event)
        self.setChecked(self.isChecked())
        self.timer.start(300)


        # 拖拽放下事件

    def longPressEvent(self):
        self.timer.stop()
        try:
            self.drag = QtGui.QDrag(self)  # 创建QDrag对象
            mimedata = QtCore.QMimeData()  # 然后必须要有mimeData对象,用于传递拖拽控件的原始index信息
            self.prj.library['itemposition'] = [-50, -50]
            self.drag.setMimeData(mimedata)
            pixmap = QtGui.QPixmap(self.size())
            pixmap.fill(QColor(192, 192, 192, 0.5))  # 绘制为透明度为0.5的白板
            painter = QPainter(pixmap)
            painter.setOpacity(0.5)  # painter透明度为0.5
            painter.drawPixmap(self.rect(), self.grab())  # 这个很有用，自动绘制整个控件
            painter.end()
            self.drag.setPixmap(pixmap)
            self.prj.library['DragEventObject'] = self.item
            self.drag.exec_(Qt.MoveAction)  # 这个作为drag对象必须执行
        except Exception as e:
            print(traceback.format_exc())


class acceptDeleteBox(QtWidgets.QCheckBox):
    def __init__(self, parent, rect):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setGeometry(rect)
        self.setStyleSheet('background-color: transparent;')
        self.setMinimumSize(20, 5000)
        # self.hide()
        # self.label = QtWidgets.QLabel(parent = self)
        # self.label.setText('Delete')
        # self.label.setGeometry(int(self.width()*0.2),int(self.height()*0.2),int(self.width()*0.6),int(self.height()*0.6))
        # self.label.setStyleSheet(f'color: white;opacity: 0.5;font-size:{int(self.height()*0.6)}px;')
        self.show()

    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent):
        self.setStyleSheet('border:1px solid transparent;background-color: rgb(200,200,230);opacity: 0.5;')
        a0.setDropAction(Qt.MoveAction)
        a0.accept()

    def dragLeaveEvent(self, a0: QtGui.QDragLeaveEvent):
        self.setStyleSheet('background-color: transparent;')

    def dropEvent(self, a0: QtGui.QDropEvent):
        self.parent().deleteEvent()


class IDFEditorBox(QtWidgets.QPushButton):
    def __init__(self, parent=None, item: IDFsearchresult = None, prj=None, rect=QtCore.QRect(0, 0, 220, 150)):
        super().__init__(parent)
        self.prj = prj
        self.setGeometry(rect)
        self.setMinimumHeight(rect.height())
        self.setAcceptDrops(True)
        self.setText('                                       ')
        self.girdLayout = QtWidgets.QGridLayout(self)
        self.girdLayout.setContentsMargins(5, 5, 5, 5)
        self.girdLayout.setObjectName("girdLayout")
        self.item = item
        if item:
            tab_style = titlestylesheet
            idfclass = QtWidgets.QLabel(item.idfclass)
            nametab = QtWidgets.QLabel('NAME')
            fieldtab = QtWidgets.QLabel('FIELD')
            valuetab = QtWidgets.QLabel('VALUE')
            idfclass.setStyleSheet(tab_style)
            nametab.setStyleSheet(tab_style)
            fieldtab.setStyleSheet(tab_style)
            valuetab.setStyleSheet(tab_style)

            self.fieldcombobox = QtWidgets.QComboBox(self)
            self.fieldcombobox.setEditable(True)
            self.fieldcombobox.addItems(item.obj.fieldnames[2:])
            self.fieldcombobox.currentIndexChanged.connect(self.updateSearchResult)
            self.fieldcombobox.setMinimumHeight(int((self.height() - 12) / 4))
            if item.field:
                self.fieldcombobox.setCurrentText(item.field)
            item = IDFEditor(item, field=self.fieldcombobox.currentText())
            if prj:
                prj.editor.append(item)
            itemname = item.name if len(str(item.name)) <= 30 else item.name[:30] + '...'
            # self.itemvalue = QtWidgets.QLabel(str(item.value))
            self.itemvalue = QtWidgets.QLineEdit()
            self.itemvalue.setText(str(item.value))
            self.itemvalue.value = str(item.value)
            self.updateSearchResult()

            self.girdLayout.setColumnStretch(1, 2)
            self.girdLayout.addWidget(idfclass, 0, 0, 1, 2)
            self.girdLayout.addWidget(nametab, 1, 0)
            self.girdLayout.addWidget(fieldtab, 2, 0)
            self.girdLayout.addWidget(valuetab, 3, 0)
            self.girdLayout.addWidget(QtWidgets.QLabel(str(itemname)), 1, 1)
            self.girdLayout.addWidget(self.fieldcombobox, 2, 1)
            self.girdLayout.addWidget(self.itemvalue, 3, 1)

            self.setToolTip(self.item.obj.__repr__())

        self.setGeometry(rect)
        self.setMinimumHeight(rowHight*4)

    def updateSearchResult(self):
        if isinstance(self.item, IDFsearchresult):
            self.item = IDFEditor(self.item, field=self.fieldcombobox.currentText())
        else:
            self.item.field = self.fieldcombobox.currentText()
            self.item.value = self.item.obj[str(self.item.field)]

        self.itemvalue.setText(str(self.item.value))
        self.itemvalue.value = str(self.item.value)

    def mousePressEvent(self, event):
        try:
            if self.itemvalue.text() != self.itemvalue.value:
                texts = f"Do you want to change the baseline value?\n {self.item.__repr__()}\n{self.itemvalue.value} => {self.itemvalue.text()}"
                reply = QtWidgets.QMessageBox.question(self, "Change Baseline Value",
                                                       texts,
                                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                       QtWidgets.QMessageBox.Yes)
                if reply == QtWidgets.QMessageBox.Yes:
                    self.item.obj[self.item.field] = self.itemvalue.text()
                    self.itemvalue.value = self.itemvalue.text()
                    self.prj.model.save()
                else:
                    self.itemvalue.setText(self.itemvalue.value)
                return

            self.drag = QtGui.QDrag(self)  # 创建QDrag对象
            mimedata = QtCore.QMimeData()  # 然后必须要有mimeData对象,用于传递拖拽控件的原始index信息
            self.prj.library['itemposition'] = [-50, -50]
            self.drag.setMimeData(mimedata)
            pixmap = QtGui.QPixmap(self.size())
            pixmap.fill(QColor(192, 192, 192, 0.5))  # 绘制为透明度为0.5的白板
            painter = QPainter(pixmap)
            painter.setOpacity(0.5)  # painter透明度为0.5
            painter.drawPixmap(self.rect(), self.grab())  # 这个很有用，自动绘制整个控件
            painter.end()
            self.drag.setPixmap(pixmap)
            self.drag.setHotSpot(event.pos())
            self.prj.library['DragEventObject'] = self.item
            self.parent().parent().acceptDelete()
            self.drag.exec_(Qt.MoveAction)  # 这个作为drag对象必须执行
        except Exception as e:
            print(traceback.format_exc())

        # 拖拽放下事件


class IDFGroupEditorBox(QtWidgets.QWidget):
    def __init__(self, parent=None, item: IDFGroupEditor = None, prj: project = None,
                 rect=QtCore.QRect(0, 0, 220, 100), dataSheet=None):
        super(IDFGroupEditorBox, self).__init__(parent)
        self.setStyleSheet(GEditorStyleSheet)
        self.item = item
        self.prj = prj
        self.setGeometry(rect)
        if dataSheet:
            self.dataSheet = dataSheet
            self.dataSheetMTime = os.path.getmtime(self.dataSheet)
        else:
            self.dataSheet = None
            self.dataSheetMTime = None
        self.mainWidget = None
        self.idfobjectlist = {}
        self.uniqueLayout = QtWidgets.QHBoxLayout(self)

        self.initFromGEditor(item)

    def initFromGEditor(self, Geditor):
        try:
            totalLine=0
            self.item = Geditor
            if self.mainWidget:
                _tempWidget = self.mainWidget
                self.mainWidget = QtWidgets.QWidget(self)
                self.uniqueLayout.replaceWidget(_tempWidget, self.mainWidget)
                _tempWidget.deleteLater()
            else:
                self.mainWidget = QtWidgets.QWidget(self)
                self.uniqueLayout.addWidget(self.mainWidget)
            self.mainWidget.objSubWidget = []
            self.mainWidget.QLayout = QtWidgets.QVBoxLayout(self.mainWidget)


            if self.item:
                self.idfobjectlist = {}
                for editor in self.item.editors:
                    objnamestr=(editor.idfclass + '>' + editor.name).upper()
                    if objnamestr not in self.idfobjectlist.keys():
                        self.idfobjectlist[objnamestr] = {}
                    fieldnames = editor.obj.fieldnames[2:]
                    for field in fieldnames:
                        if field not in self.idfobjectlist[objnamestr]:
                            self.idfobjectlist[objnamestr][field] = {
                                'editor': None, 'checkbox': None, 'checked': False
                            }
                            fcbox = QtWidgets.QCheckBox(self)
                            fcbox.setText(field)
                            fcbox.clicked.connect(self.clickField)
                            fcbox.objstr = editor.idfclass + '>' + editor.name + '>' + field
                            self.idfobjectlist[objnamestr][field]['checkbox'] = fcbox
                    self.idfobjectlist[objnamestr][editor.field]['editor'] = editor
                    self.idfobjectlist[objnamestr][editor.field]['checkbox'].setChecked(True)
                    self.idfobjectlist[objnamestr][editor.field]['checked'] = True

                for ki, key in enumerate(self.idfobjectlist.keys()):
                    subWidget = QtWidgets.QWidget(self.mainWidget)
                    subWidget.gridLayout = QtWidgets.QGridLayout(subWidget)
                    self.mainWidget.objSubWidget.append(subWidget)

                    # objTab
                    totalLine += 1
                    objTab = QtWidgets.QLabel(key)
                    objTab.setStyleSheet(titlestylesheet)
                    objTab.setFixedHeight(rowHight)
                    subWidget.gridLayout.addWidget(objTab, 0, 0,1,4)
                    subWidget.gridLayout.setRowStretch(0, 1)

                    # checkbox
                    for i, field in enumerate(self.idfobjectlist[key].keys()):
                        subWidget.gridLayout.addWidget(
                            self.idfobjectlist[key][field]['checkbox'],
                            int(np.floor(i / 4)) + 1, i % 4
                        )
                        subWidget.gridLayout.setRowStretch(int(np.floor(i / 4)) + 1, 1)
                    totalLine += int(np.floor(len((self.idfobjectlist[key].keys()))/4))+1
                    self.mainWidget.QLayout.addWidget(subWidget)

            self.openButtun = QtWidgets.QPushButton('OpenFile')
            self.openButtun.setText('Open...')
            self.openButtun.clicked.connect(self.openFile)
            self.mainWidget.QLayout.addWidget(self.openButtun)
            totalLine+=1

            self.setMinimumHeight(totalLine*rowHight+50)
            self.setMinimumWidth(self.mainWidget.sizeHint().width())
            self.clickField()
            # print([f'{k}:{len(self.idfobjectlist[k])}' for k in self.idfobjectlist.keys()])

        except Exception as e:
            print(traceback.format_exc())

    def dump(self):
        if not self.dataSheet:
            dataSheet = self.prj.tempFolder + r'\ged' + utils.generate_code(4) + '.csv'
            self.packGroupEditor().to_csv(dataSheet)
            self.dataSheet=dataSheet
            self.dataSheetMTime = os.path.getmtime(self.dataSheet)
        else:
            self.item.to_csv(self.dataSheet)
            self.dataSheetMTime = os.path.getmtime(self.dataSheet)

    def checkUpdate(self,init=False):
        if self.dataSheet:
            if self.dataSheetMTime != os.path.getmtime(self.dataSheet):
                gEditor = IDFGroupEditor.load(self.prj.model, self.dataSheet)
                self.dataSheetMTime = os.path.getmtime(self.dataSheet)
                if init:
                    self.initFromGEditor(gEditor)
                else:
                    self.item = gEditor
                    for editor in self.item.editors:
                        self.idfobjectlist[(editor.idfclass + '>' + editor.name).upper()][editor.field]['editor'] = editor
                return True
        return False
    def openFile(self):
        if not self.checkUpdate():
            self.dump()
        os.startfile(self.dataSheet)

    def clickField(self):
        try:
            self.checkUpdate()
            for key in self.idfobjectlist.keys():
                for field in self.idfobjectlist[key].keys():
                    itemdict = self.idfobjectlist[key][field]
                    if itemdict['checkbox'].isChecked() != itemdict['checked']:
                        if itemdict['checkbox'].isChecked():
                            editor = IDFEditor.eval(self.prj.model, itemdict['checkbox'].objstr)
                            editor.args = [editor.value, self.item.params_num]
                            self.item = IDFGroupEditor.merge(self.item, editor)
                            itemdict['checked'] = True
                            itemdict['editor'] = editor
                        else:
                            self.item.drop(itemdict['checkbox'].objstr)
                            itemdict['checked'] = False
                            itemdict['editor'] = None
            self.dump()
        except Exception as e:
            print(traceback.format_exc())

    def packGroupEditor(self):
        self.checkUpdate()
        editors = []
        for key in self.idfobjectlist.keys():
            for field in self.idfobjectlist[key].keys():
                itemdict = self.idfobjectlist[key][field]
                if itemdict['checked']:
                    editors.append(itemdict['editor'])
        gEditor = IDFGroupEditor(*editors)
        return gEditor

    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent):
        self.setStyleSheet('background-color: rgb(220,220,250);')
        a0.setDropAction(Qt.MoveAction)
        a0.accept()

    def dragLeaveEvent(self, a0: QtGui.QDragLeaveEvent):
        self.setStyleSheet('background-color: white;')

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super(IDFGroupEditorBox, self).mousePressEvent(event)
        try:
            if event.button() == Qt.RightButton:
                self.drag = QtGui.QDrag(self)  # 创建QDrag对象
                self.drag.setHotSpot(event.pos())

                mimedata = QtCore.QMimeData()  # 然后必须要有mimeData对象,用于传递拖拽控件的原始index信息
                pos = self.mapFromGlobal(event.globalPos())
                self.prj.library['itemposition'] = [-pos.x(), -pos.y()]
                self.drag.setMimeData(mimedata)
                pixmap = QtGui.QPixmap(self.size())
                pixmap.fill(QColor(192, 192, 192, 0.5))  # 绘制为透明度为0.5的白板
                painter = QPainter(pixmap)
                painter.setOpacity(0.5)  # painter透明度为0.5
                painter.drawPixmap(self.rect(), self.grab())  # 这个很有用，自动绘制整个控件
                painter.end()
                self.drag.setPixmap(pixmap)
                self.prj.library['DragEventObject'] = self.packGroupEditor()
                self.parent().childPressEvent(self)
                self.deleteLater()
                self.drag.exec_(Qt.MoveAction)  # 这个作为drag对象必须执行

        except Exception as e:
            traceback.print_exc()

class ResultBox(QtWidgets.QWidget):
    def __init__(self,prj:project,parent=None, rect=QtCore.QRect(0, 0, 220, 150)):
        super(ResultBox, self).__init__(parent=parent)
        self.setGeometry(rect)
        self.result=None
        self.Dialog=None
        self.prj = prj
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.timeStep = QtWidgets.QWidget(self)
        self.variables_Scroll = QtWidgets.QScrollArea(self)
        self.calculator = QtWidgets.QWidget(self)
        self.timeStep.setStyleSheet(GEditorStyleSheet)
        self.calculator.setStyleSheet(GEditorStyleSheet)
        self.variablesWidget = QtWidgets.QWidget(self.variables_Scroll)
        self.variables_Scroll.setGeometry(QtCore.QRect(0, 0, 500, rowHight * 6))
        self.variables_Scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.variables_Scroll.setWidgetResizable(False)
        self.exportResult = QtWidgets.QPushButton('Export')
        self.exportResult.setText('Export to *.Csv')
        self.exportResult.clicked.connect(self.toCsv)
        self.visualize = QtWidgets.QPushButton('visualize')
        self.visualize.setText('Plot the Result')
        self.visualize.clicked.connect(self.plot)
        self.showBox = []
        self.validVariables = []
        self.initResultWidget()

    def initResultWidget(self):
        try:
            # Time step area
            self.timeStep.Layout = QtWidgets.QVBoxLayout(self.timeStep)
            self.timeStep.buttonGroup = QtWidgets.QButtonGroup()
            self.timeStep.Title = QtWidgets.QLabel('Temporal Resolution')
            self.timeStep.Title.setStyleSheet(titlestylesheet)
            self.timeStep.selectBox = []
            self.timeStep.selection = None
            for i,freq in enumerate([utils.TimeStep,utils.Hourly,utils.Daily,utils.Monthly,utils.Annually,utils.RunPeriod]):
                tsSelectBox = QtWidgets.QRadioButton(self.timeStep)
                tsSelectBox.setText(utils.to_sql_frequency(freq))
                tsSelectBox.hint = freq
                self.timeStep.Layout.addWidget(tsSelectBox)
                self.timeStep.buttonGroup.addButton(tsSelectBox,i)
                self.timeStep.selectBox.append(tsSelectBox)
            self.timeStep.buttonGroup.buttonClicked[int].connect(self.updateVariables)

            # variables Area
            self.variables_Scroll.Title = QtWidgets.QLabel('Select Variables')
            self.variables_Scroll.Title.setStyleSheet(titlestylesheet)
            self.variables_Scroll.varBox = {}
            self.variablesWidget.Layout = QtWidgets.QVBoxLayout(self.variablesWidget)
            self.variables_Scroll.setWidget(self.variablesWidget)
            self.variables_Scroll.variableSearch = QtWidgets.QLineEdit(self)
            self.variables_Scroll.variableSearch.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.variables_Scroll.variableSearch.setAlignment(Qt.AlignVCenter)
            self.variables_Scroll.variableSearch.setFont(QtGui.QFont('Calibri', 12))
            self.variables_Scroll.variableSearch.textChanged.connect(self.searchVariables)

            # calculator Area
            self.calculator.Layout = QtWidgets.QVBoxLayout(self.calculator)
            self.calculator.buttonGroup = QtWidgets.QButtonGroup()
            self.calculator.Title = QtWidgets.QLabel('Statistical Method')
            self.calculator.Title.setStyleSheet(titlestylesheet)
            self.calculator.selectBox = []
            self.calculator.selection = None
            for i, method in enumerate([np.array,np.sum,np.mean,np.median,np.std,np.min,np.max]):
                methodName = ['rawData','sum','mean','median','std','min','max']
                tsSelectBox = QtWidgets.QRadioButton(self.calculator)
                tsSelectBox.setText(methodName[i])
                tsSelectBox.hint = method
                self.calculator.Layout.addWidget(tsSelectBox)
                self.calculator.buttonGroup.addButton(tsSelectBox, i)
                self.calculator.selectBox.append(tsSelectBox)

            for key in self.prj.model.variables.keys():
                self.variables_Scroll.varBox[key] = []
                for var in self.prj.model.variables[key]:
                    _name = f"{var.key},{var.type},{var.units}"
                    shortName = f"{var.key},{var.type[:40]}...,{var.units}" if len(_name) > 60 else _name
                    _varBox = QtWidgets.QCheckBox(self.variablesWidget)
                    _varBox.setText(shortName)
                    _varBox.setToolTip(_name)
                    _varBox.hint=var
                    self.variables_Scroll.varBox[key].append(_varBox)

            # summary target
            self.calculator.caseSummary = QtWidgets.QCheckBox(self.calculator)
            self.calculator.caseSummary.setText('summary cases')
            self.calculator.caseSummary.clicked.connect(self.caseSummaryChangeText)
            self.calculator.caseSummary.click()

            # selectAll
            self.variables_Scroll.selectAll = QtWidgets.QPushButton(self.variables_Scroll)
            self.variables_Scroll.selectAll.setText('SELECT ALL')
            self.variables_Scroll.selectAll.clicked.connect(self.selectAll)

            # timestep area
            self.gridLayout.addWidget(self.timeStep.Title, 0, 0, 1, 1)
            self.gridLayout.addWidget(self.timeStep, 1, 0, 2, 1)
            self.gridLayout.addWidget(self.calculator.caseSummary, 3, 0, 1, 1)
            # variables area
            keyWord = QtWidgets.QLabel('KeyWords:')
            keyWord.setStyleSheet(titlestylesheet)
            self.gridLayout.addWidget(self.variables_Scroll.Title, 0, 1, 1, 3)
            self.gridLayout.addWidget(self.variables_Scroll, 1, 1, 1, 3)
            self.gridLayout.addWidget(keyWord, 2, 1, 1, 1)
            self.gridLayout.addWidget(self.variables_Scroll.variableSearch, 2, 2, 1, 1)
            self.gridLayout.addWidget(self.variables_Scroll.selectAll, 2, 3, 1, 1)
            # calculator area
            self.gridLayout.addWidget(self.calculator.Title, 0, 4, 1, 1)
            self.gridLayout.addWidget(self.calculator, 1, 4, 2, 1)
            # self.gridLayout.addWidget(self.calculator.caseSummary, 2, 3, 1, 1)
            # self.gridLayout.addWidget(self.exportResult, 3, 0, 1, 1)
            self.gridLayout.addWidget(self.visualize, 3, 1, 1, 4)
            self.gridLayout.setRowMinimumHeight(0,rowHight)
            self.gridLayout.setRowMinimumHeight(1, compressedRowHight*6)
            self.gridLayout.setRowMinimumHeight(2, rowHight)
            self.gridLayout.setRowStretch(0, 1)
            self.gridLayout.setRowStretch(1, 6)
            self.gridLayout.setRowStretch(2, 1)
        except Exception as e:
            traceback.print_exc()

    def selectAll(self):
        for _varBox in self.showBox:
            _varBox.setChecked(True)
    def caseSummaryChangeText(self):
        if self.calculator.caseSummary.isChecked():
            self.calculator.caseSummary.setText('summary variables')
        else:
            self.calculator.caseSummary.setText('summary cases')
    def updateVariables(self,idx):
        try:
            self.validVariables = list(self.variables_Scroll.varBox.values())[idx]
            self.showVariables(self.validVariables)
        except Exception as e:
            traceback.print_exc()
    def showVariables(self,showBox):
        self.showBox=showBox
        for _varBoxList in self.variables_Scroll.varBox.values():
            for _varBox in _varBoxList:
                _varBox.setParent(self.variables_Scroll)
        self.variablesWidget.deleteLater()
        self.variablesWidget = QtWidgets.QWidget(self.variables_Scroll)
        self.variablesWidget.Layout = QtWidgets.QVBoxLayout(self.variablesWidget)
        self.variables_Scroll.setWidget(self.variablesWidget)
        boxMaxLength = 0
        for _varBox in self.showBox:
            self.variablesWidget.Layout.addWidget(_varBox)
            boxMaxLength = max(boxMaxLength, _varBox.sizeHint().width())
        self.variablesWidget.setGeometry(QtCore.QRect(0, 0, boxMaxLength+50, compressedRowHight * len(self.showBox)))
    def searchVariables(self):
        searhText = self.variables_Scroll.variableSearch.text().strip()
        showBox = []
        if len(searhText)>2:
            for _varBox in self.validVariables:
                if re.search(searhText, _varBox.hint.key + _varBox.hint.type ,re.IGNORECASE) != None:
                    showBox.append(_varBox)
            self.showVariables(showBox)
        if len(searhText)==0:
            self.showVariables(self.validVariables)
    def extrudeResult(self):
        try:
            _variables = []
            for _varBox in self.showBox:
                if _varBox.isChecked():
                    _variables.append(_varBox.hint)
            case = "variables" if self.calculator.caseSummary.isChecked() else "cases"
            # print(_variables,self.calculator.buttonGroup.checkedButton().hint,self.timeStep.buttonGroup.checkedButton().hint)
            result = self.prj.model.group_result(variable=_variables,
                                        calculator=self.calculator.buttonGroup.checkedButton().hint,
                                        frequency=self.timeStep.buttonGroup.checkedButton().hint,
                                        x=case)
            result.metaData['method'] = self.calculator.buttonGroup.checkedButton().text()
            return result
        except Exception as e:
            traceback.print_exc()

    def toCsv(self):
        try:
            if self.prj.model is not None:
                filePath, filetype = QtWidgets.QFileDialog.getSaveFileName(self, "Select the CSV saving path", "./",
                                                                           'CSV Files (*.csv)')
                if filePath:
                    result = self.extrudeResult()
                    result.to_csv(filePath)
                    os.startfile(filePath)
        except Exception as e:
            traceback.print_exc()

    def plot(self):
        try:
            from matplotlib import pyplot as plt
            result = self.extrudeResult()
            for i, dat in enumerate(result.data):
                plt.plot(dat)
                plt.ylabel(f"{result.metaData['method']}({result.variables[i].units})")
                plt.xlabel(result.frequency)
                plt.title(result.variables[i].key+'\n'+result.variables[i].type)
                figurePath = os.path.join(self.prj.tempFolder, 'line' + utils.generate_code(5) + '.png')
                plt.savefig(figurePath)
                plt.clf()
                self.Dialog = plotToWindow(Dialog=self.Dialog,figurePath=figurePath,methodName='plot')
            self.Dialog.exec_()
        except Exception as e:
            traceback.print_exc()
# class IDFGroupEditorBoxLageacy(QtWidgets.QCheckBox):
#
#     def __init__(self, parent=None, item: IDFGroupEditor = None, prj: project = None,
#                  rect=QtCore.QRect(0, 0, 220, 100), clickElement=None):
#         super(IDFGroupEditorBox, self).__init__(parent)
#         if isinstance(item, IDFEditor):
#             item = IDFGroupEditor(item)
#         self.clickElement = clickElement
#         self.item = item
#         self.prj = prj
#         self.setGeometry(rect)
#         self.gridlayout = QtWidgets.QGridLayout(self)
#         self.gridlayout.setContentsMargins(25, 10, 10, 10)
#         self.objstrbox = {}
#         self.fieldeditbox = {}
#         self.checkedLast = self.isChecked()
#         if item:
#             self.idfobjectlist = {}
#             for editor in item.editors:
#                 if editor.idfclass + '>' + editor.name not in self.idfobjectlist.keys():
#                     self.idfobjectlist[editor.idfclass + '>' + editor.name] = {}
#                     fieldnames = editor.obj.fieldnames[2:]
#                     for field in fieldnames:
#                         self.idfobjectlist[editor.idfclass + '>' + editor.name][field] = {
#                             'editor': None, 'checked': False, 'checkbox': None, 'fieldobject': None
#                         }
#                 self.idfobjectlist[editor.idfclass + '>' + editor.name][editor.field]['editor'] = editor
#
#             groupindex = -1
#             for key in self.idfobjectlist.keys():
#                 groupindex += 1
#                 objTab = QtWidgets.QLabel(' ')
#                 objTab.setStyleSheet(titlestylesheet)
#                 objTab.setMinimumWidth(20)
#                 self.gridlayout.addWidget(objTab, groupindex, 0)
#
#                 # eidtingBox
#                 editingbox = QtWidgets.QWidget(self)
#                 editingbox.gridlayout = QtWidgets.QGridLayout(editingbox)
#                 editingbox.gridlayout.setContentsMargins(0, 0, 0, 0)
#                 self.fieldeditbox[key] = editingbox
#                 self.gridlayout.addWidget(editingbox, groupindex, 1)
#
#                 # objstrbox
#                 objstrbox = QtWidgets.QLabel(key)
#                 objstrbox.setStyleSheet(titlestylesheet)
#                 self.objstrbox[key] = objstrbox
#                 editingbox.gridlayout.addWidget(objstrbox, 0, 0, 1, 3)
#
#                 # checkbox
#                 fieldnames = list(self.idfobjectlist[key].keys())
#                 for i in range(len(fieldnames)):
#                     field = fieldnames[i]
#                     fcbox = QtWidgets.QCheckBox(self)
#                     fcbox.setText(field)
#                     fcbox.objstr = key + '>' + field
#                     fcbox.clicked.connect(self.click_field)
#                     editingbox.gridlayout.addWidget(fcbox, int(np.floor(i / 4)) + 1, i % 4)
#
#                     self.idfobjectlist[key][field]['checkbox'] = fcbox
#
#             for editor in item.editors:
#                 self.idfobjectlist[editor.idfclass + '>' + editor.name][editor.field]['checkbox'].setChecked(True)
#             self.click_field()
#             self.arrange()
#
#     def click_field(self):
#         try:
#             for key in self.idfobjectlist.keys():
#                 for field in self.idfobjectlist[key].keys():
#                     itemdict = self.idfobjectlist[key][field]
#                     if itemdict['checkbox'].isChecked() != itemdict['checked']:
#                         if not itemdict['checked']:
#                             samplerline = self.create_sampler_object(itemdict['checkbox'].objstr)
#                             samplerline.rowindex = self.fieldeditbox[key].gridlayout.rowCount()
#                             self.fieldeditbox[key].gridlayout.addWidget(samplerline,
#                                                                         self.fieldeditbox[key].gridlayout.rowCount(), 0,
#                                                                         1, 4)
#                             itemdict['checked'] = True
#                         else:
#                             itemdict['fieldobject'].deleteLater()
#                             itemdict['fieldobject'] = None
#                             itemdict['checked'] = False
#                             self.reset_editing_box(key)
#             self.arrange()
#         except Exception as e:
#             print(traceback.format_exc())
#
#     def reset_editing_box(self, key):
#         editingbox = self.fieldeditbox[key]
#         new_editingbox = QtWidgets.QWidget(self)
#         new_editingbox.gridlayout = QtWidgets.QGridLayout(new_editingbox)
#         new_editingbox.gridlayout.setContentsMargins(0, 0, 0, 0)
#         checkboxs = [self.idfobjectlist[key][field]['checkbox'] for field in self.idfobjectlist[key]]
#         fieldobjects = [self.idfobjectlist[key][field]['fieldobject'] for field in self.idfobjectlist[key] if
#                         self.idfobjectlist[key][field]['fieldobject']]
#         for i in range(len(checkboxs)):
#             new_editingbox.gridlayout.addWidget(checkboxs[i], int(np.floor(i / 4)), i % 4)
#         for line in fieldobjects:
#             new_editingbox.gridlayout.addWidget(line, new_editingbox.gridlayout.rowCount(), 0, 1,
#                                                 new_editingbox.gridlayout.columnCount())
#         row, col, _, _ = self.gridlayout.getItemPosition(self.gridlayout.indexOf(editingbox))
#         self.gridlayout.removeWidget(editingbox)
#         self.gridlayout.addWidget(new_editingbox, row, col)
#         editingbox.deleteLater()
#         self.fieldeditbox[key] = new_editingbox
#
#     def create_sampler_object(self, objstr):
#         objstr2 = objstr.split('>')
#         key = objstr2[0] + '>' + objstr2[1]
#         field = objstr2[2]
#
#         samplerline = QtWidgets.QWidget(self)
#         samplerline.HBoxLayout = QtWidgets.QHBoxLayout(samplerline)
#         samplerline.HBoxLayout.setContentsMargins(0, 0, 0, 0)
#
#         if not self.idfobjectlist[key][field]['editor']:
#             self.idfobjectlist[key][field]['editor'] = IDFEditor.eval(self.prj.model, objstr)
#
#         # sampler combobox
#         fieldcombobox = QtWidgets.QComboBox(self)
#         fieldcombobox.setEditable(True)
#         samplernamelist = [sam.name for sam in samplerList]
#         fieldcombobox.addItems(samplernamelist)
#         currenttext = self.idfobjectlist[key][field]['editor'].sampler.name
#         currentindex = samplernamelist.index(currenttext)
#         fieldcombobox.objstr = objstr
#         fieldcombobox.currentIndexChanged.connect(lambda objstr: self.updatesampler(fieldcombobox.objstr))
#         fieldcombobox.setCurrentIndex(currentindex)
#
#         samplerline.HBoxLayout.addWidget(QtWidgets.QLabel(field))
#         samplerline.HBoxLayout.addWidget(fieldcombobox)
#         self.idfobjectlist[key][field]['fieldobject'] = samplerline
#
#         self.updatesampler(objstr)
#
#         return samplerline
#
#     def updatesampler(self, objstr):
#         try:
#             objstr2 = objstr.split('>')
#             key = objstr2[0] + '>' + objstr2[1]
#             field = objstr2[2]
#             samplerline = self.idfobjectlist[key][field]['fieldobject']
#             samitem = samplerline.HBoxLayout.itemAt(1)
#             if samitem:
#                 samindex = samitem.widget().currentIndex()
#                 if samindex == 0:
#                     self.idfobjectlist[key][field]['editor'].apply_generator(_sampler=samplerList[0],
#                                                                              args=[self.idfobjectlist[key][field][
#                                                                                        'editor'].value])
#                 else:
#                     self.idfobjectlist[key][field]['editor'].apply_generator(_sampler=samplerList[samindex],
#                                                                              args=defaultArgsList[samindex])
#
#                 argsbox = self.create_argsbox(objstr)
#
#                 try:
#                     samplerline.HBoxLayout.removeWidget(samplerline.argsbox)
#                     samplerline.argsbox.deleteLater()
#                     samplerline.argsbox = argsbox
#                     samplerline.HBoxLayout.addWidget(argsbox)
#                 except:
#                     samplerline.argsbox = argsbox
#                     samplerline.HBoxLayout.addWidget(argsbox)
#
#         except Exception as e:
#             print(traceback.format_exc())
#
#     def create_argsbox(self, objstr):
#         objstr2 = objstr.split('>')
#         key = objstr2[0] + '>' + objstr2[1]
#         field = objstr2[2]
#
#         # args editing box
#         argsbox = QtWidgets.QWidget(self)
#         argsbox.HBoxLayout = QtWidgets.QHBoxLayout(argsbox)
#         argsbox.HBoxLayout.setContentsMargins(0, 0, 0, 0)
#         argsbox.argsedit = []
#         for args_name, args in zip(self.idfobjectlist[key][field]['editor'].sampler.args_name,
#                                    self.idfobjectlist[key][field]['editor'].args):
#             argsbox.HBoxLayout.addWidget(QtWidgets.QLabel(args_name))
#             argsbox.argsedit.append(QtWidgets.QLineEdit(argsbox))
#             argsbox.argsedit[-1].setText(str(args))
#             argsbox.objstr = objstr
#             argsbox.argsedit[-1].textChanged.connect(lambda objstr: self.change_args(argsbox.objstr))
#             argsbox.HBoxLayout.addWidget(argsbox.argsedit[-1])
#
#         return argsbox
#
#     def change_args(self, objstr):
#         objstr2 = objstr.split('>')
#         key = objstr2[0] + '>' + objstr2[1]
#         field = objstr2[2]
#
#         samplerline = self.idfobjectlist[key][field]['fieldobject']
#         editor = self.idfobjectlist[key][field]['editor']
#         item = samplerline.HBoxLayout.itemAt(1)
#         if item:
#             argsbox = item.widget()
#             args = [lineedit.text() for lineedit in argsbox.argsedit]
#             editor.args = args
#             editor.generate()
#
#     def arrange(self, rowHeight=30):
#         total_row = np.sum([box.gridlayout.rowCount() for box in self.fieldeditbox.values()])
#         self.setGeometry(self.pos().x(), self.pos().y(), 800, int(total_row * rowHeight))
#         self.setMinimumHeight(int(total_row * rowHeight))
#         for i in range(self.gridlayout.rowCount()):
#             self.gridlayout.setRowStretch(i, 10)
#             self.gridlayout.setRowMinimumHeight(i,
#                                                 list(self.fieldeditbox.values())[i].gridlayout.rowCount() * rowHeight)
#         self.gridlayout.setColumnStretch(0, 1)
#         self.gridlayout.setColumnStretch(1, 99)
#
#         for editingbox in self.fieldeditbox.values():
#             for i in range(editingbox.gridlayout.rowCount()):
#                 editingbox.gridlayout.setRowStretch(i, 10)
#                 editingbox.gridlayout.setRowMinimumHeight(i, rowHeight)
#
#             for i in range(editingbox.gridlayout.columnCount()):
#                 editingbox.gridlayout.setColumnStretch(i, 10)
#                 editingbox.gridlayout.setColumnStretch(i, 100)
#
#     def packGroupEditor(self):
#         editors = []
#         for key in self.idfobjectlist.keys():
#             for field in self.idfobjectlist[key].keys():
#                 itemdict = self.idfobjectlist[key][field]
#                 if itemdict['checked']:
#                     editors.append(itemdict['editor'])
#         geditor = IDFGroupEditor(*editors)
#         return geditor
#
#     def dragEnterEvent(self, a0: QtGui.QDragEnterEvent):
#         self.setStyleSheet('background-color: rgb(220,220,250);')
#         a0.setDropAction(Qt.MoveAction)
#         a0.accept()
#
#     def dragLeaveEvent(self, a0: QtGui.QDragLeaveEvent):
#         self.setStyleSheet('background-color: white;')
#
#     def mousePressEvent(self, event: QtGui.QMouseEvent):
#         super(IDFGroupEditorBox, self).mousePressEvent(event)
#         try:
#             if event.button() == Qt.RightButton:
#                 self.drag = QtGui.QDrag(self)  # 创建QDrag对象
#                 self.drag.setHotSpot(event.pos())
#
#                 mimedata = QtCore.QMimeData()  # 然后必须要有mimeData对象,用于传递拖拽控件的原始index信息
#                 pos = self.mapFromGlobal(event.globalPos())
#                 self.prj.library['itemposition'] = [-pos.x(), -pos.y()]
#                 self.drag.setMimeData(mimedata)
#                 pixmap = QtGui.QPixmap(self.size())
#                 pixmap.fill(QColor(192, 192, 192, 0.5))  # 绘制为透明度为0.5的白板
#                 painter = QPainter(pixmap)
#                 painter.setOpacity(0.5)  # painter透明度为0.5
#                 painter.drawPixmap(self.rect(), self.grab())  # 这个很有用，自动绘制整个控件
#                 painter.end()
#                 self.drag.setPixmap(pixmap)
#                 self.prj.library['DragEventObject'] = self.packGroupEditor()
#                 self.clickElement.childRightPressEvent(self)
#                 self.deleteLater()
#                 self.drag.exec_(Qt.MoveAction)  # 这个作为drag对象必须执行
#
#             elif event.button() == Qt.LeftButton:
#                 if self.isChecked() != self.checkedLast:
#                     self.checkedLast = self.isChecked()
#                     self.clickElement.childLeftPressEvent()
#         except Exception as e:
#             traceback.print_exc()


# class LineChart(QtWidgets.QFrame):
#     def __init__(self, parent, rect: QtCore.QRect, data: list, color: list):
#         super(LineChart, self).__init__(parent=parent)
#         self.setGeometry(rect)
#         self.data = [np.array(dataTwins) for dataTwins in data]
#         self.xDim = np.array([[np.min(xSeries, axis=0), np.max(xSeries, axis=0)] for xSeries in data])
#         self.yDim = np.array([[np.min(ySeries, axis=1), np.max(ySeries, axis=1)] for ySeries in data])
#         self.xDim = [np.min(self.xDim, axis=0), np.max(self.xDim, axis=1)]
#         self.yDim = [np.min(self.yDim, axis=0), np.max(self.yDim, axis=1)]
#         self.lineColor = color
#
#     def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
#         self.painter = QPainter()
#         self.painter.begin(self)
#
#         for color, dataSeries in zip(self.lineColor, self.data):
#             self.drewLines(color, dataSeries[:, 0], dataSeries[:, 1])
#
#         self.drewLine([0, 0], [0, self.height()])
#         self.drewLine([0, self.width()], [0, 0])
#
#         for i in range(10):
#             self.drewLine([0, 5], [self.height() / 10 * i, self.height() / 10 * i])
#             self.drewLine([self.width() / 10 * i, self.width() / 10 * i], [self.height() - 5, self.height()])
#         self.painter.end()
#
#     def drewLines(self, color: QColor, xSeries, ySeries):
#         pen = QtGui.QPen(color, 2, Qt.SolidLine)
#         self.painter.setPen(pen)
#         xSeries = self.width() * (np.array(xSeries) - self.xDim[0]) / (self.xDim[1] - self.xDim[0])
#         ySeries = self.height() * (np.array(ySeries) - self.yDim[0]) / (self.yDim[1] - self.yDim[0])
#         for i in range(len(xSeries) - 1):
#             # 四个参数分别是横坐标的起始位置，纵坐标的起始位置，横坐标的最终位置，纵坐标的最终位置
#             self.painter.drawLine(xSeries[i], ySeries[i], xSeries[i + 1], ySeries[i + 1])
#
#     def drewLine(self, xSeries, ySeries):
#         pen = QtGui.QPen(QColor(0, 0, 0), 2, Qt.SolidLine)
#         self.painter.setPen(pen)
#         self.painter.drawLine(xSeries[0], ySeries[0], xSeries[-1], ySeries[-1])
