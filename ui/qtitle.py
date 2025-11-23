from PyQt5 import QtCore, QtGui, QtWidgets


class QTitle(QtWidgets.QLabel):
    def __init__(self, *__args):
        """
        Custom QPushButton with predefined styles for selected and unselected states.
        
        Parameters
        ----------
        *__args : tuple
            Variable length argument list passed to the parent QPushButton constructor.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
        super(QTitle, self).__init__(*__args)
        self.setAlignment(QtCore.Qt.AlignCenter)


class QTitleButton(QtWidgets.QPushButton):

    unselectStyleSheet = """.QTitleButton{
    	border:1px solid rgb(130,53,113);
    	border-radius:5px;
    	padding: 1px;
    	color: rgb(130,53,113);
    	text-transform:uppercase;
    	font-weight:Bold;
    	font-size:15 px;
        background-color:white;
    }

    .QTitleButton:hover{
    	border:1px solid rgb(130,53,113);
    	border-radius:5px;
    	padding: 1px;
    	color: white;
    	text-transform:uppercase;
    	font-weight:Bold;
    	font-size:15 px;
        background-color:rgb(130,53,113);
    }

    .QTitleButton:pressed{
    	border:1px solid rgb(93,55,85);
    	border-radius:5px;
    	padding: 1px;
    	color: white;
    	text-transform:uppercase;
    	font-weight:Bold;
    	font-size:15 px;
        background-color:rgb(93,55,85);
    }"""
    selectStyleSheet = """.QTitleButton{
	border:1px solid rgb(130,53,113);
	border-radius:5px;
	padding: 1px;
	color: white;
	text-transform:uppercase;
	font-weight:Bold;
	font-size:15 px;
    background-color:rgb(130,53,113);
}

.QTitleButton:hover{
	border:1px solid rgb(93,55,85);
	border-radius:5px;
	padding: 1px;
	color: white;
	text-transform:uppercase;
	font-weight:Bold;
	font-size:15 px;
    background-color:rgb(93,55,85);
}

.QTitleButton:pressed{
	border:1px solid rgb(43,35,55);
	border-radius:5px;
	padding: 1px;
	color: white;
	text-transform:uppercase;
	font-weight:Bold;
	font-size:15 px;
    background-color:rgb(43,35,55);
}
"""

    def __init__(self, *__args):
        """
        Initialize the QTitleButton with optional arguments.
        
        Parameters
        ----------
        *__args : tuple
            Variable length argument list passed to the parent class constructor.
        
        Returns
        -------
        None
        """
        super(QTitleButton, self).__init__(*__args)
        self.setStyleSheet(self.unselectStyleSheet)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)


class ExecText(QtWidgets.QTextEdit):
    def __init__(self, parent=None,exec=None,QA=None):
        """
        Initialize the ExecText object with optional parent, exec, and QA parameters.
        
        Parameters
        ----------
        parent : object, optional
            The parent object, typically a QWidget or similar GUI element. Default is None.
        exec : object, optional
            Execution context or callable to be associated with the instance. Default is None.
        QA : object, optional
            QA (question-answer) context or data to be associated with the instance. Default is None.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
        super(ExecText, self).__init__(parent)
        self.exec = exec
        self.QA = QA
        self.lastText=''
    def keyPressEvent(self, e):
        """
        Handle key press events for the text widget.
        
        Parameters
        ----------
        e : QKeyEvent
            The key event containing information about the pressed key, including the key code and modifiers.
        
        Returns
        -------
        None
            This function does not return a value.
        """
        super(ExecText, self).keyPressEvent(e)

        if e.key() == QtCore.Qt.Key_Up:
            if self.toPlainText()=='':
                self.setText(self.lastText)

        if e.modifiers() == QtCore.Qt.ControlModifier:
            if e.key() == QtCore.Qt.Key_Return:
                self.QA()

        if e.key() == QtCore.Qt.Key_Enter:
                self.exec()

