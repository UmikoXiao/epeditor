import time

import json
import os
import sys
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QFrame
from PyQt5.QtGui import QTextCursor, QPainter, QPalette, QColor
from .main import Ui_MainWindow
from epeditor import *
import traceback
from .idfwidget import editorWidget, groupEditorWidget, searchWidget, relateSearchWidget, resultWidget
from .idfbox import IDFSearchResultBox
from .qtitle import QTitleButton
from .style import *
from .moosasQA import sendQuestion, cleanMsg

app = QtWidgets.QApplication(sys.argv)


class Signal(QObject):
    text_update = pyqtSignal(str)

    def write(self, text):
        self.text_update.emit(str(text))
        # loop = QEventLoop()
        # QTimer.singleShot(100, loop.quit)
        # loop.exec_()
        QApplication.processEvents()


def get_dir(hint):
    with open('defaultDir.json', 'r+') as f:
        dirs = json.load(f)
        if hint in dirs:
            if os.path.exists(dirs[hint]):
                return dirs[hint]
        return '.'


def write_dir(hint, path):
    dirs = {}
    with open('defaultDir.json', 'r+') as f:
        dirs = json.load(f)
    with open('defaultDir.json', 'w+') as f:
        dirs[hint] = os.path.dirname(path)
        json.dump(dirs, f)


class TextStream(QObject):
    def __init__(self, stdout):
        super().__init__()
        self.printer = stdout

    def write(self, text):
        _translate = QtCore.QCoreApplication.translate
        self.printer.repaint()
        self.printer.setText(_translate("MainWindow", text))
        self.printer.repaint()
        QApplication.processEvents()

    def flush(self):
        return


class MultiInputDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """
        fields  : list[str]         每栏提示文本
        defaults: list[str] | None 默认值
        """
        super().__init__(parent)
        self.setWindowTitle('Parallelized Event Dialog')
        self.edits = []

        self.vBoxLayout = QtWidgets.QVBoxLayout(self)

        # simulation method
        self.CoreSelect = QtWidgets.QWidget(self)
        self.CoreSelect.Layout = QtWidgets.QHBoxLayout(self.CoreSelect)
        self.CoreSelect.buttonGroup = QtWidgets.QButtonGroup()
        self.CoreSelect.Title = QtWidgets.QLabel('Simulation Method')
        self.CoreSelect.setStyleSheet(GEditorStyleSheet)
        self.CoreSelect.Title.setStyleSheet(titlestylesheet)

        self.CoreSelect.Local = QtWidgets.QRadioButton(self.CoreSelect)
        self.CoreSelect.Local.setText('Local')
        self.CoreSelect.Local.hint = 'Local'
        self.CoreSelect.Layout.addWidget(self.CoreSelect.Local)
        self.CoreSelect.buttonGroup.addButton(self.CoreSelect.Local, 0)
        self.CoreSelect.Local.click()

        self.CoreSelect.Cloud = QtWidgets.QRadioButton(self.CoreSelect)
        self.CoreSelect.Cloud.hint = 'Cloud'
        self.CoreSelect.Cloud.setText('Cloud')
        self.CoreSelect.Layout.addWidget(self.CoreSelect.Cloud)
        self.CoreSelect.buttonGroup.addButton(self.CoreSelect.Cloud, 1)

        # parameters
        self.localParameters = QtWidgets.QWidget(self)
        self.localParameters.Layout = QtWidgets.QHBoxLayout(self.localParameters)
        self.localParameters.setStyleSheet(GEditorStyleSheet)
        self.localParameters.forceCPU = QtWidgets.QCheckBox(self.localParameters)
        self.localParameters.forceCPU.setText('fix allocate CPUs')
        self.localParameters.Layout.addWidget(self.localParameters.forceCPU)
        self.localParameters.cpus = QtWidgets.QLineEdit(self.localParameters)
        self.localParameters.cpus.setText('8')
        self.localParameters.Layout.addWidget(self.localParameters.cpus)

        # OK
        self.OK = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok,
                                             Qt.Horizontal, self)
        self.OK.accepted.connect(self.accept)

        # layout
        self.vBoxLayout.addWidget(self.CoreSelect.Title)
        self.vBoxLayout.addWidget(self.CoreSelect)
        self.vBoxLayout.addWidget(self.localParameters)
        self.vBoxLayout.addWidget(self.OK)

    def values(self):
        """返回当前所有文本"""
        core = self.CoreSelect.buttonGroup.checkedButton().hint == 'Local'
        return {'core': core, 'cpus': int(self.localParameters.cpus.text()),
                'forceCPU': self.localParameters.forceCPU.isChecked()}


# 中间类Window的写法
class Window(Ui_MainWindow, QtWidgets.QMainWindow):
    def closeEvent(self, a0):
        cleanMsg()

    def __init__(self, MainWindow, prj=project()):
        super(Window, self).__init__()
        self.setupUi(MainWindow)
        self.prj = prj
        self.project_folder = None
        self.showDir = '.'
        self.MainWindow = MainWindow

        # 实时显示输出, 将控制台的输出重定向到界面中
        # sys.stdout = self.TextStream(self.massage)
        self.stdout = Signal()
        self.stdout.text_update.connect(self.updatetext)
        sys.stdout = self.stdout
        self.saved = False
        self.project_path = ''
        self.exectext.setMinimumHeight(5)
        self.prj.library['DragEventObject'] = None
        self.initLayout()

    def initLayout(self):
        self.cleanBrowser(False)
        _translate = QtCore.QCoreApplication.translate
        # IDFEditor editing area
        self.editorBoxArea = editorWidget(parent=self.IDFEditorDumpArea, prj=self.prj, window=self)
        self.editorBoxArea.setGeometry(QtCore.QRect(0, 0, self.IDFEditorDumpArea.width(), 269))
        self.editorBoxArea.setObjectName("IDFDumpAreaWidget")
        self.IDFEditorDumpArea.setWidget(self.editorBoxArea)

        # SearchResultArea
        self.searchResultArea.keywordArea = searchWidget(parent=self.searchResultArea, prj=self.prj, window=self)
        self.searchResultArea.relatedArea = relateSearchWidget(parent=self.searchResultArea, prj=self.prj, window=self)
        self.searchResultArea.keywordArea.setObjectName("tab_search")
        self.searchResultArea.relatedArea.setObjectName("tab_node")
        self.searchResultArea.addTab(self.searchResultArea.keywordArea, "")
        self.searchResultArea.addTab(self.searchResultArea.relatedArea, "")
        self.searchResultArea.setTabText(self.searchResultArea.indexOf(self.searchResultArea.keywordArea),
                                         _translate("MainWindow", "Select by search"))
        self.searchResultArea.setTabText(self.searchResultArea.indexOf(self.searchResultArea.relatedArea),
                                         _translate("MainWindow", "Select by reference"))

        # ProcessingArea
        self.analysisArea.Layout = QtWidgets.QVBoxLayout(self.analysisArea)
        self.groupEditorArea_Scroll = QtWidgets.QScrollArea(self.analysisArea)
        self.groupEditorArea_Scroll.setGeometry(QtCore.QRect(109, 109, 200, 200))
        self.groupEditorArea_Scroll.setObjectName("scrollArea")
        self.groupEditorArea_Scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.groupEditorArea_Scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.groupEditorArea_Scroll.setWidgetResizable(False)
        self.analysisArea.Layout.addWidget(self.groupEditorArea_Scroll)

        # ProcessingArea-GroupEditor
        self.groupEditorArea = groupEditorWidget(parent=self.groupEditorArea_Scroll, prj=self.prj, window=self)
        self.groupEditorArea.setGeometry(
            QtCore.QRect(0, 0, 800, 400))
        self.groupEditorArea.setObjectName("groupEditorArea")
        self.groupEditorArea_Scroll.setWidget(self.groupEditorArea)

        # ProcessingArea-ResultAnalysis
        self.resultAnalysisArea = resultWidget(parent=self.analysisArea, prj=self.prj, window=self)
        self.resultAnalysisArea.setGeometry(
            QtCore.QRect(0, 0, self.groupEditorArea_Scroll.width(), self.groupEditorArea_Scroll.height()))
        self.resultAnalysisArea.setObjectName("resultAnalysisArea")

        self.PutthemintoGroup.clicked.connect(self.clickStage2)
        self.ResultAnalysis.clicked.connect(self.clickStage3)
        self.clickStage2()

        # menu
        self.actionImport_Baseline_IDF.triggered.connect(self.action_import_idf)
        self.actionSave.triggered.connect(self.action_save)
        self.actionSave.setShortcut('Ctrl + S')
        self.actionSave_As.triggered.connect(self.action_saveAs)
        self.actionSave_As.setShortcut('Ctrl + Shift + S')
        self.actionLoad.triggered.connect(self.action_load)
        self.actionIDFReference.triggered.connect(self.action_idfreference)
        self.actionPythonDocument.triggered.connect(self.action_readme)
        self.actionAbout.triggered.connect(self.action_printAbout)
        self.actionOpen_Project_Folder.triggered.connect(self.action_prjfolder)
        self.actionOpen_IDD_Folder.triggered.connect(self.action_iddfolder)
        self.actionExport_Simulation_Params.triggered.connect(self.action_SimParams)
        self.actionWrite.triggered.connect(self.action_write)
        self.actionSimulation.triggered.connect(self.action_Simulation)
        self.actionContinueSimulation.triggered.connect(self.action_continueSimulation)
        self.actionSet_Result_Folder.triggered.connect(self.action_Result_Folder)

        self.exec.clicked.connect(self.click_QA)
        self.exectext.QA = self.click_QA
        self.exectext.exec = self.executionLine
        self.exec_lable.setStyleSheet(self.exec_lable.selectStyleSheet)
        self.exec_lable.clicked.connect(self.cleanBrowser)
        with open(r'.\ui\main.qss') as f:
            qss1 = f.read()
            app.setStyleSheet(qss1)

        if self.prj.model is None:
            self.importHint = {}
            self.importHint['analysisArea'] = QtWidgets.QPushButton(self.analysisArea)
            self.importHint['analysisArea'].setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                                          QtWidgets.QSizePolicy.Expanding)
            self.importHint['analysisArea'].setStyleSheet(suggestionBoxStyleSheet)
            self.importHint['analysisArea'].setFont(QtGui.QFont('Arial', 30))
            self.importHint['analysisArea'].clicked.connect(self.action_import_idf)
            self.importHint['analysisArea'].setText('Import a baseline *.idf...')

            self.analysisArea.Layout.replaceWidget(self.groupEditorArea_Scroll, self.importHint['analysisArea'])
            self.groupEditorArea_Scroll.hide()
            print('Please import a baseline *.idf...')
        else:
            self.groupEditorArea_Scroll.show()
            self.importHint['analysisArea'].hide()
            self.groupEditorArea_Scroll.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.analysisArea.Layout.replaceWidget(self.importHint['analysisArea'], self.groupEditorArea_Scroll)

    def updatetext(self, text):
        """更新textBrowser"""
        _translate = QtCore.QCoreApplication.translate
        # self.massage.setText()
        cursor = self.textBrowser.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.textBrowser.insertPlainText(_translate("MainWindow", text))
        self.textBrowser.setTextCursor(cursor)
        self.textBrowser.ensureCursorVisible()

    def action_write(self):
        try:
            geditor, fileNames = self.groupEditorArea.crossAllGroupEditors()
            filePath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select the saving path",get_dir('simulation'))
            if filePath:
                write_dir('simulation', filePath)
                self.prj.model.write(geditor, filePath, fileNames)
        except Exception as e:
            traceback.print_exc()

    def action_Simulation(self):
        try:
            if self.prj.model:
                if not self.prj.model.folder:
                    print('******IDFs haven\'t write yet, select a folder******')
                    self.action_write()
                print('******Select a weather file******')
            else:
                print('******baseline haven\'t imported, select a folder******')
                filePath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select the project path", get_dir('simulation'))
                if filePath:
                    write_dir('simulation', filePath)
                    self.prj.model = IDFModel(r'\doc\sample.idf')
                    self.prj.model.folder = filePath

            if self.prj.model.folder:
                self.simulation()

        except Exception as e:
            traceback.print_exc()

    def action_continueSimulation(self):
        try:
            if not self.prj.model:
                self.prj.model = IDFModel(r'\doc\sample.idf')
            if not self.prj.model.folder:
                filePath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select the project path", get_dir('simulation'))
                if filePath:
                    write_dir('simulation', filePath)
                    self.prj.model.folder = filePath
            if self.prj.model.folder:
                self.simulation()
        except Exception as e:
            traceback.print_exc()

    def simulation(self):
        filePath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Select the EnergyPlus Weather Files",
                                                                   get_dir('weather'),
                                                                   'EnergyPlus Weather Files (*.epw)')
        if filePath:
            # return {'core': core, 'cpus': int(self.localParameters.cpus.text()),
            #         'forceCPU': self.localParameters.forceCPU.isChecked()}
            write_dir('weather', filePath)
            dlg = MultiInputDialog(self)
            if dlg.exec_() == QtWidgets.QDialog.Accepted:
                val = dlg.values()
                self.prj.model.simulation(epw=filePath, overwrite=False, stdout=self.stdout,
                                          local=val['core'], process_count=val['cpus'], forceCPU=val['forceCPU'])
                print('******Simulation begin, turn to CMD....******')
                self.resultAnalysisArea.initResultView()
                print('******ALL DONE******')

    def action_idfreference(self):
        os.system(r'doc\InputOutputReference.pdf')

    def action_readme(self):
        os.system(r'doc\ReadMe.md')

    def action_printAbout(self):
        with open(r'doc\About.md') as f:
            print(f.read())

    def action_Result_Folder(self):
        try:
            filePath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select the result folder", get_dir('simulation'))
            if filePath:
                self.prj.model.read_folder(filePath)
                write_dir('simulation',filePath)
                self.resultAnalysisArea.initResultView()
                try:
                    self.exportButton.clicked.disconnect()
                except Exception as e:
                    pass
                self.exportButton.clicked.connect(self.resultAnalysisArea.resultBox.toCsv)
        except Exception as e:
            traceback.print_exc()

    def action_prjfolder(self):
        if self.project_folder:
            os.system("explorer.exe %s" % self.project_folder)

    def action_iddfolder(self):
        os.system("explorer.exe .\\epeditor\\idd")

    def action_SimParams(self):
        try:
            geditor = self.groupEditorArea.crossAllGroupEditors()
            filePath, filetype = QtWidgets.QFileDialog.getSaveFileName(self, "Select the saving path",  get_dir('project'),
                                                                       'Csv Files (*.csv)')
            if filePath:
                write_dir('project', filePath)
                geditor.to_csv(filePath)
        except Exception as e:
            traceback.print_exc()

    def action_save(self):
        try:
            if self.saved:
                self.prj.save(self.project_path)
                print(f'Project save to: {self.project_path}')
            else:
                self.action_saveAs()
        except Exception as e:
            print(traceback.format_exc())

    def action_saveAs(self):
        try:
            filePath, filetype = QtWidgets.QFileDialog.getSaveFileName(self, "Select the saving path",  get_dir('project'),
                                                                       'Epeditor Zip Files (*.zip)')
            if filePath:
                write_dir('project', filePath)
                self.prj.save(filePath)
                print(f'Project save to: {filePath}')
                self.project_path = filePath
                self.project_folder = os.path.dirname(filePath)
                self.saved = True

        except Exception as e:
            print(traceback.format_exc())

    def action_load(self):
        try:
            filePath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Select the project file", get_dir('project'),
                                                                       'Epeditor Zip Files (*.zip)')
            if filePath:
                write_dir('project', filePath)
                self.prj = project.load(filePath)
                window = self.MainWindow
                self.__init__(window, prj=self.prj)
                self.prj.stdout = self.stdout
                self.project_path = filePath
                self.project_folder = os.path.dirname(filePath)
                self._updatePrj(self.prj)
                self.saved = True
                self.prj.library['DragEventObject'] = None
                # self.initLayout()
                if len(self.prj.editor) > 0:
                    self.editorBoxArea.addEditorBox(self.prj.editor, overwrite=False)
                    self.editorBoxArea.setMinimumWidth(280)

                print(f'Loading Finish. Select a EpBunch to start......\n>>>model = IDFModel({filePath})')
        except Exception as e:
            print(traceback.format_exc())

    def _updatePrj(self, prj):
        self.searchResultArea.relatedArea.relateProcessingArea.prj = prj
        self.searchResultArea.keywordArea.prj = prj
        self.searchResultArea.relatedArea.prj = prj
        self.groupEditorArea.prj = prj
        self.editorBoxArea.prj = prj
        self.resultAnalysisArea.prj = prj

    def action_import_idf(self):
        try:
            filePath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Select the baseline *.idf file",
                                                                       get_dir('project'),
                                                                       'EnergyPlus Input Files (*.idf)')
            if filePath:
                write_dir('project', filePath)
                self.prj = project(IDFModel(filePath), stdout=self.stdout)
                self.prj.library['references'] = self.prj.get_references(processes=4, stdout=self.stdout)
                self.prj.library['DragEventObject'] = None
                window = self.MainWindow
                self.__init__(window, prj=self.prj)
                self._updatePrj(self.prj)
                print(f'Loading Finish. Select a EpBunch to start......\n>>>model = IDFModel({filePath})')
        except Exception as e:
            print(traceback.format_exc())

    def cleanBrowser(self, reconnect=True):
        self.textBrowser.clear()
        if reconnect:
            msg = cleanMsg()
            print(msg)
        print(time.ctime())
        print('To execute lines: (numEnter)')
        self.exec_L("print('Hello world!')")
        print('To talk with MoosasQA: (Ctrl + Enter)')
        print('>>>How are you?')
        print(
            "MoosasQA:I'm just a computer program, so I don't have feelings, but I'm here to help you! How can I assist you today?")

    def click_QA(self):
        try:
            lines = self.exectext.toPlainText()
            print('>>>' + lines)
            answer = sendQuestion(lines)
            print(f'MoosasQA:{answer}')
            self.exectext.lastText = lines
            self.exectext.setText('')
        except Exception as e:
            print(traceback.format_exc())

    def executionLine(self):
        try:
            lines = self.exectext.toPlainText()
            self.exec_L(lines)
        except Exception as e:
            print(traceback.format_exc())

    def exec_L(self, args):
        model = self.prj.model
        print('>>>' + args)
        if args[0] == '!' or args[0] == '！':
            answer = sendQuestion(args[1:])
            print(f'MoosasQA:{answer}')
        else:
            exec(args)
        self.exectext.lastText = args
        self.exectext.setText('')

    def click_Add(self):
        try:
            adding = []
            for i in np.arange(self.searchResultArea.keywordArea.SearchResultLayout.count() - 1, -1, -1):
                element = self.searchResultArea.keywordArea.SearchResultLayout.itemAt(i)
                if element.widget():
                    element = element.widget()
                    if isinstance(element, IDFSearchResultBox):
                        if element.isChecked():
                            adding.append(element.item)
            self.editorBoxArea.addEditorBox(adding)
        except Exception as e:
            print(traceback.format_exc())

    def click_Add_Node(self):
        try:
            adding = []
            for i in np.arange(self.searchResultArea.relatedArea.relateProcessingArea.gridlayout.count() - 1, -1, -1):
                element = self.searchResultArea.relatedArea.relateProcessingArea.gridlayout.itemAt(i)
                if element.widget():
                    element = element.widget()
                    if isinstance(element, IDFSearchResultBox):
                        if element.isChecked():
                            adding.append(element.item)
            self.editorBoxArea.addEditorBox(adding)
        except Exception as e:
            print(traceback.format_exc())

    def clickStage2(self):
        self.PutthemintoGroup.setStyleSheet(QTitleButton.selectStyleSheet)
        self.ResultAnalysis.setStyleSheet(QTitleButton.unselectStyleSheet)
        self.exportButton.setText('From *.csv')
        try:
            self.exportButton.clicked.disconnect()
        except Exception as e:
            pass
        self.exportButton.clicked.connect(self.groupEditorArea.editorFromCSV)
        self.resultAnalysisArea.hide()
        self.groupEditorArea_Scroll.show()
        self.groupEditorArea.show()
        self.analysisArea.Layout.replaceWidget(self.resultAnalysisArea, self.groupEditorArea_Scroll)

    def clickStage3(self):
        self.ResultAnalysis.setStyleSheet(QTitleButton.selectStyleSheet)
        self.PutthemintoGroup.setStyleSheet(QTitleButton.unselectStyleSheet)
        self.exportButton.setText('Results to *.csv')
        try:
            self.exportButton.clicked.disconnect()
        except Exception as e:
            pass
        self.groupEditorArea.hide()
        self.groupEditorArea_Scroll.hide()
        self.resultAnalysisArea.show()
        self.analysisArea.Layout.replaceWidget(self.groupEditorArea_Scroll, self.resultAnalysisArea)
        if self.prj.model:
            if self.prj.model.folder:
                self.resultAnalysisArea.initResultView()
                self.exportButton.clicked.connect(self.resultAnalysisArea.resultBox.toCsv)
