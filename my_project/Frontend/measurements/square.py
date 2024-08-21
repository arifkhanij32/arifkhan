
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patches as patches

import numpy as np
import matplotlib
import matplotlib.lines
from PyQt5.QtCore import Qt
import sqlite3
import uuid
from .constants import *
import copy


class Square(FigureCanvas):
    def __init__(
        self,
        squareButtonActivated,
        measurementToggle,
        canvas,
        ax,
        figure,
        fillToggle,
        parent,
    ):
        global squareHover
        squareHover = False
        # self.fig, self.ax = plt.subplots()
        # self.canvas = FigureCanvas(self.fig)
        # super().__init__(self.fig)
        # self.setParent(parent)
        self.mainWindow = parent

        self.squareButtonActivated = squareButtonActivated
        
       

        # self.showMeasurement = measurementToggle
        self.showMeasurement = self.getMeasurementToggle()
        self.fillColor = self.getFillToggle()
       
        self.canvas = canvas
        self.fig = figure
        self.ax = ax

        # self.ax.set_xlim(0, self.pixel_data.shape[1])  # Set x-axis limits to image width
        # self.ax.set_ylim(self.pixel_data.shape[0], 0)
        
        super().__init__(self.fig)

        self.setFocusPolicy(Qt.StrongFocus)
        self.startPoint = None
        self.square = None
        self.squares = []
        self.markers = []
        self.annotations = []
        self.text_annotation = None
        # self.showMeasurement = False
        self.hovered_square = None
        self.square_data = {}
        self.selected_square = None
        self.moving_marker = None
        self.moving_square = None
        self.moving_square_offset = (0, 0)
        self.moving_annotation = None
        self.moving_annotation_offset = (0, 0)
        self.square_id=0
        self.squareStorageDict={}
        self.squareStorageDictOriginal={}

        self.selected_id=None
        self.delDbList=[]

        # self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        # self.canvas.mpl_connect('button_press_event', self.on_press)
        # self.canvas.mpl_connect('motion_notify_event', self.on_move)
        # self.canvas.mpl_connect('button_release_event', self.on_release)

        # if image_path:
        #     self.load_image(image_path)
        self.setupEventConnections()

    def setupEventConnections(self):
        try:
            # Connect key press event
            self.canvas.mpl_connect("key_press_event", self.squareKeyPressEvent)
        except:
            pass
    ########################################################################
        
    def dbConnection(self):
        mydb = sqlite3.connect("mainApplication.db")
        return mydb

    def getIndexInSquare(self):
        return self.mainWindow.getIndex()

    def getMeasurementToggle(self):
        return self.mainWindow.updatedMeasurementValue()

    def getFillToggle(self):
        return self.mainWindow.updatedFillValue()

    def on_hover(self, event):
        hoveredSquareAnnot = None
        squareHover = False
        # #print(self.square_data)
        self.clear_highlights()
        if event.xdata is not None and event.ydata is not None:
            for id, data in self.square_data.items():
                if (
                    id is None or data is None or data["markers"] is None
                ):  # Add this check
                    continue

                for marker in data["markers"]:
                    if self.is_near_marker(event, [marker]):
                        if data["annotation"]:
                            data["annotation"].set_color(HOVER_ANNOTATION_TEXT_COLOR)
                            # data["annotation"].set_bbox(
                            #     dict(
                                    # facecolor=HOVER_ANNOTATION_BOX_FACE_COLOR,
                                    # alpha=0.5,
                                    # edgecolor=HOVER_ANNOTATION_BOX_EDGE_COLOR,
                                    # boxstyle=ANNOTATION_BOX_STYLE,
                                    
                            #     )
                            # )
                            marker.set_color(HOVER_MARKER_COLOR)
                    # self.canvas.draw_idle()
                    # return

            for id, data in self.square_data.items():
                if (
                    id is None or data is None or data["annotation"] is None
                ):  # Add this check
                    # squareHover = not squareHover
                    continue
                
                if data["annotation"] and data["annotation"] is not None:
                    if self.is_near_text(event, data["annotation"]):
                        square =data["square"]
                        self.hoveredSquareAnnot = data["annotation"]
                        # #print('data["annotation"]:',hoveredSquareAnnot)
                        # Highlight the square, text annotation, and markers
                        self.highlight_elements(square, data)
                        self.canvas.draw_idle()
                    # return

            # If not near text, check if near any square edges
            for id, data in self.square_data.items():
                if id is None or data["square"] is None:  # Add this check
                    continue
                
                square=data["square"]
                if self.is_near_edge(event, square.get_bbox()):
                    squareHover = not squareHover
                    # #print("sq:",squareHover)

                    # Highlight the square, text annotation, and markers
                    self.highlight_elements(square, data)
                    self.canvas.draw_idle()
                    # return

    def is_near_marker(self, event, markers, threshold=5):
        mouse_point = np.array([event.xdata, event.ydata])
        for marker in markers:
            # Each marker is a Line2D object; get the xy data
            # xdata, ydata = marker.get_xdata(), marker.get_ydata()
            xdata = np.atleast_1d(marker.get_xdata())
            ydata = np.atleast_1d(marker.get_ydata())
            for x, y in zip(xdata, ydata):
                marker_point = np.array([x, y])
                # Compute the distance from the mouse to the marker
                distance = np.linalg.norm(mouse_point - marker_point)
                if distance < threshold:
                    return True
        return False
    
    def is_near_text(self, event, annotation, threshold=10):
        #print("ffffffffffffffffffffffffffffffffff",annotation)
        if annotation is None:
            return False
        if event.xdata is not None and event.ydata is not None:
            # Get the bounding box of the annotation in display units
            if annotation is not None:
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

    def is_near_edge(self, event, bbox, edge_threshold=2):
        x, y = event.xdata, event.ydata
        distances = [x - bbox.xmin, bbox.xmax - x, y - bbox.ymin, bbox.ymax - y]
        min_distance = min(distances)
        # Determine if the cursor is within the threshold distance to any edge
        near_edge = min_distance < edge_threshold
        # Verify that the cursor is within the extended bounds of the square
        within_bounds = (
            bbox.xmin - edge_threshold <= x <= bbox.xmax + edge_threshold
            and bbox.ymin - edge_threshold <= y <= bbox.ymax + edge_threshold
        )
        return near_edge and within_bounds    
    
    def highlight_elements(self, square, data):
        if square is None or data is None :
            return
        if square != self.selected_square:
            if data["square"] is not None:
                data["square"].set_edgecolor(HOVER_MARKER_COLOR)
            if data["annotation"] is not None:
                data["annotation"].set_color(HOVER_ANNOTATION_TEXT_COLOR)
                # data["annotation"].set_bbox(
                #     dict(
                #         facecolor=HOVER_ANNOTATION_BACKGROUND_COLOR,
                #         alpha=0.5,
                #         edgecolor=HOVER_ANNOTATION_BOX_EDGE_COLOR,
                #         boxstyle=ANNOTATION_BOX_STYLE,
                #     )
                # )
            # hoveredSquareAnnot=data["annotation"]
            for marker in data["markers"]:
                marker.set_color(MARKER_COLOR)

    def clear_highlights(self):
        for id, data in self.square_data.items():
            if id is None or data is None :
                continue
            square=data["square"]
            if square != self.selected_square:
                if square is not None:
                    square.set_edgecolor(LINE_COLOR)
                if data["annotation"] is not None:
                    data["annotation"].set_color(ANNOTATION_TEXT_COLOR)
                    # data["annotation"].set_bbox(
                    #     dict(
                            # facecolor=ANNOTATION_BOX_FACE_COLOR,
                            # alpha=0.5,
                            # edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                            # boxstyle=ANNOTATION_BOX_STYLE,
                    
                    #     )
                    # )
                for marker in data["markers"]:
                    marker.set_color(MARKER_COLOR)
        self.canvas.draw_idle()

    def highlight_selected_square(self):
        if self.selected_square:
            
            data = self.square_data[self.selected_id]
            square=data["square"]
            square.set_edgecolor(SQUARE_EDGE_COLOR)

            if data["annotation"]:
                data["annotation"].set_color(SELECTION_ANNOTATION_TEXT_COLOR)
                # data["annotation"].set_bbox(
                #     dict(
                        # facecolor=SELECTED_ANNOTATION_FACE_COLOR,
                        # alpha=0.5,
                        # edgecolor=ANNOTATION_BOX_EDGE_COLOR,
                        # boxstyle=ANNOTATION_BOX_STYLE,
                #     )
                # )
            for marker in data["markers"]:
                marker.set_color(SELECTED_MARKER_COLOR)
            self.canvas.draw_idle()

    def reset_square_highlight(self, id):
        if id is None:
            return
        data = self.square_data[id]
        square=data["square"]
        if data:
            square.set_edgecolor(RESET_SQUARE_EDGE_COLOR)
            if data["annotation"]:
                data["annotation"].set_color(ANNOTATION_TEXT_COLOR)
                # data["annotation"].set_bbox(
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

    def squareKeyPressEvent(self, event):
        # print("sq delete")
        # if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
        if type(event.key) == str:
            if event.key.lower().strip() == "delete".lower().strip():
                event.key = 16777223
        else:
            pass
        if str(event.key) == str(Qt.Key_Delete):
            # print("sq delete 1")
            if self.selected_square:
                # print("sq delete 2")
                self.remove_selected_square()
                
                self.canvas.draw_idle()

    def remove_selected_square(self):
        if self.selected_id is not None:
            # Remove from display
            data = self.square_data.get(self.selected_id)
            if data:
                if data["square"]:
                    data["square"].remove()
                if data["annotation"]:
                    data["annotation"].remove()
                for marker in data["markers"]:
                    marker.remove()
                
                # Remove from data structure
                del self.square_data[self.selected_id]
            self.remove_square_from_storage(self.selected_id)
            # Reset selected square and redraw canvas
            self.selected_square = None
            self.selected_id = None
            self.canvas.draw_idle()

    


    def remove_square_from_storage(self, square_id):
    # Check if the patient ID level exists
        if self.patientID in self.squareStorageDict:
            # Check if the patient series name level exists
            if self.patientSeriesName in self.squareStorageDict[self.patientID]:
                # Check if the image index level exists
                if self.canvasIndex in self.squareStorageDict[self.patientID][self.patientSeriesName]:
                    if self.imageIndex in self.squareStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex]:
                        # Get the list of squares for the current image
                        square_info_list = self.squareStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex]
                        for (index, d) in enumerate(square_info_list):
                            if d["id"] == square_id:
                                self.delDbList.append(d["uuid"])
                        # Find the index of the square with the given ID
                        square_index = next((index for (index, d) in enumerate(square_info_list) if d["id"] == square_id), None)
                        
                        # If the square is found, remove it
                        if square_index is not None:
                            del square_info_list[square_index]
                        
                        # If the list of squares is now empty, you might want to remove the entry for the imageIndex as well
                        # if not square_info_list:
                        #     del self.squareStorageDict[self.patientID][self.patientSeriesName][self.imageIndex]
                        #     # Further cleanup could be done here if the series or patient levels are now empty

                        # #print(f"Removed square with ID {square_id} from storage.")
    
    def on_press(self, event):
        self.py, self.px = self.mainWindow.pixelSpacing
        self.pixel_data=self.getPixelData()
        self.showMeasurement = self.getMeasurementToggle()
        self.ax=self.getAxes()
        self.canvas=self.getCanvas()
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        
        self.fillColor=self.getFillToggle()

        self.squareButtonActivated=self.getSquareActivation()
        if self.squareButtonActivated:
            if event.button == Qt.LeftButton:

                if event.xdata is not None and event.ydata is not None:
                    if self.selected_square:
                        self.reset_square_highlight(self.selected_id)
                        self.selected_square=None   
                    self.selected_id = None

                    for id, data in self.square_data.items():
                        if id is None :  # Add this check
                            continue
                        # if data["markers"] != None:
                        #     markers = data["markers"]
                        if 'image_index' in data and data['image_index'] != self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                        if 'canvas_index' in data and data['canvas_index'] != self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        for i, marker in enumerate(data["markers"]):
                            if self.is_near_marker(event, [marker]):
                                square=data["square"]
                                self.moving_marker = (square, i)
                                self.startPoint = None  # Ensure new square is not started
                                self.selected_square=square
                                self.selected_id=id
                                # #print("marker selecteedd")
                                return
                    # self.selected_square = None

                    for id, data in self.square_data.items():
                        if id is None or data["square"] is None:  # Add this check
                            continue
                        if 'image_index' in data and data['image_index'] != self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                        if 'canvas_index' in data and data['canvas_index'] != self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        square=data["square"]
                        
                        if self.is_near_edge(event, square.get_bbox()):
                            self.moving_square = square
                            self.selected_id=id
                            self.moving_square_offset = (
                                event.xdata - square.get_bbox().xmin,
                                event.ydata - square.get_bbox().ymin,
                            )
                            self.selected_square = square  # Set the selected square
                            self.highlight_selected_square()
                            return

                    for id, data in self.square_data.items():
                        if id is None:  # Add this check
                            continue
                        if 'image_index' in data and data['image_index'] != self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue 
                        if 'canvas_index' in data and data['canvas_index'] != self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        if data["annotation"]:
                            if self.is_near_text(event, data["annotation"]):
                                self.moving_annotation = (id, data["annotation"])
                                self.selected_id=id
                                self.moving_annotation_offset = (
                                    event.xdata - data["annotation"].get_position()[0],
                                    event.ydata - data["annotation"].get_position()[1],
                                )
                                self.selected_square = square   
                                self.highlight_selected_square()
                                return

                    if not self.moving_marker:
                        self.fillColor = self.getFillToggle()
                        self.startPoint = (event.xdata, event.ydata)
                        self.square = None

                    if self.text_annotation and self.showMeasurement:
                        self.text_annotation.set_text("")
                        self.text_annotation = None

                    if self.markers:
                        for marker in self.markers:
                            if isinstance(marker, matplotlib.lines.Line2D):
                                marker.remove()
                        self.markers.clear()

    def on_move(self, event):
        self.showMeasurement = self.getMeasurementToggle()
        self.fillColor = self.getFillToggle()
        
        if self.moving_marker and event.xdata is not None and event.ydata is not None:
            square, marker_idx = self.moving_marker
            self.resize_square(square, marker_idx, event.xdata, event.ydata)
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
            data = self.square_data[id]
            data["annotation_moved"] = True
            self.highlight_selected_square()
            square_info_list = self.squareStorageDict.get(self.patientID, {}).get(self.patientSeriesName, {}).get(self.canvasIndex, {}).get(self.imageIndex, [])
            for square_info in square_info_list:
                if square_info["id"] == id:
                    # Update the annotation position
                    # This assumes that the annotation object or its position data is directly stored and accessible
                    square_info["annotation"].set_position((new_x, new_y))
                    square_info["annotation_moved"] = True
                    break  # Found the target annotation, no need to continue

        self.canvas.draw_idle()
            # self.canvas.draw_idle()

        if self.moving_square and event.xdata is not None and event.ydata is not None:
            new_x = event.xdata - self.moving_square_offset[0]
            new_y = event.ydata - self.moving_square_offset[1]

            new_x = min(max(new_x, 0), self.pixel_data.shape[1] - self.moving_square.get_width())
            new_y = min(max(new_y, 0), self.pixel_data.shape[0] - self.moving_square.get_height())
            
            # Assuming `self.moving_square_id` holds the ID of the moving square.
            data = self.square_data.get(self.selected_id, {})
            # old_data = data.copy()  # Make a copy of the current data
            
            self.rect_width = abs(data['square'].get_width())
            self.rect_height = abs(data['square'].get_height())
            # Remove the old square and markers
            
            if data:
                square = data['square']  # Assuming this is the reference to your moving square
                square.set_xy((new_x, new_y))
                # old_square = old_data['square']
                # if old_square in self.ax.patches:
                #     old_square.remove()

                for marker in data["markers"]:
                    marker.remove()
                data["markers"] = [] 

                for point in self.calculate_square_corners(square):
                    marker = self.ax.plot(point[0], point[1], "r+",markersize=MARKER_SIZE)[0]
                    data["markers"].append(marker)

                data = self.square_data[self.selected_id]
                stat_str, pixel_count = self.calculate_statistics(
                    new_x, new_y,self.rect_width,self.rect_height
                )
                area_str = self.area_measure(self.rect_width, self.rect_height)
                final_str = f"{stat_str}\n{area_str} ({pixel_count} px)"

            if data["annotation"]:
                data["annotation"].set_text(final_str)

            if data.get("annotation") and not data.get("annotation_moved", False):
                annotation = data["annotation"]
                annotation_x = new_x + self.rect_width
                annotation_y = new_y + self.rect_height
                annotation.set_position((annotation_x, annotation_y))
            else:
                annotation=data["annotation"]
            # Update square_data with new square reference using its ID
            # self.square_data[self.selected_id] = new_data
            
            square_info_list = self.squareStorageDict.get(self.patientID, {}).get(self.patientSeriesName, {}).get(self.canvasIndex, {}).get(self.imageIndex, [])
            for square_info in square_info_list:
                if square_info["id"] == self.selected_id:
                    # Update the annotation position
                    square_info["square"] = data["square"]
                    square_info["annotation"]=data["annotation"]
                    square_info["markers"] = data["markers"]
                    break 

            # self.canvas.mpl_connect("button_press_event", self.on_press)
            # self.canvas.mpl_connect("motion_notify_event", self.on_move)
            # self.canvas.mpl_connect("key_press_event", self.squareKeyPressEvent)
            self.canvas.draw_idle()

        if self.startPoint is not None:
            # Drawing a new square
            x0, y0 = self.startPoint
            x1, y1 = event.xdata, event.ydata
            self.rect_width = abs(x1 - x0)
            self.rect_height = abs(y1 - y0)
            self.rect_x = min(x0, x1)
            self.rect_y = min(y0, y1)

            if self.square:
                self.square.remove()
                self.square = None
                # self.canvas.draw_idle()

            if self.text_annotation and self.showMeasurement:
                self.text_annotation.set_text("")
                self.text_annotation = None

            if self.markers:
                for marker in self.markers:
                    if isinstance(marker, matplotlib.lines.Line2D):
                        marker.remove()
                self.markers.clear()

            # self.showMeasurement = True
            self.draw_square(event, showMeasurement=self.showMeasurement)
            self.canvas.draw_idle()

    def on_release(self, event):
        self.imageIndex = self.getimageIndex()
        self.showMeasurement = self.getMeasurementToggle()
        self.fillColor = self.getFillToggle()
        self.canvasIndex = self.getCanvaIndex()

        if self.moving_marker:
            self.moving_marker = None

        if self.moving_square:
            # Finalize the position of the square and its annotation
            # data = self.square_data.pop(self.selected_id, None)
            # self.square_data[
            #     self.selected_id
            # ] = data  # Update with the new square reference
            
            self.moving_square = None
            self.canvas.draw_idle()

        if self.moving_annotation:
            # id, annotation = self.moving_annotation
            # data = self.square_data[id]
            # data["annotation"] = annotation
            self.moving_annotation = None
            self.canvas.draw_idle()

        if (
            event.xdata is not None
            and event.ydata is not None
            and self.startPoint is not None
        ):
            self.square_data[self.square_id] = {
                "square": self.square,
                "annotation": self.text_annotation,
                "markers": self.markers,
                "annotation_moved": False,
                "image_index": self.imageIndex,
                "canvas_index":self.canvasIndex
            }

            self.uid=uuid.uuid4() # 4     
            conn = self.dbConnection()
            cur = conn.cursor()
            query = "SELECT EXISTS(SELECT 1 FROM squareData WHERE uuid = ?)"
            # Execute the query, replacing '?' with the new_uuid
            cur.execute(query, (str(self.uid),))
            exists = cur.fetchone()[0] 
            # self.text_id+=1
            if self.uid == exists:
                self.uid = uuid.uuid4()
            else :
                pass


            self.squareStorage(self.square, self.markers, self.text_annotation)
                # squareDictIndexVal = self.square_data[self.square]["imageIndex"]
            # #print(if self.currentImageIndexSeries == squareDictIndexVal :)
            self.square_id+=1
            self.startPoint = None
            self.square = None
            self.text_annotation = None
            self.markers = []
            self.canvas.draw_idle()

        


    def resize_square(self, square, marker_idx, new_x, new_y):
        # Retrieve the current bounding box of the square
        bbox = square.get_bbox()
        # Calculate new positions and dimensions based on the marker being dragged
        if marker_idx == 0:  # Top-left marker
            new_width = bbox.xmax - new_x
            new_height = bbox.ymax - new_y
            new_xmin = new_x
            new_ymin = new_y

        if marker_idx == 2:  # Top-right marker
            new_width = new_x - bbox.xmin
            new_height = bbox.ymax - new_y
            new_xmin = bbox.xmin
            new_ymin = new_y

        if marker_idx == 1:  # Bottom-left marker
            new_width = bbox.xmax - new_x
            new_height = new_y - bbox.ymin
            new_xmin = new_x
            new_ymin = bbox.ymin

        if marker_idx == 3:  # Bottom-right marker
            new_width = new_x - bbox.xmin
            new_height = new_y - bbox.ymin
            new_xmin = bbox.xmin
            new_ymin = bbox.ymin

        if new_width < 0 or new_height < 0:
            return

        new_width = max(min(new_width, self.pixel_data.shape[1] - new_xmin), 1)
        new_height = max(min(new_height, self.pixel_data.shape[0] - new_ymin), 1)
        # Set the new bounds for the square
        square.set_bounds(new_xmin, new_ymin, new_width, new_height)

        # Update the annotation position and text
        data = self.square_data[self.selected_id]
        stat_str, pixel_count = self.calculate_statistics(
            new_xmin, new_ymin, new_width, new_height
        )
        area_str = self.area_measure(new_width, new_height)
        final_str = f"{stat_str}\n{area_str} ({pixel_count} px)"
        if data["annotation"]:
            data["annotation"].set_text(final_str)

        if not data.get("annotation_moved", False):
            if data["annotation"]:
                data["annotation"].set_position(
                    (new_xmin + new_width, new_ymin + new_height)
                )

        # Update markers
        new_markers = []
        for point in self.calculate_square_corners(square):
            marker = self.ax.plot(point[0], point[1], "r+",markersize=MARKER_SIZE)[0]
            new_markers.append(marker)

        # Remove old markers
        for marker in data["markers"]:
            marker.remove()

        data["markers"] = new_markers
        square_info_list = self.squareStorageDict.get(self.patientID, {}).get(self.patientSeriesName, {}).get(self.canvasIndex, {}).get(self.imageIndex, [])
        for square_info in square_info_list:
            if square_info["id"] == self.selected_id:
                square_info["square"].set_bounds(new_xmin, new_ymin, new_width, new_height)
                square_info["markers"]=new_markers
                # square_info["annotation"].set_position((new_xmin + new_width, new_ymin + new_height))
                square_info["annotation"]= data["annotation"]
                break         
        self.canvas.draw_idle()

    def calculate_square_corners(self, square):
        bbox = square.get_bbox()
        return [
            (bbox.xmin, bbox.ymin),
            (bbox.xmin, bbox.ymax),
            (bbox.xmax, bbox.ymin),
            (bbox.xmax, bbox.ymax),
        ]

    def draw_square(self, event, showMeasurement):
        x1, y1 = event.xdata, event.ydata
        # Determine the coordinates based on the drag direction
        bottom_left_x = min(self.startPoint[0], x1)
        bottom_left_y = min(self.startPoint[1], y1)
        top_right_x = max(self.startPoint[0], x1)
        top_right_y = max(self.startPoint[1], y1)

        # Calculate the width and height of the rectangle
        rect_width = abs(x1 - self.startPoint[0])
        rect_height = abs(y1 - self.startPoint[1])

        # Determine the corners of the rectangle
        self.points = [
            (bottom_left_x, bottom_left_y),
            (top_right_x, bottom_left_y),
            (bottom_left_x, top_right_y),
            (top_right_x, top_right_y),
        ]

        # self.fillColor = False

        # Draw the rectangle
        if self.fillColor:
            self.square = patches.Rectangle(
                (bottom_left_x, bottom_left_y),
                rect_width,
                rect_height,
                edgecolor=FILL_COLOR,
                facecolor=FILL_COLOR,
            )
        else:
            self.square = patches.Rectangle(
                (bottom_left_x, bottom_left_y),
                rect_width,
                rect_height,
                linewidth = LINE_WIDTH,
                edgecolor=FILL_COLOR,
                facecolor="None",
            )
        self.ax.add_patch(self.square)
        self.square.set_zorder(2)  # Ensure it's on top

        # If showing measurements, calculate statistics and area, and place the text annotation
        if showMeasurement:
            stat_str, pixel_count = self.calculate_statistics(
                bottom_left_x, bottom_left_y, rect_width, rect_height
            )
            area = self.area_measure(rect_width, rect_height)
            self.final_str = stat_str + "\n" + area + " (" + str(pixel_count) + " px)"
            # Adjust text placement to the bottom-right corner of the rectangle
            bottom_right_corner = self.points[3]  # Assuming this is the correct corner
            font_size = self.calculate_font_size(self.ax)#dynamic font
            self.text_annotation = self.ax.text(
                bottom_right_corner[0],
                bottom_right_corner[1],
                self.final_str,
                # fontsize=ANNOTATION_FONT_SIZE,
                fontsize=font_size,
                color=ANNOTATION_TEXT_COLOR
            )
            # self.text_annotation.set_bbox(
            #     dict(
            #         facecolor=ANNOTATION_BOX_FACE_COLOR,
            #         alpha=0.5,
            #         edgecolor=ANNOTATION_BOX_EDGE_COLOR,
            #         boxstyle=ANNOTATION_BOX_STYLE,
            #     )
            # )
            # self.text_annotations.append(self.text_annotation)
        self.markers = [self.ax.plot(x, y, "r+",markersize=MARKER_SIZE)[0] for x, y in self.points]

        # else:
        #     self.markers = [self.ax.plot(x, y, "r+")[0] for x, y in self.points]

        self.canvas.draw_idle()

    def calculate_statistics(self, left_x, top_y, rect_width, rect_height):
        if self.pixel_data is not None:
            right_x = left_x + rect_width
            bottom_y = top_y + rect_height

            y, x = np.ogrid[: self.pixel_data.shape[0], : self.pixel_data.shape[1]]
            mask = (x >= left_x) & (x < right_x) & (y >= top_y) & (y < bottom_y)

            # Extract pixels within the square
            selected_pixels = self.pixel_data[mask]
            # Check if the array is empty
            if selected_pixels.size > 0:
                # Calculate statistics
                mean_pxl = np.mean(selected_pixels)
                sd_pxl = np.std(selected_pixels)
                min_pxl = np.min(selected_pixels)
                max_pxl = np.max(selected_pixels)
                pixel_count = np.sum(mask)  # Count the pixels in the square

                stat_str = f"Mean: {mean_pxl:.2f} SD: {sd_pxl:.2f}\nMin: {min_pxl:.2f} Max: {max_pxl:.2f}"
            else:
                # Handle the case where no pixels are selected
                stat_str = "No pixels selected"
                pixel_count = 0

            return stat_str, pixel_count
        else:
            return "No Data", 0

    def area_measure(self, rect_width, rect_height):
        area = (rect_width * self.px) * (rect_height * self.py) / 4
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
            
    def creatingOriginalDict(self,square_info_original):
        if self.patientID not in self.squareStorageDictOriginal:
            self.squareStorageDictOriginal[self.patientID] = {}

        # Ensure the patient series name level exists
        if self.patientSeriesName not in self.squareStorageDictOriginal[self.patientID]:
            self.squareStorageDictOriginal[self.patientID][self.patientSeriesName] = {}

        # Ensure the image index level exists
        if self.canvasIndex not in self.squareStorageDictOriginal[self.patientID][self.patientSeriesName]:
            self.squareStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex] ={}

        if self.imageIndex not in self.squareStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.squareStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []

        # Now that we've ensured all levels exist, append the square information
        self.squareStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(square_info_original)

    def squareStorage(self, square, markers, annotation, uid=None):
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.canvasIndex=self.getCanvaIndex()

        if uid is None:
            square_info={
                "id":self.square_id,
                "square": square,
                "markers": markers,
                "annotation": annotation,
                "annotation_moved":False,
                "uuid":self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }
        else:
            square_info={
                "id":self.square_id,
                "square": square,
                "markers": markers,
                "annotation": annotation,
                "annotation_moved":False,
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        if uid is None:
            square_info_original={
                "id":self.square_id,
                "square": self.custom_deepcopy(square),
                "markers": markers,
                "annotation": annotation,
                "annotation_moved":False,
                "uuid":self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }
        else:
            square_info_original={
                "id":self.square_id,
                "square":  self.custom_deepcopy(square),
                "markers": markers,
                "annotation": annotation,
                "annotation_moved":False,
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        # Ensure the patient ID level exists
        if self.patientID not in self.squareStorageDict:
            self.squareStorageDict[self.patientID] = {}

        # Ensure the patient series name level exists
        if self.patientSeriesName not in self.squareStorageDict[self.patientID]:
            self.squareStorageDict[self.patientID][self.patientSeriesName] = {}

        # Ensure the image index level exists
        if self.canvasIndex not in self.squareStorageDict[self.patientID][self.patientSeriesName]:
            self.squareStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex] ={}

        if self.imageIndex not in self.squareStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.squareStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []

        # Now that we've ensured all levels exist, append the square information
        self.squareStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(square_info)
        #print("square storage in function", self.squareStorageDict)
        self.creatingOriginalDict(square_info_original)

    def giveSquareStorageDict(self):
        # #print("squareStorage in give",self.squareStorageDict)
        return self.squareStorageDict
       
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
    def getSquareActivation(self):
        return  self.mainWindow.giveSquareActivation()
    def getPixelData(self):
        return self.mainWindow.givePixelData()
    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()
    def calculate_font_size(self, ax):
        """Calculate font size based on the dimensions of the axes."""
        bbox = ax.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
        # Calculate font size as a fraction of the subplot height
        height_in_pixels = self.fig.dpi * bbox.height
        return max(6, min(12, height_in_pixels * 0.02))  # Adjust the scaling factor as needed

    def update_annotation_font_sizes(self):
        """Update the font sizes of all annotations according to the new layout."""
        for ax in self.fig.axes:
            font_size = self.calculate_font_size(ax)
            for text in ax.texts:
                text.set_fontsize(font_size)
        self.canvas.draw_idle()