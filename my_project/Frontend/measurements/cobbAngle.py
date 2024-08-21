
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt
from matplotlib.lines import Line2D

from matplotlib.figure import Figure
from .constants import *
import sqlite3
import uuid
import copy


class cobbAngleMeasureApp(FigureCanvas):
    def __init__(
        self,
        cobAngleButtonActivated,
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
        # # Create a Matplotlib figure and canvas
        # self.figure, self.ax = plt.subplots()
        # self.canvas = FigureCanvas(self.figure)
        # self.canvas.mpl_connect("button_press_event", self.mousePressEvent)
        # self.canvas.mpl_connect("motion_notify_event", self.mouseMoveEvent)
        # self.canvas.mpl_connect("button_release_event", self.mouseReleaseEvent)
        # self.canvas.mpl_connect('motion_notify_event', self.on_hover)

        # Set up the main window
        # self.setWindowTitle("Angle Measure")
        # self.setGeometry(100, 100, 800, 600)

        # # Create a central widget and layout
        # central_widget = QWidget()
        # layout = QVBoxLayout(central_widget)
        # layout.addWidget(self.canvas)
        # self.setCentralWidget(central_widget)

        self.dicom_image = imgDCM
        self.py, self.px = self.dicom_image.PixelSpacing
        self.pixel_data = self.dicom_image.pixel_array
        self.processedDCM = processedDCM
        self.canvas = canvas
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = ax
        FigureCanvas.__init__(self, fig)
        self.mainWindow = parent
        self.cobAngleButtonActivated = self.cobbAngleActivation()
        self.canvasIndex = self.getCanvaIndex()


        width = width
        height = height
        dpi = dpi

        # self.setParent(parent)

        # Initialize variables for drawing lines
        self.drawing = False
        self.xdata = []
        self.ydata = []
        self.points = []
        self.current_line = []
        self.angle = None
        self.text_annotation = None
        self.drawing_line = 1
        self.angle_lines = {}
        self.angle_id = 1
        self.angle_list = []
        self.angle_annotations = {}
        self.angle_markers = {}
        self.set_marker = None
        self.selected_angle_id = None
        self.selected = False
        self.selected_line = None
        self.selected_marker = None
        self.start_dragging = False
        self.dragging_annotation = None
        self.dragging_annotation_offset = (0, 0)
        self.independent_annotation_positions = {}
        self.cobbAngleStorageDict = {}
        self.cobbAngleStorageDictOriginal = {}

        self.delDbList=[]
        self.setupEventConnections()

    def setupEventConnections(self):
        try:
            # Connect key press event
            self.canvas.mpl_connect("key_press_event", self.cobbKeyPressEvent)
        except:
            pass
######################################################
    def dbConnection(self):
        mydb = sqlite3.connect("mainApplication.db")
        return mydb


    def cobbAngleActivation(self):
        return self.mainWindow.getCobbAngleActivation()

    def cobbOn_hover(self, event):
        self.set_marker = False
        if event.xdata is not None and event.ydata is not None:
            hovered_angle_id = None
            hovered_marker_id = None
            for angle_id, lines in self.angle_lines.items():
                line1, line2 = lines[0]
                # Unpack the tuple of lines
                if self.is_cursor_near_line(event, line1) or self.is_cursor_near_line(
                    event, line2
                ):
                    hovered_angle_id = angle_id
                    break
            for angle_id, annotation in self.angle_annotations.items():
                if self.is_cursor_near_annotation(event, annotation[0]):
                    hovered_angle_id = angle_id
                    break

            for angle_id, markers in self.angle_markers.items():
                if len(markers[0]) == 4:
                    p1, p2, p3, p4 = markers[0]
                    if (
                        self.is_cursor_near_marker(event, p1)
                        or self.is_cursor_near_marker(event, p2)
                        or self.is_cursor_near_marker(event, p3)
                        or self.is_cursor_near_marker(event, p4)
                    ):
                        hovered_marker_id = angle_id
                        self.set_marker = True
                        break
            for angle_id in self.angle_lines.keys():
                if angle_id == hovered_marker_id or angle_id == hovered_angle_id:
                    self.highlight_angle(angle_id)
                else:
                    self.reset_angle_highlight(angle_id)

            self.canvas.mpl_connect("button_press_event", self.cobbMousePressEvent)
            self.canvas.mpl_connect("motion_notify_event", self.cobbMouseMoveEvent)
            self.canvas.draw_idle()

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
                        # facecolor=ANNOTATION_BOX_FACE_COLOR,
                        # alpha=0.5,
                        # edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                        # boxstyle=ANNOTATION_BOX_STYLE,
                        annotation[0].set_color(ANNOTATION_TEXT_COLOR)
                #     )
                # )

    def cobbKeyPressEvent(self, event):
        if type(event.key) == str:
            if event.key.lower().strip() == "delete".lower().strip():
                event.key = 16777223
        else:
            pass
        if str(event.key) == str(Qt.Key_Delete):
            # if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            if self.selected_angle_id:
                self.remove_selected_angle_id()
                self.canvas.draw_idle()

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
            patient_series_data = self.cobbAngleStorageDict.get(self.patientID, {}).get(self.patientSeriesName, {}).get(self.canvasIndex, {}).get(self.imageIndex, [])
            updated_angles = [angle for angle in patient_series_data if angle["id"] != self.selected_angle_id]
            self.cobbAngleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = updated_angles
            for angle in patient_series_data :
                if angle["id"] == self.selected_angle_id:
                    uid=angle["uuid"] 
                    self.delDbList.append(uid)
            
        
        
        self.selected_angle_id = None
        self.canvas.draw()

    def is_cursor_near_line(self, event, line, threshold=3):
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
        try:
            line_unitvec = line_vec / line_len
            point_vec_scaled = point_vec / line_len
        except:
            pass
        t = np.dot(line_unitvec, point_vec_scaled)
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        nearest = line_vec * t
        closest_point = p1 + nearest
        return closest_point

    def is_cursor_near_annotation(self, event, annotation, threshold=1):
        bbox = annotation.get_window_extent(self.canvas.renderer)
        if bbox.contains(event.x, event.y):
            return True
        else:
            return False

    def is_cursor_near_marker(self, event, marker, threshold=7):
        if event.xdata is None or event.ydata is None:
            return False
        mouse_point = np.array([event.xdata, event.ydata])
        marker_point = np.array(marker)
        distance = np.linalg.norm(mouse_point - marker_point)
        return distance < threshold

    def highlight_selected_angle(self, angle_id):
        lines = self.angle_lines.get(angle_id)
        annotation = self.angle_annotations.get(angle_id)
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
                    # facecolor=ANNOTATION_BOX_FACE_COLOR,
                    # alpha=0.5,
                    # edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                    # boxstyle=ANNOTATION_BOX_STYLE,
                    annotation[0].set_color(ANNOTATION_TEXT_COLOR)
            #     )
            # )
        self.canvas.draw_idle()

    def cobbMousePressEvent(self, event):
        self.cobAngleButtonActivated = self.cobbAngleActivation()
        self.ax=self.getAxes()
        self.canvas=self.getCanvas()
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.cobbAngleButtonActivated=self.getCobbAngleActivation()
        self.canvasIndex = self.getCanvaIndex()

        if self.cobbAngleButtonActivated:

            if event.button == Qt.LeftButton and self.cobAngleButtonActivated:
                self.drawing = False

                if self.selected_angle_id is not None:
                    self.reset_selected_angle_highlight(self.selected_angle_id)
                    self.selected_angle_id = None

                # Check if any line or annotation is selected
                self.selected = False
                # print("ggggggggggggggggggggggggggggggg",self.angle_lines)
                for angle_id, lines in self.angle_lines.items():
                    if lines[1] != self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue
                    
                    if lines[2] != self.canvasIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue
                    
                    line1, line2 = lines[0]
                    self.cobblines=lines[0]
                    if self.set_marker != True:
                        if self.is_cursor_near_line(event, line1):
                            self.selected_angle_id = angle_id
                            self.selected_line = line1
                            self.start_dragging = True
                            self.original_mouse_position = (event.xdata, event.ydata)
                            self.highlight_selected_angle(angle_id)
                            self.selected = True
                            break  # No need to check further if a line is already selected
                        if self.is_cursor_near_line(event, line2):
                            self.selected_angle_id = angle_id
                            self.start_dragging = True
                            self.selected_line = line2
                            self.original_mouse_position = (event.xdata, event.ydata)
                            self.highlight_selected_angle(angle_id)
                            self.selected = True
                            break
                if not self.selected:
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
                            ax_pos = self.ax.transData.transform(
                                (annotation[0].get_position())
                            )
                            self.dragging_annotation_offset = (
                                ax_pos[0] - event.x,
                                ax_pos[1] - event.y,
                            )
                            self.highlight_selected_angle(angle_id)
                            self.selected = True
                            break  # No need to check further if an annotation is already selected
                if not self.selected:
                    for angle_id, markers in self.angle_markers.items():
                        if markers[1] != self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        try:
                            if markers[2] != self.canvasIndex:
                                # print("found duplicateeeeeeeeeeeeeeeee")
                                continue
                        except:
                            pass
                        p1, p2, p3, p4 = markers[0]
                        if self.is_cursor_near_marker(event, p1):
                            self.selected_marker = ("start", angle_id, 0)
                            self.start_dragging = True
                            self.selected = True
                            break
                        elif self.is_cursor_near_marker(event, p2):
                            self.selected_marker = ("end", angle_id, 0)
                            self.start_dragging = True
                            self.selected = True
                            break
                        elif self.is_cursor_near_marker(event, p3):
                            self.selected_marker = ("start", angle_id, 1)
                            self.start_dragging = True
                            self.selected = True
                            break
                        elif self.is_cursor_near_marker(event, p4):
                            self.selected_marker = ("end", angle_id, 1)
                            self.start_dragging = True
                            self.selected = True
                            break
                # Start drawing a new angle only if no line or annotation is selected
                if not self.selected:
                    x, y = int(event.xdata), int(event.ydata)
                    self.points.append((x, y))
                    self.drawing = True
                    if len(self.points) == 2 or len(self.points) == 4:
                        self.drawing_line += 1

    def cobbMouseMoveEvent(self, event):
        self.cobAngleButtonActivated = self.cobbAngleActivation()
        self.canvasIndex = self.getCanvaIndex()
        if (
            self.drawing
            and event.button == Qt.LeftButton
            and self.cobAngleButtonActivated
            and event.xdata is not None and event.ydata is not None        ):

            x, y = int(event.xdata), int(event.ydata)
            self.xdata.append(x)
            self.ydata.append(y)
            self.draw_lines(eventType="move")
            if len(self.points) == 3:
                p1, p2, p3 = self.points[0], self.points[1], (x, y)
                self.measure_angle(p1, p2, self.points[2], p3, eventType="move")

        if (
            self.start_dragging
            and self.selected_angle_id is not None
            and self.set_marker != True
        ):
            # moving whole line
            dx = event.xdata - self.original_mouse_position[0]
            dy = event.ydata - self.original_mouse_position[1]
            self.move_angle(self.selected_angle_id, dx, dy)
            self.original_mouse_position = (event.xdata, event.ydata)
            self.canvas.draw_idle()

        if self.start_dragging and self.selected_marker:
            marker_type, angle_id, line_index = self.selected_marker
            line = self.angle_lines[angle_id][0][line_index]
            xdata, ydata = line.get_data()
            if marker_type == "start":
                xdata[0], ydata[0] = event.xdata, event.ydata
            else:  # 'end'
                xdata[1], ydata[1] = event.xdata, event.ydata
            line.set_data(xdata, ydata)

            # Recalculate angle
            x1, y1 = self.angle_lines[angle_id][0][0].get_data()
            x2, y2 = self.angle_lines[angle_id][0][1].get_data()

            p1 = np.array([x1[0], y1[0]])  # Start point of the first line
            p2 = np.array(
                [x1[-1], y1[-1]]
            )  # End point of the first line (shared point)
            p3 = np.array([x2[0], y2[0]])  # Start point of the second line
            p4 = np.array([x2[-1], y2[-1]])

            self.recalculate_angle(angle_id, p1, p2, p3, p4)
            self.update_marker_positions(angle_id, p1, p2, p3, p4)
            self.canvas.draw_idle()


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
                        patient_series_data = self.cobbAngleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex]
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

    def update_marker_positions(self, angle_id, p1, p2, p3, p4):
        # Update the position of the markers in the dictionary
        self.angle_markers[angle_id][0] = (p1, p2, p3, p4)

    def recalculate_angle(self, angle_id, p1, p2, p3, p4):
        self.canvasIndex = self.getCanvaIndex()
        lines = self.angle_lines[angle_id]
        line1, line2 = lines[0]

        vector1 = np.array(p1) - np.array(p2)
        vector2 = np.array(p4) - np.array(p3)

        try:
            angle_rad = np.arccos(
                np.dot(vector1, vector2)
                / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
            )
            angle_deg = np.degrees(angle_rad)
        except RuntimeWarning:
            angle_rad = np.nan

        # Constrain angle to 90 degrees
        if angle_deg > 90:
            angle_deg = 180 - angle_deg
            self.angle = angle_deg
            angle_txt = str(round(angle_deg, 2)) + "°"
            annotation = self.angle_annotations.get(angle_id)
            annotation[0].set_text(angle_txt)

            if angle_id in self.independent_annotation_positions:
                self.new_annotation_pos = self.independent_annotation_positions[angle_id]
            else:
                if annotation[0]:
                    vertex = np.array(p1)
                    offset = (8, 3)
                    self.new_annotation_pos = vertex + offset
                    annotation[0].set_position(self.new_annotation_pos)

        else:
            self.angle = angle_deg
            angle_txt = str(round(angle_deg, 2)) + "°"
            annotation = self.angle_annotations.get(angle_id)
            annotation[0].set_text(angle_txt)

            if angle_id in self.independent_annotation_positions:
                self.new_annotation_pos = self.independent_annotation_positions[angle_id]
            else:
                if annotation:
                    vertex = np.array(p2)
                    offset = (8, 3)
                    self.new_annotation_pos = vertex + offset
                    annotation[0].set_position(self.new_annotation_pos)
        try:
            patient_series_data = self.cobbAngleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex]
            for angle_info in patient_series_data:
                if angle_info['id'] == angle_id:
                    # Update angle measurement
                    angle_info['annotation']['text'] = angle_txt
                    angle_info['anglelines']=[lines[0][0],lines[0][1]]
                    # Update position
                    angle_info['annotation']['position'] = self.new_annotation_pos
                    break
        except KeyError as e:
            pass

        self.canvas.draw_idle()

    def move_angle(self, angle_id, dx, dy):
        self.canvasIndex = self.getCanvaIndex()
        newAnnotationBool= False
        if self.selected_line:
            new_xdata = self.selected_line.get_xdata() + dx
            new_ydata = self.selected_line.get_ydata() + dy
            self.selected_line.set_data(new_xdata, new_ydata)
            # Update the marker positions for the moved line
            if self.selected_line is self.angle_lines[self.selected_angle_id][0][0]:
                # Update markers for the first line
                p1, p2, p3, p4 = self.angle_markers[self.selected_angle_id][0]
                self.angle_markers[self.selected_angle_id][0] = (
                    (new_xdata[0], new_ydata[0]),
                    (new_xdata[1], new_ydata[1]),
                    p3,
                    p4,
                )
            else:
                # Update markers for the second line
                p1, p2, p3, p4 = self.angle_markers[self.selected_angle_id][0]
                self.angle_markers[self.selected_angle_id][0] = (
                    p1,
                    p2,
                    (new_xdata[0], new_ydata[0]),
                    (new_xdata[1], new_ydata[1]),
                )

        # Update annotation
        if angle_id in self.independent_annotation_positions:
            self.new_annotation_pos = self.independent_annotation_positions[angle_id]
            newAnnotationBool= True

        else:
            if self.selected_line is self.angle_lines[angle_id][0][0]:
                # Update annotation normally if no independent position

                annotation = self.angle_annotations[angle_id]
                x, y = annotation[0].get_position()
                self.new_annotation_pos = (x + dx, y + dy)
                annotation[0].set_position(self.new_annotation_pos)
                newAnnotationBool= True

        index=self.cobblines.index(self.selected_line)
        try:       
            patient_series_data = self.cobbAngleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex]
            for angle_info in patient_series_data:
                if angle_info['id'] == angle_id:
                    angle_info['anglelines'][index]=self.selected_line
                    # Update line positions in stored data
                    if self.selected_line is self.angle_lines[angle_id][0][0]:
                        angle_info['markerPositions'] = (
                            (new_xdata[0], new_ydata[0]),
                            (new_xdata[1], new_ydata[1]),
                            angle_info['markerPositions'][2],
                            angle_info['markerPositions'][3],
                        )
                    else:  # For the second line
                        angle_info['markerPositions'] = (
                            angle_info['markerPositions'][0],
                            angle_info['markerPositions'][1],
                            (new_xdata[0], new_ydata[0]),
                            (new_xdata[1], new_ydata[1]),
                        )

                    # Update annotation position
                    if  newAnnotationBool:  
                        angle_info['annotation']['position'] = self.new_annotation_pos
                    break
                
        except KeyError as e:
            pass

        self.canvas.draw_idle()

    def cobbMouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            if not self.selected:
                x, y = int(event.xdata), int(event.ydata)
                self.xdata.append(x)
                self.ydata.append(y)
                self.points.append((x, y))
                self.draw_lines(eventType="release")
                if len(self.points) == 4:
                    self.measure_angle(
                        self.points[0],
                        self.points[1],
                        self.points[2],
                        (x, y),
                        eventType="press",
                    )
                    last_Angle_Key=list(self.angle_lines.keys())[-1]
                    last_angle= self.angle_lines[last_Angle_Key]
                    last_key = list(self.angle_annotations.keys())[-1]  # Get the last key added to the dictionary
                    last_annotation = self.angle_annotations[last_key] 
                    last_Marker_key=list(self.angle_markers.keys())[-1]
                    last_marker = self.angle_markers[last_Marker_key] 

                    self.uid=uuid.uuid4() # 4     
                    conn = self.dbConnection()
                    cur = conn.cursor()
                    query = "SELECT EXISTS(SELECT 1 FROM cobbAngleData WHERE uuid = ?)"
                    # Execute the query, replacing '?' with the new_uuid
                    cur.execute(query, (str(self.uid),))
                    exists = cur.fetchone()[0] 
                    # self.text_id+=1
                    if self.uid == exists:
                        self.uid = uuid.uuid4()
                    else :
                        pass

                    self.cobbAngleStorage(last_angle[0],last_annotation[0],last_marker[0])
                    self.angle_id += 1
                self.xdata = []
                self.ydata = []

        if event.button == Qt.LeftButton:
            if self.start_dragging and self.selected_angle_id is not None:
                self.start_dragging = False
                self.selected_line = None

        if self.start_dragging and self.selected_marker:
            self.start_dragging = False
            self.selected_marker = None

        if event.button == Qt.LeftButton and self.dragging_annotation:
            self.dragging_annotation = None
            self.dragging_annotation_offset = (0, 0)

    def draw_lines(self, eventType):
        if eventType == "move" and self.cobAngleButtonActivated:
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
            self.canvas.draw()

        elif eventType == "release":
            if self.current_line and self.current_line in self.ax.lines:
                self.current_line.remove()
            x_final = [self.xdata[0], self.xdata[-1]]
            y_final = [self.ydata[0], self.ydata[-1]]
            line1 = Line2D(
                x_final,
                y_final,
                linestyle="-",
                linewidth=LINE_WIDTH,
                marker="+",
                markersize=MARKER_SIZE,
                markeredgecolor=MARKER_EDGE_COLOR,
                color=DRAW_LINE_RELEASE,
            )
            self.ax.add_line(line1)
            self.angle_list.append(line1)

    def measure_angle(self, p1, p2, p3, p4, eventType):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()


        vector1 = np.array(p1) - np.array(p2)
        vector2 = np.array(p4) - np.array(p3)
        try:
            angle_rad = np.arccos(
                np.dot(vector1, vector2)
                / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
            )
            angle_deg = np.degrees(angle_rad)
        except RuntimeWarning:
            angle_rad = np.nan
            
        vertex1 = np.array(p1)
        vertex2 = np.array(p2)
        offset = (8, 1)
        # Constrain angle to 90 degrees
        if angle_deg > 90:
            angle_deg = 180 - angle_deg
            self.angle = angle_deg
            angle_txt = str(round(angle_deg, 2)) + "°"

            if self.text_annotation:
                self.text_annotation.set_text(angle_txt)
                pos = vertex1 + offset
                self.text_annotation.set_position((pos[0], pos[1]))
            else:
                pos = vertex1 + offset
                self.text_annotation = self.ax.text(
                    pos[0],
                    pos[1],
                    angle_txt,
                    color=ANNOTATION_TEXT_COLOR,
                    fontsize=ANNOTATION_FONT_SIZE,
                    # bbox=dict(
                    #     facecolor=ANNOTATION_BOX_FACE_COLOR,
                    #     alpha=0.5,
                    #     edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                    #     boxstyle=ANNOTATION_BOX_STYLE,
                    # ),
                )
        else:
            self.angle = angle_deg
            angle_txt = str(round(angle_deg, 2)) + "°"
            font_size = self.calculate_font_size()  # Get dynamic font size
            if self.text_annotation:
                self.text_annotation.set_text(angle_txt)
                self.text_annotation.set_text(angle_txt)#dynamic font
                pos = vertex2 + offset
                self.text_annotation.set_position((pos[0], pos[1]))
            else:
                pos = vertex2 + offset
                self.text_annotation = self.ax.text(
                    pos[0],
                    pos[1],
                    angle_txt,
                    color=ANNOTATION_TEXT_COLOR,
                    # fontsize=ANNOTATION_FONT_SIZE,
                    fontsize=font_size  # Use dynamic font size
                    # bbox=dict(
                    #     facecolor=ANNOTATION_BOX_FACE_COLOR,
                    #     alpha=0.5,
                    #     edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                    #     boxstyle=ANNOTATION_BOX_STYLE,
                    # ),
                )

        self.canvas.draw_idle()

        if eventType == "press":
            self.angle_lines[self.angle_id] = [self.angle_list,self.imageIndex,self.canvasIndex]
            self.angle_annotations[self.angle_id] = [self.text_annotation,self.imageIndex,self.canvasIndex]
            self.angle_markers[self.angle_id] = [(p1, p2, p3, p4),self.imageIndex,self.canvasIndex]
            
            self.points = []
            self.xdata = []
            self.ydata = []
            self.lines = []
            self.angle_list = []
            self.text_annotation = None
        return self.angle
    
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
        if self.patientID not in self.cobbAngleStorageDictOriginal:
                self.cobbAngleStorageDictOriginal[self.patientID] = {}
        if self.patientSeriesName not in self.cobbAngleStorageDictOriginal[self.patientID]:
            self.cobbAngleStorageDictOriginal[self.patientID][self.patientSeriesName] = {}
        if self.canvasIndex not in self.cobbAngleStorageDictOriginal[self.patientID][self.patientSeriesName]:
            self.cobbAngleStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
        if self.imageIndex not in self.cobbAngleStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.cobbAngleStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []
          
        
        # self.cobbAngleStorageDictOriginal[self.patientID][self.patientSeriesName][self.imageIndex].append(angle_info)
        patient_series_data = self.cobbAngleStorageDictOriginal.setdefault(self.patientID, {}).setdefault(self.patientSeriesName, {}).setdefault(self.canvasIndex, {}).setdefault(self.imageIndex, [])
        patient_series_data.append(angle_info)
    
    def cobbAngleStorage(self, angle, annotation, markerPositions, uid=None):
        # Assuming annotation is a matplotlib Text instance and markerPositions are structured as needed
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.canvasIndex = self.getCanvaIndex()

        if uid is None:
            angle_info = {
                "id":self.angle_id,
                "anglelines": angle,
                "annotation": {
                    "text": annotation.get_text(),
                    "position": annotation.get_position()
                },
                "markerPositions": markerPositions,
                "uuid" :self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        else:
            angle_info = {
                "id":self.angle_id,
                "anglelines": angle,
                "annotation": {
                    "text": annotation.get_text(),
                    "position": annotation.get_position()
                },
                "markerPositions": markerPositions,
                "uuid" :uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex

            }

        if uid is None:
            angle_info_original = {
                "id":self.angle_id,
                "anglelines": self.custom_deepcopy(angle),
                "annotation": {
                    "text": annotation.get_text(),
                    "position": annotation.get_position()
                },
                "markerPositions": copy.deepcopy(markerPositions),
                "uuid" :self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        else:
            angle_info_original = {
                "id":self.angle_id,
                "anglelines": self.custom_deepcopy(angle),
                "annotation": {
                    "text": annotation.get_text(),
                    "position": annotation.get_position()
                },
                "markerPositions": copy.deepcopy(markerPositions),
                "uuid" :uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex

            }

        if self.patientID not in self.cobbAngleStorageDict:
            self.cobbAngleStorageDict[self.patientID] = {}
        if self.patientSeriesName not in self.cobbAngleStorageDict[self.patientID]:
            self.cobbAngleStorageDict[self.patientID][self.patientSeriesName] = {}
        if self.canvasIndex not in self.cobbAngleStorageDict[self.patientID][self.patientSeriesName]:
            self.cobbAngleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
        if self.imageIndex not in self.cobbAngleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.cobbAngleStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []
          
        
        # self.cobbAngleStorageDict[self.patientID][self.patientSeriesName][self.imageIndex].append(angle_info)
        patient_series_data = self.cobbAngleStorageDict.setdefault(self.patientID, {}).setdefault(self.patientSeriesName, {}).setdefault(self.canvasIndex, {}).setdefault(self.imageIndex, [])
        patient_series_data.append(angle_info)

        self.creatingOriginalAngleDict(angle_info_original)

    def giveCobbAngleStorageDict(self):
        return self.cobbAngleStorageDict
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
    def getCobbAngleActivation(self):
        return  self.mainWindow.giveCobbAngleActivation()
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


#     def load_image(self, image_path):
#         self.dicom_image = pydicom.dcmread(image_path)
#         self.py,self.px = self.dicom_image.PixelSpacing
#         self.pixel_data = self.dicom_image.pixel_array
#         self.ax.imshow(self.pixel_data, cmap="gray")
#         self.canvas.draw_idle()



# # def main():
#     app = QApplication(sys.argv)
#     window = cobbAngleMeasureApp()
#     window.load_image("case1_008.dcm")
#     window.show()
#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     main()