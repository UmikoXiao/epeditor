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
        """
        Emit a text update signal and process pending GUI events.
        
        Parameters
        ----------
        text : str
            The text to be emitted via the text_update signal. Will be converted to string if not already.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.text_update.emit(str(text))
        # loop = QEventLoop()
        # QTimer.singleShot(100, loop.quit)
        # loop.exec_()
        QApplication.processEvents()


def get_dir(hint):
    """
    Get the directory path associated with a given hint from a JSON configuration file.
    
    Parameters
    ----------
    hint : str
        The key to look up in the JSON file 'defaultDir.json'. Represents a directory alias.
    
    Returns
    -------
    str
        The directory path associated with the hint if it exists and is valid; otherwise, returns '.' (current directory).
    """
    with open('defaultDir.json', 'r+') as f:
        dirs = json.load(f)
        if hint in dirs:
            if os.path.exists(dirs[hint]):
                return dirs[hint]
        return '.'


def write_dir(hint, path):
    """
    Write a directory path associated with a hint to a JSON file.
    
    Parameters
    ----------
    hint : str
        The key or identifier used to store the directory path in the JSON file.
    path : str
        The full file path from which the directory name will be extracted and stored.
    
    Returns
    -------
    None
        This function does not return any value.
    """
    dirs = {}
    with open('defaultDir.json', 'r+') as f:
        dirs = json.load(f)
    with open('defaultDir.json', 'w+') as f:
        dirs[hint] = os.path.dirname(path)
        json.dump(dirs, f)


class TextStream(QObject):
    def __init__(self, stdout):
        """
        Initialize the instance with a specified output stream.
        
        Parameters
        ----------
        stdout : file-like object
            The output stream to which the printer will write. This should be a file-like object that supports writing strings.
        
        Returns
        -------
        None
        """
        super().__init__()
        self.printer = stdout

    def write(self, text):
        """
        Update the printer text in the MainWindow and process GUI events.
        
        Parameters
        ----------
        text : str
            The text string to be displayed in the printer widget of the MainWindow.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        _translate = QtCore.QCoreApplication.translate
        self.printer.repaint()
        self.printer.setText(_translate("MainWindow", text))
        self.printer.repaint()
        QApplication.processEvents()

    def flush(self):
        """Flush the internal buffer or state of the object.
        
        This method is intended to clear or write any buffered data, 
        though the specific behavior may depend on the implementation.
        
        Parameters
        ----------
        self : MultiInputDialog
            The instance of MultiInputDialog on which the flush method is called.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        return


class MultiInputDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """
        Initialize the Parallelized Event Dialog with UI components for simulation method selection and local parameters.
        
        Parameters
        ----------
        parent : QtWidgets.QWidget or None, optional
            Parent widget. If None, the dialog will be independent.
        
        Returns
        -------
        None
        """
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
        """
        Handle the close event by performing cleanup operations.
        
        Parameters
        ----------
        a0 : QCloseEvent
            The close event object that triggered this method.
        
        Returns
        -------
        None
        """
        cleanMsg()

    def __init__(self, MainWindow, prj=project()):
        """
        Initialize the Window instance with UI setup and project configuration.
        
        Parameters
        ----------
        MainWindow : QMainWindow
            The main window object to be used for UI setup.
        prj : project, optional
            The project instance to be associated with the window (default is a new project()).
        
        Returns
        -------
        None
        """
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
        """
        Initialize the layout and UI components of the main window.
        
        This method sets up the graphical user interface elements including the IDF editor, 
        search result area, group editor, result analysis area, and various buttons and menus. 
        It also connects signals to their respective slots and applies stylesheet formatting. 
        The layout is adjusted based on whether a baseline IDF file has been loaded.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have attributes such as
            `IDFEditorDumpArea`, `searchResultArea`, `analysisArea`, `prj`, `PutthemintoGroup`,
            `ResultAnalysis`, and various `action*` menu items.
        
        Returns
        -------
        None
        """
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
        self.importButton = QtWidgets.QPushButton(self.analysisArea)
        self.importButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)
        self.importButton.setStyleSheet(suggestionBoxStyleSheet)
        self.importButton.setFont(QtGui.QFont('Arial', 30))
        self.importButton.clicked.connect(self.action_import_idf)
        self.importButton.setText('Import a baseline *.idf...')
        self.importButton.hide()

        # ProcessingArea-ResultAnalysis
        self.resultAnalysisArea = resultWidget(parent=self.analysisArea, prj=self.prj, window=self)
        self.resultAnalysisArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
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
            self.importButton.show()
            self.analysisArea.Layout.replaceWidget(self.groupEditorArea_Scroll, self.importButton)
            self.groupEditorArea_Scroll.hide()
            print('Please import a baseline *.idf...')
        else:
            self.groupEditorArea_Scroll.show()
            self.importButton.hide()
            self.groupEditorArea_Scroll.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.analysisArea.Layout.replaceWidget(self.importButton, self.groupEditorArea_Scroll)

    def updatetext(self, text):
        """
        Update the text in the text browser widget.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method.
        text : str
            The text string to be appended to the text browser.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        """更新textBrowser"""
        _translate = QtCore.QCoreApplication.translate
        # self.massage.setText()
        cursor = self.textBrowser.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.textBrowser.insertPlainText(_translate("MainWindow", text))
        self.textBrowser.setTextCursor(cursor)
        self.textBrowser.ensureCursorVisible()

    def action_write(self):
        """
        Perform batch writing of IDF files to a selected directory.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have
            attributes `groupEditorArea` and `prj`, where `prj` contains a `model` with
            a `write` method, and methods `get_dir` and `write_dir` are available for 
            handling directory paths.
        
        Returns
        -------
        None
            This function does not return any value. It performs side effects by writing 
            files to the file system and may display GUI messages or error traces.
        """
        try:
            geditor, fileNames = self.groupEditorArea.crossAllGroupEditors()
            QtWidgets.QMessageBox.information(self,"Select the saving path","请选择一个文件夹，idf文件将会批量写入该文件夹\nSelect a folder to drop the idf files!")
            filePath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select the saving path",get_dir('simulation'))
            if filePath:
                write_dir('simulation', filePath)
                self.prj.model.write(geditor, filePath, fileNames)
        except Exception as e:
            traceback.print_exc()

    def action_Simulation(self):
        """
        Run the simulation process, handling model and weather file setup if necessary.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the project and model attributes.
            Must have a `prj` attribute with a `model` (IDFModel) that may contain a `folder` path.
        
        Returns
        -------
        None
            This function does not return any value. It performs actions such as prompting the user for directories,
            writing files, and initiating a simulation via `self.simulation()`.
        """
        try:
            if self.prj.model:
                if not self.prj.model.folder:
                    print('******IDFs haven\'t write yet, select a folder******')
                    self.action_write()
                print('******Select a weather file******')
            else:
                print('******baseline haven\'t imported, select a folder******')
                QtWidgets.QMessageBox.information(self, "Select the idf folder",
                                                  "基线模型没有导入，请直接选择一个要模拟的文件夹（所有IDF都在里面）\nBaseline has not imported. Select a folder where the idf files are located, for simulation.")
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
        """
        Continue the simulation process by ensuring model and folder are properly set.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have a `prj` 
            attribute with a `model` (IDFModel) and associated attributes such as `folder`. 
            Also requires access to GUI elements like QMessageBox and QFileDialog via `QtWidgets`.
        
        Returns
        -------
        None
            This function does not return any value. It performs actions such as setting up 
            the model, prompting user input for directory selection, and initiating simulation.
        """
        try:
            if not self.prj.model:
                self.prj.model = IDFModel(os.path.abspath(r'doc\Base-Office.idf'))
            if not self.prj.model.folder:
                QtWidgets.QMessageBox.information(self, "Select the idf folder",
                                                  "基线模型没有导入，请直接选择一个要模拟的文件夹（所有IDF都在里面）\nBaseline has not imported. Select a folder where the idf files are located, for simulation.")
                filePath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select the project path", get_dir('simulation'))
                if filePath:
                    write_dir('simulation', filePath)
                    self.prj.model.folder = filePath
            if self.prj.model.folder:
                self.simulation()
        except Exception as e:
            traceback.print_exc()

    def simulation(self):
        """
        Run the simulation by selecting an EnergyPlus Weather (EPW) file and configuring simulation parameters.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the GUI and project model. It provides access to UI elements,
            project data, and configuration settings required for the simulation.
        
        Returns
        -------
        None
            This function does not return any value. It performs actions including opening file dialogs,
            executing a simulation, updating the UI state, and connecting signals upon completion.
        """
        QtWidgets.QMessageBox.information(self, "Select the weather",
                                          "选择一个EPW气象文件用于模拟\nSelect the EnergyPlus Weather file for simulation.")
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
                QtWidgets.QMessageBox.information(self, "warning",
                                                  "模拟即将开始，相关信息在CMD打印\nSimulation is ready, please turn to CMD....")
                self.prj.model.simulation(epw=filePath, overwrite=False, stdout=self.stdout,
                                          local=val['core'], process_count=val['cpus'], forceCPU=val['forceCPU'])
                print('******Simulation begin, turn to CMD....******')
                self.prj.model.read_folder(self.prj.model.folder)
                self.clickStage3()
                try:
                    self.exportButton.clicked.disconnect()
                except Exception as e:
                    pass
                self.exportButton.clicked.connect(self.resultAnalysisArea.resultBox.toCsv)
                print('******ALL DONE******')

    def action_idfreference(self):
        """Open the InputOutputReference.pdf document using the system's default PDF viewer.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. This parameter is required for method binding but is not used within the function.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        os.system(r'doc\InputOutputReference.pdf')

    def action_readme(self):
        """Open the ReadMe.md file located in the doc directory using the default system application.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. This parameter is required for method binding but is not used within the function.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        os.system(r'doc\ReadMe.md')

    def action_printAbout(self):
        """
        Print the contents of the About.md file.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        with open(r'doc\About.md') as f:
            print(f.read())

    def action_Result_Folder(self):
        """
        Handle selection and processing of a result folder for simulation analysis.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have attributes 
            `prj`, `resultAnalysisArea`, and `exportButton`. The `prj` attribute should 
            contain a `model` for handling IDF data, and `resultAnalysisArea` should support 
            result initialization and export functionality.
        
        Returns
        -------
        None
            This function does not return any value. It performs side effects including 
            updating the project model, reading result data from a directory, initializing 
            the result view, and connecting the export button to CSV export functionality.
        """
        try:
            if not self.prj.model:
                self.prj.model = IDFModel(os.path.abspath(r'doc\Base-Office.idf'))
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
        """
        Open the project folder in Windows Explorer.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the `project_folder` attribute.
            It is expected to have a `project_folder` attribute of type str or None,
            representing the path to the project directory.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        if self.project_folder:
            os.system("explorer.exe %s" % self.project_folder)

    def action_iddfolder(self):
        """
        Open the IDD folder in Windows Explorer.
        
        This function opens the 'idd' directory located inside the 'epeditor' folder 
        using the default file explorer on Windows.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. This parameter is 
            required for method consistency within the class, though it is not 
            directly used in the function.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        os.system("explorer.exe .\\epeditor\\idd")

    def action_SimParams(self):
        """
        Save simulation parameters to a CSV file.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have
            attributes `groupEditorArea` and `groupEditorArea.crossAllGroupEditors()` returning
            a data structure with a `to_csv` method, and a valid parent widget for GUI operations.
        
        Returns
        -------
        None
            This function does not return any value. It performs a side effect of writing
            simulation parameters to a specified CSV file.
        """
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
        """
        Save the current project to the existing project path or prompt for a new path if not previously saved.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have attributes `saved` (bool),
            `prj` (object with a `save` method), and `project_path` (str). The `action_saveAs` method must also be defined.
        
        Returns
        -------
        None
            This function does not return any value. It performs side effects by saving the project and printing status or error messages.
        """
        try:
            if self.saved:
                self.prj.save(self.project_path)
                print(f'Project save to: {self.project_path}')
            else:
                self.action_saveAs()
        except Exception as e:
            print(traceback.format_exc())

    def action_saveAs(self):
        """
        Save the current project to a specified file path.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have
            attributes `prj`, `project_path`, `project_folder`, and `saved`, as well
            as methods `get_dir` and `write_dir`. It should also be a QtWidgets.QWidget
            or compatible Qt class to use QFileDialog.
        
        Returns
        -------
        None
            This function does not return any value. It performs side effects such as
            saving the project to disk, updating instance attributes, and printing status
            or error messages.
        """
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
        """
        Load a project from a specified ZIP file path using a file dialog.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have 
            attributes such as `prj`, `MainWindow`, `stdout`, `project_path`, 
            `project_folder`, `saved`, and methods like `__init__`, `_updatePrj`, 
            and `write_dir`. The `prj` attribute will be replaced with the loaded 
            project data.
        
        Returns
        -------
        None
            This function does not return any value. It modifies the state of the 
            instance by loading and initializing the project, updating internal 
            references, and refreshing the UI components accordingly.
        """
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
        """
        Update the project reference in multiple UI areas.
        
        Parameters
        ----------
        prj : object
            The project object to be assigned to various areas within the interface.
        
        Returns
        -------
        None
        """
        self.searchResultArea.relatedArea.relateProcessingArea.prj = prj
        self.searchResultArea.keywordArea.prj = prj
        self.searchResultArea.relatedArea.prj = prj
        self.groupEditorArea.prj = prj
        self.editorBoxArea.prj = prj
        self.resultAnalysisArea.prj = prj

    def action_import_idf(self):
        """
        Import an EnergyPlus IDF file into the project.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have 
            attributes `MainWindow`, `stdout`, `prj`, and methods `__init__`, `_updatePrj`, 
            as well as access to helper functions `get_dir`, `write_dir`, and `project`.
        
        Returns
        -------
        None
            This function does not return any value. It updates the project state and UI 
            upon successfully loading the IDF file, or prints an error traceback if failed.
        """
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
        """
        Clean and reset the browser interface with optional reconnection message.
        
        Parameters
        ----------
        reconnect : bool, optional
            If True, prints a reconnection message using `cleanMsg()`. Default is True.
        
        Returns
        -------
        None
            This function does not return any value.
        """
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
        """
        Handle and process a user question via QA interface.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have an `exectext` 
            attribute representing a text widget with methods `toPlainText`, `setText`, and 
            storage of `lastText`.
        
        Returns
        -------
        None
            This function does not return any value. It processes the input text, sends it 
            for question answering, updates the text widget, and handles exceptions by printing tracebacks.
        """
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
        """
        Execute the code from the plain text of exectext and handle exceptions.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have
            an attribute `exectext` (a QTextEdit or similar object) providing the
            method `toPlainText()`, and a method `exec_L` for executing the retrieved lines.
        
        Returns
        -------
        None
            This function does not return any value. It executes the provided code lines
            via `exec_L` and prints a traceback if an exception occurs.
        """
        try:
            lines = self.exectext.toPlainText()
            self.exec_L(lines)
        except Exception as e:
            print(traceback.format_exc())

    def exec_L(self, args):
        """
        Execute a command or question based on input arguments.
        
        Parameters
        ----------
        args : str
            The input string to be processed. If it starts with '!' or '！', 
            it is treated as a question and sent to an external QA system; 
            otherwise, it is executed as a Python command.
        
        Returns
        -------
        None
            This function does not return any value.
        """
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
        """
        Handle the add action by collecting checked search result items and adding them to the editor box.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have attributes `searchResultArea`, 
            `editorBoxArea`, and methods or properties related to the search result layout and keyword area.
        
        Returns
        -------
        None
            This function does not return any value. It performs side effects by modifying the editor box area.
        """
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
        """
        Add selected nodes from search results to the editor box.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Assumes the presence 
            of attributes: searchResultArea, editorBoxArea, and related structures 
            including gridlayout and IDFSearchResultBox widgets.
        
        Returns
        -------
        None
            This function does not return any value.
        """
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
        """
        Switches the interface to Stage 2, displaying the group editor from CSV import.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have attributes 
            such as PutthemintoGroup, ResultAnalysis, exportButton, resultAnalysisArea, 
            groupEditorArea, groupEditorArea_Scroll, analysisArea, and importButton, which 
            are GUI elements managed during the stage transition.
        
        Returns
        -------
        None
            This function does not return any value.
        """
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
        if self.prj.model is None:
            self.importButton.show()
            self.analysisArea.Layout.replaceWidget(self.groupEditorArea_Scroll, self.importButton)
            self.groupEditorArea_Scroll.hide()
    def clickStage3(self):
        """
        Activate stage 3 of the UI workflow, configuring the interface for result analysis.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have attributes 
            such as ResultAnalysis, PutthemintoGroup, exportButton, groupEditorArea, 
            importButton, groupEditorArea_Scroll, resultAnalysisArea, analysisArea, and prj, 
            which are used to manage UI state and data.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.ResultAnalysis.setStyleSheet(QTitleButton.selectStyleSheet)
        self.PutthemintoGroup.setStyleSheet(QTitleButton.unselectStyleSheet)
        self.exportButton.setText('Results to *.csv')
        try:
            self.exportButton.clicked.disconnect()
        except Exception as e:
            pass
        self.groupEditorArea.hide()
        self.importButton.hide()
        self.groupEditorArea_Scroll.hide()
        self.resultAnalysisArea.show()
        self.resultAnalysisArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.analysisArea.Layout.replaceWidget(self.importButton, self.resultAnalysisArea)
        if self.prj.model:
            self.analysisArea.Layout.replaceWidget(self.groupEditorArea_Scroll, self.resultAnalysisArea)
            if self.prj.model.folder:
                self.resultAnalysisArea.initResultView()
                self.exportButton.clicked.connect(self.resultAnalysisArea.resultBox.toCsv)
