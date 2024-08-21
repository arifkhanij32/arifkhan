
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
import uuid
from .constants import *
import sqlite3
import uuid
import copy


class AngleMeasureApp(FigureCanvas):
    def __init__(
        self,
        angleButtonActivated,
        imgDCM,
        processedDCM,
        canvas,
        ax,
        figure,
        parent,
        width=5,
        height=4,
        dpi=100,
       
    ):
        # super().__init__()
        # # Create a Matplotlib figure and canvas
        # self.figure, self.ax = plt.subplots()
        # self.canvas = FigureCanvas(self.figure)
        # self.canvas.mpl_connect("button_press_event", self.mousePressEvent)
        # self.canvas.mpl_connect("motion_notify_event", self.mouseMoveEvent)
        # self.canvas.mpl_connect("button_release_event", self.mouseReleaseEvent)
        # self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        # self.setFocusPolicy(Qt.StrongFocus)
        # self.setWindowTitle("Angle Measure")
        # self.setGeometry(100, 100, 800, 600)

        # central_widget = QWidget()
        # layout = QVBoxLayout(central_widget)
        # layout.addWidget(self.canvas)
        # self.setCentralWidget(central_widget)

        self.angleButtonActivated = angleButtonActivated
        self.dicom_image = imgDCM
        self.mainWindow = parent
        # ##print(f"dicom image {self.dicom_image}")
        self.py, self.px = self.dicom_image.PixelSpacing
        self.pixel_data = self.dicom_image.pixel_array
        self.processedDCM = processedDCM
        self.canvas = canvas

        width = width
        height = height
        dpi = dpi

        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = ax

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        self.angle_data = {}
        self.drawing = False
        self.xdata = []
        self.ydata = []
        self.points = []
        self.current_line = []
        self.text_annotation = None
        self.start_line = False
        self.angle_lines = {}
        self.angle_markers = {}  # Stores lines for each angle
        self.angle_annotations = {}  # Stores annotations for each angle
        self.current_angle_id = 1.0
        self.set_marker = None
        self.selected_angle_id = None
        self.start_dragging = False
        self.annotation_position = None
        self.dragging_annotation = None
        self.dragging_annotation_offset = (0, 0)
        self.independent_annotation_positions = {}
        self.angleStorageDict = {}
        self.angleStorageDictOriginal={}
        self.delDbList=[]



        self.dragging_marker = False
        self.dragging_marker_angle_id = None
        self.dragging_marker_index = None

        self.is_dragging = False  # New flag to track dragging state
        self.canvasIndex = self.getCanvaIndex()
        self.setupEventConnections()

    def setupEventConnections(self):
        try:
            # Connect key press event
            self.canvas.mpl_connect("key_press_event", self.keyPressEvent)
        except:
            pass
    #######################################################
    def dbConnection(self):
        mydb = sqlite3.connect("mainApplication.db")
        return mydb

    def on_hover(self, event):

        self.set_marker = False
        if event.xdata is not None and event.ydata is not None:
            hovered_angle_id = None
            hovered_marker = None
            for angle_id, markers in self.angle_markers.items():
                hovered_marker = self.is_cursor_near_marker(event, markers[0])
                if hovered_marker is not None:
                    hovered_angle_id = angle_id
                    self.set_marker = True
                    break

            for angle_id, annotation in self.angle_annotations.items():
                if self.is_cursor_near_annotation(event, annotation[0]):
                    hovered_angle_id = angle_id
                    break

            for angle_id, lines in self.angle_lines.items():
                line1, line2 = lines[0]
                if self.set_marker != True:  # Unpack the tuple of lines
                    if self.is_cursor_near_line(
                        event, line1
                    ) or self.is_cursor_near_line(event, line2):
                        hovered_angle_id = angle_id
                        break

            for angle_id in self.angle_lines.keys():
                if angle_id == hovered_angle_id:
                    self.highlight_angle(angle_id)
                else:
                    self.reset_angle_highlight(angle_id)

            self.canvas.mpl_connect("button_press_event", self.mousePressEvent)
            self.canvas.mpl_connect("motion_notify_event", self.mouseMoveEvent)
            # # self.canvas.mpl_connect(
            # #                 "motion_notify_event", self.mouseReleaseEvent
            # #             )
            self.canvas.draw_idle()

    def is_cursor_near_marker(self, event, marker_positions, marker_threshold=5):
        if event.xdata is None or event.ydata is None:
            return None
        inv = self.ax.transData.inverted()
        mouse_point = np.array(inv.transform((event.x, event.y)))
        # First check for the middle marker which is the intersection of the lines
        intersection_x = marker_positions[0][0][-1]  # End of the first line's x
        intersection_y = marker_positions[0][1][-1]  # End of the first line's y
        intersection_point = np.array([intersection_x, intersection_y])

        # Check if the mouse is near the intersection point
        if np.linalg.norm(mouse_point - intersection_point) < marker_threshold:
            return (
                "middle",
                0,
            )  # Return 'middle' type with line index 0, assuming this is where intersection is

        # Now check start and end markers of the lines
        for i, (x_positions, y_positions) in enumerate(marker_positions):
            for j, (x, y) in enumerate(zip(x_positions, y_positions)):
                # Skip the last point of the first line and first point of the second line
                # because that's our intersection point (middle marker) handled above
                if i == 0 and j == len(x_positions) - 1 or i == 1 and j == 0:
                    continue
                marker_type = "start" if j == 0 else "end"
                marker_point = np.array([x, y])
                distance = np.linalg.norm(mouse_point - marker_point)
                if distance < marker_threshold:
                    return marker_type, i
        return None

    def is_cursor_near_annotation(self, event, annotation, threshold=5):
        bbox = annotation.get_window_extent(self.canvas.renderer)
        if bbox.contains(event.x, event.y) and bbox is not None:
            return True
        else:
            return False

    def is_cursor_near_line(self, event, line, threshold=5):
        if event.xdata is None or event.ydata is None:
            return False
        mouse_point = np.array([event.xdata, event.ydata])
        xdata, ydata = line.get_data()
        line_points = np.column_stack((xdata, ydata))

        for i in range(len(line_points) - 1):
            p1 = line_points[i]
            p2 = line_points[i + 1]
            closest_point = self.closest_point_on_segment(p1, p2, mouse_point)
            distance = np.linalg.norm(mouse_point - closest_point)
            if distance < threshold:
                return True
        return False

    def closest_point_on_segment(self, p1, p2, p3):
        line_vec = p2 - p1
        point_vec = p3 - p1
        line_len = np.linalg.norm(line_vec)
        line_unitvec = line_vec / line_len
        point_vec_scaled = point_vec / line_len
        t = np.dot(line_unitvec, point_vec_scaled)
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        nearest = line_vec * t
        closest_point = p1 + nearest
        return closest_point

    def highlight_angle(self, angle_id):
        if angle_id != self.selected_angle_id:
            lines = self.angle_lines.get(angle_id)
            annotation = self.angle_annotations.get(angle_id)
            if lines:
                line1, line2 = lines[0]
                line1.set_color(HIGHLIGHT_LINE_COLOUR)
                line2.set_color(HIGHLIGHT_LINE_COLOUR)
                if self.set_marker == True:
                    line1.set_markeredgecolor(HIGHLIGHT_LINE_COLOUR)
                    line2.set_markeredgecolor(HIGHLIGHT_LINE_COLOUR)
                    line1.set_color(RESET_LINE_COLOUR)
                    line2.set_color(RESET_LINE_COLOUR)
            if annotation:
                # annotation.set_bbox(
                #     dict(
                        # facecolor=HOVER_ANNOTATION_BACKGROUND_COLOR,
                        # alpha=0.5,
                        # edgecolor=HOVER_ANNOTATION_BOX_EDGE_COLOR,
                        # boxstyle=ANNOTATION_BOX_STYLE,
                        annotation[0].set_color(HOVER_ANNOTATION_TEXT_COLOR)
                #     )
                # )

    def reset_angle_highlight(self, angle_id):
        if angle_id != self.selected_angle_id:
            lines = self.angle_lines.get(angle_id)
            annotation = self.angle_annotations.get(angle_id)
            if lines:
                line1, line2 = lines[0]
                line1.set_color(RESET_LINE_COLOUR)
                line2.set_color(RESET_LINE_COLOUR)
                line1.set_markeredgecolor(RESET_MARKER_EDGE_COLOR)
                line2.set_markeredgecolor(RESET_MARKER_EDGE_COLOR)
            if annotation:
                # annotation.set_bbox(
                #     dict(
                #         # facecolor=ANNOTATION_BOX_FACE_COLOR,
                        # alpha=0.5,
                        # edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                        # boxstyle=ANNOTATION_BOX_STYLE,
                        annotation[0].set_color(ANNOTATION_TEXT_COLOR),
                #     )
                # )

    def live_update_angle(self, p1, p2, current_point, angle_id):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex=self.getCanvaIndex()
        vector1 = np.array(p1) - np.array(p2)
        vector2 = np.array(current_point) - np.array(p2)
        try:
            angle_rad = np.arccos(
                np.dot(vector1, vector2)
                / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
            )
            angle_deg = np.degrees(angle_rad)
        except RuntimeWarning:
            angle_deg = np.nan
        angle_txt = str(round(angle_deg, 2)) + "°"
        annotation_position = (p2[0] + 9, p2[1] + 3)
        font_size = self.calculate_font_size()  # Dynamically calculate the font size
        if angle_id in self.angle_annotations:
            annotation=self.angle_annotations[angle_id]
            annotation[0].set_position(annotation_position)
            annotation[0].set_text(angle_txt)
            annotation[0].set_fontsize(font_size)#dynamic font

        else:
            updannotation = self.ax.text(
                annotation_position[0] + 9,
                annotation_position[1] + 3,
                angle_txt,
                color=ANNOTATION_TEXT_COLOR,
                # fontsize=ANNOTATION_FONT_SIZE,
                fontsize=font_size,
                # bbox=dict(
                #     facecolor=ANNOTATION_BOX_FACE_COLOR,
                #     alpha=0.5,
                #     edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                #     boxstyle=ANNOTATION_BOX_STYLE,
                # ),
            )
            annotation=[updannotation,self.imageIndex,self.canvasIndex]
            self.text_annotation = annotation[0]
            self.angle_annotations[angle_id] = annotation

        self.canvas.draw_idle()

    def highlight_selected_angle(self, angle_id):
        lines = self.angle_lines.get(angle_id)
        annotation = self.angle_annotations.get(angle_id)
        marker = self.angle_markers.get(angle_id)
        if lines:
            line1, line2 = lines[0]
            line1.set_color(HIGHLIGHT_LINE_COLOUR1)
            line2.set_color(HIGHLIGHT_LINE_COLOUR1)
            line1.set_markeredgecolor(HIGHLIGHT_MARKER_EDGE_COLOR)
            line2.set_markeredgecolor(HIGHLIGHT_MARKER_EDGE_COLOR)
        if annotation:
            # annotation.set_bbox(
            #     dict(
                    # facecolor=HOVER_ANNOTATION_BACKGROUND_COLOR,
                    # alpha=0.5,
                    # edgecolor=HOVER_ANNOTATION_BOX_EDGE_COLOR,
                    # boxstyle=ANNOTATION_BOX_STYLE,
                    annotation[0].set_color(SELECTION_ANNOTATION_TEXT_COLOR)
            #     )
            # )
        self.canvas.draw_idle()

    def reset_selected_angle_highlight(self, angle_id):
        lines = self.angle_lines.get(angle_id)
        annotation = self.angle_annotations.get(angle_id)
        if lines:
            line1, line2 = lines[0]
            line1.set_color(RESET_LINE_COLOUR)
            line2.set_color(RESET_LINE_COLOUR)
            line1.set_markeredgecolor(HIGHLIGHT_LINE_COLOUR1)
            line2.set_markeredgecolor(HIGHLIGHT_LINE_COLOUR1)
        if annotation:
            # annotation.set_bbox(
            #     dict(
            #         # facecolor=ANNOTATION_BOX_FACE_COLOR,
                    # alpha=0.5,
                    # edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                    # boxstyle=ANNOTATION_BOX_STYLE,
                    annotation[0].set_color(ANNOTATION_TEXT_COLOR)
            #     )
            # )
        self.canvas.draw_idle()

    def keyPressEvent(self, event):
        if type(event.key) == str:
            if event.key.lower().strip() == "delete".lower().strip():
                event.key = 16777223
        else:
            pass
        if str(event.key) == str(Qt.Key_Delete):
            if self.selected_angle_id:
                self.remove_selected_angle_id()
                

    def remove_selected_angle_id(self):
        self.canvasIndex = self.getCanvaIndex()
        if self.selected_angle_id is not None:
            if self.selected_angle_id in self.angle_lines:
                lines = self.angle_lines[self.selected_angle_id]
                for line in lines[0]:
                    if line in self.ax.lines:
                        line.remove()
                del self.angle_lines[self.selected_angle_id]

            if self.selected_angle_id in self.angle_markers:
                del self.angle_markers[self.selected_angle_id]

            if self.selected_angle_id in self.angle_annotations:
                annotation = self.angle_annotations[self.selected_angle_id]
                annotation[0].remove()
                del self.angle_annotations[self.selected_angle_id]

            # # Reset selected angle ID and redraw the canvas
            # self.selected_angle_id = None
            # self.canvas.draw_idle()
            # if self.selected_angle_id in self.angle_annotations:
            #     annotation = self.angle_annotations.pop(self.selected_angle_id)
            #     annotation.remove()

            # Update the angle storage dictionary
            patient_series_data = self.angleStorageDict.get(self.patientID, {}).get(self.patientSeriesName, {}).get(self.canvasIndex, {}).get(self.imageIndex, [])
            updated_angles = [angle for angle in patient_series_data if angle["id"] != self.selected_angle_id]
            for angle in patient_series_data :
                if angle["id"] == self.selected_angle_id:
                    uid=angle["uuid"] 
                    self.delDbList.append(uid)

            self.angleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = updated_angles

            self.canvas.draw_idle()
            self.selected_angle_id = None

    def mousePressEvent(self, event):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()
        self.ax=self.getAxes()
        self.canvas=self.getCanvas()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.angleButtonActivated=self.getAngleActivation()

        if self.angleButtonActivated:
            
            
            if event.button == Qt.LeftButton:
                # self.has_moved = False  # Reset the flag on a new mouse press
                # Set the dragging flag to True only if there's an existing point to start from
                # if len(self.points) == 1:
                #     self.is_dragging = True
                if self.selected_angle_id is not None:
                    self.reset_selected_angle_highlight(self.selected_angle_id)
                    self.selected_angle_id = None
                for angle_id, lines in self.angle_lines.items():
                    
                    if lines[1] != self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue 
                   
                    if lines[2] != self.canvasIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue

                    line1, line2 = lines[0]
                    if self.set_marker != True:
                        if (
                            self.is_cursor_near_line(event, line1)
                            or self.is_cursor_near_line(event, line2)
                            and self.set_marker != True
                        ):
                            # ##print("is near line")
                            self.selected_angle_id = angle_id
                            self.start_dragging = True
                            self.original_mouse_position = (event.xdata, event.ydata)
                            # ##print("selected ",self.selected_angle_id)
                            self.highlight_selected_angle(angle_id)
                            return
                
                for angle_id, annotation in self.angle_annotations.items():
                    if annotation[1] != self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue 
                    try:
                        if annotation[2] != self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                    except:
                        pass
                    if self.is_cursor_near_annotation(event, annotation[0]):
                        self.selected_angle_id = angle_id
                        self.dragging_annotation = annotation[0]
                        ax_pos = self.ax.transData.transform((annotation[0].get_position()))
                        self.dragging_annotation_offset = (
                            ax_pos[0] - event.x,
                            ax_pos[1] - event.y,
                        )
                        self.highlight_selected_angle(angle_id)
                        return

                # Check if the click is near any existing angle markers
                for angle_id, markers in self.angle_markers.items():
                    if  markers[1]!= self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue 
                    try:
                        if  markers[2]!= self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                    except:
                        pass
                    marker_info = self.is_cursor_near_marker(event, markers[0])
                    if marker_info is not None:
                        marker_type, marker_index = marker_info
                        # #print("marker_type, marker_index:",marker_type, marker_index)
                        # If a middle marker is clicked, set up for dragging
                        if marker_type == "middle":
                            self.dragging_marker = True
                            self.dragging_marker_angle_id = angle_id
                            self.dragging_marker_index = (marker_type, marker_index)
                            self.highlight_selected_angle(angle_id)
                            return  # Exit since we found a marker to drag
                        if marker_type == "end" or marker_type == "start":
                            # #print("angle_id, markers:",angle_id, markers)
                            # ##print(list(markers))
                            marker_index = self.is_cursor_near_marker(event, markers[0])
                            # ##print("marker hovered")
                            # #print("index",marker_index)
                            if marker_index is not None:
                                self.dragging_marker = True
                                self.dragging_marker_angle_id = angle_id
                                self.dragging_marker_index = marker_index
                                # ##print(marker_index)
                                self.set_marker = True
                                return

                x, y = int(event.xdata), int(event.ydata)  # to draw new line

                if self.drawing and len(self.points) == 2:
                    self.drawing = False
                    self.xdata.append(x)
                    self.ydata.append(y)
                    self.draw_lines(eventType="press")
                    self.points.append((self.xdata[-1], self.ydata[-1]))
                    last_Angle_Key=list(self.angle_lines.keys())[-1]
                    last_angle= self.angle_lines[last_Angle_Key]
                    last_key = list(self.angle_annotations.keys())[-1]  # Get the last key added to the dictionary
                    last_annotation = self.angle_annotations[last_key] 
                    last_Marker_key=list(self.angle_markers.keys())[-1]
                    last_marker = self.angle_markers[last_Marker_key] 
                    

                    self.uid=uuid.uuid4() # 4     
                    conn = self.dbConnection()
                    cur = conn.cursor()
                    query = "SELECT EXISTS(SELECT 1 FROM angleData WHERE uuid = ?)"
                    # Execute the query, replacing '?' with the new_uuid
                    cur.execute(query, (str(self.uid),))
                    exists = cur.fetchone()[0] 
                    # self.text_id+=1
                    if self.uid == exists:
                        self.uid = uuid.uuid4()
                    else :
                        pass

                    self.angleStorage(last_angle[0],last_annotation[0],last_marker[0])
                    self.current_angle_id += 1.0
                    self.points = []
                    self.xdata = []
                    self.ydata = []

                else:
                    self.temp_line = None
                    self.drawing = True
                    self.xdata = [x]
                    self.ydata = [y]
                    self.points = [(x, y)]

                    self.start_line = True

    def mouseMoveEvent(self, event):
        self.has_moved = True
        self.canvasIndex = self.getCanvaIndex()

        if self.drawing and self.start_line:
            # Set the flag when the mouse is moved
            x, y = int(event.xdata), int(event.ydata)
            self.xdata.append(x)
            self.ydata.append(y)
            self.draw_lines(eventType="move")
            
            if len(self.points) == 2:
                self.live_update_angle(
                    self.points[0],
                    (self.xdata[0], self.ydata[0]),
                    (x, y),
                    self.current_angle_id,
                )

        if (
            self.start_dragging
            and self.selected_angle_id is not None
            and self.set_marker != True
        ):
            dx = event.xdata - self.original_mouse_position[0]
            dy = event.ydata - self.original_mouse_position[1]
            self.move_angle(self.selected_angle_id, dx, dy)
            self.original_mouse_position = (event.xdata, event.ydata)

        if self.dragging_annotation:
            new_x = event.x + self.dragging_annotation_offset[0]
            new_y = event.y + self.dragging_annotation_offset[1]
            new_pos = self.ax.transData.inverted().transform((new_x, new_y))
            new_pos_int = (int(new_pos[0]), int(new_pos[1]))
            self.dragging_annotation.set_position(new_pos_int)

            # Update the independent position
            for angle_id, annotation in self.angle_annotations.items():
                if annotation[0] is self.dragging_annotation:
                    self.independent_annotation_positions[angle_id] = new_pos_int
                    try:
                        patient_series_data = self.angleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex]
                        for angle_info in patient_series_data:
                            if angle_info['id'] == angle_id:
                                # Assuming the structure contains 'annotation' with 'position'
                                angle_info['annotation']['position'] = new_pos_int
                                break
                    except KeyError:
                        pass
                        # Handle the case where identifiers might not directly match
                    break
            self.canvas.draw_idle()

        if self.dragging_marker and self.set_marker == True:
            new_x, new_y = int(event.xdata), int(event.ydata)

            # Get the angle ID and marker index
            angle_id = self.dragging_marker_angle_id
            # marker_index = self.dragging_marker_index
            marker_type, marker_index = self.dragging_marker_index

            # Get the lines and markers for the selected angle
            lines = self.angle_lines[angle_id]
            markers = self.angle_markers[angle_id]
            
            # Update the position of the selected marker
            x_positions, y_positions = markers[0][marker_index]
            # if marker_index == 0:  # If the first marker (start point) of the line is
            # selected
            intersection_x = markers[0][0][0][-1]  # x_end_line_1
            intersection_y = markers[0][0][1][-1]  # y_end_line_1
            self.annotation_position = (intersection_x + 9, intersection_y + 3)

            if marker_type == "start":
                x_positions[0], y_positions[0] = new_x, new_y
                line = lines[0][marker_index]
                line.set_xdata(x_positions)
                line.set_ydata(y_positions)

            else:  # If the second marker (end point) of the line is selected
                x_positions[-1], y_positions[-1] = new_x, new_y
                line = lines[0][marker_index]
                line.set_xdata(x_positions)
                line.set_ydata(y_positions)

            if marker_type == "middle":
                # Move both lines connected to the middle marker
                lines = self.angle_lines[self.dragging_marker_angle_id]
                markers = self.angle_markers[self.dragging_marker_angle_id]

                # Adjust the first line's end and the second line's start
                x_positions1, y_positions1 = markers[0][0]
                x_positions1[-1], y_positions1[-1] = new_x, new_y
                x_positions2, y_positions2 = markers[0][1]
                x_positions2[0], y_positions2[0] = new_x, new_y

                # Update the lines with the new positions
                lines[0][0].set_xdata(x_positions1)
                lines[0][0].set_ydata(y_positions1)
                lines[0][1].set_xdata(x_positions2)
                lines[0][1].set_ydata(y_positions2)

                # End point of the second line

                # Calculate the average position for the annotation
                self.annotation_position = x_positions1[-1] + 8, y_positions1[-1] + 3
                # Recalculate the angle with updated line positions
                self.recalculate_angle(
                    self.dragging_marker_angle_id, self.annotation_position
                )

                self.canvas.draw_idle()
                return

            # Recalculate and update the angle
            try:
                self.recalculate_angle(angle_id, self.annotation_position)
            except:
                pass
            self.canvas.draw_idle()

    def recalculate_angle(self, angle_id, position):
        self.canvasIndex = self.getCanvaIndex()

        if angle_id not in self.angle_lines:
            return  # Exit if the angle_id is not found

        lines = self.angle_lines[angle_id]
        line1, line2 = lines[0]  # Unpack the two lines

        # Extract the endpoints of the lines
        x1, y1 = line1.get_data()
        x2, y2 = line2.get_data()

        # Assuming p2 (end point of line1) is the intersection point
        p1 = np.array([x1[0], y1[0]])  # Start point of the first line
        p2 = np.array([x1[-1], y1[-1]])  # End point of the first line (shared point)
        p3 = np.array([x2[0], y2[0]])  # Start point of the second line
        p4 = np.array([x2[-1], y2[-1]])  # End point of the second line

        # Calculate the vectors
        vector1 = p1 - p2
        vector2 = p4 - p2

        # Calculate the angle
        angle_rad = np.arccos(
            np.dot(vector1, vector2)
            / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
        )
        angle_deg = np.degrees(angle_rad)

        # Update the annotation
        angle_txt = f"{angle_deg:.2f}°"
        if angle_id in self.angle_annotations:
            annotation = self.angle_annotations[angle_id]
            annotation[0].set_text(angle_txt)

        if angle_id in self.independent_annotation_positions:
            new_annotation_pos = self.independent_annotation_positions[angle_id]
        else:
            # Update annotation normally if no independent position
            annotation = self.angle_annotations[angle_id]
            annotation[0].set_position(position)
        # Redraw the canvas
        try:
            patient_series_data = self.angleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex]
            for angle_info in patient_series_data:
                if angle_info['id'] == angle_id:
                    # Update angle measurement
                    angle_info['annotation']['text'] = angle_txt
                    angle_info['anglelines']=[lines[0][0],lines[0][1]]
                    # Update position
                    angle_info['annotation']['position'] = position if not angle_id in self.independent_annotation_positions else new_annotation_pos
                    break
        except KeyError as e:
            pass

    # Redraw the canvas
        self.canvas.draw_idle()

    def move_angle(self, angle_id, dx, dy):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()

        lines = self.angle_lines[angle_id]
        line1 = lines[0][0]
        new_x1data = line1.get_xdata() + dx
        new_y1data = line1.get_ydata() + dy
        line1.set_data(new_x1data, new_y1data)

        line2 = lines[0][1]
        new_x2data = line2.get_xdata() + dx
        new_y2data = line2.get_ydata() + dy
        line2.set_data(new_x2data, new_y2data)
            

        # Update annotation
        if angle_id in self.independent_annotation_positions:
            new_annotation_pos = self.independent_annotation_positions[angle_id]
        else:
            # Update annotation normally if no independent position
            annotation = self.angle_annotations[angle_id]
            x, y = annotation[0].get_position()
            new_annotation_pos = (x + dx, y + dy)
            annotation[0].set_position(new_annotation_pos)

        # Update markers
        if angle_id in self.angle_markers:
            markers = self.angle_markers[angle_id]
            new_markers = []
            for x_positions, y_positions in markers[0]:
                new_x_positions = x_positions + dx
                new_y_positions = y_positions + dy
                new_markers.append((new_x_positions, new_y_positions))
            self.angle_markers[angle_id] = [new_markers,self.imageIndex,self.canvasIndex]
    
        patient_series_data = self.angleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex]
        for angle_info in patient_series_data:
            if angle_info['id'] == angle_id:
                # Update line positions in stored data (if stored)
                # Update annotation position
                angle_info['annotation']['position'] = new_annotation_pos
                angle_info['anglelines']=[line1,line2]
                # Update marker positions (if stored)
                new_marker_positions = []
                for x_positions, y_positions in angle_info['markerPositions']:
                    new_x_positions = x_positions + dx
                    new_y_positions = y_positions + dy
                    new_marker_positions.append((new_x_positions, new_y_positions))
                angle_info['markerPositions'] = new_marker_positions

                break
        # Handle the case where the angle_id or other identifiers do not match
        
        self.canvas.draw_idle()

    def mouseReleaseEvent(self, event):
        if self.has_moved:
            if event.button == Qt.LeftButton:
                if self.start_dragging and self.selected_angle_id is not None:
                    self.start_dragging = False
                    self.finalize_angle_position(
                        self.selected_angle_id, event.xdata, event.ydata
                    )

                if self.dragging_annotation:
                    self.dragging_annotation = None
                    self.dragging_annotation_offset = (0, 0)

                if self.dragging_marker:
                    self.dragging_marker = False
                    self.dragging_marker_angle_id = None
                    self.dragging_marker_index = None
                    self.set_marker = False

                if self.drawing:
                    x, y = int(event.xdata), int(event.ydata)
                    if len(self.points) == 1:
                        self.xdata.append(x)
                        self.ydata.append(y)
                        
                        self.draw_lines(eventType="release")
                        self.points.append((self.xdata[-1], self.ydata[-1]))
                        self.xdata = [self.xdata[-1]]
                        self.ydata = [self.ydata[-1]]
                    elif len(self.points) == 2:
                        self.drawing = False
                        self.points = []
                        self.xdata = []
                        self.ydata = []

            self.is_dragging = False
            self.has_moved = False

    def finalize_angle_position(self, angle_id, final_x, final_y):
        dx = final_x - self.original_mouse_position[0]
        dy = final_y - self.original_mouse_position[1]

        if angle_id in self.angle_lines:
            lines = self.angle_lines[angle_id]
            for line in lines[0]:
                xdata, ydata = line.get_data()
                line.set_data(xdata + dx, ydata + dy)

        if angle_id in self.angle_annotations:
            annotation = self.angle_annotations[angle_id]
            x, y = annotation[0].get_position()
            annotation[0].set_position((x + dx, y + dy))

        if angle_id in self.angle_markers:
            markers = self.angle_markers[angle_id]
            for i in range(len(markers[0])):
                x_positions, y_positions = markers[0][i]
                new_x_positions = [int(x + dx) for x in x_positions]
                new_y_positions = [int(y + dy) for y in y_positions]
                markers[0][i] = (new_x_positions, new_y_positions)

        self.canvas.draw_idle()

    def draw_lines(self, eventType):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()
        if self.selected_angle_id is not None:
            self.reset_angle_highlight(self.selected_angle_id)
            self.selected_angle_id = None

        if eventType == "move":
            if self.current_line and self.current_line in self.ax.lines:
                self.current_line.remove()
            x_final = [self.xdata[0], self.xdata[-1]]
            y_final = [self.ydata[0], self.ydata[-1]]
            self.current_line = Line2D(
                x_final,
                y_final,
                linestyle="-",
                linewidth=LINE_WIDTH,
                marker="+",
                markersize=MARKER_SIZE,
                markeredgecolor=MARKER_EDGE_COLOR,
                color=ANGLE_LINE_COLOR,
            )
            self.ax.add_line(self.current_line)

        elif eventType == "press":
            if self.current_line:
                self.current_line.remove()
            x_final = [self.xdata[0], self.xdata[-1]]
            y_final = [self.ydata[0], self.ydata[-1]]
            line2 = Line2D(
                x_final,
                y_final,
                linestyle="-",
                linewidth=LINE_WIDTH,
                marker="+",
                markersize=MARKER_SIZE,
                markeredgecolor="r",
                color=DRAW_LINE_PRESS,
            )
            self.ax.add_line(line2)
            self.line2_m_pos = (line2.get_xdata(), line2.get_ydata())
            self.angle_lines[self.current_angle_id] = [[self.temp_line, line2],self.imageIndex,self.canvasIndex]
            self.angle_markers[self.current_angle_id] = [[
                self.temp_marker,
                self.line2_m_pos,
            ],self.imageIndex,self.canvasIndex]
            
            
            """[    ([x_start_line_1, x_end_line_1], [y_start_line_1, y_end_line_1]),
    ([x_start_line_2, x_end_line_2], [y_start_line_2, y_end_line_2])
]"""
            # self.angle_annotations[self.current_angle_id] = [self.text_annotation,self.imageIndex,self.canvasIndex]

        elif eventType == "release":
            x_final = [self.xdata[0], self.xdata[-1]]
            y_final = [self.ydata[0], self.ydata[-1]]
            line1 = Line2D(
                x_final,
                y_final,
                linestyle="-",
                linewidth=LINE_WIDTH,
                marker="+",
                markersize=MARKER_SIZE,
                markeredgecolor="r",
                color=DRAW_LINE_RELEASE,
            )
            self.ax.add_line(line1)
            self.temp_line = line1
            self.temp_marker = (line1.get_xdata(), line1.get_ydata())

    def is_selected_angle(self, angle, selected_angle_id):
        return angle.get('id') == selected_angle_id
    

    def custom_deepcopy(self,obj):
        if isinstance(obj, dict):
            return {key: self.custom_deepcopy(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.custom_deepcopy(item) for item in obj]
        elif hasattr(obj, 'frozen') and callable(getattr(obj, 'frozen')):
            return obj.frozen()
        else:
            try:
                return copy.deepcopy(obj)
            except Exception:
                return obj
            

    def creatingOriginalAngleDict(self,angle_info):
        if self.patientID not in self.angleStorageDictOriginal:
            self.angleStorageDictOriginal[self.patientID] = {}
        if self.patientSeriesName not in self.angleStorageDictOriginal[self.patientID]:
            self.angleStorageDictOriginal[self.patientID][self.patientSeriesName] = {}
        if self.canvasIndex not in self.angleStorageDictOriginal[self.patientID][self.patientSeriesName]:
            self.angleStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
        if self.imageIndex not in self.angleStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.angleStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []
        
        
        
        self.angleStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(angle_info)

    def angleStorage(self, angle, annotation, markerPositions , uid=None):
        # Assuming annotation is a matplotlib Text instance and markerPositions are structured as needed
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.canvasIndex = self.getCanvaIndex()
        
        if uid is None:
            angle_info = {
            "id":self.current_angle_id,
            "anglelines": angle,
            "annotation": {
                "text": annotation.get_text(),
                "position": annotation.get_position()
            },
            "markerPositions": markerPositions,

            "uuid":self.uid ,
            "image_index":self.imageIndex,
            "canvas_index":self.canvasIndex
        }
        else:
            angle_info = {
                "id":self.current_angle_id,
                "anglelines": angle,
                "annotation": {
                    "text": annotation.get_text(),
                    "position": annotation.get_position()
                },
                "markerPositions": markerPositions,
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        if uid is None:
            angle_info_original = {
            "id":self.current_angle_id,
            "anglelines": self.custom_deepcopy(angle),
            "annotation": {
                "text": annotation.get_text(),
                "position": annotation.get_position()
            },
            "markerPositions": copy.deepcopy(markerPositions),

            "uuid":self.uid ,
            "image_index":self.imageIndex,
            "canvas_index":self.canvasIndex
        }
            
        else:
            angle_info_original = {
                "id":self.current_angle_id,
                "anglelines": self.custom_deepcopy(angle),
                "annotation": {
                    "text": annotation.get_text(),
                    "position": annotation.get_position()
                },
                "markerPositions": copy.deepcopy(markerPositions),
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        if self.patientID not in self.angleStorageDict:
            self.angleStorageDict[self.patientID] = {}
        if self.patientSeriesName not in self.angleStorageDict[self.patientID]:
            self.angleStorageDict[self.patientID][self.patientSeriesName] = {}
        if self.canvasIndex not in self.angleStorageDict[self.patientID][self.patientSeriesName]:
            self.angleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
        if self.imageIndex not in self.angleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.angleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []
        
        # self.angleStorageDict[self.patientID][self.patientSeriesName][self.imageIndex].append(angle_info)
        patient_series_data = self.angleStorageDict.setdefault(self.patientID, {}).setdefault(self.patientSeriesName, {}).setdefault(self.canvasIndex, {}).setdefault(self.imageIndex, [])
        patient_series_data.append(angle_info)
        # print("self.angleStorageDict",self.angleStorageDict)
        self.creatingOriginalAngleDict(angle_info_original)

    def giveAngleStorageDict(self):
        return self.angleStorageDict
    def giveAngleStorageDictOriginal(self):
        return self.angleStorageDictOriginal
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
    def getAngleActivation(self):
        return  self.mainWindow.giveAngleActivation()
    
    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()
    
    
    def calculate_font_size(self):
        """Calculate font size based on the dimensions of the axes."""
        bbox = self.ax.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        height = bbox.height * self.figure.dpi  # Convert height to pixels
        # Adjust font size based on the height of the axes
        return max(6, min(12, height * 0.02))   # Example scaling factor

    def update_annotation_font_sizes(self):
        """Update the font sizes of all annotations according to the new layout."""
        font_size = self.calculate_font_size()
        for angle_id, annotation in self.angle_annotations.items():
            annotation[0].set_fontsize(font_size)
        self.canvas.draw_idle()

    def on_resize(self, event):
        """Handle the resize event to update font sizes."""
        self.update_annotation_font_sizes()
 