
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pydicom
from scipy.interpolate import make_interp_spline
from PyQt5.QtCore import Qt
import uuid
import sqlite3
from .constants import *
import copy



class ClosedPoly(FigureCanvas):
    def __init__(
        self,
        closedPolygonButtonActivated,
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
        self.closedPolygonButtonActivated = closedPolygonButtonActivated
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
        self.last_point = None
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
        self.closedPolyStorageDict={}
        self.closedPolyStorageDictOriginal={}

        self.mainWindow=parent
        self.polygon_id=0
        self.delDbList=[]

        

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
        self.double_click_text = " Double-click \nto finish drawing"
        self.polygon_measurements = (
            {}
        )  # Dictionary to store area and perimeter for each polygon
        self.A_P_current_annot = None
        self.length = 0
        self.area = 0
        self.closed = False
        self.closed_polygons = []  # List to store closed polygon coordinates
        self.current_polygon = {
            "xs": [],
            "ys": [],
        }  # Store coordinates for the current polygon
        self.setupEventConnections()

    def setupEventConnections(self):
        try:
            # Connect key press event
            self.canvas.mpl_connect("key_press_event", self.keyPressEvent)
        except:
            pass
    # ---------------------------------------------------------------------------------------------------------------------------------------------------------------
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
            if self.del_current_line or self.del_current_annot:
                self.del_current_line.remove()
                try:
                    for annotlist in self.previous_annot:
                        if annotlist[0]==self.del_current_annot:
                    
                        # self.previous_annot.remove(self.del_current_annot)
                            self.del_current_annot.remove()
                        
                            self.annot_to_line.pop(
                                self.del_current_annot, None
                            ) 
                            break # Remove the entry from the dictionary
                    # Remove the line from the previous_sets list
                    # self.previous_sets = [
                    #     line
                    #     for line in self.previous_sets
                    #     if line != self.del_current_line
                    # ]
                    # Also remove the markers associated with the line
                    markers_to_remove = [
                        (marker, line)
                        for marker, line, imageindex ,canvasindex in self.previous_markers
                        if line == self.del_current_line
                    ]
                    for marker, _ in markers_to_remove:
                        marker.remove() 
                        self.remove_close_polygon_from_storage()
                         # Remove the marker from the figure
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
        

    def on_mouse_press(self, event):
        # print('closepress')
        self.py, self.px = self.mainWindow.pixelSpacing
        self.ax=self.getAxes()
        self.canvas=self.getCanvas()
        self.imageIndex = self.getimageIndex()
        # #print("self.imageIndex", self.imageIndex)
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.closedPolygonButtonActivated = self.getCloseActivation()
        if self.closedPolygonButtonActivated:
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
                        self.canvas.draw_idle()
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
                            # #print("idx, marker, line:",idx, marker, line)
                            self.dragging_marker = True
                            self.selected_line=line
                            self.dragged_marker = (idx, marker, line)

                            for annot, assoc_line in self.annot_to_line.items():
                                if assoc_line == line:
                                    self.selected_annotation = annot
                                    break
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
                                    for marker, assoc_line, imageindex ,canvasindex in self.previous_markers
                                    if assoc_line == self.del_current_line
                                ]
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

    def on_mouse_motion(self, event):
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
            for patient_id, patient_data in self.closedPolyStorageDict.items():
                for series_name, series_data in patient_data.items():
                    for canvaId, canva in series_data.items():
                        for image_index, polygons in canva.items():

                            for polygon in polygons:
                                # Assuming the annotation text is unique and can be used as an identifier
                                if polygon["annotation"]["text"] == annot.get_text():
                                    # Update the annotation's position
                                    polygon["annotation"]["position"] = (new_x, new_y)
                                    return
            self.canvas.draw_idle()
            return  # Exit the function to avoid marker dragging logic when dragging annotations

        if self.dragging_marker and self.dragged_marker and self.selected_line:
            idx, marker, line = self.dragged_marker
            
            old_x, old_y = marker.get_data()
            dx = event.xdata - old_x
            dy = event.ydata - old_y
            marker.set_data(event.xdata, event.ydata)
           
            xs, ys = [], []
            for m, l,index, canvasindex  in self.previous_markers:
                if l == line:
                    x_data = m.get_xdata()
                    y_data = m.get_ydata()
                    # Handle both scalar and array cases
                    xs.append(x_data if np.isscalar(x_data) else x_data[0])
                    ys.append(y_data if np.isscalar(y_data) else y_data[0])
            # ##print("xs, ys:",xs, ys)
            xs = list(xs)
            ys = list(ys)
            # Close the polygon if it's a complete one
            if len(xs) > 2 and (xs[0], ys[0]) != (xs[-1], ys[-1]):
                xs.append(xs[0])
                ys.append(ys[0])
            line_index = next((i for i, v in enumerate(self.previous_sets) if v[0] == line), None)
            # Only move the annotation if the first marker of the line is being dragged
            first_marker = self.previous_markers[
                self.polygon_start_indices[line_index]
            ][0]
            # ##print("first_marker:",first_marker )
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

            # Check if the line is a closed polygon
            if self.is_polygon_closed(line):
                # Recalculate area and perimeter
                area, perimeter = self.calculate_area_and_perimeter(xs, ys)
                # Update annotation text
                # self.update_annotation_text(line, area, perimeter)
                # Update the annotation text for the given line
                for annot, assoc_line in self.annot_to_line.items():
                    if assoc_line == line:
                        self.area_perimeter_text = self.display_Area_Peri_measurement(
                            area, perimeter
                        )
                        #print("area_perimeter_text",self.area_perimeter_text)
                        annot.set_text(self.area_perimeter_text)
                        break
            update_marker=[]
            for markers, assoc_line, imageindex, canvasindex in self.previous_markers:
                if assoc_line == line:
                    if markers== marker:
                        markers.set_data(event.xdata, event.ydata)
                    update_marker.append(markers)
            self.update_polygon_vertices_in_storage(line=line, new_vertices=update_marker,area_perimeter_text=self.area_perimeter_text)

    def update_polygon_vertices_in_storage(self, line, new_vertices,area_perimeter_text):
        for patient_id, patient_data in self.closedPolyStorageDict.items():
            for series_name, series_data in patient_data.items():
                for canvaId, canva in series_data.items():
                    for image_index, polygons in canva.items():

                        for polygon in polygons:
                            #print("polygon['line']",polygon["line"])
                            #print("line",line)
                            if polygon["line"] == line:
                                polygon["annotation"]["text"]=area_perimeter_text
                                polygon["markers"] = new_vertices
                                polygon["line"] == line
                                    # Update the vertices list
                                return
                    
    def on_mouse_release(self, event):
        if self.drag_data:
            self.drag_data = None
        # Stop dragging the marker
        if self.dragging_marker:
            self.dragging_marker = False
            self.dragged_marker = None
            self.canvas.draw_idle()

    # ---------------------------------------------------------------------------------------------------------------------------------------------------------------

    def clicked_on_marker(self, event):
        # Iterate over the markers of the selected line
        for marker, line, imageindex, canvasindex in self.previous_markers:
            if line == self.del_current_line and marker.contains(event)[0]:
                return True  # Click was on a marker
        return False  # Click was not on a marker

    def clicked_on_annotation(self, event):
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

    def extract_coordinate(self, data):
        return data if np.isscalar(data) else data[0]

    def add_marker_to_selected_line(self, event):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()


        ix, iy = event.xdata, event.ydata
        # Existing logic for calculating distances and identifying the closest segment
        segment_distances = []
        segment_indices = []
        markers_on_line = [
            (marker, idx)
            for idx, (marker, assoc_line, imageindex,canvasindex) in enumerate(self.previous_markers)
            if assoc_line == self.del_current_line
        ]
        # #print("markers_on_line",markers_on_line)
        # #print("self.previous_markers",self.previous_markers)

        closing_segment = (markers_on_line[0][0], markers_on_line[-1][0])
        #print("closing_segment",closing_segment)
        if len(markers_on_line) > 1:
            closing_dist = self.point_to_segment_distance(
                ix,
                iy,
                self.extract_coordinate(closing_segment[0].get_xdata()),
                self.extract_coordinate(closing_segment[0].get_ydata()),
                self.extract_coordinate(closing_segment[1].get_xdata()),
                self.extract_coordinate(closing_segment[1].get_ydata()),
            )
            segment_distances.append(closing_dist)
            segment_indices.append((len(markers_on_line) - 1, 0))

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

        closest_segment_index = np.argmin(segment_distances)
        if segment_indices[closest_segment_index][1] == 0:
            insert_index = len(self.previous_markers)
        else:
            insert_index = segment_indices[closest_segment_index][0] + 1

        # Add the new marker
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
        self.selected_markers.append(new_marker)
        self.previous_markers.insert(insert_index, (new_marker, self.del_current_line,self.imageIndex,self.canvasIndex))

        # Convert tuples to lists for manipulation
        line_xs, line_ys = list(
            zip(
                *[
                    (
                        self.extract_coordinate(m.get_xdata()),
                        self.extract_coordinate(m.get_ydata()),
                    )
                    for m, l, index,canvasindex in self.previous_markers
                    if l == self.del_current_line
                ]
            )
        )
        line_xs = list(line_xs)
        line_ys = list(line_ys)
        marker_list=[]
        for marker in self.previous_markers:
            if marker[1]==self.del_current_line:
                marker_list.append(marker[0])

        #print("marker_list", marker_list)

        for patient_id, patient_data in self.closedPolyStorageDict.items():
            for series_name, series_data in patient_data.items():
                for canvaId, canva in series_data.items():
                    for image_index, polygons in canva.items():
                        for polygon in polygons:
                            if polygon["line"] == self.del_current_line:
                                polygon["markers"] = marker_list
                                #print("after insert points", self.closedPolyStorageDict)
                                return
                            
        
        # self.recalculate_line_length(self.del_current_line, line_xs, line_ys)
        self.figure.canvas.draw_idle()

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
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

    def is_polygon_closed(self, line):
        # Check if the first and last points of the line's data are the same
        xs, ys = line.get_data()
        return (xs[0], ys[0]) == (xs[-1], ys[-1])

   

    def calculate_area_and_perimeter(self, xs, ys):
        # Ensure there are enough points to form a polygon
        if len(xs) < 3 or len(ys) < 3:
            return 0, 0
        # Ensure the polygon is closed
        if xs[0] != xs[-1] or ys[0] != ys[-1]:
            xs = xs + [xs[0]]
            ys = ys + [ys[0]]
        # Calculate area using the Shoelace formula
        area = 0
        n = (
            len(xs) - 1
        )  # Number of vertices (excluding the duplicate of the first vertex)
        for i in range(n):
            area += xs[i] * ys[i + 1] - ys[i] * xs[i + 1]
        area = abs(area) / 2
        # Calculate perimeter
        perimeter = 0
        for i in range(n):
            dx = xs[i + 1] - xs[i]
            dy = ys[i + 1] - ys[i]
            perimeter += np.sqrt(dx * dx + dy * dy)
        # #print("inside calc", area, perimeter)
        return area, perimeter

    def on_hover(self, event):
        if event.inaxes != self.axes:
            return
        # Hide markers for all lines
        # print("onn hhoverrrrrr",self.previous_markers)
        for marker, line, imageindex,canvasindex  in self.previous_markers:
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
        self.canvas.draw_idle()

    def apply_glow_effect(self, annotation, glow=False):
        if annotation is None:
            return  # Do nothing if the annotation is None
        if glow:
            # annotation.set_bbox(
            #     dict(
                    # facecolor=HOVER_ANNOTATION_BACKGROUND_COLOR, edgecolor=HOVER_ANNOTATION_BOX_EDGE_COLOR, boxstyle=ANNOTATION_BOX_STYLE
                    annotation.set_color(HOVER_ANNOTATION_TEXT_COLOR)
            #         )
            # )
        else:
            # annotation.set_bbox(
                # dict(
                    # facecolor=ANNOTATION_BOX_FACE_COLOR, edgecolor=ANNOTATION_BOX_EDGE_COLOR, boxstyle=ANNOTATION_BOX_STYLE
                    annotation.set_color(ANNOTATION_TEXT_COLOR)
            #          )
            # )

    def apply_glow_effect_line(self, line, glow=False):
        if self.item_selected:
            self.del_current_line.set_color(POLY_HOVER_LINE_COLOR)
            self.del_current_line.set_linewidth(LINE_WIDTH)
            # marker.set_visible(True)
        elif glow:
            line.set_color(POLY_GLOW_LINE_COLOR1)
            line.set_linewidth(
               LINE_WIDTH
            )  # Adjust the width to your liking for the glow effect
        else:
            line.set_color(POLY_GLOW_LINE_COLOR2)  # Change 'lime' to the original color of your lines
            line.set_linewidth(
                LINE_WIDTH
            )  # Change 0.7 to the original linewidth of your lines
            self.canvas.draw_idle()

    # def load_image(self, image_path):
    #     self.dicom_image = pydicom.dcmread(image_path)
    #     self.py, self.px = self.dicom_image.PixelSpacing
    #     self.pixel_data = self.dicom_image.pixel_array
    #     self.axes.imshow(self.pixel_data, cmap="gray")
    #     self.draw()

    def update_figure(self):
        if hasattr(self, "temp_line") and self.temp_line in self.axes.lines:
            self.temp_line.remove()
            del self.temp_line

        if len(self.xs) > 1 and len(self.ys) > 1:
            curve_xs, curve_ys = self.calculate_bezier_curve(self.xs, self.ys)
            (self.temp_line,) = self.axes.plot(
                curve_xs, curve_ys, "-", color=POLY_GLOW_LINE_COLOR2, linewidth=LINE_WIDTH
            )
        else:
            (self.temp_line,) = self.axes.plot(
                self.xs, self.ys, "-", color=POLY_GLOW_LINE_COLOR2, linewidth=LINE_WIDTH
            )
        # self.axes.plot(self.xs, self.ys, 'o', color='lime', markeredgecolor='cornsilk', markerfacecolor='cornsilk', markersize=4.5)
        self.draw()

    # Add this method to the PlotCanvas class
    def deselect_markers(self):
        if (
            self.selected_prev_line is not None
        ):  # Check if selected_prev_line is not None
            self.selected_prev_line.set_color(POLY_GLOW_LINE_COLOR2)
            self.selected_prev_line.set_linewidth(LINE_WIDTH)
        for marker in self.selected_markers:
            marker.set_markeredgecolor(POLY_DESELECT_MARKER_COLOR)
            marker.set_markerfacecolor(POLY_DESELECT_MARKER_COLOR)
            marker.set_markersize(POLY_MARKER_SIZE)
        self.selected_markers.clear()  # Clear the list after reverting the colors

    def add_point(self, event):
        # print('closeaddpoint')
        self.py, self.px = self.mainWindow.pixelSpacing
        self.axes=self.getAxes()
        self.canvas=self.getCanvas()
        self.imageIndex = self.getimageIndex()
        # #print("self.imageIndex", self.imageIndex)
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.closedPolygonButtonActivated = self.getCloseActivation()
        if self.closedPolygonButtonActivated :
            if event.button == Qt.LeftButton:
                if event.dblclick:
                    # print("double clicked 1")
                    # #print("self.xs:",self.xs)
                    # if len(self.xs) > 1:
                    if len(self.xs) >= 3:
                        # print("double clicked 2")
                        # self.xs.append(self.xs[0])
                        # self.ys.append(self.ys[0])
                        self.finish_drawing()
                    else:
                        if self.closed_polygons : 
                            self.closed_polygons.pop()  
                            self.current_polygon = {"xs": [], "ys": []}  # Reset the current polygon
                    return
                # print('closeafterreturn1')
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
                    return  # Do nothing when clicking on an existing annotation
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
                if not clicked_on_annotation and not hovering_over_line and self.item_selected:
                    # #print("important")
                    self.deselect_markers()  # Deselect markers of the previously selected line
                    self.del_current_line = None
                    self.del_current_annot = None
                    self.item_selected = False
                    self.selected_prev_line = None
                    self.canvas.draw_idle()
                    return
                # print('closeafterreturn2')
                if event.inaxes != self.axes:
                    return
                # print('closeafterreturn3')
                if not clicked_on_annotation and not hovering_over_line:
                    ix, iy = event.xdata, event.ydata
                    self.xs.append(ix)
                    self.ys.append(iy)
                    self.current_polygon["xs"].append(ix)
                    self.current_polygon["ys"].append(iy)
                    # Store the marker
                    (marker,) = self.axes.plot(
                        ix,
                        iy,
                        "o",
                        color=POLY_GLOW_LINE_COLOR2,
                        markeredgecolor=POLY_DESELECT_MARKER_COLOR,
                        markerfacecolor=POLY_DESELECT_MARKER_COLOR,
                        markersize=POLY_MARKER_SIZE,
                    )
                    self.current_markers.append(marker)  # Keep track of the current markers
                    if self.last_point is not None:
                        temp_x = ix - self.last_point[0]
                        temp_y = iy - self.last_point[1]
                        line_length = np.sqrt((temp_x * self.px) ** 2 + (temp_y * self.py) ** 2)
                        self.length += line_length
                    self.last_point = (ix, iy)
                    self.update_figure()
                    if self.current_polygon["xs"]:
                        self.update_length_and_area()
                    self.display_length_annotation()
            # self.canvas.mpl_connect("button_press_event", self.add_point)

    def display_length_annotation(self, drawing=False):
        # Calculate the length string based on whether we are still drawing or not
        length_str = (
            "{:.2f} cm".format(self.length / 10.0)
            if self.length >= 10.0
            else "{:.2f} mm".format(self.length)
        )
        # if drawing:
        # #print("length_str:",length_str)
        # length_str_txt=length_str+self.double_click_text
        length_str_txt = self.double_click_text
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
            # bbox=dict(facecolor=ANNOTATION_BOX_FACE_COLOR, edgecolor=ANNOTATION_BOX_EDGE_COLOR, boxstyle=ANNOTATION_BOX_STYLE),
        )
        self.current_annot.set_picker(True)
        self.draw()

    def display_Area_Peri_measurement(self, A, P, drawing=False):
        area = A
        area_cm2 = round(area / 100, 2)
        perimeter = P
        if perimeter < 10.0:
            perimeter_str = "{:.2f}".format(perimeter) + " mm"
        else:
            perimeter_str = "{:.2f}".format(perimeter / 10.0) + " cm"
        area_str = "{:.2f}".format(area_cm2) + " cm2"
        text = f"Perimeter: {perimeter_str}\nArea: {area_str}"
        return text

    def update_length_and_area(self):
        # Calculate the area using the shoelace formula
        if len(self.closed_polygons) > 0:
            last_polygon = self.closed_polygons[-1]
            x = np.array(last_polygon["xs"])
            y = np.array(last_polygon["ys"])
            temp_x = np.dot(x, np.roll(y, 1))
            temp_y = np.dot(y, np.roll(x, 1))
            area = round(0.5 * np.abs((temp_x * self.px) - (temp_y * self.py)), 2)
            length = round(
                np.sum(np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2)) * self.px, 2
            )
            last_polygon["area"] = area
            last_polygon["perimeter"] = length
            return area, length

    def calculate_bezier_curve(self, xs, ys, smoothness=1000):
        # Make sure there are enough points to calculate the curve
        if len(xs) < 3 or len(ys) < 3:
            return xs, ys
        # The following adjustment assumes that the first and last points are the same for a closed polygon
        if (xs[0], ys[0]) == (xs[-1], ys[-1]):
            # Extend the points list for a smooth closed loop
            xs = np.r_[
                xs[-3:-1], xs, xs[1:3]
            ]  # Extend with the second-to-last and second points
            ys = np.r_[ys[-3:-1], ys, ys[1:3]]

            # Generate more points for the curve
            points = np.array(list(zip(xs, ys)))
            t = np.linspace(0, 1, len(points))
            spline_x = make_interp_spline(t, points[:, 0], k=2)
            spline_y = make_interp_spline(t, points[:, 1], k=2)
            t_new = np.linspace(
                t[2], t[-3], smoothness
            )  # Exclude the first and last two points for the final curve
            xs_new = spline_x(t_new)
            ys_new = spline_y(t_new)
        else:
            # Non-closed polygon or not enough points for a Bezier curve
            points = np.array(list(zip(xs, ys)))
            t = np.linspace(0, 1, len(points))
            spline_x = make_interp_spline(t, points[:, 0], k=2)
            spline_y = make_interp_spline(t, points[:, 1], k=2)
            t_new = np.linspace(0, 1, smoothness)
            xs_new = spline_x(t_new)
            ys_new = spline_y(t_new)
        # #print("xs_new, ys_new",xs_new, ys_new)    
        return xs_new, ys_new
    


    def remove_close_polygon_from_storage(self):
        self.imageIndex = self.getimageIndex()
        # Assuming each polygon's annotation text is unique and used as an identifier
        if self.del_current_annot:
            annot_text = self.del_current_annot.get_text()
            # Find and remove the polygon data from storage based on annotation text
            for image_polygons in self.closedPolyStorageDict.values():
                for series_polygons in image_polygons.values():
                    for canvaPoly in series_polygons.values():
                        for i, polygon in enumerate(canvaPoly.get(self.imageIndex, [])):
                            if polygon.get('annotation', {}).get('text') == annot_text:
                                self.delDbList.append(polygon['uuid'])
                                del canvaPoly[self.imageIndex][i]
                                return


    def finish_drawing(self):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()

        line_markers=[]

        if hasattr(self, "temp_line") and self.temp_line in self.axes.lines:
            self.temp_line.remove()
            del self.temp_line
        # Ensure the first and last points are the same (closed polygon)
        if len(self.xs) > 2 and (self.xs[0], self.ys[0]) != (self.xs[-1], self.ys[-1]):
            self.xs.append(self.xs[0])
            self.ys.append(self.ys[0])
        # Now create a Bezier curve for the closed polygon
        if (
            len(self.xs) > 3
            and len(self.ys) > 3
            and (self.xs[0], self.ys[0]) == (self.xs[-1], self.ys[-1])
        ):  # Ensure we have more than 3 points to form a curve
            curve_xs, curve_ys = self.calculate_bezier_curve(self.xs, self.ys)
            (line,) = self.axes.plot(
                curve_xs, curve_ys, "-", color=POLY_GLOW_LINE_COLOR2, linewidth=LINE_WIDTH
            )
        else:
            # If there are not enough points for a Bezier curve, just draw straight lines
            (line,) = self.axes.plot(self.xs, self.ys, "-", color=POLY_GLOW_LINE_COLOR2, linewidth=LINE_WIDTH)
        for marker in self.current_markers:
            self.previous_markers.append((marker, line, self.imageIndex,self.canvasIndex))

        #print("self.previous_marker",self.previous_markers)    
        self.current_markers.clear()  # Clear the list of current markers after associating
        line.set_pickradius(5)  # 5 points tolerance
        if self.previous_markers:
            self.polygon_start_indices.append(len(self.previous_markers))
        self.current_polygon["xs"].append(self.current_polygon["xs"][0])
        self.current_polygon["ys"].append(self.current_polygon["ys"][0])
        self.closed_polygons.append(self.current_polygon)
        self.current_polygon = {"xs": [], "ys": []}  # Reset the current polygon
        self.closed = True
        A, P = self.update_length_and_area()
        area_perimeter = self.display_Area_Peri_measurement(A, P)
        self.annot_to_line[self.current_annot] = line
        #print("self.annot_to_lines",self.annot_to_line)
        self.previous_sets.append([line,self.imageIndex,self.canvasIndex])
        #print(self.previous_sets)
        for annot, assoc_line in self.annot_to_line.items():
            if assoc_line == line:
                annot.set_text(
                    annot.get_text()
                    .replace(self.double_click_text, area_perimeter)
                    .strip()
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
        query = "SELECT EXISTS(SELECT 1 FROM cPolyData WHERE uuid = ?)"
        # Execute the query, replacing '?' with the new_uuid
        cur.execute(query, (str(self.uid),))
        exists = cur.fetchone()[0] 
        # self.text_id+=1
        if self.uid == exists:
            self.uid = uuid.uuid4()
        else :
            pass

        self.ClosedPolyStorage(line,line_markers)  # Call ClosedPolyStorage here
        self.polygon_id+=1
        area_perimeter = None
        self.xs, self.ys = [], []
        self.length = 0
        self.last_point = None
        self.hover_active = False  # Reset the hover flag
        self.current_annot = None
        self.closed = True
        self.canvas.draw()
    

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
            
    def creatingOriginalDict(self,polygon_data_original):
        patient_polygons = self.closedPolyStorageDictOriginal.setdefault(self.patientID, {})
        series_polygons = patient_polygons.setdefault(self.patientSeriesName, {})
        canva_polygons = series_polygons.setdefault(self.canvasIndex, {})
        image_polygons = canva_polygons.setdefault(self.imageIndex, [])
        image_polygons.append(polygon_data_original) 

    def ClosedPolyStorage(self,line,markers,annotation=None, uid=None):
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.canvasIndex = self.getCanvaIndex()

        if uid is None:
            polygon_data = {
                "id": self.polygon_id,
                "line":line,
                "markers": markers,  # List of (x, y) tuples for the polygon's vertices
            
                "annotation": {
                    "text": self.current_annot.get_text() if self.current_annot else "",
                    "position": self.current_annot.get_position() if self.current_annot else (0, 0)
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
            polygon_data_Original = {
                "id": self.polygon_id,
                "line":self.custom_deepcopy(line),
                "markers": markers,  # List of (x, y) tuples for the polygon's vertices
            
                "annotation": {
                    "text": self.current_annot.get_text() if self.current_annot else "",
                    "position": self.current_annot.get_position() if self.current_annot else (0, 0)
                },
                "uuid":self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex

            }
        else:
            polygon_data_Original = {
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


        
        # Retrieve or initialize the storage structure for the current patient, series, and image index
        patient_polygons = self.closedPolyStorageDict.setdefault(self.patientID, {})
        series_polygons = patient_polygons.setdefault(self.patientSeriesName, {})
        canva_polygons = series_polygons.setdefault(self.canvasIndex, {})
        image_polygons = canva_polygons.setdefault(self.imageIndex, [])
        image_polygons.append(polygon_data)  # Store the polygon data
        # print("ClosedPolyStorage",self.closedPolyStorageDict)

        self.creatingOriginalDict(polygon_data_Original)
        





# Example of usage
# Assuming 'closedPoly' is an instance of 'ClosedPoly'
# closedPoly = ClosedPoly(...)
# polygon_id = closedPoly.ClosedPolyStorage()
# Now 'closedPoly.closedPolyStorageDict' contains the stored polygon data



    def giveClosedPolyStorageDict(self):
        # #print("angle dict inside angle", self.angleStorageDict)
        return self.closedPolyStorageDict
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
    def getCloseActivation(self):
        return self.mainWindow.giveCloseActivation()
    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()
 
    def calculate_font_size(self, ax):
        """Calculate font size based on the dimensions of the axes."""
        bbox = ax.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        height = bbox.height * self.figure.dpi  # Convert height to pixels
        # Adjust font size based on the height of the axes
        return max(6, min(12, height * 0.02))  # Example scaling factor
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


# class MainWindow(QMainWindow):
#     def __init__(self, image_path):
#         super(MainWindow, self).__init__()
#         self.canvas = PlotCanvas(self, width=5, height=4)
#         self.canvas.mpl_connect('button_press_event', self.canvas.add_point)
#         self.canvas.load_image(image_path)
#         layout = QVBoxLayout()
#         layout.addWidget(self.canvas)
#         widget = QWidget()
#         widget.setLayout(layout)
#         self.setCentralWidget(widget)
#         self.setWindowTitle('Open Polygon')
#     def keyPressEvent(self, event):
#         self.canvas.keyPressEvent(event)  # Call the keyPressEvent method of the PlotCanvas
# app = QApplication(sys.argv)
# image_path = "case1_008.dcm"
# window = MainWindow(image_path)
# window.show()
# sys.exit(app.exec_())