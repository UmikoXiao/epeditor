import numpy as np

import os,shutil
from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
import traceback
class FigureDialog(QtWidgets.QDialog):
    def __init__(self,parent=None):
        """
        Initialize the FigureDialog with an optional parent widget.
        
        Parameters
        ----------
        parent : QtWidgets.QWidget, optional
            Parent widget to which this dialog belongs. Default is None.
        
        Returns
        -------
        None
        """
        super(FigureDialog, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle('Figure')
        self.tab = QtWidgets.QTabWidget(self)
        self.Layout=QtWidgets.QVBoxLayout(self)
        self.Layout.addWidget(self.tab)
        self.resize(600, 400)
        self.figures=[]
    def addFigure(self,figurePath,hint):
        """
        Add a figure to the tabbed interface with a specified path and tab hint.
        
        Parameters
        ----------
        figurePath : str
            Path to the figure file to be added.
        hint : str
            Text label for the tab associated with the figure.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        figWidget = figureWidget(self,figurePath)
        figWidget.setObjectName(hint)
        self.figures.append(figWidget)
        self.tab.addTab(figWidget,'')
        self.tab.setTabText(self.tab.indexOf(figWidget),hint)
class figureWidget(QtWidgets.QWidget):
    def __init__(self,parent=None,figurePath=None):
        """
        Initialize a figure widget with an optional parent and image path.
        
        Parameters
        ----------
        parent : QtWidgets.QWidget or None, optional
            Parent widget to which this figureWidget belongs. Default is None.
        figurePath : str or None, optional
            Path to the image file to be displayed in the widget. Default is None.
        
        Returns
        -------
        None
            This constructor does not return any value.
        """
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
        """
        Save the figure to a user-specified file path using a file dialog.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Must have attributes `figurePath` (str)
            representing the current path of the figure, and must inherit from a Qt widget (e.g., QtWidgets.QWidget)
            to support the file dialog.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        try:
            filePath, filetype = QtWidgets.QFileDialog.getSaveFileName(self, "Select the saving path", "./",
                                                                       'Png File (*.png)')
            if filePath:
                shutil.copy(self.figurePath,filePath)
                print(f'Figure save to: {filePath}')

        except Exception as e:
            print(traceback.format_exc())

def plotToWindow(methodName,figurePath,Dialog=None):
    """
    Create or update a figure dialog window with a given figure.
    
    Parameters
    ----------
    methodName : str
        The name of the method to be displayed or associated with the figure.
    figurePath : str
        File path to the figure image to be added to the dialog.
    Dialog : FigureDialog or None, optional
        An existing dialog instance. If not provided, a new FigureDialog is created and shown.
    
    Returns
    -------
    FigureDialog
        The dialog instance with the added figure, either newly created or updated.
    """
    if not Dialog:
        Dialog = FigureDialog()
        Dialog.show()
        Dialog.addFigure(figurePath,methodName)
        Dialog.setModal(True)
    else:
        Dialog.addFigure(figurePath,methodName)
    return Dialog

