from PyQt5 import QtCore, QtGui, QtWidgets


class QTitle(QtWidgets.QLabel):
    def __init__(self, *__args):
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
        super(QTitleButton, self).__init__(*__args)
        self.setStyleSheet(self.unselectStyleSheet)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)


class ExecText(QtWidgets.QTextEdit):
    def __init__(self, parent=None,exec=None,QA=None):
        super(ExecText, self).__init__(parent)
        self.exec = exec
        self.QA = QA
        self.lastText=''
    def keyPressEvent(self, e):
        super(ExecText, self).keyPressEvent(e)

        if e.key() == QtCore.Qt.Key_Up:
            if self.toPlainText()=='':
                self.setText(self.lastText)

        if e.modifiers() == QtCore.Qt.ControlModifier:
            if e.key() == QtCore.Qt.Key_Return:
                self.QA()

        if e.key() == QtCore.Qt.Key_Enter:
                self.exec()

