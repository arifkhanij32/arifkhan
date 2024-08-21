
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patches as patches

import numpy as np

import matplotlib
import matplotlib.lines
from PyQt5.QtCore import Qt
import sqlite3
import uuid
from .constants import *
import traceback
import copy


class Ellipse(FigureCanvas):
    def __init__(
        self,
        ellipseButtonActivated,
        imgDCM,
        canvas,
        ax,
        figure,
        measurementToggle,
        processedDCM,
        fillToggle,
        parent,
    ):
        global ellipseHover
        ellipseHover = False
        # #print("ellipse1")

        self.ellipseButtonActivated = ellipseButtonActivated
        self.dicom_image = imgDCM
        self.py, self.px = self.dicom_image.PixelSpacing
        self.processedDCM = processedDCM
        self.pixel_data = self.dicom_image.pixel_array

        self.canvas = canvas
        self.mainWindow = parent
        self.fig = figure
        self.ax = ax
        self.showMeasurement = self.getMeasurementToggle()
        self.fillColor = self.getFillToggle()
        self.canvasIndex = self.getCanvaIndex()


        super().__init__(self.fig)


        self.setParent(parent)
        self.moving_marker = None
        self.moving_annotation = None
        self.moving_annotation_offset = (0, 0)
        self.setFocusPolicy(Qt.StrongFocus)
        self.startPoint = None
        # self.fillColor = False
        self.ellipse = None
        self.ellipses = []
        self.ellipse_data = {}
        self.selected_id=None

        self.selected_ellipse = None
        self.markers = []
        self.annotations = []
        self.text_annotation = None
        # self.showMeasurement = False
        self.hovered_ellipse = None
        self.moving_ellipse = None
        self.moving_ellipse_offset = (0, 0)
        self.markers_dict = {}
        self.text_annotations = []
        self.delDbList=[]

        # self.ellipse_annotation_map = {}
        # self.annotation_ellipse_map = {}
        # self.marker_ellipse_map = {}
        self.ellipse_id=1

        self.ellipseStorageDict={}
        self.ellipseStorageDictOriginal={}
        self.is_moving_ellipse = False
        # self.canvas.mpl_connect("key_press_event", self.keyPressEvent)

        # self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        # self.canvas.mpl_connect('button_press_event', self.on_press)
        # self.canvas.mpl_connect('motion_notify_event', self.on_move)
        # self.canvas.mpl_connect('button_release_event', self.on_release)
        self.setupEventConnections()

    def setupEventConnections(self):
        try:
            # Connect key press event
            self.canvas.mpl_connect("key_press_event", self.keyPressEvent)
        except:
            pass
##############################################################################################
    
    def dbConnection(self):
        mydb = sqlite3.connect("mainApplication.db")
        return mydb
    
    def getMeasurementToggle(self):
        return self.mainWindow.updatedMeasurementValue()

    def getFillToggle(self):
        return self.mainWindow.updatedFillValue()

    def on_hover(self, event):
        ellipseHover = False
        self.clear_highlights()

        if event.xdata is not None and event.ydata is not None:
            self.hoveredEllipseAnnot = None
            for id, data in self.ellipse_data.items():
                if (
                    id is None or data is None or data["markers"] is None
                ):  # Add this check
                    continue

                for marker in data["markers"]:
                    if self.is_near_marker(event, [marker]):
                        if data["annotation"]:
                            data["annotation"].set_color(HOVER_ANNOTATION_TEXT_COLOR)
                            #     dict(
                            #         facecolor=HOVER_ANNOTATION_BOX_FACE_COLOR,
                            #         alpha=0.5,
                            #         edgecolor=HOVER_ANNOTATION_BOX_EDGE_COLOR,
                            #         boxstyle=ANNOTATION_BOX_STYLE,
                            #     )
                            # )
                            # If yes, change the color of that marker only
                            marker.set_color(HOVER_MARKER_COLOR)
                            # self.fig.canvas.draw_idle()
                        # return

            for id, data in self.ellipse_data.items():
                if id is None:  # Add this check
                    continue
                ellipse =data["ellipse"]
                #print("ellipse on hover",ellipse)
                if self.is_near_edge(ellipse, event):
                    ellipseHover = not ellipseHover
                    # #print("ellipseHover :",ellipseHover)
                    self.highlight_elements(ellipse, data)
                    self.canvas.draw_idle()
                    # return

            for id, data in self.ellipse_data.items():
                if (
                    id is None or data is None or data["annotation"] is None
                ):  # Add this check
                    continue
                if data["annotation"]:
                    if self.is_near_text(event, data["annotation"]):
                        ellipse=data["ellipse"]
                        self.hoveredEllipseAnnot = data["annotation"]
                        self.highlight_elements(ellipse, data)
                        self.canvas.draw_idle()
                        # return

    def is_near_marker(self, event, markers, threshold=5):
        mouse_point = np.array([event.xdata, event.ydata])
        for marker in markers:
            # Ensure xdata and ydata are treated as iterables
            xdata = np.atleast_1d(marker.get_xdata())
            ydata = np.atleast_1d(marker.get_ydata())
            
            for x, y in zip(xdata, ydata):
                marker_point = np.array([x, y])
                distance = np.linalg.norm(mouse_point - marker_point)
                if distance < threshold:
                    return True
        return False
    
    # def is_near_marker(self, event, markers, threshold=5):
    #     mouse_point = np.array([event.xdata, event.ydata])
    #     for marker in markers:
    #         xdata, ydata = marker.get_xdata(), marker.get_ydata()
    #         for x, y in zip(xdata, ydata):
    #             marker_point = np.array([x, y])
    #             distance = np.linalg.norm(mouse_point - marker_point)
    #             if distance < threshold:
    #                 return True
    #     return False

    def is_near_text(self, event, annotation, threshold=10):
        if annotation is None:
            return False
        if event.xdata is not None and event.ydata is not None:
            # Get the bounding box of the annotation in display units
            bbox = annotation.get_window_extent()
            # Transform the bounding box to data coordinates
            bbox_data = bbox.transformed(self.ax.transData.inverted())
            # Inflate the bounding box by the threshold to create a larger hit area
            bbox_data_expanded = bbox_data.expanded(
                1 + threshold / bbox_data.width, 1 + threshold / bbox_data.height
            )
            return bbox_data_expanded.contains(event.xdata, event.ydata)
        else:
            return False

    def is_near_edge(self, ellipse, event):
        threshold = 2
        if ellipse is None:
            return False
        if not event.xdata or not event.ydata and ellipse is None :
            return False
        #print("ellipse",ellipse)
        center_x, center_y = ellipse.center
        rx, ry = ellipse.width / 2, ellipse.height / 2
        # Check for zero or very small ellipse to avoid division by zero
        if rx < 1e-6 or ry < 1e-6:
            return False
        dx, dy = event.xdata - center_x, event.ydata - center_y
        distance = ((dx / rx) ** 2 + (dy / ry) ** 2) ** 0.5
        return distance <= 1 + threshold / min(
            rx, ry
        ) and distance >= 1 - threshold / min(rx, ry)

    def highlight_elements(self, ellipse, data):
        if ellipse is None or data is None :
            return
        if ellipse != self.selected_ellipse:
            # print("hoveerrerrr")
            data["ellipse"].set_edgecolor("yellow")
            if data["annotation"] is not None:
                data["annotation"].set_color(HOVER_ANNOTATION_TEXT_COLOR)
                #     dict(
                #         facecolor=HOVER_ANNOTATION_BACKGROUND_COLOR,
                #         alpha=0.5,
                #         edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                #         boxstyle=ANNOTATION_BOX_STYLE,
                #     )
                # )
            for marker in data["markers"]:
                marker.set_color(MARKER_COLOR)

    def clear_highlights(self):
        for id, data in self.ellipse_data.items():
            if id is None or data is None :
                continue
            ellipse=data["ellipse"]
            if ellipse != self.selected_ellipse:
                if data["ellipse"] is not None:
                    data["ellipse"].set_edgecolor("lime")
                if data["annotation"] is not None:
                    data["annotation"].set_color(ANNOTATION_TEXT_COLOR)
                        # dict(
                        #     facecolor=ANNOTATION_BOX_FACE_COLOR,
                        #     alpha=0.5,
                        #     edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                        #     boxstyle=ANNOTATION_BOX_STYLE,
                        # )
                    # )
                for marker in data["markers"]:
                    marker.set_color(MARKER_COLOR)
        self.canvas.draw_idle()

    def highlight_selected_ellipse(self):
        if self.selected_ellipse:
            data = self.ellipse_data[self.selected_id]
            ellipse=data["ellipse"]
            ellipse.set_edgecolor(ELLIPSE_EDGE_COLOR)

            if data["annotation"]:
                data["annotation"].set_color(SELECTION_ANNOTATION_TEXT_COLOR)
                #     dict(
                #         facecolor=SELECTED_ANNOTATION_FACE_COLOR,
                #         alpha=0.5,
                #         edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                #         boxstyle=ANNOTATION_BOX_STYLE,
                #     )
                # )
            for marker in data["markers"]:
                marker.set_color(SELECTED_MARKER_COLOR)
            self.canvas.draw_idle()

    def reset_ellipse_highlight(self, id):
        if id is None:
            return
        data = self.ellipse_data.get(id, None)
        ellipse=data["ellipse"]
        if data:
            ellipse.set_edgecolor(RESET_ELLIPSE_EDGE_COLOR)
            if data["annotation"]:
                data["annotation"].set_color(ANNOTATION_TEXT_COLOR)
                #     dict(
                #         facecolor=ANNOTATION_BOX_FACE_COLOR,
                #         alpha=0.5,
                #         edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                #         boxstyle=ANNOTATION_BOX_STYLE,
                #     )
                # )
            for marker in data["markers"]:
                marker.set_color(MARKER_COLOR)
        self.canvas.draw_idle()


        
    def keyPressEvent(self, event):
        # if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
        if type(event.key) == str:
            if event.key.lower().strip() == "delete".lower().strip():
                event.key = 16777223
        else:
            pass
        if str(event.key) == str(Qt.Key_Delete):
            if self.selected_ellipse:
                self.remove_selected_ellipse()
                self.canvas.draw_idle()

    def remove_selected_ellipse(self):
        # print("ellipse delete 1")
        if self.selected_ellipse:
            self.remove_ellipse_from_storage(self.selected_id)

            if self.selected_ellipse in self.ax.patches:
                self.selected_ellipse.remove()
            data = self.ellipse_data.pop(self.selected_id, {})
            if data.get("annotation"):
                data["annotation"].remove()
            for marker in data.get("markers", []):
                marker.remove()

            self.selected_ellipse = None
            self.canvas.draw_idle()

    def remove_ellipse_from_storage(self, ellipse_id):
    # Check if the patient ID level exists
        if self.patientID in self.ellipseStorageDict:
            # Check if the patient series name level exists
            if self.patientSeriesName in self.ellipseStorageDict[self.patientID]:
                if self.canvasIndex in self.ellipseStorageDict[self.patientID][self.patientSeriesName]:
                    # Check if the image index level exists
                    if self.imageIndex in self.ellipseStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex]:
                        # Get the list of ellipses for the current image
                        ellipse_info_list = self.ellipseStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex]
                        for (index, d) in enumerate(ellipse_info_list):
                            if d["id"] == ellipse_id:
                                self.delDbList.append(d["uuid"])
                        # #print("ellipse del",self.delDbList)
                        # Find the index of the ellipse with the given ID
                        ellipse_index = next((index for (index, d) in enumerate(ellipse_info_list) if d["id"] == ellipse_id), None)
                        
                        # If the ellipse is found, remove it
                        if ellipse_index is not None:
                            del ellipse_info_list[ellipse_index]
                            
                            # If the list of ellipses is now empty, you might want to remove the entry for the imageIndex as well
                            # if not ellipse_info_list:
                            #     del self.ellipseStorageDict[self.patientID][self.patientSeriesName][self.imageIndex]
                                # Further cleanup could be done here if the series or patient levels are now empty

                            # #print(f"Removed ellipse with ID {ellipse_id} from storage.")

    def on_press(self, event):
        self.py, self.px = self.mainWindow.pixelSpacing
        self.showMeasurement = self.getMeasurementToggle()
        self.ax=self.getAxes()
        self.canvas=self.getCanvas()
        self.canvasIndex = self.getCanvaIndex()
        # if self.lineButtonActivated:
        # #print("sm L", sMeasurementToggle)
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        # #print("image no",self.imageIndex)
        self.fillColor = self.getFillToggle()
        self.ellipseButtonActivated=self.getEllipseActivation()
        if self.ellipseButtonActivated:
            # #print("self.imageIndex", self.imageIndex)
            if event.button == Qt.LeftButton:
                if event.xdata is not None and event.ydata is not None:
                    if self.selected_ellipse:
                        self.reset_ellipse_highlight(self.selected_id)
                        self.selected_ellipse=None
                    self.selected_id = None
                    for id, data in self.ellipse_data.items():
                        if 'image_index' in data and data['image_index'] != self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        if 'canvas_index' in data and data['canvas_index'] != self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                        if id is None:  # Add this check
                            continue
                        ellipse=data["ellipse"]
                        if self.is_near_edge(ellipse, event):
                            self.is_moving_ellipse = True 
                            self.selected_id=id # Mark that we are moving an ellipse
                            self.moving_ellipse_offset = (
                                ellipse.center[0] - event.xdata,
                                ellipse.center[1] - event.ydata,
                            )
                            self.selected_ellipse = ellipse
                            self.highlight_selected_ellipse()
                            return
                        
                    for id, data in self.ellipse_data.items():
                        if data["ellipse"] is None or data["markers"] is None:
                            continue
                        if 'image_index' in data and data['image_index'] != self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                        if 'canvas_index' in data and data['canvas_index'] != self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        ellipse=data["ellipse"]
                        for marker in data["markers"]:
                            if self.is_near_marker(event, [marker], threshold=5):
                                self.selected_ellipse = ellipse
                                self.selected_id=id
                                self.moving_marker = marker
                                return

                    for id, data in self.ellipse_data.items():
                        if data["ellipse"] is None or data["annotation"] is None:  # Add this check
                            continue
                        if 'image_index' in data and data['image_index'] != self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                        if 'canvas_index' in data and data['canvas_index'] != self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        ellipse=data["ellipse"]
                        if self.is_near_text(event, data["annotation"]):
                            self.moving_annotation = (id, data["annotation"])
                            self.selected_id=id
                            self.moving_annotation_offset = (
                                event.xdata - data["annotation"].get_position()[0],
                                event.ydata - data["annotation"].get_position()[1],
                            )
                            self.selected_ellipse = ellipse
                            self.highlight_selected_ellipse()
                            #print("ellipsesssssss",self.ellipseStorageDict)
                            return
                        

                    if not self.moving_marker:
                        self.startPoint = (event.xdata, event.ydata)
                        self.ellipse = None

                    if self.text_annotation and self.showMeasurement:
                        self.text_annotation.set_text("")
                        self.text_annotation = None

                    if self.markers:
                        for marker in self.markers:
                            if isinstance(marker, matplotlib.lines.Line2D):
                                marker.remove()
                        self.markers.clear()

    def on_move(self, event):
        try:
            self.showMeasurement = self.getMeasurementToggle()
            self.fillColor = self.getFillToggle()
            if self.moving_marker and self.selected_ellipse:
                new_width, new_height, new_center = self.calculate_ellipse_size_from_marker(
                    event
                )

                self.selected_ellipse.width = new_width
                self.selected_ellipse.height = new_height
                self.selected_ellipse.center = new_center

                # Update marker positions
                self.update_marker_positions(new_width, new_height, new_center)

                width, height = self.selected_ellipse.width, self.selected_ellipse.height
                center_x, center_y = (
                    self.selected_ellipse.center[0],
                    self.selected_ellipse.center[1],
                )

                stat_str, pixel_count = self.calculate_statistics(
                    center_x, center_y, width, height
                )
                area = self.area_measure(width, height)
                # Update annotation
                data = self.ellipse_data[self.selected_id]

                if data["annotation"]:
                    final_str = stat_str + "\n" + area + " (" + str(pixel_count) + " px)"
                    data["annotation"].set_text(final_str)

                ellipse_info_list = self.ellipseStorageDict.get(self.patientID, {})\
                                                    .get(self.patientSeriesName, {})\
                                                    .get(self.canvasIndex, {})\
                                                    .get(self.imageIndex, [])
                
                for ellipse_info in ellipse_info_list:
                    if ellipse_info["id"] == self.selected_id:
                        # Update the ellipse dimensions and center
                        ellipse = ellipse_info["ellipse"]
                        ellipse.width, ellipse.height = self.selected_ellipse.width, self.selected_ellipse.height
                        ellipse.center = self.selected_ellipse.center

                        self.update_marker_positions_in_storage(new_width, new_height, new_center)
                        
                    # Update annotation with new statistics and area
                        if ellipse_info["annotation"]:
                        
                            if not data["annotation_moved"]:
                                if data["annotation"]:
                                    # Calculate new annotation position
                                    annotation_x = new_center[0] + new_width / 2
                                    annotation_y = new_center[1] + new_height / 2
                                    
                                    center_x, center_y = ellipse.center
                                    width, height = ellipse.width, ellipse.height
                                    stat_str, pixel_count = self.calculate_statistics(center_x, center_y, width, height)
                                    area = self.area_measure(width, height)
                                    final_str = stat_str + "\n" + area + " (" + str(pixel_count) + " px)"
                                    ellipse_info["annotation"].set_text(final_str)
                                    ellipse_info["annotation"].set_position((annotation_x, annotation_y))
                            
                                    break 
                self.canvas.draw_idle()

            if (
                self.moving_annotation
                and event.xdata is not None
                and event.ydata is not None
            ):
                id, annotation = self.moving_annotation
                new_x = event.xdata - self.moving_annotation_offset[0]
                new_y = event.ydata - self.moving_annotation_offset[1]
                annotation.set_position((new_x, new_y))
                data = self.ellipse_data.get(id, {})
                data["annotation_moved"] = True
                self.highlight_selected_ellipse()
                ellipse_info_list = self.ellipseStorageDict.get(self.patientID, {}).get(self.patientSeriesName, {}).get(self.canvasIndex, {}).get(self.imageIndex, [])
                for ellipse_info in ellipse_info_list:
                    if ellipse_info["id"] == id:
                        # Update the annotation position
                        # This assumes that the annotation object or its position data is directly stored and accessible
                        ellipse_info["annotation"].set_position((new_x, new_y))
                        ellipse_info["annotation_moved"] = True
                        break  # Found the target annotation, no need to continue

            self.canvas.draw_idle()

            if (
                self.is_moving_ellipse
                and self.selected_ellipse
                and event.xdata is not None
                and event.ydata is not None
            ):
                # Calculate the change in position
                dx = (
                    event.xdata
                    + self.moving_ellipse_offset[0]
                    - self.selected_ellipse.center[0]
                )
                dy = (
                    event.ydata
                    + self.moving_ellipse_offset[1]
                    - self.selected_ellipse.center[1]
                )
                xlims = self.ax.get_xlim()
                ylims = self.ax.get_ylim()

                
                
                # Update the position of the ellipse
                new_center_x = self.selected_ellipse.center[0] + dx
                new_center_y = self.selected_ellipse.center[1] + dy

                left_edge = new_center_x - self.selected_ellipse.width / 2
                right_edge = new_center_x + self.selected_ellipse.width / 2
                bottom_edge = new_center_y - self.selected_ellipse.height / 2
                top_edge = new_center_y + self.selected_ellipse.height / 2

                if left_edge < xlims[0] or right_edge > xlims[1] or bottom_edge < ylims[1] or top_edge > ylims[0]:
                    return
                
                self.selected_ellipse.center = (new_center_x, new_center_y)

                width, height = self.selected_ellipse.width, self.selected_ellipse.height
                center_x, center_y = (
                    self.selected_ellipse.center[0],
                    self.selected_ellipse.center[1],
                )

                stat_str, pixel_count = self.calculate_statistics(
                    center_x, center_y, width, height
                )
                area = self.area_measure(width, height)
                
                # Update the position of the annotation
                data = self.ellipse_data[self.selected_id]
                if data["annotation"]:
                    final_str = stat_str + "\n" + area + " (" + str(pixel_count) + " px)"
                    data["annotation"].set_text(final_str)
                
                if not data["annotation_moved"]:
                    if data["annotation"]:
                        annotation_x, annotation_y = data["annotation"].get_position()
                        data["annotation"].set_position(
                            (annotation_x + dx, annotation_y + dy)
                        )

                # Update the position of the markers
                for marker in data["markers"]:
                    marker.set_xdata(marker.get_xdata() + dx)
                    marker.set_ydata(marker.get_ydata() + dy)

                for patient_id, patient_data in self.ellipseStorageDict.items():
                    for series_name, series_data in patient_data.items():
                        for canva_id, canva in series_data.items():
                            for image_index, ellipse_info_list in canva.items():
                
                                for ellipse_info in ellipse_info_list:
                                    if ellipse_info["id"] == self.selected_id:
                                        ellipse=ellipse_info["ellipse"]
                                        # Update ellipse center if you store it
                                        ellipse_info["ellipse"].center = (new_center_x, new_center_y)
                                        center_x, center_y = ellipse.center
                                        width, height = ellipse.width, ellipse.height
                                        stat_str, pixel_count = self.calculate_statistics(center_x, center_y, width, height)
                                        area = self.area_measure(width, height)
                                        final_str = stat_str + "\n" + area + " (" + str(pixel_count) + " px)"
                                        # print("final str",final_str)
                                        if ellipse_info["annotation"] is not None:
                                            ellipse_info["annotation"].set_text(final_str)
                                        # Update markers' positions
                                        for i, stored_marker in enumerate(ellipse_info["markers"]):
                                            # Assuming markers are matplotlib objects in the list
                                            # new_x, new_y = data["markers"][i].get_xdata()[0], data["markers"][i].get_ydata()[0]
                                            xdata = np.atleast_1d(data["markers"][i].get_xdata())
                                            ydata = np.atleast_1d(data["markers"][i].get_ydata())

                                            # Assuming there should only be one point per marker, use the first element.
                                            # This is safe as np.atleast_1d ensures xdata and ydata are arrays.
                                            new_x = xdata[0]
                                            new_y = ydata[0]
                                            stored_marker.set_xdata(new_x)
                                            stored_marker.set_ydata(new_y)
                                        
                                        # Update the annotation position if it wasn't manually moved
                                        if not ellipse_info["annotation_moved"] and ellipse_info["annotation"]:
                                            ellipse_info["annotation"].set_position((annotation_x + dx, annotation_y + dy))
                                        
                                        break  # Found and updated the target ellipse, no need to continue

                self.canvas.draw_idle()
                self.canvas.mpl_connect("button_press_event", self.on_press)
                self.canvas.mpl_connect("motion_notify_event", self.on_move)
            
                self.canvas.draw_idle()

            if self.is_moving_ellipse and self.selected_ellipse and event.xdata is not None and event.ydata is not None:
                # Calculate new center based on movement
                new_center_x = event.xdata + self.moving_ellipse_offset[0]
                new_center_y = event.ydata + self.moving_ellipse_offset[1]

                # Update the ellipse's position
                self.selected_ellipse.center = (new_center_x, new_center_y)

                self.canvas.draw_idle()

            if self.startPoint is not None:
                if (
                    event.xdata is not None
                    and event.ydata is not None
                    and self.startPoint is not None
                ):
                    if self.text_annotation and self.showMeasurement:
                        self.text_annotation.set_text("")

                    if self.markers:
                        for marker in self.markers:
                            marker.remove()
                        self.markers.clear()

                    if self.ellipse:
                        self.ellipse.remove()
                        # self.ellipse=None

                    # self.showMeasurement = True # Change here for showmeasurement
                    eventType = "Move"
                    self.draw_ellipse(
                        event, showMeasurement=self.showMeasurement, eventType=eventType
                    )
                    self.canvas.draw_idle()
        except:
            print(traceback.format_exc())

    
    def on_release(self, event):
        self.imageIndex = self.getimageIndex()
        self.showMeasurement = self.getMeasurementToggle()
        self.fillColor = self.getFillToggle()
        self.canvasndex=self.getCanvaIndex()
        if self.moving_annotation:
           id, annotation = self.moving_annotation
           data = self.ellipse_data.get(id, {})
           data["annotation"] = annotation

           self.moving_annotation = None
           self.canvas.draw_idle()

        if self.moving_marker:
            self.moving_marker = None
        if self.is_moving_ellipse:
            self.is_moving_ellipse = False
            self.canvas.draw_idle()

        if (
            event.xdata is not None
            and event.ydata is not None
            and self.startPoint is not None
        ):
            # #print("self.ellipse",self.ellipse)
            self.ellipse_data[self.ellipse_id] = { 
                "ellipse":self.ellipse,
                "annotation": self.text_annotation,
                "markers": self.markers,
                "annotation_moved": False,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }
            # self.ellipse_data[self.ellipse] = self.ellipse_data
            # #print("self.ellipse_data",self.ellipse_data)
            # #print("self.ellipse_data[id]['ellipse']",self.ellipse_data[self.ellipse_id]["ellipse"])

            self.uid=uuid.uuid4() # 4     
            conn = self.dbConnection()
            cur = conn.cursor()
            query = "SELECT EXISTS(SELECT 1 FROM ellipseData WHERE uuid = ?)"
            # Execute the query, replacing '?' with the new_uuid
            cur.execute(query, (str(self.uid),))
            exists = cur.fetchone()[0] 
            # self.text_id+=1
            if self.uid == exists:
                self.uid = uuid.uuid4()
            else :
                pass

            # Call ellipseStorage here to save the current state
            self.ellipseStorage(self.ellipse, self.markers, self.text_annotation)
            self.ellipse_id+=1
            self.startPoint = None
            self.ellipse = None
            self.text_annotation = None
            self.markers = []
            self.canvas.draw_idle()
        self.moving_marker = None

    def update_marker_positions(self, new_width, new_height, new_center):
       
        # Calculate the positions of the four corners of the ellipse's bounding box
        half_width = new_width / 2
        half_height = new_height / 2
        top_right = (new_center[0] + half_width, new_center[1] - half_height)
        top_left = (new_center[0] - half_width, new_center[1] - half_height)
        bottom_right = (new_center[0] + half_width, new_center[1] + half_height)
        bottom_left = (new_center[0] - half_width, new_center[1] + half_height)

        data = self.ellipse_data[self.selected_id]
        if not data["annotation_moved"]:
            if data["annotation"]:
                # Calculate new annotation position
                annotation_x = new_center[0] + new_width / 2
                annotation_y = new_center[1] + new_height / 2
                data["annotation"].set_position((annotation_x, annotation_y))
            # Update the position of each marker

        markers = self.ellipse_data[self.selected_id]["markers"]
        if len(markers) == 4:
            markers[0].set_xdata([top_right[0]])
            markers[0].set_ydata([top_right[1]])
            
            markers[1].set_xdata([top_left[0]])
            markers[1].set_ydata([top_left[1]])
          


            markers[2].set_xdata([bottom_right[0]])
            markers[2].set_ydata([bottom_right[1]])
            


            markers[3].set_xdata([bottom_left[0]])
            markers[3].set_ydata([bottom_left[1]])
            

    def update_marker_positions_in_storage(self, new_width, new_height, new_center):
    # Retrieve the list of ellipses for the current image
        
        ellipse_info_list = self.ellipseStorageDict.get(self.patientID, {})\
                                                    .get(self.patientSeriesName, {})\
                                                    .get(self.canvasIndex, {})\
                                                    .get(self.imageIndex, [])

        for ellipse_info in ellipse_info_list:
            if ellipse_info["id"] == self.selected_id:
                # Calculate the positions of the four corners of the ellipse's bounding box
                half_width = new_width / 2
                half_height = new_height / 2
                top_right = (new_center[0] + half_width, new_center[1] - half_height)
                top_left = (new_center[0] - half_width, new_center[1] - half_height)
                bottom_right = (new_center[0] + half_width, new_center[1] + half_height)
                bottom_left = (new_center[0] - half_width, new_center[1] + half_height)

                # Update the position of each marker in the storage
                markers = ellipse_info.get("markers", [])
                if len(markers) == 4:
                    markers[0].set_data(top_right[0], top_right[1])
                    markers[1].set_data(top_left[0], top_left[1])
                    markers[2].set_data(bottom_right[0], bottom_right[1])
                    markers[3].set_data(bottom_left[0], bottom_left[1])

                break  # Exit loop after updating the selected ellipse    

    def calculate_ellipse_size_from_marker(self, event):
        # Get current ellipse properties
        center_x, center_y = self.selected_ellipse.center
        width = self.selected_ellipse.width
        height = self.selected_ellipse.height
        half_width = width / 2
        half_height = height / 2

        # Determine which marker is being moved
        moving_marker_index = self.ellipse_data[self.selected_id]["markers"].index(
            self.moving_marker
        )
        #print("moving_marker_index",moving_marker_index)
        # Calculate new width, height, and center based on the marker being moved

        if moving_marker_index == 0:
            # Top Right marker
            new_width = max(event.xdata - (center_x - half_width), 1)
            new_height = max((center_y + half_height) - event.ydata, 1)

        elif moving_marker_index == 1:  # Top Left marker
            new_width = max((center_x + half_width) - event.xdata, 1)
            new_height = max((center_y + half_height) - event.ydata, 1)

        elif moving_marker_index == 2:  # Bottom Right marker
            new_width = max(event.xdata - (center_x - half_width), 1)
            new_height = max(event.ydata - (center_y - half_height), 1)

        elif moving_marker_index == 3:  # Bottom Left marker
            new_width = max((center_x + half_width) - event.xdata, 1)
            new_height = max(event.ydata - (center_y - half_height), 1)

        # Calculate new center
        new_center_x = center_x + (new_width - width) / 2 * (
            -1 if moving_marker_index in [1, 3] else 1
        )
        new_center_y = center_y + (new_height - height) / 2 * (
            -1 if moving_marker_index in [0, 1] else 1
        )

        return new_width, new_height, (new_center_x, new_center_y)

    def draw_ellipse(self, event, showMeasurement, eventType):
        width = abs(event.xdata - self.startPoint[0])
        height = abs(event.ydata - self.startPoint[1])
        center_x = (event.xdata + self.startPoint[0]) / 2
        center_y = (event.ydata + self.startPoint[1]) / 2

        self.set_ellipse_vertices(event, width, height)

        if self.fillColor:
            self.ellipse = patches.Ellipse(
                (center_x, center_y), width, height, edgecolor=FILL_COLOR, facecolor=FILL_COLOR
            )
        else:
            self.ellipse = patches.Ellipse(
                (center_x, center_y), width, height, edgecolor=FILL_COLOR, facecolor="None"
            )

        self.ax.add_patch(self.ellipse)
        self.ellipse.set_zorder(2)

        if showMeasurement:
            stat_str, pixel_count = self.calculate_statistics(
                center_x, center_y, width, height
            )
            area = self.area_measure(width, height)
            self.final_str = stat_str + "\n" + area + " (" + str(pixel_count) + " px)"
            annotation_x = center_x + width / 2
            annotation_y = center_y + height / 2
            font_size = self.calculate_font_size(self.ax)
            self.text_annotation = self.ax.text(
                annotation_x, annotation_y, self.final_str,
                #  fontsize=ANNOTATION_FONT_SIZE,
                fontsize=font_size,  # Set the font size dynamically
                 color=ANNOTATION_TEXT_COLOR
            )
            self.text_annotation.set_color(ANNOTATION_TEXT_COLOR)
            #     dict(
            #         facecolor=ANNOTATION_BOX_FACE_COLOR,
            #         alpha=0.5,
            #         edgecolor=ANNOTATION_BOX_EDGE_COLOR,
            #         boxstyle=ANNOTATION_BOX_STYLE,
            #     )
            # )
            self.text_annotations.append(self.text_annotation)
        self.markers = [self.ax.plot(x, y, "r+",markersize=MARKER_SIZE)[0] for x, y in self.points]
            

        self.canvas.draw_idle()
        # for marker in self.markers:
        #     self.marker_ellipse_map[marker] = self.ellipse

    def set_ellipse_vertices(self, event, width, height):
        # Determine the coordinates of the bounding rectangle of the ellipse
        rect_x_min = min(self.startPoint[0], event.xdata)
        rect_x_max = max(self.startPoint[0], event.xdata)
        rect_y_min = min(self.startPoint[1], event.ydata)
        rect_y_max = max(self.startPoint[1], event.ydata)

        # Define the corners of the rectangle
        self.top_left = (rect_x_min, rect_y_min)
        self.top_right = (rect_x_max, rect_y_min)
        self.bottom_left = (rect_x_min, rect_y_max)
        self.bottom_right = (rect_x_max, rect_y_max)

        # Add other conditions for different cases
        self.points = [
            self.top_right,
            self.top_left,
            self.bottom_right,
            self.bottom_left,
        ]

    def calculate_statistics(self, center_x, center_y, width, height):
        try:
            if self.pixel_data is not None:
                semi_major_axis = width / 2
                semi_minor_axis = height / 2

                if semi_major_axis == 0 or semi_minor_axis == 0:
                    # Handle the case where the ellipse dimensions are too small
                    return "Invalid ellipse dimensions", 0

                # Create a meshgrid of x and y coordinates
                y, x = np.ogrid[: self.pixel_data.shape[0], : self.pixel_data.shape[1]]

                # Calculate the mask
                mask = (
                    (x - center_x) ** 2 / semi_major_axis**2
                    + (y - center_y) ** 2 / semi_minor_axis**2
                ) <= 1

                if not np.any(mask):
                    # Handle the case where the mask is empty
                    return "Empty ellipse mask", 0

                # Apply mask to extract pixels within the ellipse
                selected_pixels = self.pixel_data[mask]
                # Calculate mean and standard deviation
                mean_pxl = round(np.mean(selected_pixels), 2)
                sd_pxl = round(np.std(selected_pixels), 2)
                min_pxl = round(np.min(selected_pixels), 2)
                max_pxl = round(np.max(selected_pixels), 2)
                pixel_count = np.sum(mask)  # Count the pixels inside the ellipse
                stat_str = (
                    "Mean: "
                    + str(mean_pxl)
                    + " SD: "
                    + str(sd_pxl)
                    + "\n"
                    + "Min: "
                    + str(min_pxl)
                    + " Max: "
                    + str(max_pxl)
                )
                return stat_str, pixel_count
            else:
                return "No pixel data or ellipse", 0
        except:
            print("ellipse traceback",traceback.format_exc())

    def area_measure(self, width, height):
        area = np.pi * (width * self.px) * (height * self.py) / 4
        area = area / 100
        area_str = "Area: " + "{:.2f}".format(area) + " cm2"
        return area_str
    
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
            
    def creatingOriginalDict(self,ellipse_info_original):
        if self.patientID not in self.ellipseStorageDictOriginal:
            self.ellipseStorageDictOriginal[self.patientID] = {}

        # Ensure the patient series name level exists
        if self.patientSeriesName not in self.ellipseStorageDictOriginal[self.patientID]:
            self.ellipseStorageDictOriginal[self.patientID][self.patientSeriesName] = {}

        # Ensure the image index level exists
        if self.canvasIndex not in self.ellipseStorageDictOriginal[self.patientID][self.patientSeriesName]:
            self.ellipseStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
            
        if self.imageIndex not in self.ellipseStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.ellipseStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []

        # Now that we've ensured all levels exist, append the ellipse information
        self.ellipseStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(ellipse_info_original)
    
    def ellipseStorage(self, ellipse, markers, annotation, uid=None):
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.canvasIndex = self.getCanvaIndex()
        if uid is None:
            ellipse_info={
                "id":self.ellipse_id,
                "ellipse": ellipse,
                "markers": markers,
                "annotation": annotation,
                "annotation_moved":False,
                "uuid":self.uid ,
                "image_index": self.imageIndex,
                "canvas_index":self.canvasIndex
            }
        else:
            ellipse_info={
                "id":self.ellipse_id,
                "ellipse": ellipse,
                "markers": markers,
                "annotation": annotation,
                "annotation_moved":False,
                "uuid":uid,
                "image_index": self.imageIndex,
                "canvas_index":self.canvasIndex 
            }

        if uid is None:
            ellipse_info_original={
                "id":self.ellipse_id,
                "ellipse": ellipse,
                "markers": markers,
                "annotation": annotation,
                "annotation_moved":False,
                "uuid":self.uid ,
                "image_index": self.imageIndex,
                "canvas_index":self.canvasIndex
            }
        else:
            ellipse_info_original={
                "id":self.ellipse_id,
                "ellipse": ellipse,
                "markers": markers,
                "annotation": annotation,
                "annotation_moved":False,
                "uuid":uid,
                "image_index": self.imageIndex,
                "canvas_index":self.canvasIndex 
            }

        # Ensure the patient ID level exists
        if self.patientID not in self.ellipseStorageDict:
            self.ellipseStorageDict[self.patientID] = {}

        # Ensure the patient series name level exists
        if self.patientSeriesName not in self.ellipseStorageDict[self.patientID]:
            self.ellipseStorageDict[self.patientID][self.patientSeriesName] = {}

        # Ensure the image index level exists
        if self.canvasIndex not in self.ellipseStorageDict[self.patientID][self.patientSeriesName]:
            self.ellipseStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
            
        if self.imageIndex not in self.ellipseStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.ellipseStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []

        # Now that we've ensured all levels exist, append the ellipse information
        self.ellipseStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(ellipse_info)
        # print("ellipse storage in function", self.ellipseStorageDict)
        self.creatingOriginalDict(ellipse_info_original)

    def giveEllipseStorageDict(self):
        # #print("ellipseStorage in give",self.ellipseStorageDict)
        return self.ellipseStorageDict
       
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
    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()
    def getEllipseActivation(self):
        return  self.mainWindow.giveEllipseActivation()
    def calculate_font_size(self, ax):
        """Calculate font size based on the dimensions of the axes."""
        bbox = ax.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
        # Calculate font size as a fraction of the subplot height
        height_in_pixels = self.fig.dpi * bbox.height
        return max(6, min(12, height_in_pixels * 0.02))   # Adjust the scaling factor as needed

    def update_annotation_font_sizes(self):
        """Update the font sizes of all annotations according to the new layout."""
        for ax in self.fig.axes:
            font_size = self.calculate_font_size(ax)
            for text in ax.texts:
                text.set_fontsize(font_size)
        self.canvas.draw_idle()