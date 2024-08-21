
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from scipy.interpolate import make_interp_spline
from PyQt5.QtCore import Qt
from .constants import *
import sqlite3
import uuid
import copy


class OpenPoly(FigureCanvas):
    def __init__(
        self,
        openPolygonButtonActivated,
        imgDCM,
        processedDCM,
        canvas,
        ax,
        figure,
        parent=None,
        width=5,
        height=4,
        dpi=100,
        
    ):
        

        self.openPolygonButtonActivated = openPolygonButtonActivated
        self.dicom_image = imgDCM
        # ##print(f"dicom image {self.dicom_image}")
        self.py, self.px = self.dicom_image.PixelSpacing
        self.pixel_data = self.dicom_image.pixel_array
        self.processedDCM = processedDCM
        self.canvas = canvas

        width = width
        height = height
        dpi = dpi

        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = ax


        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        self.polygon_id=0
        self.last_point = None
        self.length = 0
        self.xs = []
        self.ys = []
        self.previous_sets = []  # List to store previous sets of points and lines
        self.previous_annot = []  # List to store annotations for each polygon
        self.current_annot = None
        self.annot_to_line = {}  # Maps annotations to their respective lines
        self.dragging = False
        self.hover_active = False

        self.drag_data = None  # Store data for dragging annotation
        self.previous_markers = []  # List to store markers for each point # MODIFIED
        self.current_markers = []
        self.del_current_line = None
        self.del_current_annot = None
        self.openPolyStorageDict = {}
        self.openPolyStorageDictOriginal={}
        self.delDbList=[]
        self.mainWindow=parent
        self.background = None

        # self.openAddPoint = self.canvas.mpl_connect("button_press_event", self.add_point)
        # self.openPress = self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        # self.openRelease = self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        # self.openMove = self.canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)
        # self.openKeyPress = self.canvas.mpl_connect('key_press_event', self.keyPressEvent)
        # self.openHover = self.canvas.mpl_connect('motion_notify_event', self.on_hover)

        self.selected_markers = []  # List to store markers of the selected line
        self.item_selected = False  # New flag to track if an item is selected
        self.selected_prev_line = None  # to chane the color of the prev line to  from hotpink to lime  if new line is clciked
        self.dragging_marker = False
        self.dragged_marker = None
        self.polygon_start_indices = [
            0
        ]  # List to store the start indices of each polygon's markers
        self.annotation_moved = (
            {}
        )  # Maps annotations to a boolean indicating manual movement
        # When creating a new annotation, initialize its flag to False
        self.annotation_moved[self.current_annot] = False
        self.line_selected_for_new_marker = (
            False  # New flag to determine if the next click should add a marker
        )
        self.double_click_text = " \n\nDouble-click \nto finish drawing "
        self.setupEventConnections()

    def setupEventConnections(self):
        try:
            # Connect key press event
            self.canvas.mpl_connect("key_press_event", self.keyPressEvent)
        except:
            pass
    # ---------------------------------------------------------------------------------
    def dbConnection(self):
        mydb = sqlite3.connect("mainApplication.db")
        return mydb
    
    def keyPressEvent(self, event):
        if type(event.key) == str:
            if event.key.lower().strip() == "delete".lower().strip():
                event.key = 16777223
        else:
            pass
        if str(event.key) == str(Qt.Key_Delete):
            # if event.key() == Qt.Key_Delete:
            if self.del_current_line or self.del_current_annot:
                # Call remove() on the line artist itself, not on self.axes.lines
                self.del_current_line.remove()

                # Remove the associated annotation
                try:
                    for annotlist in self.previous_annot:
                        if annotlist[0]==self.del_current_annot:
                    
                        # self.previous_annot.remove(self.del_current_annot)
                            self.del_current_annot.remove()
                        
                            self.annot_to_line.pop(
                                self.del_current_annot, None
                            ) 
                            break
                    # Remove the line from the previous_sets list
                    # self.previous_sets = [
                    #     line
                    #     for line in self.previous_sets
                    #     if line != self.del_current_line
                    # ]

                    # Also remove the markers associated with the line
                    markers_to_remove = [
                        (marker, line)
                        for marker, line, imageindex,canvasindex in self.previous_markers
                        if line == self.del_current_line
                    ]

                    for marker, _ in markers_to_remove:
                        marker.remove()  # Remove the marker from the figure
                        self.remove_open_polygon_from_storage()
                    # Now filter out the removed markers from the previous_markers list
                    # self.previous_markers = [
                    #     ml
                    #     for ml in self.previous_markers
                    #     if ml[1] != self.del_current_line
                    # ]  # Use second element for comparison

                    # Redraw the canvas

                    self.canvas.draw_idle()
                except:
                    pass
                finally:
                    self.del_current_line = None
                    self.del_current_annot = None
                    self.item_selected = False

    def remove_open_polygon_from_storage(self):
        self.imageIndex = self.getimageIndex()
        # Assuming each polygon's annotation text is unique and used as an identifier
        if self.del_current_annot:
            annot_text = self.del_current_annot.get_text()
            # Find and remove the polygon data from storage based on annotation text
            for image_polygons in self.openPolyStorageDict.values():
                for series_polygons in image_polygons.values():
                    for canvasPolygon in series_polygons.values():
                        for i, polygon in enumerate(canvasPolygon.get(self.imageIndex, [])):
                            if polygon.get('annotation', {}).get('text') == annot_text:
                                self.delDbList.append(polygon['uuid'])
                                del canvasPolygon[self.imageIndex][i]   
                                return

    def on_mouse_press(self, event):
        # print("open onpress")
        self.py, self.px = self.mainWindow.pixelSpacing
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()
        self.ax=self.getAxes()
        self.canvas=self.getCanvas()
        # #print("self.imageIndex", self.imageIndex)
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.openPolygonButtonActivated = self.getOpenActivation()
        
        # if event.xdata is not None and event.ydata is not None:
        # ##print("inside mouse press")
        if self.openPolygonButtonActivated:
            #print(
            #     f"self.openPolygonButtonActivated inside open polygon press itself{self.openPolygonButtonActivated}"
            # )
            if event.button == Qt.LeftButton:
                # Check if the line is already selected, and we are clicking on it again
                if self.item_selected and event.inaxes is not None:
                    line = self.del_current_line
                    # Verify we clicked on the line and not on a marker
                    if (
                        line
                        and line.contains(event)[0]
                        and not self.clicked_on_marker(event)
                        and not self.clicked_on_annotation(event)
                    ):
                        # Create a new marker on the line at the click position
                        self.add_marker_to_selected_line(event)
                        return  # Prevent other mouse press actions if we added a marker

                # if event.inaxes is not None and self.hover_active:
                if event.inaxes is not None:
                    self.deselect_markers()  # Deselect markers of the previously selected line

                    for annot in self.previous_annot:
                        if  annot[1]!= self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                        if  annot[2]!= self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        annot=annot[0]
                        try:
                            contains, _ = annot.contains(event)
                            if contains:
                                # Calculate the offset from the click position to the annotation's current position
                                offset = (
                                    event.xdata - annot.get_position()[0],
                                    event.ydata - annot.get_position()[1],
                                )
                                self.del_current_annot = annot
                                self.drag_data = {"annot": annot, "offset": offset}
                                self.del_current_line = self.annot_to_line.get(annot)
                                self.selected_prev_line = self.annot_to_line.get(annot)

                                markers_to_change = [
                                    marker
                                    for marker, assoc_line, imageindex,canvasindex in self.previous_markers
                                    if assoc_line == self.del_current_line
                                ]

                                # Change the color of these markers to pink
                                # ##print("markers_to_change:",markers_to_change)
                                for marker in markers_to_change:
                                    # marker.set_color('pink')
                                    marker.set_markeredgecolor(POLY_HOVER_MARKER_COLOR)
                                    marker.set_markerfacecolor(POLY_HOVER_MARKER_COLOR)
                                    marker.set_markersize(POLY_MARKER_SIZE)
                                self.del_current_line.set_color(POLY_HOVER_LINE_COLOR)
                                self.selected_markers = (
                                    markers_to_change  # Keep track of the selected markers
                                )

                                self.item_selected = True  # Set the item_selected flag
                                self.canvas.draw_idle()

                                break  # Break the loop as we found our annotation
                        except:
                            pass

                    for idx, (marker, line, imageindex,canvasindex) in enumerate(self.previous_markers):
                        if  imageindex != self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        if  canvasindex != self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue  
                        if marker.contains(event)[0]:
                            # ##print("idx, marker, line:",idx, marker, line)
                            self.dragging_marker = True
                            self.dragged_marker = (idx, marker, line)
                            # return  # Exit the method as we found our marker

                    for line in self.previous_sets:
                        if  line[1]!= self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                        if  line[2]!= self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        line=line[0]
                        try:
                            contains, _ = line.contains(event)
                            if contains:
                                self.del_current_line = line
                                self.selected_prev_line = line

                                self.del_current_line.set_color(POLY_HOVER_LINE_COLOR)

                                markers_to_change = [
                                    marker
                                    for marker, assoc_line, imageindex,canvasindex in self.previous_markers
                                    if assoc_line == self.del_current_line
                                ]

                                # Change the color of these markers to pink
                                # ##print("markers_to_change:",markers_to_change)
                                for marker in markers_to_change:
                                    # marker.set_color('pink')
                                    marker.set_markeredgecolor(POLY_HOVER_MARKER_COLOR)
                                    marker.set_markerfacecolor(POLY_HOVER_MARKER_COLOR)
                                    marker.set_markersize(POLY_MARKER_SIZE)

                                # Find the associated annotation for the clicked line
                                for annot, assoc_line in self.annot_to_line.items():
                                    if assoc_line == line:
                                        self.del_current_annot = annot
                                        break
                                self.selected_markers = (
                                    markers_to_change  # Keep track of the selected markers
                                )
                                self.item_selected = True  # Set the item_selected flag

                                self.canvas.draw_idle()
                                # return  # Exit the method
                        except:
                            pass

                self.background = self.canvas.copy_from_bbox(self.axes.bbox)

    def clicked_on_marker(self, event):
        if self.openPolygonButtonActivated:
            # ##print("inside clicked on marker")
            # Iterate over the markers of the selected line
            for marker, line, imageindex, canvasindex in self.previous_markers:
                if line == self.del_current_line and marker.contains(event)[0]:
                    return True  # Click was on a marker
            return False  # Click was not on a marker

    def clicked_on_annotation(self, event):
        if self.openPolygonButtonActivated:
            # ##print("inside clicked on annotation")
            # Iterate over the annotations
            for annot in self.previous_annot:
                if  annot[1]!= self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue 
                if  annot[2]!= self.canvasIndex:
                    # print("found duplicateeeeeeeeeeeeeeeee")
                    continue
                if annot[0] is not None:
                    if annot[0].contains(event)[0]:
                        return True  # Click was on an annotation
            return False  # Click was not on an annotation

    def on_mouse_release(self, event):
        if self.openPolygonButtonActivated:
            #print(
            #     f"self.openPolygonButtonActivated inside open  release polygon itself{self.openPolygonButtonActivated}"
            # )

            # ##print("inside on move")
            if self.drag_data:
                self.drag_data = None
            # Stop dragging the marker
            if self.dragging_marker:
                self.dragging_marker = False
                self.dragged_marker = None
                self.canvas.draw_idle()

    def extract_coordinate(self, data):
        return data if np.isscalar(data) else data[0]

    def add_marker_to_selected_line(self, event):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()


        # Get the clicked position
        ix, iy = event.xdata, event.ydata

        # List to store distances from the new marker to each line segment
        segment_distances = []
        segment_indices = []

        # Calculate distances from the new marker to each segment of the associated line
        markers_on_line = [
            (marker, idx)
            for idx, (marker, assoc_line, imageindex,canvasindex) in enumerate(self.previous_markers)
            if assoc_line == self.del_current_line
        ]
        # for i in range(len(markers_on_line) - 1):
        #     marker1, idx1 = markers_on_line[i]
        #     marker2, idx2 = markers_on_line[i + 1]
        #     mx1, my1 = marker1.get_xdata()[0], marker1.get_ydata()[0]
        #     mx2, my2 = marker2.get_xdata()[0], marker2.get_ydata()[0]

        #     # Calculate the shortest distance from the point to the line segment
        #     dist = self.point_to_segment_distance(ix, iy, mx1, my1, mx2, my2)
        #     segment_distances.append(dist)
        #     segment_indices.append((idx1, idx2))

        for i in range(len(markers_on_line) - 1):
            marker1, idx1 = markers_on_line[i]
            marker2, idx2 = markers_on_line[i + 1]
            mx1, my1 = self.extract_coordinate(
                marker1.get_xdata()
            ), self.extract_coordinate(marker1.get_ydata())
            mx2, my2 = self.extract_coordinate(
                marker2.get_xdata()
            ), self.extract_coordinate(marker2.get_ydata())
            dist = self.point_to_segment_distance(ix, iy, mx1, my1, mx2, my2)
            segment_distances.append(dist)
            segment_indices.append((idx1, idx2))

        # Find the index of the closest segment
        if segment_distances:
            closest_segment_index = np.argmin(segment_distances)
            # Insert index is after the first marker of the closest segment
            insert_index = segment_indices[closest_segment_index][0] + 1
        else:
            insert_index = 0  # If there are no segments, set index to 0

        # Add the new marker at the midpoint of the closest segment
        (new_marker,) = self.axes.plot(
            ix,
            iy,
            "o",
            color=POLY_HOVER_MARKER_COLOR,
            markeredgecolor=POLY_HOVER_MARKER_COLOR,
            markerfacecolor=POLY_HOVER_MARKER_COLOR,
            markersize=POLY_MARKER_SIZE,
            zorder=1,
        )
        self.selected_markers.append(
            new_marker
        )  # Add the new marker to the selected markers list

        # Ensure the line has a higher z-order than the marker (e.g., zorder=2)
        self.del_current_line.set_zorder(2)

        # Insert the new marker into the previous_markers list at the determined position
        self.previous_markers.insert(insert_index, (new_marker, self.del_current_line,self.imageIndex,self.canvasIndex))
        
        marker_list=[]
        for marker in self.previous_markers:
            if marker[1]==self.del_current_line:
                marker_list.append(marker[0])

        #print("marker_list", marker_list)

        for patient_id, patient_data in self.openPolyStorageDict.items():
            for series_name, series_data in patient_data.items():
                for image_index, canvas in series_data.items():
                    for image_index, polygons in canvas.items():
                        for polygon in polygons:
                            if polygon["line"] == self.del_current_line:
                                polygon["markers"] = marker_list
                                return
                        
        #print("after insert points", self.openPolyStorageDict)
        # Redraw the canvas
        self.draw_idle()

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        if self.openPolygonButtonActivated:
            # #print("inside point to segment distance")
            # Calculate the distance from the point (px, py) to the segment defined by (x1, y1) and (x2, y2)
            dx = x2 - x1
            dy = y2 - y1
            if dx == dy == 0:  # The segment's points are coincident
                return np.sqrt((px - x1) ** 2 + (py - y1) ** 2)
            # Calculate the t that minimizes the distance
            t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))  # Clamp t to the range [0, 1]
            # Find the closest point on the segment
            nearest_x = x1 + t * dx
            nearest_y = y1 + t * dy
            return np.sqrt((px - nearest_x) ** 2 + (py - nearest_y) ** 2)

    def recalculate_line_length(self, line, xs, ys):
        if self.openPolygonButtonActivated:
            # #print("inside recalculate line length")
            # Calculate the new length based on the updated x and y coordinates
            new_length = 0
            for i in range(len(xs) - 1):
                segment_length = np.sqrt(
                    (xs[i + 1] - xs[i]) ** 2 + (ys[i + 1] - ys[i]) ** 2
                )
                new_length += (
                    segment_length * self.px
                )  # Assuming self.px is the pixel spacing in mm

            # Find the annotation associated with the line
            for annot, assoc_line in self.annot_to_line.items():
                if assoc_line == line:
                    # Update the annotation text with the new length
                    if new_length < 10.0:
                        self.length_str = "{:.2f} mm".format(new_length)
                    else:
                        self.length_str = "{:.2f} cm".format(new_length / 10.0)
                    annot.set_text(self.length_str)
                    break

    def on_mouse_motion(self, event):
        if self.openPolygonButtonActivated:
            # #print("inside on mouse motion")
            # Handle dragging of annotations
            if self.drag_data is not None:
                annot = self.drag_data["annot"]
                offset = self.drag_data["offset"]
                new_x = event.xdata - offset[0]
                new_y = event.ydata - offset[1]
                annot.set_position((new_x, new_y))
                self.annotation_moved[
                    annot
                ] = True  # Set the flag to True when the annotation is moved

                for patient_id, patient_data in self.openPolyStorageDict.items():
                    for series_name, series_data in patient_data.items():
                        for image_index, canvas in series_data.items():
                            for image_index, polygons in canvas.items():
                                for polygon in polygons:
                                    # Assuming the annotation text is unique and can be used as an identifier
                                    if polygon["annotation"]["text"] == annot.get_text():
                                        # Update the annotation's position
                                        polygon["annotation"]["position"] = (new_x, new_y)
                                        return
                self.canvas.draw_idle()
                return  # Exit the function to avoid marker dragging logic when dragging annotations

            if self.dragging_marker and self.dragged_marker:
                idx, marker, line = self.dragged_marker
                old_x, old_y = marker.get_data()
                dx = event.xdata - old_x
                dy = event.ydata - old_y
                marker.set_data(event.xdata, event.ydata)

            try:
                xs, ys = [], []
                for m, l,index,canvasindex in self.previous_markers:
                    if l == line:
                        x_data = m.get_xdata()
                        y_data = m.get_ydata()
                        # Handle both scalar and array cases
                        xs.append(x_data if np.isscalar(x_data) else x_data[0])
                        ys.append(y_data if np.isscalar(y_data) else y_data[0])

                line_index = next((i for i, v in enumerate(self.previous_sets) if v[0] == line), None)
                # Only move the annotation if the first marker of the line is being dragged
                first_marker = self.previous_markers[
                    self.polygon_start_indices[line_index]
                ][0]
                if marker == first_marker:
                    # Move the annotation with the first marker
                    for annot, assoc_line in self.annot_to_line.items():
                        if assoc_line == line and not self.annotation_moved.get(
                            annot, False
                        ):
                            annot_x, annot_y = annot.get_position()
                            annot.set_position((annot_x + dx, annot_y + dy))
                            break

                # Redraw the line
                if len(xs) > 2 and len(ys) > 2:
                    curve_xs, curve_ys = self.calculate_bezier_curve(xs, ys)
                    line.set_data(curve_xs, curve_ys)
                else:
                    line.set_data(xs, ys)

                # Recalculate the total length of the line with the updated marker position
                self.recalculate_line_length(line, xs, ys)
                update_marker=[]
                for markers, assoc_line, imageindex ,canvasindex in self.previous_markers:
                    if assoc_line == line:
                        if markers== marker:
                            markers.set_data(event.xdata, event.ydata)
                        update_marker.append(markers)
                self.update_polygon_vertices_in_storage(line=line, new_vertices=update_marker,perimeter_text=self.length_str)
                self.draw_idle()

            except Exception as e:
                pass
                # #print("Error in on_mouse_motion:", e)

    def update_polygon_vertices_in_storage(self, line, new_vertices,perimeter_text):
        for patient_id, patient_data in self.openPolyStorageDict.items():
            for series_name, series_data in patient_data.items():
                for image_index, canvas in series_data.items():
                    for image_index, polygons in canvas.items():
                        for polygon in polygons:
                            #print("polygon['line']",polygon["line"])
                            #print("line",line)
                            if polygon["line"] == line:
                                polygon["annotation"]["text"]=perimeter_text
                                polygon["markers"] = new_vertices
                                polygon["line"] == line
                                    # Update the vertices list
                                return
    def on_hover(self, event):
        self.canvasIndex=self.getCanvaIndex()
        if self.openPolygonButtonActivated:
            # ##print("inside on hover")
            if event.inaxes != self.axes:
                return

            # Hide markers for all lines
            for marker, line,imageindex,canvasindex in self.previous_markers:
                marker.set_visible(False)
                self.canvas.draw_idle()

            # Reset all lines and annotations to their non-glowing state
            for line in self.previous_sets:
                self.apply_glow_effect_line(line[0], glow=False)
            for annot in self.previous_annot:
                self.apply_glow_effect(annot[0], glow=False)

            if self.item_selected:
                # If an item is selected, ensure its markers remain visible
                for marker, line, imageindex,canvasindex in self.previous_markers:
                    if line == self.del_current_line:
                        marker.set_visible(True)
                        # self.canvas.draw_idle()

            # Check for hover on annotations and highlight the associated line
            for annot in self.previous_annot:
                if  annot[1]!= self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue 
                if  annot[2]!= self.canvasIndex:
                    # print("found duplicateeeeeeeeeeeeeeeee")
                    continue
                annot=annot[0]
                if annot is not None:
                    try:
                        contains, _ = annot.contains(event)
                        if contains:
                            self.apply_glow_effect(annot, glow=True)
                            if (
                                annot in self.annot_to_line
                            ):  # Check if this annotation has an associated line
                                self.apply_glow_effect_line(
                                    self.annot_to_line[annot], glow=True
                                )
                                # Make the markers for this line visible
                                for marker, line, imageindex,canvasindex in self.previous_markers:
                                    if line == self.annot_to_line[annot]:
                                        marker.set_visible(True)
                            self.hover_active = True
                            self.canvas.draw_idle()
                            return  # Exit after finding the hovered annotation
                    except:
                        pass

            # Check for hover on lines and highlight the associated annotation
            for line in self.previous_sets:
                line=line[0]
                if line.contains(event)[0]:
                    self.apply_glow_effect_line(line, glow=True)
                    # Find the associated annotation and highlight it
                    for annot, assoc_line in self.annot_to_line.items():
                        if assoc_line == line:
                            self.apply_glow_effect(annot, glow=True)
                            # Make the markers for this line visible
                            for marker, assoc_line, imageindex,canvasindex in self.previous_markers:
                                if assoc_line == line:
                                    marker.set_visible(True)
                            break  # Break once the associated annotation is found and highlighted
                    self.hover_active = True
                    self.canvas.draw_idle()
                    return  # Exit after finding the hovered line

            # If nothing is hovered, ensure no hover effects are active and all markers are hidden
            self.hover_active = False

            # self.canvas.mpl_connect(
            #         "button_press_event", self.on_mouse_press
            #     )
            # self.canvas.mpl_connect(
            #             "motion_notify_event", self.on_mouse_motion
            #         )
            # self.canvas.mpl_connect(
            #             "button_press_event", self.add_point
            #         )
            self.canvas.draw_idle()

    def apply_glow_effect(self, annotation, glow=False):
        if self.openPolygonButtonActivated:
            # ##print("inside apply glow effect")
            if annotation is None:
                return  # Do nothing if the annotation is None
            if glow:
                # annotation.set_bbox(
                #     dict(
                #         # facecolor=HOVER_ANNOTATION_BACKGROUND_COLOR, edgecolor=GLOW_ANNOTATION_BOX_EDGE_COLOR, boxstyle=ANNOTATION_BOX_STYLE
                        annotation.set_color(HOVER_ANNOTATION_TEXT_COLOR)
                #         )
                # )
            else:
                # annotation.set_bbox(
                #     dict(
                        # facecolor=ANNOTATION_BOX_FACE_COLOR, edgecolor=ANNOTATION_BOX_EDGE_COLOR, boxstyle=ANNOTATION_BOX_STYLE
                        annotation.set_color(ANNOTATION_TEXT_COLOR)
                #         )
                # )

    def apply_glow_effect_line(self, line, glow=False):
        if self.openPolygonButtonActivated:
            # ##print("inside apply glow effect line")
            if self.item_selected:
                self.del_current_line.set_color(GLOW_ANNOTATION_BOX_EDGE_COLOR)
                self.del_current_line.set_linewidth(LINE_WIDTH)
                # marker.set_visible(True)
            elif glow:
                line.set_color(POLY_GLOW_LINE_COLOR1)
                line.set_linewidth(
                   LINE_WIDTH
                )  # Adjust the width to your liking for the glow effect
            else:
                line.set_color(
                     POLY_GLOW_LINE_COLOR2
                )  # Change 'lime' to the original color of your lines
                line.set_linewidth(
                    LINE_WIDTH
                )  # Change LINE_WIDTH to the original linewidth of your lines

                self.canvas.draw_idle()

    # ---------------------------------------------------------------------------------

    # def load_image(self, image_path):
    #     self.dicom_image = pydicom.dcmread(image_path)
    #     self.py, self.px = self.dicom_image.PixelSpacing
    #     self.pixel_data = self.dicom_image.pixel_array
    #     self.axes.imshow(self.pixel_data, cmap="gray")
    #     self.canvas.draw_idle()

    def update_figure(self):
        if self.openPolygonButtonActivated:
            # #print("inside update figure")
            if hasattr(self, "temp_line") and self.temp_line in self.axes.lines:
                self.temp_line.remove()
                del self.temp_line

            if len(self.xs) > 1 and len(self.ys) > 1:
                curve_xs, curve_ys = self.calculate_bezier_curve(self.xs, self.ys)
                (self.temp_line,) = self.axes.plot(
                    curve_xs, curve_ys, "-", color=LINE_COLOR, linewidth=LINE_WIDTH
                )
            else:
                (self.temp_line,) = self.axes.plot(
                    self.xs, self.ys, "-", color=LINE_COLOR, linewidth=LINE_WIDTH
                )
            # self.axes.plot(self.xs, self.ys, 'o', color='lime', markeredgecolor='cornsilk', markerfacecolor='cornsilk', markersize=4.5)
            self.canvas.draw_idle()

    # Add this method to the PlotCanvas class
    def deselect_markers(self):
        if self.openPolygonButtonActivated:
            # #print("inside deselect markers")
            if (
                self.selected_prev_line is not None
            ):  # Check if selected_prev_line is not None
                self.selected_prev_line.set_color(LINE_COLOR)
                self.selected_prev_line.set_linewidth(LINE_WIDTH)
            for marker in self.selected_markers:
                marker.set_markeredgecolor(POLY_DESELECT_MARKER_COLOR)
                marker.set_markerfacecolor(POLY_DESELECT_MARKER_COLOR)
                marker.set_markersize(POLY_MARKER_SIZE)

            # line_to_hide = self.selected_prev_line
            # ##print(f"Hiding markers for line: {line_to_hide}")  # Debug ##print

            # for marker, line in self.previous_markers:
            #     if line == line_to_hide:
            #         ##print(f"Hiding marker: {marker}")  # Debug ##print
            #         marker.set_visible(False)
            # # line_to_hide=None
            # self.canvas.draw_idle()

            self.selected_markers.clear()  # Clear the list after reverting the colors

    def add_point(self, event):
        # print("openaddpoint")
        self.py, self.px = self.mainWindow.pixelSpacing
        self.imageIndex = self.getimageIndex()
        self.axes=self.getAxes()
        self.canvas=self.getCanvas()
        # #print("self.imageIndex", self.imageIndex)
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.openPolygonButtonActivated = self.getOpenActivation()
        if self.openPolygonButtonActivated:
            if event.button == Qt.LeftButton:
                if event.xdata is not None and event.ydata is not None:
                    if self.openPolygonButtonActivated:
                        # #print("inside add point")
                        # ##print("clicked_on_annotation:",clicked_on_annotation)
                        # ##print("hovering_over_line:",hovering_over_line)
                        if event.dblclick:
                            if len(self.xs) > 1:
                                # #print("double click")
                                self.finish_drawing()
                            return
                        # print("openafterreturn1")
                        clicked_on_annotation = False
                        for annot in self.previous_annot:
                            if  annot[1]!= self.imageIndex:
                                # print("found duplicateeeeeeeeeeeeeeeee")
                                continue
                            if  annot[2]!= self.canvasIndex:
                                # print("found duplicateeeeeeeeeeeeeeeee")
                                continue
                            try:
                                contains, _ = annot[0].contains(event)
                                if contains:
                                    clicked_on_annotation = True
                                    break
                            except:
                                pass

                        if clicked_on_annotation:
                            # #print("clicked on annotation")

                            return  # Do nothing when clicking on an existing annotation
                        # print("openafterreturn2")
                        hovering_over_line = False
                        for line in self.previous_sets:
                            if  line[1]!= self.imageIndex:
                                # print("found duplicateeeeeeeeeeeeeeeee")
                                continue
                            if  line[2]!= self.canvasIndex:
                                # print("found duplicateeeeeeeeeeeeeeeee")
                                continue
                            try:
                                if line[0].contains(event)[0]:
                                    hovering_over_line = True
                                    break
                            except:
                                pass

                        # to de-select the selected line by single click
                        if (
                            not clicked_on_annotation
                            and not hovering_over_line
                            and self.item_selected
                        ):
                            # #print("deselect the line")
                            self.deselect_markers()  # Deselect markers of the previously selected line

                            self.del_current_line = None
                            self.del_current_annot = None
                            self.item_selected = False
                            self.selected_prev_line = None

                            self.canvas.draw_idle()

                            return
                        
                        # print("openafterreturn3")
                        
                        # if event.inaxes != self.axes:
                        #     ##print("add point 2")

                        #     return

                        if not clicked_on_annotation and not hovering_over_line:
                            # #print("ix iy code")
                            ix, iy = event.xdata, event.ydata
                            # #print(ix)
                            # #print(iy)
                            self.xs.append(ix)
                            self.ys.append(iy)

                            # Store the marker
                            (marker,) = self.axes.plot(
                                ix,
                                iy,
                                "o",
                                color=LINE_COLOR,
                                markeredgecolor=POLY_DESELECT_MARKER_COLOR,
                                markerfacecolor=POLY_DESELECT_MARKER_COLOR,
                                markersize=POLY_MARKER_SIZE,
                            )
                            # #print("store the marker")
                            self.current_markers.append(
                                marker
                            )  # Keep track of the current markers

                            if self.last_point is not None:
                                temp_x = ix - self.last_point[0]
                                temp_y = iy - self.last_point[1]
                                line_length = np.sqrt(
                                    (temp_x * self.px) ** 2 + (temp_y * self.py) ** 2
                                )
                                self.length += line_length
                            self.last_point = (ix, iy)
                            self.update_figure()
                            self.display_length_annotation()
                        self.canvas.mpl_connect("button_press_event", self.add_point)

    # def calculate_bezier_curve(self, xs, ys, smoothness=1000):
    #     if self.openPolygonButtonActivated:
    #         # #print("inside calculate bezirer curve")
    #         if len(xs) < 3 or len(ys) < 3:
    #             return xs, ys
    #         points = np.array(list(zip(xs, ys)))
    #         t = np.linspace(0, 1, len(points))
    #         spline_x = make_interp_spline(t, points[:, 0], k=2)
    #         spline_y = make_interp_spline(t, points[:, 1], k=2)
    #         t_new = np.linspace(min(t), max(t), smoothness)
    #         xs_new = spline_x(t_new)
    #         ys_new = spline_y(t_new)
    #         return xs_new, ys_new

    def calculate_bezier_curve(self, xs, ys, smoothness=1000):
        if self.openPolygonButtonActivated:
            # Validation: Check if xs and ys are valid
            if not (np.all(np.isfinite(xs)) and np.all(np.isfinite(ys))):
                #print("Invalid values in xs or ys")
                return xs, ys  # Return the original points if invalid values are found

            if len(xs) < 3 or len(ys) < 3:
                return xs, ys

            points = np.array(list(zip(xs, ys)))
            t = np.linspace(0, 1, len(points))
            try:
                spline_x = make_interp_spline(t, points[:, 0], k=2)
                spline_y = make_interp_spline(t, points[:, 1], k=2)
            except ValueError as e:
                #print(f"Error in spline creation: {e}")
                return xs, ys  # Return the original points if spline creation fails

            t_new = np.linspace(min(t), max(t), smoothness)
            xs_new = spline_x(t_new)
            ys_new = spline_y(t_new)
            return xs_new, ys_new

    def display_length_annotation(self, drawing=False):
        if self.openPolygonButtonActivated:
            # #print("inside display length annotation")
            # Calculate the length string based on whether we are still drawing or not
            length_str = (
                "{:.2f} cm".format(self.length / 10.0)
                if self.length >= 10.0
                else "{:.2f} mm".format(self.length)
            )
            # if drawing:
            length_str_txt = length_str + self.double_click_text
            font_size = self.calculate_font_size(self.axes)  # Dynamically calculate the font size based on the axes
            if self.current_annot:
                self.current_annot.remove()
            self.current_annot = self.axes.text(
                self.xs[0] + 7,
                self.ys[0] + 3,
                length_str_txt,
                color=ANNOTATION_TEXT_COLOR,
                # fontsize=ANNOTATION_FONT_SIZE,
                fontsize=font_size
                # bbox=dict(
                #     facecolor=ANNOTATION_BOX_FACE_COLOR, edgecolor=ANNOTATION_BOX_EDGE_COLOR, boxstyle=ANNOTATION_BOX_STYLE
                # ),
            )
            self.current_annot.set_picker(True)
            self.canvas.draw_idle()

    def finish_drawing(self):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()

        line_markers=[]
        if self.openPolygonButtonActivated:
            # #print("inside finish drawing")
            if hasattr(self, "temp_line") and self.temp_line in self.axes.lines:
                self.temp_line.remove()
                del self.temp_line

            if len(self.xs) > 2 and len(self.ys) > 2:
                curve_xs, curve_ys = self.calculate_bezier_curve(self.xs, self.ys)
                (line,) = self.axes.plot(
                    curve_xs, curve_ys, "-", color=LINE_COLOR, linewidth=LINE_WIDTH
                )
            else:
                (line,) = self.axes.plot(
                    self.xs, self.ys, "-", color=LINE_COLOR, linewidth=LINE_WIDTH
                )

            # self.current_line=line
            for marker in self.current_markers:
                self.previous_markers.append((marker, line,self.imageIndex,self.canvasIndex))
            self.current_markers.clear()  # Clear the list of current markers after associating

            line.set_pickradius(5)  # 5 points tolerance
            if self.previous_markers:
                self.polygon_start_indices.append(len(self.previous_markers))
            # ##print("self.polygon_start_indices len:",self.polygon_start_indices)
            self.annot_to_line[self.current_annot] = line
            self.previous_sets.append([line,self.imageIndex,self.canvasIndex])
            for annot, assoc_line in self.annot_to_line.items():
                if assoc_line == line:
                    # ##print("self.annot_to_line:",annot.get_text())
                    # ##print(annot.get_text().replace("Double-click to finish drawing", '').strip())
                    annot.set_text(
                        annot.get_text().replace(self.double_click_text, "").strip()
                    )
                    break
            if self.current_annot:
                self.previous_annot.append([self.current_annot,self.imageIndex,self.canvasIndex])
                self.current_annot.set_picker(
                    True
                )  # Make sure the finished annotation is also selectable

            for marker, assoc_line, imageindex,canvasindex in self.previous_markers:
                if assoc_line == line:
                    line_markers.append(marker)
            
            self.uid=uuid.uuid4() # 4     
            conn = self.dbConnection()
            cur = conn.cursor()
            query = "SELECT EXISTS(SELECT 1 FROM oPolyData WHERE uuid = ?)"
            # Execute the query, replacing '?' with the new_uuid
            cur.execute(query, (str(self.uid),))
            exists = cur.fetchone()[0] 
            # self.text_id+=1
            if self.uid == exists:
                self.uid = uuid.uuid4()
            else :
                pass
            
            self.OpenPolyStorage(line,line_markers)
            self.polygon_id+=1
            self.xs, self.ys = [], []
            self.length = 0
            self.last_point = None
            self.hover_active = False  # Reset the hover flag
            self.current_annot = None

            self.canvas.draw_idle()

    def creatingOriginalDict(self,polygon_data_original):
        # Ensure the storage dictionary hierarchy is patientID -> patientSeriesName -> imageIndex -> list of polygons
        patient_polygons = self.openPolyStorageDictOriginal.setdefault(self.patientID, {})
        series_polygons = patient_polygons.setdefault(self.patientSeriesName, {})
        canvas_polygons = series_polygons.setdefault(self.canvasIndex, {})
        image_polygons = canvas_polygons.setdefault(self.imageIndex, [])
        # Append the current polygon data to the list of polygons for the current image
        image_polygons.append(polygon_data_original)

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

    def OpenPolyStorage(self, line, markers ,annotation=None, uid=None):
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.canvasIndex = self.getCanvaIndex()


        if uid is None:
            # Structure for storing polygon data
            polygon_data = {
                "id": self.polygon_id,
                "line": line,  # Reference to the matplotlib line object
                "markers": markers,  # List of marker objects associated with the polygon
                "annotation": {
                    "text": self.current_annot.get_text() if self.current_annot else "",
                    "position": self.current_annot.get_position() if self.current_annot else (0, 0),
               
                },
                "uuid":self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }
        else:
            polygon_data = {
                "id": self.polygon_id,
                "line": line,  # Reference to the matplotlib line object
                "markers": markers,  # List of marker objects associated with the polygon
                "annotation": {
                    "text": annotation.get_text() if annotation else "",
                    "position": annotation.get_position() if annotation else (0, 0)
                },
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex

            }

        if uid is None:
            # Structure for storing polygon data
            polygon_data_original = {
                "id": self.polygon_id,
                "line": self.custom_deepcopy(line),  # Reference to the matplotlib line object
                "markers": markers,  # List of marker objects associated with the polygon
                "annotation": {
                    "text": self.current_annot.get_text() if self.current_annot else "",
                    "position": self.current_annot.get_position() if self.current_annot else (0, 0),
               
                },
                "uuid":self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }
        else:
            polygon_data_original = {
                "id": self.polygon_id,
                "line": self.custom_deepcopy(line),  # Reference to the matplotlib line object
                "markers": markers,  # List of marker objects associated with the polygon
                "annotation": {
                    "text": annotation.get_text() if annotation else "",
                    "position": annotation.get_position() if annotation else (0, 0)
                },
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex

            }


        
        # Ensure the storage dictionary hierarchy is patientID -> patientSeriesName -> imageIndex -> list of polygons
        patient_polygons = self.openPolyStorageDict.setdefault(self.patientID, {})
        series_polygons = patient_polygons.setdefault(self.patientSeriesName, {})
        canvas_polygons = series_polygons.setdefault(self.canvasIndex, {})
        image_polygons = canvas_polygons.setdefault(self.imageIndex, [])
        # Append the current polygon data to the list of polygons for the current image
        image_polygons.append(polygon_data)

        self.creatingOriginalDict(polygon_data_original)
        
    

        # Debug #print to verify storage
        # print("OpenPolyStorageDict updated:", self.openPolyStorageDict)

        

    def givePolyStorageDict(self):
        return self.openPolyStorageDict
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
    def getOpenActivation(self):
        return self.mainWindow.giveOpenActivation()
    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()
    def calculate_font_size(self, ax):
        """Calculate font size based on the dimensions of the axes."""
        bbox = ax.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        height = bbox.height * self.figure.dpi  # Convert height to pixels
        # Adjust font size based on the height of the axes
        return max(6, min(12, height * 0.02)) 
       
    def update_annotation_font_sizes(self):
        """Update the font sizes of all annotations according to the new layout."""
        for ax in self.figure.axes:
            font_size = self.calculate_font_size(ax)
            for text in ax.texts:
                text.set_fontsize(font_size)
        self.canvas.draw_idle()

    def on_resize_event(self, event):
        """Handle the resize event to update font sizes."""
        self.update_annotation_font_sizes()
        self.display_length_annotation(drawing=True)  # Redisplay annotations with potentially updated positions
        self.canvas.draw_idle()