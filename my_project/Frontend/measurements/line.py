
from PyQt5.QtCore import Qt
from matplotlib.lines import Line2D
from PyQt5.QtWidgets import QMainWindow
import math
import matplotlib
from .constants import *
import uuid
import sqlite3
import copy


class LineTool(QMainWindow):
    def __init__(
        self,
        lineButtonActivated,
        canvas,
        ax,
        figure,
        dicomImage,
        measurementToggle,
        parent,
    ):
        global isLineHover
        isLineHover = False
        global sMeasurementToggle
        super().__init__()
        self.lineButtonActivated = lineButtonActivated
        self.canvas = canvas
        self.ax = ax
        self.figure = figure
        # sMeasurementToggle = measurementToggle
        self.mainWindow = parent

        sMeasurementToggle = self.getMeasurementToggle()

        self.dicomImage = dicomImage
        self.py, self.px = self.dicomImage.PixelSpacing
        # print(f"px {self.px} py {self.py}")
        # print("parent:", parent)

        # self.figure, self.ax = plt.subplots()
        # self.canvas = FigureCanvas(self.figure)

        # self.canvas.mpl_connect("button_press_event", self.mousePressEvent)
        # self.canvas.mpl_connect("motion_notify_event", self.mouseMoveEvent)
        # self.canvas.mpl_connect("button_release_event", self.mouseReleaseEvent)
        # self.canvas.mpl_connect("motion_notify_event", self.update_hover)
        # self.canvas.mpl_connect('key_press_event', self.keyPressEvent)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.setFocus()


        self.line_id=0
        self.drawing = False
        self.lines = []
        self.xdata = []
        self.ydata = []
        self.delDbList=[]

        self.text_annotation = None
        self.line_text_dict = {}
        self.hover_states = {}
        self.hovered_lines = set()
        self.current_lines = []
        self.lineStorageDict={}
        self.lineStorageDictOriginal={}
        self.current_line = None
        self.selected_line = None
        self.selected_annotation = None
        self.line_offset = None
        self.dragging_item = None  # 'line' or 'annotation'
        self.initial_annotation_offset = (
            None  # Offset between line endpoint and annotation
        )
        self.moved_annotations = set()
        self.annotation_offset = (0, 0)  # Initialize with a default value
        self.measurement_box_moved = {}  # Tracks if the measurement box was moved first
        self.moving_line = False
        self.moved_annot={}
        self.dragging_annotation = None
        self.selected_endpoint = None
        self.is_dragging_endpoint = False
        self.annotation_moved_first = {}
        self.last_drawn_line = None
        self.last_drawn_annotation = None
        self.del_selected_line = None
        self.del_selected_annotation = None
        self.background = None
        self.bool_line_hower = None
        self.setupEventConnections()
    # -----------------------------------------------------------------------
    def setupEventConnections(self):
        try:
            # Connect key press event
            self.canvas.mpl_connect("key_press_event", self.DeletePressEvent)
        except:
            pass

    def dbConnection(self):
        mydb = sqlite3.connect("mainApplication.db")
        return mydb

    def getMeasurementToggle(self):
        return self.mainWindow.updatedMeasurementValue()

    def globalLineHover(self, val):
        global bool_line_hower
        bool_line_hower = val
        # print("globalLineHover:", bool_line_hower)
        return bool_line_hower

    def setMeasurementToggle(
        self,
    ):
        global sMeasurementToggle
        # print("sMeasurementToggle:", sMeasurementToggle)
        sMeasurementToggle = not sMeasurementToggle

    def DeletePressEvent(self, event):
        if type(event.key) == str:
            if event.key.lower().strip() == "delete".lower().strip():
                event.key = 16777223
        else:
            pass
        if str(event.key) == str(Qt.Key_Delete):
            if self.del_selected_line or self.del_selected_annotation:
                # Remove the line and annotation from the display
                self.del_selected_line.remove()
                if self.del_selected_annotation is not None:
                    self.del_selected_annotation.remove()

                # Remove the line from the current lines list if present
                # if self.del_selected_line in self.current_lines:
                #     self.current_lines.remove(self.del_selected_line)

                # Remove the line and annotation from the line-text dictionary
                if self.del_selected_line in self.line_text_dict:
                    del self.line_text_dict[self.del_selected_line]
                
                
                 # Remove the line from the line storage dictionary
                self.remove_line_from_storage(self.del_selected_line)
                # Clear the selected items to avoid repeated deletion
                self.del_selected_line = None
                self.del_selected_annotation = None
                # annotation=None
            self.canvas.draw_idle()

            if self.last_drawn_line or self.last_drawn_annotation:
                # Safely remove the last drawn line from the canvas and tracking list
                try:
                    self.last_drawn_line.remove()
                    # if self.last_drawn_line in self.current_lines:
                    #     self.current_lines.remove(self.last_drawn_line)
                except ValueError:
                    # Handle the case where the line was not in the list
                    pass

                # Safely remove the last drawn annotation from the canvas and dictionary
                try:
                    if self.last_drawn_annotation is not None:
                        self.last_drawn_annotation.remove()
                    if self.last_drawn_line in self.line_text_dict:
                        del self.line_text_dict[self.last_drawn_line]
                except ValueError:
                    # Handle the case where the line or annotation was not in the dictionary
                    pass

                # Clear the last drawn line and annotation
                self.last_drawn_line = None
                self.last_drawn_annotation = None

                # Redraw the canvas to reflect the changes
            self.canvas.draw_idle()

    def remove_line_from_storage(self, line):
        # Iterate through the lineStorageDict and remove the line information
        for patient_id, patient_data in self.lineStorageDict.items():
            for series_name, series_data in patient_data.items():
                for canvaid, canva in series_data.items():
                    for image_index, lines_info in canva.items():
                        for index, line_info in enumerate(lines_info):
                            if line_info["line"] == line:
                                self.delDbList.append(line_info["uuid"])
                                del self.lineStorageDict[patient_id][series_name][canvaid][image_index][index]
                                
                                # If the line info list becomes empty, remove the key
                                # if not self.lineStorageDict[patient_id][series_name][image_index]:
                                #     del self.lineStorageDict[patient_id][series_name][image_index]
            #                         # If the series data becomes empty, remove the key
            #                         if not self.lineStorageDict[patient_id][series_name]:
            #                             del self.lineStorageDict[patient_id][series_name]
            #                             # If the patient data becomes empty, remove the key
            #                             if not self.lineStorageDict[patient_id]:
            #                                 del self.lineStorageDict[patient_id]
            #                                 # If the lineStorageDict becomes empty, exit the loop
            #                                 if not self.lineStorageDict:
            #                                     return
            # print("Updated line storage dict:", self.lineStorageDict)

    def mousePressEvent(self, event):
        self.lineButtonActivated = self.getLineActivation()

        if self.lineButtonActivated :
            # print("insideee line" ,self.mainWindow.pixelSpacing)
            self.py, self.px = self.mainWindow.pixelSpacing
            sMeasurementToggle = self.getMeasurementToggle()
            self.ax=self.getAxes()
            self.canvas=self.getCanvas()
            self.imageIndex = self.getimageIndex()
            self.canvasIndex = self.getCanvaIndex()

            # print("self.imageIndex", self.imageIndex)
            self.patientID = self.getPatientID()
            self.patientSeriesName = self.getPatientSeriesName()

            # if self.lineButtonActivated:
            # print("sm L", sMeasurementToggle)

            if event.button == 1:  # Left mouse button
                # self.selected_line = None
                # self.selected_annotation = None
                self.del_selected_line = None
                self.del_selected_annotation = None
                # print("self.line_text_dict",self.line_text_dict)
                # for line in self.current_lines:
                for line, annotation in self.line_text_dict.items():
                    if  annotation[1]!= self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue 
                    if  annotation[2]!= self.canvasIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue
                    annotation=annotation[0]
                    
                    if line is not None:
                        if line.contains(event)[0]:
                            self.del_selected_line = line
                            # self.del_selected_annotation = self.line_text_dict.get(line, None)
                            self.del_selected_annotation = annotation
                        # break
                        if annotation is not None:
                            if annotation.contains(event)[0]:
                                self.del_selected_line = line
                                self.del_selected_annotation = annotation
                                # break

                        if self.is_near_endpoint(event.xdata, event.ydata, line):
                            self.selected_line = line
                            self.selected_endpoint = (
                                "start"
                                if self.is_near_start(event.xdata, event.ydata, line)
                                else "end"
                            )
                            # print("selected line",self.selected_line)
                            # print("end pointtttt",self.selected_endpoint)
                            value=self.line_text_dict.get(line, None)
                            if value is not None:
                                self.selected_annotation =value[0]
                            else:
                                self.selected_annotation =None
                            self.is_dragging_endpoint = True
                            return

                        if (
                            annotation is not None 
                        ):  # Ensure annotation is drawn
                            if annotation.contains(event)[0]:
                                # print("inside annot preeeeees")
                                self.selected_annotation = annotation
                                self.selected_line = line
                                # self.del_selected_line=line
                                x, y = annotation.get_position()
                                self.annotation_offset = (x - event.xdata, y - event.ydata)
                                self.dragging_item = "annotation"
                                self.moved_annot[self.selected_line]=True
                                self.moved_annotations.add(
                                    annotation
                                )  
                                # print(" self.moved_annotations", self.moved_annotations)# Mark annotation as moved
                                # self.del_selected_annotation=annotation
                                self.annotation_moved_first[annotation] = True
                                # print("self.annotation_moved_first[annotation]",self.annotation_moved_first[annotation])
                                return
                            
                        if line.contains(event)[0]:
                            self.selected_line = line
                            self.selected_annotation = annotation
                            xdata, ydata = line.get_data()
                            self.line_offset = [
                                (x - event.xdata, y - event.ydata)
                                for x, y in zip(xdata, ydata)
                            ]
                            self.dragging_item = "line"
                            # Initialize annotation_offset even when the line is selected
                            if annotation:
                                annot_x, annot_y = annotation.get_position()
                                self.annotation_offset = (
                                    annot_x - xdata[-1],
                                    annot_y - ydata[-1],
                                )
                            else:
                                self.annotation_offset = (
                                    0,
                                    0,
                                )  # Default offset if no annotation exists
                            # return

                for line in self.current_lines:
                    if  line[1]!= self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue 
                    if  line[2]!= self.canvasIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue 
                    try:
                        if line[0].contains(event)[0]:
                            self.selected_line = line[0]
                            value=self.line_text_dict.get(line[0], None)
                            if value is not None:
                                self.selected_annotation =value[0]
                            else:
                                self.selected_annotation =None
                            return
                    except Exception as ex:
                        pass

                # If no line or annotation is selected, start drawing a new line
                if event.inaxes:
                    self.xdata = [event.xdata]
                    self.ydata = [event.ydata]
                    self.drawing = True
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)

    def update_line_in_storage(self, line, annotation=None):
        for patient_id, patient_data in self.lineStorageDict.items():
            for series_name, series_data in patient_data.items():
                for canva_id, canva in series_data.items():
                    for image_index, lines_info in canva.items():

                        for line_info in lines_info:
                            if line_info["line"] == line:
                                line_info["line"] = line
                                if annotation!= None:
                                    line_info["annotation"] = annotation
                                return
                        
    def mouseMoveEvent(self, event):
        sMeasurementToggle = self.getMeasurementToggle()

        # if self.lineButtonActivated:
        if self.background is not None:
            self.canvas.restore_region(self.background)
            
        if self.dragging_item == "line" and self.selected_line:
            new_line_data = [
                (event.xdata + dx, event.ydata + dy) for dx, dy in self.line_offset
            ]
            self.selected_line.set_data(list(zip(*new_line_data)))
            # print("self.selected_annotation",self.selected_annotation)
            # print("self.moved_annotations",self.moved_annotations)

            if (self.moved_annot[self.selected_line]==False
               
            ):
                # print("inside anootation")
                # Calculate new annotation position based on the line's new endpoint
                new_annotation_pos = (
                    new_line_data[-1][0] + self.annotation_offset[0],
                    new_line_data[-1][1] + self.annotation_offset[1],
                )
                self.selected_annotation.set_position(new_annotation_pos)
                self.update_line_in_storage(self.selected_line, self.selected_annotation)
                # print("after moved annotation",self.lineStorageDict)
            else:
                
                self.update_line_in_storage(self.selected_line)    
            self.canvas.draw_idle()

        elif self.dragging_item == "annotation" and self.selected_annotation:
            # print("movvvving annnnot ")
            new_x = event.xdata + self.annotation_offset[0]
            new_y = event.ydata + self.annotation_offset[1]
            self.selected_annotation.set_position((new_x, new_y))
            self.update_line_in_storage(self.selected_line, self.selected_annotation)
            self.canvas.draw_idle()

        if self.drawing and event.inaxes:
            self.xdata.append(event.xdata)
            self.ydata.append(event.ydata)
            self.draw_lines(eventType="move", showMeasurement=sMeasurementToggle)

            # Remove any existing dragging annotation if it's an annotation object
            if isinstance(self.dragging_annotation, matplotlib.text.Text):
                self.dragging_annotation.remove()
                self.dragging_annotation = None

            if sMeasurementToggle:
                font_size = self.calculate_font_size(self.ax)
                # Calculate and display real-time distance
                # distance = self.distance_measure_while_drag(event.xdata, event.ydata)
                distance = self.calculate_distance(
                    self.xdata[0], self.ydata[0], event.xdata, event.ydata
                )
                # Create a new dragging annotation with blue face color
                self.dragging_annotation = self.ax.text(
                    event.xdata + 8,
                    event.ydata + 3,
                    distance,
                    # fontsize=ANNOTATION_FONT_SIZE,
                    fontsize=font_size,
                    color=ANNOTATION_TEXT_COLOR,
                    # bbox=dict(
                    #     facecolor=ANNOTATION_BOX_FACE_COLOR,
                    #     edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                    #     boxstyle=ANNOTATION_BOX_STYLE,
                    # ),
                )
                self.canvas.draw_idle()

        # after moving the line , to adjust the line
        if self.is_dragging_endpoint and self.selected_line and event.inaxes:
            # Get the line data and convert to lists
            xdata, ydata = self.selected_line.get_data()
            xdata, ydata = list(xdata), list(ydata)
            # Update the selected endpoint's position
            if self.selected_endpoint == "start":
                xdata[0], ydata[0] = event.xdata, event.ydata
            else:  # 'end'
                xdata[-1], ydata[-1] = event.xdata, event.ydata
            # Set the modified line data back to the line
            self.selected_line.set_data(xdata, ydata)
            if self.selected_annotation:
                # new_distance = self.calculate_distance_str(xdata[0], ydata[0], xdata[-1], ydata[-1])
                new_distance = self.calculate_distance(
                    xdata[0], ydata[0], xdata[-1], ydata[-1]
                )
                # Update the annotation text with the new distance
                self.selected_annotation.set_text(new_distance)
                # print("self.movwed annotatation",self.moved_annot)
                if self.moved_annot[self.selected_line]==True:
                    self.update_line_in_storage(self.selected_line)
                    # If moved, don't update the position with the endpoint
                    return
                else:
                    if self.selected_endpoint == "start":
                        # Update the position using the start of the line
                        self.selected_annotation.set_position(
                            (xdata[0] + 8, ydata[0] + 3)
                        )
                        self.update_line_in_storage(self.selected_line, self.selected_annotation)
                    elif self.selected_endpoint == "end":
                        self.selected_annotation.set_position(
                            (xdata[-1] + 8, ydata[-1] + 3)
                        )
                        self.update_line_in_storage(self.selected_line, self.selected_annotation)
            
        
            self.canvas.draw_idle()

    def mouseReleaseEvent(self, event):
        self.imageIndex = self.getimageIndex()
        sMeasurementToggle = self.getMeasurementToggle()
        self.canvasIndex = self.getCanvaIndex()


        # if self.lineButtonActivated:
        if self.dragging_item and event.button == 1:
            if self.dragging_item == "annotation":
                self.moved_annotations.add(self.selected_annotation)
            self.selected_line = None
            self.selected_annotation = None
            self.annotation_offset = (0, 0)  # Reset to default value
            self.line_offset = None
            self.dragging_item = None

        if event.button == 1 and event.inaxes and self.drawing:
            # Remove the dragging annotation if it's an annotation object
            if isinstance(self.dragging_annotation, matplotlib.text.Text):
                self.dragging_annotation.remove()
                self.dragging_annotation = None
            self.xdata.append(event.xdata)
            self.ydata.append(event.ydata)
            self.draw_lines(eventType="release", showMeasurement=sMeasurementToggle)
            self.drawing = False
            self.xdata = []
            self.ydata = []
            self.current_lines.append([self.current_line,self.imageIndex,self.canvasIndex])
            self.uid=uuid.uuid4() # 4     
            conn = self.dbConnection()
            cur = conn.cursor()
            query = "SELECT EXISTS(SELECT 1 FROM arrowData WHERE uuid = ?)"
            # Execute the query, replacing '?' with the new_uuid
            cur.execute(query, (str(self.uid),))
            exists = cur.fetchone()[0] 
            # self.text_id+=1
            if self.uid == exists:
                self.uid = uuid.uuid4()
            else :
                pass
            # print("current_line1", self.current_line)
            if self.current_line is not None:
                self.lineStorage(self.current_line, self.text_annotation)

                self.line_id+=1
            self.canvas.restore_region(self.background)
            try:
                self.ax.draw_artist(self.current_line)
            except Exception as ex:
                pass
            self.canvas.blit(self.ax.bbox)

            # Update the last drawn line and annotation
            self.last_drawn_line = self.current_line
            self.last_drawn_annotation = self.text_annotation
            # Finalize the current line
            self.current_line = (
                None  # Reset current_line to allow for new lines to be drawn
            )
            self.last_drawn_line = None
            self.last_drawn_annotation = None
            # self.canvas.draw_idle()

        if self.is_dragging_endpoint and event.button == 1:  # Left mouse button
            # Reset the annotation moved state if it exists
            # if self.selected_annotation in self.annotation_moved_first:
            #     self.annotation_moved_first[self.selected_annotation] = False
            if self.selected_line:
                # Calculate the distance after moving the endpoint
                xdata, ydata = self.selected_line.get_data()
                distance = self.calculate_distance(
                    xdata[0], ydata[0], xdata[-1], ydata[-1]
                )
                # If the distance is "0.00 mm", remove the line and its annotation
                if distance == "0.00 mm":
                    self.remove_line_and_annotation(self.selected_line)
                self.selected_endpoint = None
                self.selected_line = None
                self.canvas.draw_idle()
            self.is_dragging_endpoint = False
            self.selected_endpoint = None
            self.selected_line = None
            self.canvas.draw()

    # -----------------------------------------------------------------------

    def remove_line_and_annotation(self, line):
        for linelist in self.current_lines:
            if linelist[0] == line:
                self.current_lines.remove(linelist[0])
                break
        linelist[0].remove()
        if line in self.line_text_dict:
            annotation = self.line_text_dict[line]
            annotation[0].remove()
            del self.line_text_dict[line]
        self.canvas.draw_idle()

    # Add helper methods to determine if the cursor is near an endpoint
    def is_near_endpoint(self, x, y, line, threshold=3):
        xdata, ydata = line.get_data()
        start_dist = math.hypot(x - xdata[0], y - ydata[0])
        end_dist = math.hypot(x - xdata[-1], y - ydata[-1])
        return start_dist < threshold or end_dist < threshold

    def is_near_start(self, x, y, line, threshold=3):
        xdata, ydata = line.get_data()
        return math.hypot(x - xdata[0], y - ydata[0]) < threshold

    def update_hover(self, event):
        # self.isLineHover = False
        # print("true")
        threshold_distance = 3.0
        for line in self.ax.get_lines():
            line.set_color(LINE_COLOR)
            line.set_markeredgecolor(MARKER_COLOR)

        hovered_annotation = None
        hovered_line = None
        hovered_over_line = False

        for line in self.current_lines:
            line=line[0]
            if (
                self.ax is not None
                and line in self.ax.get_lines()
                and line.contains(event)[0]
            ):
                line.set_color(HOVER_LINE_COLOR)
                hovered_line = line
                hovered_over_line = True
                # self.isLineHover = not self.isLineHover

                # Check if the cursor is close to any line endpoints
                # Add a check to ensure line is not None
                if line is not None and line.contains(event)[0]:
                    points = line.get_data()
                    last_x, last_y = points[0][-1], points[1][-1]
                    first_x, first_y = points[0][0], points[1][0]
                    cursor_x, cursor_y = event.xdata, event.ydata
                    if cursor_x is not None and cursor_y is not None:
                        last_distance = (
                            (cursor_x - last_x) ** 2 + (cursor_y - last_y) ** 2
                        ) ** 0.25
                        first_distance = (
                            (cursor_x - first_x) ** 2 + (cursor_y - first_y) ** 2
                        ) ** 0.25
                        if (
                            last_distance < threshold_distance
                            or first_distance < threshold_distance
                        ):
                            line.set_color(LINE_COLOR)
                            line.set_markeredgecolor(HOVERED_MARKER_LINE_COLOR)
                            hovered_line = line
                            hovered_over_line = True

        for line, annotation in self.line_text_dict.items():
            # print("lllllololl",annotation)
            annotation=annotation[0]
            if annotation is not None:
                if annotation.figure is not None:
                    in_text_bbox = annotation.get_window_extent().contains(event.x, event.y)
                    if in_text_bbox and line is not None:
                        line.set_color(HOVER_LINE_COLOR)
                        hovered_annotation = annotation
                        self.canvas.draw()
            if line == hovered_line:
                if annotation is not None:
                    annotation.set_color(HOVER_ANNOTATION_TEXT_COLOR)
                    # annotation.set_bbox(
                    #     dict(facecolor=HOVER_ANNOTATION_BOX_FACE_COLOR, edgecolor=HOVER_ANNOTATION_BOX_EDGE_COLOR, boxstyle=ANNOTATION_BOX_STYLE)
                    # )
            elif hovered_annotation == annotation:
                if annotation is not None:
                    annotation.set_color(HOVER_ANNOTATION_TEXT_COLOR)
                    # annotation.set_bbox(
                    #     dict(facecolor=HOVER_ANNOTATION_BACKGROUND_COLOR, edgecolor=HOVER_ANNOTATION_BOX_EDGE_COLOR, boxstyle=ANNOTATION_BOX_STYLE)
                    # )
            else:
                if annotation is not None:
                    annotation.set_color(ANNOTATION_TEXT_COLOR)
                    # annotation.set_bbox(
                    #     dict(facecolor=ANNOTATION_BOX_FACE_COLOR, edgecolor=ANNOTATION_BOX_EDGE_COLOR, boxstyle=ANNOTATION_BOX_STYLE)
                    # )

        # self.canvas.mpl_connect("button_press_event", self.mousePressEvent)
        # self.canvas.mpl_connect("motion_notify_event", self.update_hover)
        # self.canvas.mpl_connect("motion_notify_event", self.mouseMoveEvent)
        # self.canvas.mpl_connect("button_release_event", self.mouseReleaseEvent)
        # self.canvas.mpl_connect("key_press_event", self.keyPressEvent)

        self.canvas.draw_idle()

    def draw_lines(self, eventType, showMeasurement):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()

        # Only update the current line data instead of removing and redrawing it
        if eventType == "move":
            # Update the line data
            if self.current_line is not None:
                # print("old lineeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
                self.current_line.set_data(
                    [self.xdata[0], self.xdata[-1]], [self.ydata[0], self.ydata[-1]]
                )
            else:
                # print("newwww lineeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
                # If there's no current line, create one
                self.current_line = Line2D(
                    [self.xdata[0], self.xdata[-1]],
                    [self.ydata[0], self.ydata[-1]],
                    linestyle="-",
                    marker="+",
                    markersize=MARKER_SIZE,
                    markeredgecolor="r",
                    linewidth=LINE_WIDTH,
                    color=LINE_COLOR,
                )
                self.ax.add_line(self.current_line)
                # print(self.current_line)
                
        elif eventType == "release":
            # Finalize the line and add a measurement annotation
            if  self.current_line is not None:
                # distance = self.distance_measure()
                distance = self.calculate_distance(
                    self.xdata[0], self.ydata[0], self.xdata[-1], self.ydata[-1]
                )
                if distance != "0.00 mm" :
                    font_size = self.calculate_font_size(self.ax)
                    if showMeasurement:
                        self.text_annotation = self.ax.text(
                            self.xdata[-1] + 8,
                            self.ydata[-1] + 3,
                            distance,
                            # fontsize=ANNOTATION_FONT_SIZE,
                            fontsize=font_size,
                            color=ANNOTATION_TEXT_COLOR,
                            # bbox=dict(
                            #     facecolor=ANNOTATION_BOX_FACE_COLOR,
                            #     edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                            #     boxstyle=ANNOTATION_BOX_STYLE,
                            # ),
                        )
                        self.line_text_dict[self.current_line] = [self.text_annotation,self.imageIndex,self.canvasIndex]
                    else:
                        self.text_annotation=None
                        self.line_text_dict[self.current_line] = [None,self.imageIndex,self.canvasIndex]
                else:
                    # If the distance is "0.00 mm", remove the current line and reset the drawing state
                    if self.current_line in self.ax.lines:
                        self.current_line.remove()  # Call remove on the artist, not on the list
                    self.current_line = None
                    self.drawing = False
                self.moved_annot[self.current_line]=False   
                # print("new insert moved annot ",self.moved_annot)
        self.canvas.restore_region(self.background)
        # self.ax.draw_artist(self.current_line)
        # self.canvas.blit(self.ax.bbox)
        self.canvas.draw_idle()

    def calculate_distance(self, x1, y1, x2, y2):
        temp_x = x2 - x1
        temp_y = y2 - y1
        distance = math.sqrt((temp_x * self.px) ** 2 + (temp_y * self.py) ** 2)
        if distance < 10.0:
            return "{:.2f} mm".format(distance)
        else:
            distance_cm = distance / 10
            return "{:.2f} cm".format(distance_cm)

    def creatingOriginalDict(self,line_info):
        if self.patientID not in self.lineStorageDictOriginal:
            self.lineStorageDictOriginal[self.patientID] = {}
        if self.patientSeriesName not in self.lineStorageDictOriginal[self.patientID]:
            self.lineStorageDictOriginal[self.patientID][self.patientSeriesName] = {}
        if self.canvasIndex not in self.lineStorageDictOriginal[self.patientID][self.patientSeriesName]:
            self.lineStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
        if self.imageIndex not in self.lineStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.lineStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []
        #Store line details and measurement text
        self.lineStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(line_info)

    def lineStorage(self,current_line, text_annotation , uid=None ):
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.canvasIndex = self.getCanvaIndex()
        # print("currrrrrrrrreeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeent lineeeeeeeeeeee",current_line)
        # print("current line 2",current_line)
        if uid is None:
            line_info={
                "id": self.line_id,
                "line": current_line,
                "annotation": text_annotation,
                "uuid":self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }
        else:
            line_info={
                "id": self.line_id,
                "line": current_line,
                "annotation": text_annotation,
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex


            }
        if uid is None:
            line_info_original={
                "id": self.line_id,
                "line": current_line,
                "annotation": text_annotation,
                "uuid":self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }
        else:
            line_info_original={
                "id": self.line_id,
                "line": current_line,
                "annotation": text_annotation,
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex


            }    

        if self.patientID not in self.lineStorageDict:
            self.lineStorageDict[self.patientID] = {}
        if self.patientSeriesName not in self.lineStorageDict[self.patientID]:
            self.lineStorageDict[self.patientID][self.patientSeriesName] = {}
        if self.canvasIndex not in self.lineStorageDict[self.patientID][self.patientSeriesName]:
            self.lineStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
        if self.imageIndex not in self.lineStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.lineStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []
        #Store line details and measurement text
        self.lineStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(line_info)
        
        self.creatingOriginalDict(line_info_original)

    def giveLineStorageDict(self):
        return self.lineStorageDict
    def giveLineStorageDictOriginal(self):
        return self.lineStorageDictOriginal
    def getPatientID(self):
        return self.mainWindow.givepatientId()
    def getPatientSeriesName(self):
        return self.mainWindow.givePatientSeriesName()
    def getimageIndex(self):
        return self.mainWindow.giveImageIndex()
    
    def getAxes(self):
        return self.mainWindow.giveAxes()   
    def getCanvas(self):
        return self.mainWindow.giveCanvas()
    def getLineActivation(self):
        return self.mainWindow.giveLineActivation()
    
    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()  
    def calculate_font_size(self, ax):
       
        bbox = ax.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        height = bbox.height * self.figure.dpi  # Convert height to pixels
        # Adjust font size based on the height of the axes
        return max(6, min(12, height * 0.02)) 
    def update_annotation_font_sizes(self):
        
        for ax in self.figure.axes:
            font_size = self.calculate_font_size(ax)
            for text in ax.texts:
                text.set_fontsize(font_size)
        self.canvas.draw_idle()