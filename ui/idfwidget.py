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
        """
        Initialize the searchWidget instance.
        
        Parameters
        ----------
        parent : QWidget
            Parent widget to which this widget belongs.
        window : QMainWindow
            Main application window associated with this widget.
        prj : project
            Project instance containing data and settings for the application.
        
        Returns
        -------
        None
        """
        super(redirectQWidget, self).__init__(parent=parent)
        self.prj: project = prj
        self.mainWindow = window


class searchWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        """
        Initialize the search widget with UI components and layout for searching and comparing items.
        
        Parameters
        ----------
        parent : QtWidgets.QWidget
            Parent widget to which this search widget belongs.
        window : object
            Main window or container window object that manages this widget.
        prj : object
            Project object containing data and configurations used by the widget.
        
        Returns
        -------
        None
        """
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
        """
        Compare the current project's IDF model with a user-selected baseline IDF file.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have 
            attributes `prj` (project object with `model` and `tempFolder`), 
            `mainWindow` (with `groupEditorArea`), and helper methods `_create_SearchResultLayout`.
        
        Returns
        -------
        None
            This function does not return a value. It opens a file dialog, computes 
            differences between IDF models, displays results in a search layout, and 
            launches a group editor interface if successful. Errors are caught and 
            printed to stdout.
        """
        try:
            if self.prj.model is not None:
                filePath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Select the baseline *.idf file", "./",
                                                                               'EnergyPlus Input Files (*.idf)')
                if filePath:
                    otherIDF = IDFModel(filePath)
                    searchResults = self.prj.model.diff(otherIDF)

                    # filter the search result with the Name as field
                    searchResults = [sr for sr in searchResults if re.search('name',sr.field,re.IGNORECASE) is None]

                    self._create_SearchResultLayout(searchResults)
                    editors = [IDFEditor(sr) for sr in searchResults]
                    tempCsv = os.path.join(self.prj.tempFolder, '_groupEditor.csv')
                    IDFGroupEditor(*editors).to_csv(tempCsv)
                    geBox = self.mainWindow.groupEditorArea.readCSV(tempCsv)
                    geBox.openFile()
                    # os.startfile(geBox.dataSheet)
        except Exception as e:
            print(traceback.format_exc())
    def _create_SearchResultLayout(self, result: list):
        """
        Create a grid layout for displaying search results in the SearchResultLayout.
        
        Parameters
        ----------
        result : list
            A list of items to be displayed in the search result layout. Each item is used to create a corresponding widget.
        
        Returns
        -------
        None
            This function does not return any value. It modifies the layout and geometry of the SearchResultLayout and associated widgets.
        """
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
        """
        Handle search operation based on class, name, and field input strings.
        
        Parameters
        ----------
        self : object
            The instance of the relateSearchWidget class, containing UI elements and project model.
            Expected to have attributes: classText, nameText, fieldText (text input fields),
            and prj (project object with a model attribute).
        
        Returns
        -------
        None
            This function does not return a value. It performs a side effect by creating a search result layout
            if the search is successful, or prints an exception traceback if an error occurs.
        """
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
        """
        Initialize the relateSearchWidget with parent, window, and project context.
        
        Parameters
        ----------
        parent : QWidget
            Parent widget to which this widget belongs.
        window : QMainWindow
            Main application window instance providing UI context and functionality.
        prj : object
            Project object containing data and settings relevant to the current session.
        
        Returns
        -------
        None
        """
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
        """
        Clear the grid in the relate processing area.
        
        This method clears all content from the grid within the relate processing area
        by calling its clearGrid method.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the relateProcessingArea attribute.
        
        Returns
        -------
        None
            This method does not return any value.
        """
        """Clear the grid in the relate processing area.
        
                This method clears all content from the grid within the relate processing area
                by calling its clearGrid method.
                """
        self.relateProcessingArea.clearGrid()


class relatedResultWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        """
        Initialize the relatedResultWidget with parent, window, and project settings.
        
        Parameters
        ----------
        parent : QWidget
            Parent widget to which this widget belongs.
        window : QWidget
            Main window or container widget associated with this widget.
        prj : object
            Project object containing configuration and data for the application.
        
        Returns
        -------
        None
        """
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
        """
        Initialize an empty board grid based on current widget dimensions.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have
            attributes `gridlayout`, `width()`, `height()`, `itemwidth`, 
            `itemheight`, `add_emptybox()`, and `arrange()`.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.gridlayout.columns = int(np.floor(self.width() / self.itemwidth))
        self.gridlayout.rows = int(np.floor(self.height() / self.itemheight))
        for i in range(self.gridlayout.rows):
            for j in range(self.gridlayout.columns):
                self.add_emptybox(i, j)
        self.arrange()

    def add_emptybox(self, i, j):
        """
        Add an empty box widget to the grid layout at the specified position.
        
        Parameters
        ----------
        i : int
            Row index where the empty box will be placed in the grid layout.
        j : int
            Column index where the empty box will be placed in the grid layout.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        emptyblock = emptyBox(self, i, j, itemheight=self.itemheight)
        self.gridlayout.addWidget(emptyblock, i, j)

    def removeitem(self, i, j):
        """
        Remove the item at the specified position (i, j) in the grid layout.
        
        Parameters
        ----------
        i : int
            Row index of the item to remove.
        j : int
            Column index of the item to remove.
        
        Returns
        -------
        None
        """
        try:
            item = self.gridlayout.itemAtPosition(i, j)
            self.gridlayout.removeItem(item)
            if item.widget():
                item.widget().deleteLater()
        except:
            return

    def clearGrid(self):
        """
        Clears the grid by removing all items and replacing them with empty boxes.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the grid layout. It is expected to have
            a `gridlayout` attribute with `rows` and `columns` properties, and methods
            `removeitem(i, j)` and `add_emptybox(i, j)`.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        for i in range(self.gridlayout.rows):
            for j in range(self.gridlayout.columns):
                self.removeitem(i, j)
                self.add_emptybox(i, j)

    def arrange(self):
        """
        Arrange the grid layout by setting row and column stretch factors and minimum dimensions.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the grid layout and associated attributes.
            Expected to have a `gridlayout` attribute with `rows` and `columns` properties,
            and `itemheight` and `itemwidth` attributes defining the minimum height and width.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        for i in range(self.gridlayout.rows):
            self.gridlayout.setRowStretch(i, 10)
            self.gridlayout.setRowMinimumHeight(i, self.itemheight)
        for j in range(self.gridlayout.columns):
            self.gridlayout.setColumnStretch(j, 10)
            self.gridlayout.setColumnMinimumWidth(j, self.itemwidth)

    def expenddgridrow(self):
        """
        Expand the grid layout by adding a new row of empty boxes.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have
            attributes `gridlayout`, `itemwidth`, `itemheight`, and methods `add_emptybox`
            and `arrange`. The `gridlayout` should have attributes `rows` and `columns`.
        
        Returns
        -------
        None
            This function does not return a value. It modifies the grid layout in place
            by adding a new row and adjusting the geometry and arrangement of items.
        """
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
        """
        Expand the grid layout by adding a new column and adjusting the geometry.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have
            attributes `gridlayout`, `itemwidth`, `itemheight`, and methods `add_emptybox`
            and `arrange`. The `gridlayout` should have attributes `rows` and `columns`.
        
        Returns
        -------
        None
            This function does not return any value. It modifies the grid layout in place
            and adjusts the geometry of the object.
        """
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
        """
        Add a box to the specified grid position and update layout.
        
        Parameters
        ----------
        row : int
            The row index in the grid layout where the box will be added.
        col : int
            The column index in the grid layout where the box will be added.
        
        Returns
        -------
        None
            This function does not return any value.
        """
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
        """
        Handle right mouse button press event to toggle display of referenced items in a grid layout.
        
        Parameters
        ----------
        self : groupEditorWidget
            The instance of the groupEditorWidget handling the event.
        event : QtGui.QMouseEvent
            The mouse event containing position and button information.
        
        Returns
        -------
        None
            This function does not return any value. It performs UI updates based on the mouse interaction.
        """
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
        """
        Initialize the groupEditorWidget with parent, window, and project settings.
        
        Parameters
        ----------
        parent : QWidget
            Parent widget to which this widget belongs.
        window : QMainWindow or QWidget
            Main window or container window that holds this widget.
        prj : object
            Project object containing configuration and data for the current project.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
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
        """
        Open group editor data in a temporary CSV file.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have
            `crossAllGroupEditors` method and `prj` attribute with `tempFolder` property.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        geditor = self.crossAllGroupEditors()
        if geditor is not None:
            tempCsv = os.path.join(self.prj.tempFolder, '_groupEditor.csv')
            geditor.to_csv(tempCsv)
            os.startfile(tempCsv)

    def editorFromCSV(self):
        """
        Open a file dialog to select and read a CSV file containing parameters.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have
            a `prj` attribute with a `model` field, and a `readCSV` method to process
            the selected CSV file.
        
        Returns
        -------
        None
            This function does not return any value. It performs side effects by
            opening a file dialog and attempting to read the selected CSV file.
        """
        try:
            if self.prj.model is not None:
                filePath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Select the params csv", "./",
                                                                           'Comma-Separated Values Files (*.csv)')
                if filePath:
                    self.readCSV(filePath)
        except Exception as e:
            print(traceback.format_exc())

    def readCSV(self,filePath):
        """
        Read and load a CSV file into the editor interface, creating a new IDFGroupEditorBox.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method.
        filePath : str
            Path to the CSV file to be read and loaded.
        
        Returns
        -------
        IDFGroupEditorBox
            The newly created and appended IDFGroupEditorBox instance corresponding to the loaded CSV file.
        """
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
        return self.geditorbox[-1]

    def emptyGroupEditor(self):
        """
        Create and return a styled QLabel widget with fixed dimensions.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Used as parent for the QLabel.
        
        Returns
        -------
        QtWidgets.QLabel
            A QLabel widget with predefined stylesheet and size properties (800x150 pixels).
        """
        emptyblock = QtWidgets.QLabel(parent=self)
        emptyblock.setStyleSheet(emptyBoxStyleSheet)
        emptyblock.setGeometry(0, 0, 800, 150)
        emptyblock.setMinimumHeight(150)
        emptyblock.setMinimumWidth(800)
        return emptyblock

    def arrange(self):
        """
        Arrange widgets in the layout by adjusting geometry and stretch factors.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have 
            a `VBoxLayout` attribute (QVBoxLayout) for managing the layout of widgets, 
            and methods `count()`, `itemAt()`, `widget()`, `setGeometry()`, and `setStretch()`.
        
        Returns
        -------
        None
            This function does not return a value. It modifies the geometry of the widget 
            and the stretch factors of the layout items in place.
        """
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
        """
        Handle the press event for a child grid node.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method.
        gridnode : QWidget
            The grid node widget to be replaced upon the press event.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        try:
            self.VBoxLayout.replaceWidget(gridnode, self.emptyGroupEditor())
            self.geditorbox.remove(gridnode)
            self.updateProjectGroupEditor()
        except Exception as e:
            print(traceback.format_exc())

    def toGroupEditor(self,item):
        """
        Convert an item to an IDFGroupEditor instance.
        
        Parameters
        ----------
        item : IDFsearchresult or IDFEditor
            The item to be converted. If it is an IDFsearchresult, it will first be 
            converted to an IDFEditor, then to an IDFGroupEditor. If the item's field 
            attribute is None or empty, it will be set to the third field in the object's 
            fieldnames list.
        
        Returns
        -------
        IDFGroupEditor
            An instance of IDFGroupEditor created from the input item.
        """
        if isinstance(item, IDFsearchresult):
            if item.field is None or item.field == '':
                item.field = item.obj.fieldnames[2]
            item = IDFEditor(item)
        if isinstance(item, IDFEditor):
            item = IDFGroupEditor(item)
        return item
    def dropEvent(self, event: QtGui.QMouseEvent):
        """
        Handle the drop event for dragging and dropping items within the layout.
        
        Parameters
        ----------
        event : QtGui.QMouseEvent
            The mouse event containing position and state information for the drop operation.
        
        Returns
        -------
        None
            This function does not return any value.
        """

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
        """
        Handle the drag enter event for the widget.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method.
        event : QDragEnterEvent
            The drag enter event to be processed. It is modified to accept the drop action and set to MoveAction.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        for i in np.arange(self.VBoxLayout.count() - 1, -1, -1):
            item = self.VBoxLayout.itemAt(i)
            if item.widget():
                if not isinstance(item.widget(), IDFGroupEditorBox):
                    item.widget().setStyleSheet(emptyBoxStyleSheetHover)
                    item.widget().setText('DROP HERE!')

        event.setDropAction(Qt.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event):
        """
        Handle the drag leave event by resetting the style and text of child widgets.
        
        Parameters
        ----------
        event : QDragLeaveEvent
            The drag leave event object that triggered the function.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        for i in np.arange(self.VBoxLayout.count() - 1, -1, -1):
            item = self.VBoxLayout.itemAt(i)
            if item.widget():
                if not isinstance(item.widget(), IDFGroupEditorBox):
                    item.widget().setStyleSheet(emptyBoxStyleSheet)
                    item.widget().setText('')

    def crossAllGroupEditors(self) -> IDFGroupEditor:
        """
        Cross all group editors and return a combined IDFGroupEditor along with file names.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the method. It is expected to have
            attributes `geditorbox` (a collection of editor boxes) and `fileNames` (a 
            list or attribute indicating associated file names).
        
        Returns
        -------
        tuple or None
            A tuple containing:
            - An `IDFGroupEditor` object resulting from the successive crossing of all 
              valid group editors from `geditorbox`. If no valid editors are found, 
              returns None.
            - The `fileNames` attribute from `self`, typically a list of file names 
              associated with the editors.
        """
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
        """
        Update the project's group editor by packing group editor data from all editor boxes.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the method. Expected to have `prj` and `geditorbox` 
            attributes, where `prj` contains a `groupeditor` attribute and `geditorbox` is a list 
            of objects with a `packGroupEditor` method.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.prj.groupeditor = [box.packGroupEditor() for box in self.geditorbox]


class editorWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        """
        Initialize the editorWidget with parent, window, and project settings.
        
        Parameters
        ----------
        parent : QWidget
            Parent widget to which this editorWidget belongs.
        window : QMainWindow or QWidget
            Main window or container window associated with this widget.
        prj : object
            Project object containing configuration and data for the editor.
        
        Returns
        -------
        None
        """
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
        """
        Add new editor boxes to the current instance if they are not already present.
        
        Parameters
        ----------
        adding : list
            A list of items to be added as editor boxes. Each item is checked for duplication
            before addition.
        overwrite : bool, optional
            If True, the items added will also be appended to the project's editor list.
            Default is True.
        
        Returns
        -------
        None
            This function does not return any value.
        """
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
        """
        Show the accept delete widget.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Assumes the instance has an `AcceptDeleteWidget` attribute.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.AcceptDeleteWidget.show()

    def deleteEvent(self):
        """
        Delete the selected event from the editor and adjust the layout accordingly.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. It is expected to have the following attributes:
            - prj: An object with a `library` dictionary containing 'DragEventObject' and an `editor` list.
            - editorboxlist: A list of widget objects representing events in the editor.
            - vboxlayout: A QVBoxLayout managing the layout of editor boxes.
            - itemHeight: Integer specifying the height of each item in the layout.
            - AcceptDeleteWidget: A widget to be hidden after deletion.
            - parent(): A method returning the parent widget, expected to have a `width()` method.
        
        Returns
        -------
        None
            This function does not return any value. It modifies the GUI layout and data structures in place.
        """
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
        """
        Handle drag enter events for the widget.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method.
        event : QDragEnterEvent
            The drag enter event to be processed, which contains information about the dragged data and allows setting the drop action.
        
        Returns
        -------
        None
            This function does not return any value. It modifies the widget's state by adding a drop hint label if conditions are met and accepts the drag event.
        """
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
        """
        Handle the drag leave event by removing the drop hint widget if a valid drag event object exists.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method.
        event : QDragLeaveEvent
            The drag leave event object representing the event.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        if self.prj.library['DragEventObject']:
            item = self.prj.library['DragEventObject']
            if isinstance(item, IDFsearchresult):
                self.vboxlayout.removeWidget(self.dropHint)
                self.dropHint.deleteLater()

    def dropEvent(self, event):
        """
        Handle the drop event by processing the dragged object and adding it as an editor box if applicable.
        
        Parameters
        ----------
        event : QDropEvent
            The drop event containing metadata about the drag operation.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.dragLeaveEvent(event)
        if self.prj.library['DragEventObject']:
            item = self.prj.library['DragEventObject']
            if isinstance(item, IDFsearchresult):
                self.addEditorBox([item])

class resultWidget(redirectQWidget):
    def __init__(self, parent, window, prj):
        """
        Initialize the resultWidget instance.
        
        Parameters
        ----------
        parent : QtWidgets.QWidget
            Parent widget to which this widget belongs.
        window : object
            Main window or container object associated with the widget.
        prj : object
            Project object containing model and configuration data; expected to have a 'model' attribute 
            which may contain a 'folder' attribute used to determine initialization behavior.
        
        Returns
        -------
        None
        """
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
        """
        Create and configure an export button widget.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have
            attributes `gridLayout`, `exportButton`, `mainWindow`, and `suggestionBoxStyleSheet`.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.gridLayout.addWidget(self.exportButton)
        self.exportButton.setStyleSheet(suggestionBoxStyleSheet)
        self.exportButton.setText("Click to Select a Result Folder...")
        self.exportButton.setFont(QtGui.QFont('Arial', 30))
        self.exportButton.clicked.connect(self.mainWindow.action_Result_Folder)
        self.exportButton.show()

    def initResultView(self):
        """
        Initialize the result view by setting up the result box and connecting export functionality.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method. Expected to have attributes 
            `exportButton`, `gridLayout`, `prj`, and `mainWindow` accessible.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.exportButton.hide()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.resultBox = ResultBox(prj=self.prj,parent=self)
        self.gridLayout.replaceWidget(self.exportButton,self.resultBox)
        self.mainWindow.exportButton.clicked.connect(self.resultBox.toCsv)


def clear_grid(layout: QtWidgets.QGridLayout, delete_widgets=True):
    """
    Clear all widgets, sub-layouts, and spacers from a QGridLayout.
    
    Parameters
    ----------
    layout : QtWidgets.QGridLayout
        The layout to be cleared.
    delete_widgets : bool
        If True, widgets and child layouts are deleted (destroyed).
        If False, only removed from the layout; widgets remain alive and can be added to another layout.
    
    Returns
    -------
    None
    """
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