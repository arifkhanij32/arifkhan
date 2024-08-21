# import sys
# import os
# from PyQt5.QtWidgets import (
#     QWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
#     QDesktopWidget,QApplication
# )
# from PyQt5.QtCore import Qt

# Assuming these imports work correctly
# from imageProcess.imageProcessing import imageDisplay
# from constants import *

# class cdWritter(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.mainwindow = parent
#         if self.mainwindow:
#             self.mainwindow.print_memory_usage()
#         self.setWindowTitle('CD Writer')
#         self.screnGeometry = QDesktopWidget().availableGeometry(self)
#         self.setGeometry(
#             int(self.screnGeometry.width() / 2) - int((self.screnGeometry.width() * 0.50) / 2),
#             int(self.screnGeometry.height() / 2) - int(self.screnGeometry.height() / 4),
#             int(self.screnGeometry.width() * 0.50),
#             int(self.screnGeometry.height() / 4),
#         )
#         layout = QHBoxLayout(self)

#         patientAddButtonsLayout = QVBoxLayout(self)

#         self.clearButton = QPushButton("Clear")
#         self.clearButton.setFixedWidth(200)  # Adjusted fixed width
#         self.clearButton.setFixedHeight(40)  # Adjusted fixed height
#         self.clearButton.setStyleSheet(self.mainwindow.buttonStyle if self.mainwindow else "")
#         self.clearButton.clicked.connect(self.ClearF)
#         patientAddButtonsLayout.addWidget(self.clearButton)

#         layout.addLayout(patientAddButtonsLayout)

#         self.patientListWidget = QListWidget()
#         self.patientListWidget.itemSelectionChanged.connect(self.listF)
#         layout.addWidget(self.patientListWidget)

#         cdWriteLayout = QVBoxLayout(self)

#         self.writeButton = QPushButton("Write")
#         self.writeButton.setFixedWidth(200)  # Adjusted fixed width
#         self.writeButton.setFixedHeight(40)  # Adjusted fixed height
#         self.writeButton.setStyleSheet(self.mainwindow.buttonStyle if self.mainwindow else "")
#         self.writeButton.clicked.connect(self.writeButtonF)
#         cdWriteLayout.addWidget(self.writeButton)

#         self.outputFolderButton = QPushButton("Output Folder")
#         self.outputFolderButton.setFixedWidth(200)  # Adjusted fixed width
#         self.outputFolderButton.setFixedHeight(40)  # Adjusted fixed height
#         self.outputFolderButton.setStyleSheet(self.mainwindow.buttonStyle if self.mainwindow else "")
#         self.outputFolderButton.clicked.connect(self.callExport)
#         cdWriteLayout.addWidget(self.outputFolderButton)

#         layout.addLayout(cdWriteLayout)

#     def listF(self):
#         # Placeholder for handling list item selection changes
#         pass

#     def ClearF(self):
#         self.patientListWidget.clear()

#     def writeButtonF(self):
#         # Placeholder for handling CD writing logic
#         pass

#     def outputFolderButtonF(self):
#         # Placeholder for handling output folder selection logic
#         pass

#     def callExport(self):
#         if self.mainwindow:
#             self.sendExe = True
#             self.mainwindow.outsideExport()
#             self.sendExe = False
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QListWidget, QDesktopWidget

class cdWritter(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainwindow = parent
        
        # Ensure mainwindow is passed and can be used
        if self.mainwindow:
            self.mainwindow.print_memory_usage()

        self.setWindowTitle('CD Writter')

        self.screenGeometry = QDesktopWidget().availableGeometry(self)
        self.setGeometry(
            int(self.screenGeometry.width() / 2)
            - int((self.screenGeometry.width() * 0.50) / 2),
            int(
                int(self.screenGeometry.height() / 2)
                - (int(self.screenGeometry.height() / 2) / 2)
            ),
            int(self.screenGeometry.width() * 0.50),
            int(self.screenGeometry.height() / 4),
        )

        layout = QHBoxLayout(self)

        # Patient buttons layout
        patientAddButtonsLayout = QVBoxLayout()  # Removed `self` as the parent here
        self.addButton = QPushButton("Add")
        self._configure_button(self.addButton)
        self.addButton.clicked.connect(self.addButtonF)
        patientAddButtonsLayout.addWidget(self.addButton)

        self.clearButton = QPushButton("Clear")
        self._configure_button(self.clearButton)
        self.clearButton.clicked.connect(self.ClearF)
        patientAddButtonsLayout.addWidget(self.clearButton)

        layout.addLayout(patientAddButtonsLayout)

        # Patient list widget
        self.patientListWidget = QListWidget()
        self.patientListWidget.itemSelectionChanged.connect(self.listF)
        layout.addWidget(self.patientListWidget)

        # CD write layout
        cdWriteLayout = QVBoxLayout()  # Removed `self` as the parent here
        self.writeButton = QPushButton("Write")
        self._configure_button(self.writeButton)
        self.writeButton.clicked.connect(self.writeButtonF)
        cdWriteLayout.addWidget(self.writeButton)

        self.outputFolderButton = QPushButton("Output Folder")
        self._configure_button(self.outputFolderButton)
        self.outputFolderButton.clicked.connect(self.outputFolderButtonF)
        cdWriteLayout.addWidget(self.outputFolderButton)

        layout.addLayout(cdWriteLayout)

    def _configure_button(self, button):
        """Helper method to configure buttons with mainwindow's properties."""
        if self.mainwindow:
            # Ensure these properties exist in mainwindow, otherwise use default values
            sidebarWidth = getattr(self.mainwindow, 'sidebarWidth', 200)
            sidebarBtnHeight = getattr(self.mainwindow, 'sidebarBtnHeight', 40)
            buttonStyle = getattr(self.mainwindow, 'buttonStyle', 'background-color: lightgray;')

            button.setFixedWidth(sidebarWidth - 100)
            button.setFixedHeight(sidebarBtnHeight)
            button.setStyleSheet(buttonStyle)

    def listF(self):
        """Placeholder for handling list widget selection change."""
        pass

    def ClearF(self):
        """Clears the patient list widget."""
        self.patientListWidget.clear()

    def addButtonF(self):
        """Placeholder for handling the Add button functionality."""
        pass

    def writeButtonF(self):
        """Placeholder for handling the Write button functionality."""
        pass

    def outputFolderButtonF(self):
        """Placeholder for handling the Output Folder button functionality."""
        pass

    def callExport(self):
        """Handles the export process."""
        self.sendExe = True
        if self.mainwindow:
            self.mainwindow.outsideExport()
        self.sendExe = False


# Assuming this is the entry point of the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = cdWritter()
    window.show()
    sys.exit(app.exec_())

# # # *****************************************************************************************

# # import sys
# # import sqlite3
# # import traceback
# # from PyQt5.QtCore import Qt, QRect
# # from PyQt5.QtWidgets import (
# #     QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QDialog, 
# #     QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
# #     QDesktopWidget, QListWidget, QHBoxLayout
# # )

# # # Ensure necessary tables are created in the database
# # def create_db_tables():
# #     try:
# #         connection = sqlite3.connect('mainApplication.db')
# #         cursor = connection.cursor()

# #         cursor.execute('''
# #         CREATE TABLE IF NOT EXISTS recycleBinTable (
# #             id INTEGER PRIMARY KEY,
# #             patientName TEXT,
# #             patientID TEXT,
# #             Age INTEGER,
# #             sex TEXT,
# #             studydate TEXT,
# #             modality TEXT,
# #             studyDesc TEXT,
# #             AccessionNumber TEXT
# #         )
# #         ''')

# #         connection.commit()
# #         connection.close()
# #     except Exception as e:
# #         print("Error creating database tables:", e)


# # class DataDialog(QDialog):
# #     def __init__(self, parent=None):
# #         super().__init__(parent)
# #         self.mainWindow = parent
# #         self.patientIDColList = []

# #         self.setWindowTitle('Data Dialog')
# #         self.screenGeometry = QDesktopWidget().availableGeometry(self)
# #         self.setGeometry(
# #             int(self.screenGeometry.width() / 2) - int((self.screenGeometry.width() * 0.50) / 2),
# #             int(self.screenGeometry.height() / 2) - int((self.screenGeometry.height() / 2) / 2),
# #             int(self.screenGeometry.width() * 0.50),
# #             int(self.screenGeometry.height() / 2),
# #         )
# #         layout = QVBoxLayout(self)

# #         # Table
# #         self.restoreTableWidget = QTableWidget()
# #         self.restoreTableWidget.setColumnCount(8)
# #         self.restoreTableWidget.setHorizontalHeaderLabels([
# #             'Patient Name', 'Patient ID', 'Age', 'Sex', 'Study Date', 'Modality', 
# #             'Study Desc', 'Accession Number'
# #         ])
# #         self.restoreTableWidget.horizontalHeader().setStretchLastSection(True)
# #         self.restoreTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
# #         self.load_data()

# #         self.restoreTableWidget.itemClicked.connect(self.load_restore_patient)

# #         # Buttons
# #         self.dataLayout = QHBoxLayout()
# #         self.actionButton = QPushButton('Recycle')
# #         self.actionButton.clicked.connect(self.do_action)
# #         self.actionButton.setFixedWidth(200)
# #         self.actionButton.setFixedHeight(40)
# #         self.actionButton.setStyleSheet(self.mainWindow.buttonStyle)

# #         self.actionDeleteButton = QPushButton('Delete Patient')
# #         self.actionDeleteButton.clicked.connect(self.do_delete)
# #         self.actionDeleteButton.setFixedWidth(200)
# #         self.actionDeleteButton.setFixedHeight(40)
# #         self.actionDeleteButton.setStyleSheet(self.mainWindow.buttonStyle)

# #         self.actionEmptyButton = QPushButton('Empty Bin')
# #         self.actionEmptyButton.clicked.connect(self.do_empty)
# #         self.actionEmptyButton.setFixedWidth(200)
# #         self.actionEmptyButton.setFixedHeight(40)
# #         self.actionEmptyButton.setStyleSheet(self.mainWindow.buttonStyle)

# #         self.dataLayout.addWidget(self.actionButton, alignment=Qt.AlignCenter)
# #         self.dataLayout.addWidget(self.actionDeleteButton, alignment=Qt.AlignCenter)
# #         self.dataLayout.addWidget(self.actionEmptyButton, alignment=Qt.AlignCenter)
# #         layout.addWidget(self.restoreTableWidget)
# #         layout.addLayout(self.dataLayout)

# #     def load_restore_patient(self, item):
# #         if self.restoreTableWidget.selectedItems():
# #             modifiers = QApplication.keyboardModifiers()
# #             if not modifiers in [Qt.ShiftModifier, Qt.ControlModifier]:
# #                 self.patientIDColList.clear()
# #                 patientIDCol = self.restoreTableWidget.item(item.row(), 1)
# #                 self.patientIDColList.append(patientIDCol.text())
# #             else:
# #                 patientIDCol = self.restoreTableWidget.item(item.row(), 1)
# #                 self.patientIDColList.append(patientIDCol.text())

# #     def load_data(self):
# #         try:
# #             connection = sqlite3.connect('mainApplication.db')
# #             cursor = connection.cursor()

# #             cursor.execute("SELECT DISTINCT patientName, patientID, Age, sex, studydate, modality, studyDesc, AccessionNumber FROM recycleBinTable")
# #             data = cursor.fetchall()

# #             self.restoreTableWidget.setRowCount(len(data))
# #             for rowIndex, rowData in enumerate(data):
# #                 for columnIndex, value in enumerate(rowData):
# #                     self.restoreTableWidget.setItem(rowIndex, columnIndex, QTableWidgetItem(str(value)))

# #             cursor.close()
# #             connection.close()
# #         except Exception:
# #             print("Error loading data:", traceback.format_exc())

# #     def fetch_patient_ids(self):
# #         patient_ids = []
# #         try:
# #             connection = sqlite3.connect('mainApplication.db')
# #             cursor = connection.cursor()

# #             cursor.execute("SELECT DISTINCT patientID FROM recycleBinTable")
# #             data = cursor.fetchall()

# #             for row in data:
# #                 patient_ids.append(row[0])

# #             cursor.close()
# #             connection.close()
# #         except Exception:
# #             print("Error fetching patient IDs:", traceback.format_exc())
# #         return patient_ids

# #     def do_action(self):
# #         self.mainWindow.restorePatient(self.patientIDColList)

# #     def do_delete(self):
# #         self.mainWindow.deletePatient(self.patientIDColList)

# #     def do_empty(self):
# #         patient_ids = self.fetch_patient_ids()
# #         self.mainWindow.emptyPatient(patient_ids)


# # class MainWindow(QMainWindow):
# #     def __init__(self):
# #         super().__init__()
# #         self.buttonStyle = "font-size: 16px; padding: 10px;"
# #         self.initUI()

# #     def initUI(self):
# #         self.setWindowTitle('Main Application Window')
# #         self.setGeometry(100, 100, 800, 600)
# #         self.show_data_dialog()

# #     def show_data_dialog(self):
# #         dialog = DataDialog(self)
# #         dialog.exec_()

# #     def restorePatient(self, patientIDColList):
# #         # Logic to restore patient data
# #         pass

# #     def deletePatient(self, patientIDColList):
# #         # Logic to delete patient data
# #         pass

# #     def emptyPatient(self, patient_ids):
# #         # Logic to empty the recycle bin
# #         pass


# # # Ensure database tables are set up
# # create_db_tables()

# # # Assuming this is the entry point of the application
# # if __name__ == "__main__":
# #     app = QApplication(sys.argv)
# #     window = MainWindow()
# #     window.show()
# #     sys.exit(app.exec_())

# # # ********************************************************************************************

# # import sys
# # from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QApplication

# # class ActivationDialog(QDialog):
# #     def __init__(self):
# #         super().__init__()
# #         self.initUI()

# #     def initUI(self):
# #         self.setWindowTitle("Enter Activation Key")
# #         layout = QVBoxLayout()
        
# #         # Label
# #         self.label = QLabel("Activation Key")
# #         layout.addWidget(self.label)
        
# #         # Line Edit
# #         self.lineEdit = QLineEdit()
# #         self.lineEdit.setEchoMode(QLineEdit.Password)  # Set the echo mode to Password
# #         layout.addWidget(self.lineEdit)
        
# #         # Buttons
# #         self.buttonsLayout = QHBoxLayout()
# #         self.okButton = QPushButton("OK")
# #         self.cancelButton = QPushButton("Cancel")
# #         self.buttonsLayout.addWidget(self.okButton)
# #         self.buttonsLayout.addWidget(self.cancelButton)
        
# #         # Connecting buttons to their respective slots
# #         self.okButton.clicked.connect(self.accept)
# #         self.cancelButton.clicked.connect(self.reject)
        
# #         layout.addLayout(self.buttonsLayout)
# #         self.setLayout(layout)

# # # Running the dialog
# # if __name__ == "__main__":
# #     app = QApplication(sys.argv)
# #     dialog = ActivationDialog()
    
# #     if dialog.exec_() == QDialog.Accepted:
# #         activation_key = dialog.lineEdit.text()
# #         print(f"Activation Key: {activation_key}")
    
# #     sys.exit(app.exec_())

# # # ***********************************************************************************************
# # import sys
# # from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
# # from PyQt5.QtCore import pyqtSignal
# # from matplotlib.figure import Figure
# # from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# # class MyFigureCanvas(FigureCanvas):
# #     doubleClicked = pyqtSignal()

# #     def __init__(self, figure, parent=None, mainwindow=None):
# #         super(MyFigureCanvas, self).__init__(figure)
# #         self._parent = parent
# #         self.mainwindow = mainwindow

# #     def mouseDoubleClickEvent(self, event):
# #         if self.mainwindow and hasattr(self.mainwindow, 'openPolygonButtonActivated') and self.mainwindow.openPolygonButtonActivated:
# #             try:
# #                 self.mainwindow.oPoly.finish_drawing()
# #             except AttributeError:
# #                 pass
     
# #         elif self.mainwindow and hasattr(self.mainwindow, 'closedPolygonButtonActivated') and self.mainwindow.closedPolygonButtonActivated:
# #             try:
# #                 self.mainwindow.cPoly.finish_drawing()
# #             except AttributeError:
# #                 pass
# #         elif self.mainwindow and hasattr(self.mainwindow, 'backuprows') and hasattr(self.mainwindow, 'backupcols') and self.mainwindow.backuprows == 1 and self.mainwindow.backupcols == 1:
# #             pass
       
# #         else:
# #             self.doubleClicked.emit()
# #             super(MyFigureCanvas, self).mouseDoubleClickEvent(event)  # Maintain normal event propagation

# # # Minimal example to demonstrate MyFigureCanvas
# # class MainWindow(QMainWindow):
# #     def __init__(self):
# #         super().__init__()
# #         self.setWindowTitle("MyFigureCanvas Example")
        
# #         # Set up some properties for testing
# #         self.openPolygonButtonActivated = False
# #         self.closedPolygonButtonActivated = False
# #         self.backuprows = 1
# #         self.backupcols = 1
        
# #         # Create a figure and canvas
# #         self.figure = Figure()
# #         self.canvas = MyFigureCanvas(self.figure, self, self)
        
# #         # Setup a simple layout
# #         central_widget = QWidget(self)
# #         layout = QVBoxLayout(central_widget)
# #         layout.addWidget(self.canvas)
# #         self.setCentralWidget(central_widget)

# # if __name__ == "__main__":
# #     app = QApplication(sys.argv)
    
# #     mainWin = MainWindow()
# #     mainWin.show()
    
# #     sys.exit(app.exec_())

# # # ***********************************************************************************************

# # import sys
# # from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow
# # from PyQt5.QtCore import Qt

# # class FullscreenGraphicsView(QGraphicsView):
# #     def __init__(self, parent=None):
# #         super().__init__(parent)

# #     def mouseDoubleClickEvent(self, event):
# #         # Close the parent widget if the right mouse button is double-clicked
# #         if event.button() == Qt.RightButton:
# #             self.parentWidget().close()

# # # Minimal example to demonstrate the FullscreenGraphicsView
# # class MainWindow(QMainWindow):
# #     def __init__(self):
# #         super().__init__()
# #         self.setWindowTitle("Fullscreen Graphics View Example")
        
# #         # Create a scene and view
# #         scene = QGraphicsScene()
# #         view = FullscreenGraphicsView(self)
# #         view.setScene(scene)
        
# #         self.setCentralWidget(view)

# # if __name__ == "__main__":
# #     app = QApplication(sys.argv)
    
# #     mainWin = MainWindow()
# #     mainWin.show()
    
# #     sys.exit(app.exec_())

# # # ***********************************************************************************************

