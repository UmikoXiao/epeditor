import copy
from eppy.modeleditor import IDF
from .idfbox import *

app = QtWidgets.QApplication(sys.argv)
frequencies = {
    "Zone Timestep": utils.TimeStep,
    "Hourly": utils.Hourly,
    "Daily": utils.Daily,
    "Monthly": utils.Monthly,
    "Run Period": utils.RunPeriod,
    "Annual": utils.Annually,
}


class redirectQWidget(QtWidgets.QWidget):
    def __init__(self, parent, window, prj):
        super(redirectQWidget, self).__init__(parent=parent)
        self.prj: project = prj
        self.mainWindow = window


class searchWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        super(searchWidget, self).__init__(parent, window, prj)

        self.label_class = QtWidgets.QLabel(self)
        self.label_class.setGeometry(QtCore.QRect(10, 10, 51, 21))
        self.label_class.setObjectName("label_class")

        self.classText = QtWidgets.QLineEdit(self)
        self.classText.setGeometry(QtCore.QRect(60, 10, 121, 20))
        self.classText.setObjectName("classText")

        self.label_name = QtWidgets.QLabel(self)
        self.label_name.setGeometry(QtCore.QRect(190, 10, 41, 21))
        self.label_name.setObjectName("label_name")

        self.nameText = QtWidgets.QLineEdit(self)
        self.nameText.setGeometry(QtCore.QRect(230, 10, 131, 20))
        self.nameText.setObjectName("nameText")

        self.label_field = QtWidgets.QLabel(self)
        self.label_field.setGeometry(QtCore.QRect(370, 10, 51, 21))
        self.label_field.setObjectName("label_field")

        self.fieldText = QtWidgets.QLineEdit(self)
        self.fieldText.setGeometry(QtCore.QRect(410, 10, 131, 20))
        self.fieldText.setObjectName("fieldText")

        self.scrollAreaSearch = QtWidgets.QScrollArea(self)
        self.scrollAreaSearch.setGeometry(QtCore.QRect(9, 39, 531, 161))
        self.scrollAreaSearch.setWidgetResizable(True)
        self.scrollAreaSearch.setObjectName("scrollArea_2")
        self.scrollAreaSearch.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollAreaSearch.setWidgetResizable(False)
        self.searchResultWidget = QtWidgets.QWidget()
        self.searchResultWidget.setObjectName("searchResultWidget")
        self.SearchResultLayout = QtWidgets.QGridLayout(self.searchResultWidget)
        self.SearchResultLayout.setContentsMargins(10, 5, 5, 5)
        self.SearchResultLayout.setObjectName("SearchResultLayout")
        self.scrollAreaSearch.setWidget(self.searchResultWidget)

        self.addbutton = QtWidgets.QPushButton(self)
        self.addbutton.setGeometry(QtCore.QRect(10, 210, 531, 23))
        self.addbutton.setObjectName("addbutton")

        self.compareButton = QtWidgets.QPushButton(self)
        self.compareButton.setGeometry(QtCore.QRect(10, 210, 531, 23))
        self.compareButton.setObjectName("compareButton")

        _translate = QtCore.QCoreApplication.translate
        self.label_class.setText(_translate("MainWindow", "CLASS"))
        self.label_name.setText(_translate("MainWindow", "NAME"))
        self.label_field.setText(_translate("MainWindow", "FIELD"))
        self.addbutton.setText(_translate("MainWindow", "Add"))
        self.compareButton.setText(_translate("MainWindow", "Compare with *.IDF"))

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setContentsMargins(5, 5, 5, 5)
        self.gridLayout.setObjectName('tabsearchlayout')
        self.gridLayout.addWidget(self.label_class, 0, 0)
        self.gridLayout.addWidget(self.classText, 0, 1)
        self.gridLayout.addWidget(self.label_name, 0, 2)
        self.gridLayout.addWidget(self.nameText, 0, 3)
        self.gridLayout.addWidget(self.label_field, 0, 4)
        self.gridLayout.addWidget(self.fieldText, 0, 5)
        self.gridLayout.addWidget(self.scrollAreaSearch, 1, 0, 1, 6)
        self.gridLayout.addWidget(self.addbutton, 2, 0, 1, 2)
        self.gridLayout.addWidget(self.compareButton, 2, 2, 1, 4)
        self.gridLayout.setRowStretch(0, 1)
        self.gridLayout.setRowStretch(1, 99)
        self.gridLayout.setRowStretch(2, 1)
        self.gridLayout.setRowMinimumHeight(2, 5)
        self.gridLayout.setColumnStretch(0, 10)
        self.gridLayout.setColumnStretch(1, 30)
        self.gridLayout.setColumnStretch(2, 10)
        self.gridLayout.setColumnStretch(3, 30)
        self.gridLayout.setColumnStretch(4, 10)
        self.gridLayout.setColumnStretch(5, 30)
        self.searchResultWidget.setGeometry(QtCore.QRect(10, 10, self.scrollAreaSearch.width(), 159))

        # self.searchButton.clicked.connect(self.click_search)
        self.classText.textChanged.connect(self.click_search)
        self.nameText.textChanged.connect(self.click_search)
        self.fieldText.textChanged.connect(self.click_search)
        self.addbutton.clicked.connect(self.mainWindow.click_Add)
        self.compareButton.clicked.connect(self.compareIDF)

    def compareIDF(self):
        try:
            if self.prj.model is not None:
                filePath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Select the baseline *.idf file", "./",
                                                                               'EnergyPlus Input Files (*.idf)')
                if filePath:
                    otherIDF = IDFModel(filePath)
                    searchResults = self.prj.model.diff(otherIDF)
                    self._create_SearchResultLayout(searchResults)
                    editors = [IDFEditor(sr) for sr in searchResults]
                    tempCsv = os.path.join(self.prj.tempFolder, '_groupEditor.csv')
                    IDFGroupEditor(*editors).to_csv(tempCsv)
                    self.mainWindow.groupEditorArea.readCSV(tempCsv)
                    os.startfile(tempCsv)
        except Exception as e:
            print(traceback.format_exc())
    def _create_SearchResultLayout(self, result: list):
        columns = 2
        itemWidth, itemHeight = self.searchResultWidget.width()/columns, rowHight*2
        row_num = np.ceil(len(result) / columns)
        clear_grid(self.SearchResultLayout)
        self.SearchResultLayout.setRowStretch(0, 0)  # 把第 0 行拉伸系数归零
        self.SearchResultLayout.setColumnStretch(0, 0)

        if len(result) <= 2:
            self.searchResultWidget.setGeometry(QtCore.QRect(10, 10, itemWidth*2, itemHeight))
        else:
            self.searchResultWidget.setGeometry(QtCore.QRect(10, 10, itemWidth*columns, int(row_num * itemHeight)))
        # for i in np.arange(self.SearchResultLayout.count() - 1, -1, -1):
        #     item = self.SearchResultLayout.itemAt(i)
        #     self.SearchResultLayout.removeItem(item)
        #     if item.widget():
        #         item.widget().deleteLater()
        # self.SearchResultLayout.setSpacing(10)
        for i in range(len(result)):
            rect = QtCore.QRect(0, 0, itemWidth, itemHeight)
            self.SearchResultLayout.addWidget(
                IDFSearchResultBox(parent=self.searchResultWidget, item=result[i], rect=rect,prj=self.prj), np.floor(i / columns),
                i % columns)
            # self.SearchResultLayout.addWidget(IDFSearchResultBox(parent=self.IDFDumpAreaWidget_2),np.floor(i / 2), i % 2)
        if len(result) ==1:
            self.SearchResultLayout.addWidget(emptyBox(self.SearchResultLayout,0,1))
            # 其他 item 类型同理处理
    def click_search(self):
        try:
            class_str = self.classText.text().strip()
            name_str = self.nameText.text().strip()
            field_str = self.fieldText.text().strip()
            if len(class_str) > 2 or len(class_str) == 0:
                if len(name_str) > 2 or len(name_str) == 0:
                    if len(field_str) > 2 or len(field_str) == 0:
                        if self.prj.model:
                            searchresult = self.prj.model.eval(class_str, name_str, field_str, False)
                            # searchresult = self.prj.model.search(class_str)
                            self._create_SearchResultLayout(searchresult)
        except Exception as e:
            print(traceback.format_exc())


class relateSearchWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        super(relateSearchWidget, self).__init__(parent, window, prj)
        _translate = QtCore.QCoreApplication.translate
        self.noticenode = QtWidgets.QLabel('* Right click on any elements to show the related idfobjects.')

        self.scrollAreaNode = QtWidgets.QScrollArea(self)
        self.scrollAreaNode.setGeometry(QtCore.QRect(9, 10, 531, 191))
        self.scrollAreaNode.setWidgetResizable(True)
        self.scrollAreaNode.setObjectName("scrollAreaNode")
        self.scrollAreaNode.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollAreaNode.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.relateProcessingArea = QtWidgets.QWidget()
        self.relateProcessingArea.setGeometry(QtCore.QRect(0, 0, 529, 189))
        self.relateProcessingArea.setObjectName("scrollAreaNodeContents")
        self.scrollAreaNode.setWidget(self.relateProcessingArea)

        self.addButtonNode = QtWidgets.QPushButton(self)
        self.addButtonNode.setGeometry(QtCore.QRect(10, 210, 331, 23))
        self.addButtonNode.setObjectName("addButtonNode")
        self.clearbuttonNode = QtWidgets.QPushButton(self)
        self.clearbuttonNode.setGeometry(QtCore.QRect(354, 210, 181, 23))
        self.clearbuttonNode.setObjectName("clearbuttonNode")
        self.addButtonNode.setText(_translate("MainWindow", "Add"))
        self.clearbuttonNode.setText(_translate("MainWindow", "Clear"))

        self.searchResultRelatedLayout = QtWidgets.QGridLayout(self)
        self.searchResultRelatedLayout.setContentsMargins(5, 5, 5, 5)
        self.searchResultRelatedLayout.addWidget(self.noticenode, 0, 0, 1, 2)
        self.searchResultRelatedLayout.addWidget(self.scrollAreaNode, 1, 0, 1, 2)
        self.searchResultRelatedLayout.addWidget(self.addButtonNode, 2, 0)
        self.searchResultRelatedLayout.addWidget(self.clearbuttonNode, 2, 1)
        self.searchResultRelatedLayout.setRowStretch(0, 1)
        self.searchResultRelatedLayout.setRowStretch(1, 99)
        self.searchResultRelatedLayout.setRowStretch(2, 1)
        self.searchResultRelatedLayout.setRowMinimumHeight(0, 20)
        self.relateProcessingArea = relatedResultWidget(parent=self, window=self.mainWindow, prj=self.prj)
        self.relateProcessingArea.setGeometry(
            QtCore.QRect(0, 0, self.scrollAreaNode.width(), self.scrollAreaNode.height()))
        self.relateProcessingArea.setObjectName("scrollAreaNodeContents")
        self.scrollAreaNode.setWidget(self.relateProcessingArea)
        self.relateProcessingArea.initEmptyBoard()

        self.addButtonNode.clicked.connect(self.mainWindow.click_Add_Node)
        self.clearbuttonNode.clicked.connect(self.click_Clear_Node)

    def click_Clear_Node(self):
        self.relateProcessingArea.clearGrid()


class relatedResultWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        super(relatedResultWidget, self).__init__(parent, window, prj)
        self.setAcceptDrops(True)
        # self.setMouseTracking(True)
        self.itemheight = 60
        self.itemwidth = 230
        self.prj = prj
        self.gridlayout = QtWidgets.QGridLayout(self)
        self.gridlayout.setContentsMargins(10, 10, 10, 10)
        self.gridlayout.setObjectName("NodeGridLayout")

    def initEmptyBoard(self):
        self.gridlayout.columns = int(np.floor(self.width() / self.itemwidth))
        self.gridlayout.rows = int(np.floor(self.height() / self.itemheight))
        for i in range(self.gridlayout.rows):
            for j in range(self.gridlayout.columns):
                self.add_emptybox(i, j)
        self.arrange()

    def add_emptybox(self, i, j):
        emptyblock = emptyBox(self, i, j, itemheight=self.itemheight)
        self.gridlayout.addWidget(emptyblock, i, j)

    def removeitem(self, i, j):
        try:
            item = self.gridlayout.itemAtPosition(i, j)
            self.gridlayout.removeItem(item)
            if item.widget():
                item.widget().deleteLater()
        except:
            return

    def clearGrid(self):
        for i in range(self.gridlayout.rows):
            for j in range(self.gridlayout.columns):
                self.removeitem(i, j)
                self.add_emptybox(i, j)

    def arrange(self):
        for i in range(self.gridlayout.rows):
            self.gridlayout.setRowStretch(i, 10)
            self.gridlayout.setRowMinimumHeight(i, self.itemheight)
        for j in range(self.gridlayout.columns):
            self.gridlayout.setColumnStretch(j, 10)
            self.gridlayout.setColumnMinimumWidth(j, self.itemwidth)

    def expenddgridrow(self):
        try:
            for j in range(self.gridlayout.columns):
                self.add_emptybox(self.gridlayout.rows, j)
            self.gridlayout.rows += 1
            self.setGeometry(0, 0, self.gridlayout.columns * self.itemwidth,
                             self.gridlayout.rows * self.itemheight)
            self.arrange()
        except Exception as e:
            print(traceback.format_exc())

    def expenddgridcolumn(self):
        try:
            for i in range(self.gridlayout.rows):
                self.add_emptybox(i, self.gridlayout.columns)
            self.add_emptybox(self.gridlayout.rows, self.gridlayout.columns)
            self.gridlayout.columns += 1
            self.setGeometry(0, 0, self.gridlayout.columns * self.itemwidth,
                             self.gridlayout.rows * self.itemheight)
            self.arrange()
        except Exception as e:
            print(traceback.format_exc())

    def addBox(self, row, col):
        try:
            if self.prj.library['DragEventObject']:
                searchresult = self.prj.library['DragEventObject']

                if row == self.gridlayout.rows - 1:
                    self.expenddgridrow()
                if col == self.gridlayout.columns - 1:
                    self.expenddgridcolumn()

                self.removeitem(row, col)
                rect = QtCore.QRect(0, 0, self.itemwidth, self.itemheight)
                searchbox = IDFSearchResultBox(parent=self, item=searchresult, rect=rect,prj=self.prj)
                searchbox.setMinimumHeight(self.itemheight - 10)
                self.gridlayout.addWidget(searchbox, row, col)

                self.arrange()
                self.prj.library['DragEventObject'] = None

        except Exception as e:
            print(traceback.format_exc())

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.RightButton:
            try:
                items = [self.gridlayout.itemAt(i) for i in range(self.gridlayout.count()) if self.gridlayout.itemAt(i)]
                widgets = [item.widget() for item in items if item.widget()]
                pos = event.pos()
                gridnode = None
                for wdiget in widgets:
                    if pos.x() > wdiget.x() and pos.x() < wdiget.x() + wdiget.width() and pos.y() > wdiget.y() and pos.y() < wdiget.y() + wdiget.height():
                        gridnode = wdiget
                        break

                if isinstance(gridnode, IDFSearchResultBox):

                    # refed, refing = self.prj.node_reference(gridnode.item)
                    # refed += refing
                    refed = gridnode.item.referred_list(obj=True)
                    row, col, _, _ = self.gridlayout.getItemPosition(self.gridlayout.indexOf(gridnode))
                    if gridnode.showed:
                        for i in range(len(refed)):
                            item = self.gridlayout.itemAtPosition(row + i, col + 1)
                            if item.widget():
                                widget = item.widget()
                                self.gridlayout.removeWidget(widget)
                                widget.deleteLater()
                            self.add_emptybox(row + i, col + 1)
                        gridnode.showed = False
                    else:
                        rect = QtCore.QRect(0, 0, self.itemwidth, self.itemheight)
                        searchresultbox = [IDFSearchResultBox(parent=self, item=searchresult, rect=rect,prj=self.prj) for
                                           searchresult in refed]
                        for i in range(len(searchresultbox)):
                            if col + 1 == self.gridlayout.columnCount():
                                self.expenddgridcolumn()
                            if row + i == self.gridlayout.rowCount():
                                self.expenddgridrow()
                            item = self.gridlayout.itemAtPosition(row + i, col + 1)
                            if item:
                                if item.widget():
                                    self.gridlayout.replaceWidget(item.widget(), searchresultbox[i])
                                    item.widget().deleteLater()
                                else:
                                    self.gridlayout.addWidget(searchresultbox[i], row + i, col + 1)
                            gridnode.showed = True
            except Exception as e:
                traceback.print_exc()


class groupEditorWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        super(groupEditorWidget, self).__init__(parent, window, prj)
        self.setAcceptDrops(True)

        self.geditorbox = []
        self.fileNames = None
        self.VBoxLayout = QtWidgets.QVBoxLayout(self)
        self.VBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.VBoxLayout.setObjectName("ProcessingGridLayout")

        self.VBoxLayout.addWidget(self.emptyGroupEditor())
        self.arrange()

    def editorToTempCSV(self):
        geditor = self.crossAllGroupEditors()
        if geditor is not None:
            tempCsv = os.path.join(self.prj.tempFolder, '_groupEditor.csv')
            geditor.to_csv(tempCsv)
            os.startfile(tempCsv)

    def editorFromCSV(self):
        try:
            if self.prj.model is not None:
                filePath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Select the params csv", "./",
                                                                           'Comma-Separated Values Files (*.csv)')
                if filePath:
                    self.readCSV(filePath)
        except Exception as e:
            print(traceback.format_exc())

    def readCSV(self,filePath):
        item, self.fileNames = IDFGroupEditor.load(self.prj.model, filePath, returnFileNames=True)
        rect = QtCore.QRect(0, 0, 500, 100)
        self.geditorbox.append(IDFGroupEditorBox(parent=self, item=item, prj=self.prj, rect=rect))
        gridnode = self.VBoxLayout.itemAt(0).widget()
        for i in range(self.VBoxLayout.count()):
            if self.VBoxLayout.itemAt(i):
                if not isinstance(self.VBoxLayout.itemAt(i), IDFGroupEditorBox):
                    gridnode = self.VBoxLayout.itemAt(i).widget()
                    break
        self.VBoxLayout.replaceWidget(gridnode, self.geditorbox[-1])
        self.VBoxLayout.addWidget(self.emptyGroupEditor(), self.VBoxLayout.count())
        gridnode.deleteLater()
        self.arrange()

    def emptyGroupEditor(self):
        emptyblock = QtWidgets.QLabel(parent=self)
        emptyblock.setStyleSheet(emptyBoxStyleSheet)
        emptyblock.setGeometry(0, 0, 800, 150)
        emptyblock.setMinimumHeight(150)
        emptyblock.setMinimumWidth(800)
        return emptyblock

    def arrange(self):
        totalheight = []
        maxWidth=0
        for i in range(self.VBoxLayout.count()):
            item = self.VBoxLayout.itemAt(i)
            if item:
                if item.widget():
                    totalheight += [item.widget().height()]
                    maxWidth = max(maxWidth, item.widget().width())


        self.setGeometry(0, 0, maxWidth, np.sum(totalheight)+self.VBoxLayout.count()*10)
        for i in range(self.VBoxLayout.count()):
            self.VBoxLayout.setStretch(i,int(totalheight[i]/np.sum(totalheight)*100))

    def childPressEvent(self, gridnode):
        try:
            self.VBoxLayout.replaceWidget(gridnode, self.emptyGroupEditor())
            self.geditorbox.remove(gridnode)
            self.updateProjectGroupEditor()
        except Exception as e:
            print(traceback.format_exc())

    def toGroupEditor(self,item):
        if isinstance(item, IDFsearchresult):
            if item.field is None or item.field == '':
                item.field = item.obj.fieldnames[2]
            item = IDFEditor(item)
        if isinstance(item, IDFEditor):
            item = IDFGroupEditor(item)
        return item
    def dropEvent(self, event: QtGui.QMouseEvent):

        try:
            for i in np.arange(self.VBoxLayout.count() - 1, -1, -1):
                item = self.VBoxLayout.itemAt(i)
                if item.widget():
                    if not isinstance(item.widget(), IDFGroupEditorBox):
                        item.widget().setStyleSheet(emptyBoxStyleSheet)
                        item.widget().setText('')

            if self.prj.library['DragEventObject']:
                items = [self.VBoxLayout.itemAt(i) for i in range(self.VBoxLayout.count()) if self.VBoxLayout.itemAt(i)]
                widgets = [item.widget() for item in items if item.widget()]
                pos = event.pos()
                gridnode = None
                for wdiget in widgets:
                    if pos.x() > wdiget.x() and pos.x() < wdiget.x() + wdiget.width() and pos.y() > wdiget.y() and pos.y() < wdiget.y() + wdiget.height():
                        gridnode = wdiget
                        break

                if gridnode is not None:
                    item = self.toGroupEditor(self.prj.library['DragEventObject'])
                    if isinstance(gridnode, IDFGroupEditorBox):
                        geditor = IDFGroupEditor.merge(gridnode.packGroupEditor(), item)
                        # new_gridnode = IDFGroupEditorBox(parent=self, item=geditor, prj=self.prj)
                        # self.VBoxLayout.replaceWidget(gridnode, new_gridnode)
                        # gridnode.deleteLater()
                        gridnode.initFromGEditor(geditor)

                    else:
                        # rect = QtCore.QRect(self.prj.library['itemposition'][0]+event.pos().x(), self.prj.library['itemposition'][1]+event.pos().y(), 500, 100)
                        rect = QtCore.QRect(0, 0, 500, 100)
                        self.geditorbox.append(IDFGroupEditorBox(parent=self, item=item, prj=self.prj,rect= rect))
                        self.VBoxLayout.replaceWidget(gridnode, self.geditorbox[-1])
                        self.VBoxLayout.addWidget(self.emptyGroupEditor(), self.VBoxLayout.count())
                        gridnode.deleteLater()
                    self.prj.library['DragEventObject'] = None
            self.arrange()
            self.updateProjectGroupEditor()
        except Exception as e:
            print(traceback.format_exc())

    def dragEnterEvent(self, event):
        for i in np.arange(self.VBoxLayout.count() - 1, -1, -1):
            item = self.VBoxLayout.itemAt(i)
            if item.widget():
                if not isinstance(item.widget(), IDFGroupEditorBox):
                    item.widget().setStyleSheet(emptyBoxStyleSheetHover)
                    item.widget().setText('DROP HERE!')

        event.setDropAction(Qt.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event):
        for i in np.arange(self.VBoxLayout.count() - 1, -1, -1):
            item = self.VBoxLayout.itemAt(i)
            if item.widget():
                if not isinstance(item.widget(), IDFGroupEditorBox):
                    item.widget().setStyleSheet(emptyBoxStyleSheet)
                    item.widget().setText('')

    def crossAllGroupEditors(self) -> IDFGroupEditor:
        geditors = []
        for box in self.geditorbox:
            try:
                geditors.append(box.packGroupEditor())
            except:
                pass
        if len(geditors) == 0: return None
        geditor = copy.deepcopy(geditors[0])
        if len(geditors) > 1:
            for i in range(1, len(geditors)):
                geditor = IDFGroupEditor.cross(geditor, geditors[i])
        return geditor,self.fileNames

    def updateProjectGroupEditor(self):
        self.prj.groupeditor = [box.packGroupEditor() for box in self.geditorbox]


class editorWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        super(editorWidget, self).__init__(parent, window, prj)
        self.itemHeight = rowHight*4
        self.prj = prj
        self.editorboxlist = []

        self.hboxlayout = QtWidgets.QHBoxLayout(self)
        self.AcceptDeleteWidget = acceptDeleteBox(parent=self, rect=QtCore.QRect(0, 0, 20, self.height()))
        self.AcceptDeleteWidget.hide()

        self.hboxlayout.setContentsMargins(5, 0, 5, 0)
        self.vboxlayoutwidget = QtWidgets.QWidget(self)
        self.hboxlayout.addWidget(self.vboxlayoutwidget)
        self.hboxlayout.addWidget(self.AcceptDeleteWidget)

        self.vboxlayout = QtWidgets.QVBoxLayout(self.vboxlayoutwidget)
        self.vboxlayout.setContentsMargins(0, 5, 0, 5)
        self.setAcceptDrops(True)

    def addEditorBox(self, adding: list, overwrite=True):
        adding_new = []
        for item in adding:
            find = False
            for itemnow in self.editorboxlist:
                if item.equal(itemnow.item):
                    find = True
                    break
            if not find:
                adding_new.append(item)

        for i in range(len(adding_new)):
            self.editorboxlist.append(
                IDFEditorBox(
                    parent=self,
                    item=adding_new[i],
                    prj=self.prj,
                    rect=QtCore.QRect(0, 0, self.width() - 20, self.itemHeight)
                ))
            self.vboxlayout.addWidget(self.editorboxlist[-1], len(self.editorboxlist) - 1)
            if overwrite:
                self.prj.editor.append(adding_new[i])

        self.setGeometry(QtCore.QRect(10, 10, self.parent().width(), self.vboxlayout.count() * (self.itemHeight+5)))

    def acceptDelete(self):
        self.AcceptDeleteWidget.show()

    def deleteEvent(self):
        try:
            if self.prj.library['DragEventObject']:
                for i in range(len(self.editorboxlist)):
                    if self.editorboxlist[i].item == self.prj.library['DragEventObject']:
                        editorbox = self.editorboxlist[i]
                        self.vboxlayout.removeWidget(editorbox)
                        editorbox.deleteLater()
                        for j in range(i + 1, len(self.editorboxlist)):
                            widget = self.editorboxlist[j]
                            self.vboxlayout.removeWidget(widget)
                            self.vboxlayout.addWidget(widget, j - 1)
                        try:
                            self.editorboxlist.remove(self.editorboxlist[i])
                            self.prj.editor.remove(editorbox.item)
                        except:
                            pass
                        break
            self.setGeometry(QtCore.QRect(10, 10, self.parent().width(), self.vboxlayout.count() * self.itemHeight))
            self.AcceptDeleteWidget.hide()
        except Exception as e:
            traceback.print_exc()

    def dragEnterEvent(self, event):
        if self.prj.library['DragEventObject']:
            item = self.prj.library['DragEventObject']
            if isinstance(item, IDFsearchresult):
                self.dropHint = QtWidgets.QLabel(parent=self)
                self.dropHint.setStyleSheet(emptyBoxStyleSheetHover)
                self.dropHint.setText('DROP HERE!')
                self.dropHint.setGeometry(0, 0, self.width() - 20, self.itemHeight*3)
                self.vboxlayout.addWidget(self.dropHint)
                event.setDropAction(Qt.MoveAction)
                event.accept()

    def dragLeaveEvent(self, event):
        if self.prj.library['DragEventObject']:
            item = self.prj.library['DragEventObject']
            if isinstance(item, IDFsearchresult):
                self.vboxlayout.removeWidget(self.dropHint)
                self.dropHint.deleteLater()

    def dropEvent(self, event):
        self.dragLeaveEvent(event)
        if self.prj.library['DragEventObject']:
            item = self.prj.library['DragEventObject']
            if isinstance(item, IDFsearchresult):
                self.addEditorBox([item])

class resultWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        super(resultWidget, self).__init__(parent, window, prj)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.exportButton = QtWidgets.QPushButton(self)
        self.exportButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.exportButton.hide()
        if self.prj.model is not None:
            if self.prj.model.folder is not None:
                self.initResultView()
            else:
                self.createExportButton()
        else:
            self.createExportButton()

    def createExportButton(self):
        self.gridLayout.addWidget(self.exportButton)
        self.exportButton.setStyleSheet(suggestionBoxStyleSheet)
        self.exportButton.setText("Click to Select a Result Folder...")
        self.exportButton.setFont(QtGui.QFont('Arial', 30))
        self.exportButton.clicked.connect(self.mainWindow.action_Result_Folder)
        self.exportButton.show()

    def initResultView(self):
        self.exportButton.hide()
        self.resultBox = ResultBox(prj=self.prj,parent=self)
        self.mainWindow.exportButton.clicked.connect(self.resultBox.toCsv)
        self.gridLayout.replaceWidget(self.exportButton,self.resultBox)


def clear_grid(layout: QtWidgets.QGridLayout, delete_widgets=True):
    """
    清空 QGridLayout 里的所有控件/子布局
    :param layout: 要清空的 QGridLayout
    :param delete_widgets: True  同时销毁控件；
                           False 仅从布局移除，控件还活着（可移到别的布局）
    """
    while layout.count():  # count() 会动态变化，必须 while
        item = layout.takeAt(0)  # 从 0 开始取，取完自动前移
        if item.widget():  # ---- 情况 1：纯控件 ----
            w = item.widget()
            layout.removeWidget(w)
            if delete_widgets:
                w.deleteLater()
        elif item.layout():  # ---- 情况 2：子布局 ----
            clear_grid(item.layout(), delete_widgets)
            item.layout().deleteLater()
        elif item.spacerItem():  # ---- 情况 3：弹簧 ----
            layout.removeItem(item.spacerItem())