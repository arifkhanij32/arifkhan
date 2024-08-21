from PyQt5.QtWidgets import (
    QMainWindow,
    QInputDialog,
    QMessageBox,QTableWidget,QTableWidgetItem
)
from PyQt5.QtWidgets import QDialog,QListWidget, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QApplication, QMainWindow, QPushButton


from PyQt5.QtCore import Qt

from .constants import *
import uuid
import sqlite3
import copy

class AnnotationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Text Annotation")

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Enter the text to annotate:", self)
        self.layout.addWidget(self.label)

        self.text_input = QLineEdit(self)
        self.layout.addWidget(self.text_input)
        # self.textAreaLayout=QVBoxLayout(self)
        # self.preDefinedTextList=QListWidget()
        # self.preDefinedTextList.itemClicked.connect(self.on_item_clicked)
        # self.layout.addWidget(self.preDefinedTextList)
        self.preDefinedTextTable = QTableWidget(self)
        self.preDefinedTextTable.setColumnCount(1)
        self.preDefinedTextTable.setRowCount(0)
        self.preDefinedTextTable.setHorizontalHeaderLabels(["Text"])
        self.preDefinedTextTable.setHorizontalHeaderItem(0, QTableWidgetItem(""))
        self.preDefinedTextTable.horizontalHeader().setVisible(False)
        self.preDefinedTextTable.verticalHeader().setVisible(False)
        self.preDefinedTextTable.setShowGrid(False)
        self.preDefinedTextTable.itemClicked.connect(self.on_item_clicked)
        self.layout.addWidget(self.preDefinedTextTable)
        # self.layout.addLayout(self.textAreaLayout)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            self)
        self.add_button = QPushButton("Add")
        self.delete_button = QPushButton("Delete")
        self.buttons.addButton(self.add_button, QDialogButtonBox.ActionRole)
        self.buttons.addButton(self.delete_button, QDialogButtonBox.ActionRole)
        self.load_predefined_texts()
        self.delete_button.clicked.connect(self.on_delete)

        self.add_button.clicked.connect(self.on_add)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def on_item_clicked(self, item):
        self.text_input.setText(item.text())

    def get_text(self):
        return self.text_input.text()
    
    def dbConnection(self):
        mydb = sqlite3.connect("mainApplication.db")
        return mydb
    
    def on_delete(self):
        mydb = self.dbConnection()
        cursor = mydb.cursor()
        # Replace 'preTextData' with your actual table name
        query = "DELETE FROM preTextData WHERE text=(?)"
        text = self.text_input.text()
        values = (text,)  # Ensure this is a tuple with a single element
        cursor.execute(query, values)
        mydb.commit()
        cursor.close()
        mydb.close()
        
        self.load_predefined_texts()
        self.text_input.clear()

    def load_predefined_texts(self):
        mydb = self.dbConnection()
        cursor = mydb.cursor()
        query = "SELECT text FROM preTextData ORDER BY text ASC"
        cursor.execute(query)
        values = cursor.fetchall()
        cursor.close()
        mydb.close()

        self.preDefinedTextTable.clearContents()
        self.preDefinedTextTable.setRowCount(0)
        column_count = 1
        for index, value in enumerate(values):
            row = index % 6
            column = index // 6
            if column >= self.preDefinedTextTable.columnCount():
                self.preDefinedTextTable.insertColumn(column)
            if row >= self.preDefinedTextTable.rowCount():
                self.preDefinedTextTable.insertRow(row)
            item= QTableWidgetItem(value[0])
            font=item.font()
            font.setBold(True)
            item.setFont(font)
            self.preDefinedTextTable.setItem(row, column,item)
        

    def on_add(self):
        mydb = self.dbConnection()
        cursor = mydb.cursor()
        # Replace 'preTextData' with your actual table name
        query = "INSERT INTO preTextData (text) VALUES (?)"
        text = self.text_input.text()
        values = (text,)  # Ensure this is a tuple with a single element
        try:
            cursor.execute(query, values)
            mydb.commit()
            self.text_input.clear()
            self.load_predefined_texts()
            print(f"Text '{text}' has been saved to the database.")
        except sqlite3.IntegrityError:
            self.show_error_message(f"Text '{text}' already exists.")
        finally:
            cursor.close()
            mydb.close()
        
        # Handle the add button click event
        # new_dialog = AddDialog(self)
        # if new_dialog.exec_() == QDialog.Accepted:
        #     text = new_dialog.get_text()
        #     if text:
        #         print(f"Additional annotation: {text}")
                # You can store this text as needed
    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()   

class ImageAnnotator(QMainWindow):
    def __init__(self, textButtonActivated, canvas, ax, figure, imgDCM, parent):
        super().__init__()
        self.textButtonActivated = textButtonActivated
        self.canvas = canvas
        self.ax = ax
        self.figure = figure
        self.dicom_image = imgDCM
        self.py, self.px = self.dicom_image.PixelSpacing
        self.pixel_data = self.dicom_image.pixel_array
        self.mainWindow = parent
        self.delDbList = []
        # self.setFocusPolicy(Qt.StrongFocus)
        self.selected_annotation = None
        self.canvas.KeyPressEvent = self.keyPressEvent
        self.is_dragging = False
        self.dragged_annotation = None
        # List to store text annotations
        self.annotations = []
        self.textStorageDict = {}
        self.textStorageDictOriginal= {}
        self.text_id = 0
        # self.show()
        self.setupEventConnections()

    def setupEventConnections(self):
        try:
            # Connect key press event
            self.canvas.mpl_connect("key_press_event", self.keyPressEvent)
        except:
            pass

    def dbConnection(self):
        mydb = sqlite3.connect("mainApplication.db")
        return mydb

    def on_click(self, event):
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.ax = self.getAxes()
        self.canvas = self.getCanvas()
        self.canvasIndex = self.getCanvaIndex()

        # print('textclick')
        if event.inaxes != self.ax:
            return

        self.textButtonActivated = self.getTextActivation()
        if self.textButtonActivated:
            if event.button == Qt.LeftButton:
                # print("image no",self.imageIndex)
                for annotation in self.annotations:
                    if annotation[1] != self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue

                    if annotation[2] != self.canvasIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue

                    try:
                        if annotation[0].contains(event)[0]:
                            self.is_dragging = True
                            self.dragged_annotation = annotation[0]
                            self.annotation_text = annotation[0].get_text()
                            self.position = annotation[0].get_position()
                            self.offset = (
                                event.xdata - annotation[0].get_position()[0],
                                event.ydata - annotation[0].get_position()[1],
                            )
                            self.selected_annotation = annotation[0]
                            break
                    except:
                        pass

                if not self.is_dragging:
                    # Get the text to annotate from the user
                    # text, ok = QInputDialog.getText(
                    #     self, "Text Annotation", "Enter the text to annotate:"
                    # )
                    dialog = AnnotationDialog(self)
                    ok = dialog.exec_() == QDialog.Accepted
                    text = dialog.get_text()

                    if ok and text:
                        font_size = self.calculate_font_size(self.ax)
                        # Place the text on the image at the clicked location
                        text_obj = self.ax.text(
                            event.xdata,
                            event.ydata,
                            text,
                            color=ANNOTATION_TEXT_COLOR,
                            # fontsize=ANNOTATION_FONT_SIZE,
                            fontsize=font_size,
                            # bbox=dict(facecolor=ANNOTATION_BOX_FACE_COLOR, alpha=0.5, boxstyle=ANNOTATION_BOX_STYLE),
                        )
                        self.canvas.draw()
                        self.position = text_obj.get_position()
                        self.annotations.append(
                            [text_obj, self.imageIndex, self.canvasIndex]
                        )

                        self.uid = uuid.uuid4()  # 4

                        conn = self.dbConnection()
                        cur = conn.cursor()
                        query = "SELECT EXISTS(SELECT 1 FROM textData WHERE uuid = ?)"

                        # Execute the query, replacing '?' with the new_uuid
                        cur.execute(query, (str(self.uid),))

                        # Fetch the result
                        exists = cur.fetchone()[0]

                        # self.text_id+=1
                        if self.uid == exists:
                            self.uid = uuid.uuid4()
                        else:
                            pass
                        self.textStorage(text_obj)

    def on_hover(self, event):
        if not self.annotations:
            return
        for annotation in self.annotations:
            # print(annotation.figure)
            try:
                if annotation[0].contains(event)[0]:
                    annotation[0].set_color(HOVER_ANNOTATION_TEXT_COLOR)
                else:
                    annotation[0].set_color(ANNOTATION_TEXT_COLOR)
            except:
                pass
        self.canvas.draw()

    def on_motion(self, event):
        if (
            self.is_dragging
            and self.dragged_annotation
            and self.annotation_text != None
        ):
            if event.inaxes == self.ax:
                new_x = event.xdata - self.offset[0]
                new_y = event.ydata - self.offset[1]
                self.dragged_annotation.set_position((new_x, new_y))
                self.canvas.draw()

    def on_release(self, event):
        if self.is_dragging and self.dragged_annotation:
            if event.inaxes == self.ax:
                new_x = event.xdata - self.offset[0]
                new_y = event.ydata - self.offset[1]
                self.dragged_annotation.set_position((new_x, new_y))
                self.annotation_text = self.annotation_text
                for patient_id, series_data in self.textStorageDict.items():
                    for series_name, canvas in series_data.items():
                        for series_name, images_data in canvas.items():
                            for image_index, annotations in images_data.items():
                                for annotation_info in annotations:
                                    if (
                                        annotation_info["annotation"]["text"]
                                        == self.annotation_text
                                    ):
                                        if (
                                            self.position
                                            == annotation_info["annotation"]["position"]
                                        ):
                                            annotation_info["annotation"][
                                                "position"
                                            ] = (new_x, new_y)

                self.annotation_text = None
                self.is_dragging = False
                self.dragged_annotation = None
                self.canvas.draw()
            else:
                self.is_dragging = False
                self.dragged_annotation = None

    def remove_text_from_storage(self, x, y, text):
        patientID, seriesName, canva, imageIndex = (
            self.getPatientID(),
            self.getPatientSeriesName(),
            self.getCanvaIndex(),
            self.getimageIndex(),
        )

        # Check if the specific patient, series, and image index exists in the dictionary
        if (
            patientID in self.textStorageDict
            and seriesName in self.textStorageDict[patientID]
            and canva in self.textStorageDict[patientID][seriesName]
            and imageIndex in self.textStorageDict[patientID][seriesName][canva]
        ):
            # Access the list of annotations for the current patient, series, and image index
            annotations_list = self.textStorageDict[patientID][seriesName][canva][
                imageIndex
            ]
            for annotation_info in annotations_list[:]:  # Copy for safe iteration
                # Extract the annotation details
                annotation_details = annotation_info["annotation"]
                # Check if the current annotation matches the specified position and text
                if (
                    annotation_details["position"] == (x, y)
                    and annotation_details["text"] == text
                ):
                    # If a match is found, remove the entire annotation_info from the list
                    annotations_list.remove(annotation_info)
                    self.delDbList.append(annotation_info["uuid"])

                    break  # Assuming each annotation is unique

    def keyPressEvent(self, event):
        if type(event.key) == str:
            if event.key.lower().strip() == "delete".lower().strip():
                event.key = 16777223
        else:
            pass
        # print("int(Qt.Key_Delete):",Qt.Key_Delete)
        # print("(event.key():",type(event.key())

        # Check if the delete key is pressed and there's a selected annotation
        if str(event.key) == str(Qt.Key_Delete) and self.selected_annotation:
            # Extract the necessary information from the selected annotation
            x, y = self.selected_annotation.get_position()
            text = self.selected_annotation.get_text()

            # Call the function with the required arguments
            self.remove_text_from_storage(x, y, text)

            # Remove the annotation from the plot
            self.selected_annotation.remove()
            self.canvas.draw_idle()

            # Update the list of annotations if it's being maintained
            # if self.selected_annotation in self.annotations:
            #     self.annotations.remove(self.selected_annotation)

            # Reset the selected annotation
            self.selected_annotation = None



    def creatingOriginalDict(self,text_info):
        if self.patientID not in self.textStorageDictOriginal:
            self.textStorageDictOriginal[self.patientID] = {}

        # Ensure the patient series name level exists
        if self.patientSeriesName not in self.textStorageDictOriginal[self.patientID]:
            self.textStorageDictOriginal[self.patientID][self.patientSeriesName] = {}

        if (
            self.canvasIndex
            not in self.textStorageDictOriginal[self.patientID][self.patientSeriesName]
        ):
            self.textStorageDictOriginal[self.patientID][self.patientSeriesName][
                self.canvasIndex
            ] = {}

        # Ensure the image index level exists
        if (
            self.imageIndex
            not in self.textStorageDictOriginal[self.patientID][self.patientSeriesName][
                self.canvasIndex
            ]
        ):
            self.textStorageDictOriginal[self.patientID][self.patientSeriesName][
                self.canvasIndex
            ][self.imageIndex] = []

        # Now that we've ensured all levels exist, append the arrow information
        self.textStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][
            self.imageIndex
        ].append(copy.deepcopy(text_info))

        print("text storage original",self.textStorageDictOriginal)


    def textStorage(self, text, uid=None):
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.canvasIndex = self.getCanvaIndex()

        if uid is None:
            text_info = {
                "id": self.text_id,
                "annotation": {
                    "text": text.get_text(),
                    "position": text.get_position(),
                },
                "uuid": self.uid,
                "image_index": self.imageIndex,
                "canvas_index": self.canvasIndex,
            }

        else:
            text_info = {
                "id": self.text_id,
                "annotation": {
                    "text": text.get_text(),
                    "position": text.get_position(),
                },
                "uuid": uid,
                "image_index": self.imageIndex,
                "canvas_index": self.canvasIndex,
            }

        if self.patientID not in self.textStorageDict:
            self.textStorageDict[self.patientID] = {}

        # Ensure the patient series name level exists
        if self.patientSeriesName not in self.textStorageDict[self.patientID]:
            self.textStorageDict[self.patientID][self.patientSeriesName] = {}

        if (
            self.canvasIndex
            not in self.textStorageDict[self.patientID][self.patientSeriesName]
        ):
            self.textStorageDict[self.patientID][self.patientSeriesName][
                self.canvasIndex
            ] = {}

        # Ensure the image index level exists
        if (
            self.imageIndex
            not in self.textStorageDict[self.patientID][self.patientSeriesName][
                self.canvasIndex
            ]
        ):
            self.textStorageDict[self.patientID][self.patientSeriesName][
                self.canvasIndex
            ][self.imageIndex] = []

        # Now that we've ensured all levels exist, append the arrow information
        self.textStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][
            self.imageIndex
        ].append(text_info)

        print("text storage",self.textStorageDict)
        print("")
        
        
        self.creatingOriginalDict(text_info)

        












        # text.set_gid(self.text_id)  # Associate the annotation with its ID
        self.text_id += 1

    def giveTextStorageDict(self):
        return self.textStorageDict
    def giveTextStorageDictOriginal(self):
        return self.textStorageDictOriginal

    def getPatientID(self):
        return self.mainWindow.givepatientId()

    def getPatientSeriesName(self):
        return self.mainWindow.givePatientSeriesName()

    def getimageIndex(self):
        return self.mainWindow.giveImageIndex()

    def getUniqueTextId(self):
        return self.mainWindow.giveUniqueTextId()

    def getAxes(self):
        return self.mainWindow.giveAxes()

    def getCanvas(self):
        return self.mainWindow.giveCanvas()

    def getTextActivation(self):
        return self.mainWindow.giveTextActivaton()

    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()

    def calculate_font_size(self, ax):
        """Calculate font size based on the dimensions of the axes."""
        bbox = ax.get_window_extent().transformed(
            self.figure.dpi_scale_trans.inverted()
        )
        # Calculate font size as a fraction of the subplot height
        height_in_pixels = self.figure.dpi * bbox.height
        return max(6, min(12, height_in_pixels * 0.02))  # Example calculation

    def update_annotation_font_sizes(self):
        """Update the font sizes of all annotations according to the new layout."""
        for ax in self.figure.axes:
            font_size = self.calculate_font_size(ax)
            for text in ax.texts:
                text.set_fontsize(font_size)
        self.canvas.draw_idle()


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     image_path = "MRBRAIN.dcm"
#     main = ImageAnnotator(image_path)
#     sys.exit(app.exec_())
