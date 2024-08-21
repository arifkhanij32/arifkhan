from PyQt5.QtWidgets import  QMainWindow

import numpy as np

from PyQt5.QtCore import Qt
from .constants import *
import uuid
import sqlite3

# global bool_arrow_hower
bool_arrow_hower = None


def globalArrowHover(val):
    global bool_arrow_hower
    bool_arrow_hower = val


class ArrowTool(QMainWindow):
    def __init__(self, arrowButtonActivated, canvas, ax, figure, parent):
        super().__init__()
        # self.image_path = image_path
        hover_threshold = 3
        self.hover_threshold = hover_threshold
        self.selected_arrow = None
        self.arrows = []
        self.dragging_item = None
        self.line_offset = None
        self.dragging_arrow = None
        self.dragging_circle = None
        self.last_drawn_arrow = None
        self.temp_arrow = None
        self.dragging_whole_arrow = False
        self.unknown_flag = True
        self.new_flag = True
        self.flag = False
        self.arrow_id=0
        self.delDbList=[]
        self.arrowButtonActivated = arrowButtonActivated
        self.canvas = canvas
        self.ax = ax
        self.figure = figure
        self.start_point = None
        self.temp_arrow = None
        self.mainWindow = parent
        self.arrowStorageDict = {}
        self.arrowStorageDictOriginal={}
        self.canvasIndex = self.getCanvaIndex()

        # try:
        # self.canvas.mpl_connect("key_press_event", self.keyPressEvent)
        # except:
        #     pass
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

    def keyPressEvent(self, event):
        if type(event.key) == str:
            if event.key.lower().strip() == "delete".lower().strip():
                event.key = 16777223
        else:
            pass
        if str(event.key) == str(Qt.Key_Delete):
            if self.selected_arrow:
                arrow, _, _ = self.selected_arrow
                self.remove_arrow(arrow)

    def remove_arrow(self, arrow):
        for a, start_circle, end_circle,imageindex,canvasindex in self.arrows:
            if a == arrow:
                start_pos = tuple(start_circle.get_offsets()[0])
                end_pos = tuple(end_circle.get_offsets()[0])

                a.remove()
                start_circle.remove()
                end_circle.remove()
                # self.arrows.remove((a, start_circle, end_circle))

                if self.selected_arrow and self.selected_arrow[0] == arrow:
                    self.reset_selected_arrow()
                self.canvas.draw_idle()

                # Remove the arrow from storage
                self.remove_arrow_from_storage(start_pos, end_pos)
                break

    def remove_arrow_from_storage(self, start_pos, end_pos):
        for patientID, seriesDict in self.arrowStorageDict.items():
            for seriesName, canvasDict in seriesDict.items():
                for canvasId, imageDict in canvasDict.items():
                    for imageIndex, arrowsList in imageDict.items():
                        for arrow_info in arrowsList[:]:  # Copy the list for safe iteration
                            s_circle = arrow_info["startcircle"]
                            e_circle = arrow_info["endcircle"]
                            if (tuple(s_circle.get_offsets()[0]) == start_pos and
                                tuple(e_circle.get_offsets()[0]) == end_pos):
                                arrowsList.remove(arrow_info)
                                self.delDbList.append(arrow_info["uuid"])
                                # If the arrows list for this image is empty, remove the image entry
                                # if not arrowsList:
                                #     del imageDict[imageIndex]
                                # # If the imageDict for this series is empty, remove the series entry
                                # if not imageDict:
                                #     del seriesDict[seriesName]
                                # # If the seriesDict for this patient is empty, remove the patient entry
                                # if not seriesDict:
                                #     del self.arrowStorageDict[patientID]
                                
                                return  # Arrow found and removed, exit the function
                        

    def on_press(self, event):
        self.ax=self.getAxes()
        self.canvas=self.getCanvas()
        self.imageIndex = self.getimageIndex()
        self.arrowButtonActivated=self.getArrowActivation()
        self.canvasIndex = self.getCanvaIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()

        if self.arrowButtonActivated:
            
            if event.inaxes != self.ax:
                return
            if event.button == Qt.LeftButton:
                arrow_clicked = False
                self.dragging_arrow = None
                self.dragging_circle = None

                for arrow, start_circle, end_circle, imageindex, canvasindex in self.arrows:
                    if imageindex != self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue
                    if canvasindex != self.canvasIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue
                    if start_circle.contains(event)[0]:
                        self.dragging_arrow = arrow
                        self.dragging_circle = start_circle
                        self.selected_arrow = (arrow, start_circle, end_circle)


                        start_circle.set_edgecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        start_circle.set_facecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        end_circle.set_facecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        end_circle.set_edgecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        self.canvas.draw_idle()
                        return
                        # Stop checking and exit the method
                    elif end_circle.contains(event)[0]:
                        self.dragging_arrow = arrow
                        self.dragging_circle = end_circle
                        self.selected_arrow = (arrow, start_circle, end_circle)

                        start_circle.set_edgecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        start_circle.set_facecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        end_circle.set_facecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        end_circle.set_edgecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        self.canvas.draw_idle()
                        return
                        

                for arrow, start_circle, end_circle, imageindex, canvasindex in self.arrows:
                    if imageindex != self.imageIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue
                    if canvasindex != self.canvasIndex:
                        # print("found duplicateeeeeeeeeeeeeeeee")
                        continue
                    if self.is_close_to_arrow(event, arrow):
                        # A different arrow is clicked, reset the old selection
                        self.reset_selected_arrow()
                        # Set the new selection
                        start_circle.set_edgecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        start_circle.set_facecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        end_circle.set_facecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        end_circle.set_edgecolor(ON_HOVER_ARROW_MARKER_COLOR)
                        start_circle.set_visible(True)
                        end_circle.set_visible(True)
                        self.selected_arrow = (arrow, start_circle, end_circle)

                        self.canvas.draw_idle()
                        arrow_clicked = True


                        break

                if arrow_clicked:
                    # Check if the click is on the arrow itself for dragging the whole arrow
                    for arrow, start_circle, end_circle, imageindex, canvasindex in self.arrows:
                        if imageindex != self.imageIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue
                        if canvasindex != self.canvasIndex:
                            # print("found duplicateeeeeeeeeeeeeeeee")
                            continue

                        if self.is_close_to_arrow(event, arrow):
                            # Set up to drag the whole arrow
                            self.dragging_arrow = arrow
                            self.dragging_circle = (
                                None  # We are not dragging a circle, but the whole arrow
                            )
                            self.selected_arrow = (arrow, start_circle, end_circle)
                            self.start_point = (event.xdata, event.ydata)
                            self.arrow_original_start = start_circle.get_offsets()[0]
                            self.arrow_original_end = end_circle.get_offsets()[0]
                            arrow_clicked = True
                            self.flag = (
                                True  # We are now dragging an arrow, so this is set to True
                            )
                            break
                
                if self.selected_arrow:
                    _, start_circle, end_circle = self.selected_arrow
                    self.old_start = tuple(start_circle.get_offsets()[0])
                    self.old_end = tuple(end_circle.get_offsets()[0])
                
                if not arrow_clicked:
                    # If we click away from an arrow, reset the selection
                    self.reset_selected_arrow()
                    self.start_point = (event.xdata, event.ydata)

    def on_move(self, event):

        # if self.selected_arrow:
        if self.arrowButtonActivated:
            if event.inaxes != self.ax:
                return
            # Handle the dragging of an entire arrow
            if self.dragging_arrow and self.dragging_circle is None:
                # Calculate the change in position since the drag started
                if self.start_point is not None:
                    dx = event.xdata - self.start_point[0]
                    dy = event.ydata - self.start_point[1]
                    new_start = self.arrow_original_start + np.array([dx, dy])
                    new_end = self.arrow_original_end + np.array([dx, dy])

                    # Update the position of the arrow and the circles
                    arrow, start_circle, end_circle = self.selected_arrow
                    arrow.set_position(new_start)
                    arrow.xy = new_end
                    start_circle.set_offsets(new_start)
                    end_circle.set_offsets(new_end)
                    self.flag = True
                    self.canvas.draw_idle()
                    # return
            elif self.dragging_circle:
                _, start_circle, end_circle = self.selected_arrow
                self.old_start = tuple(start_circle.get_offsets()[0])
                self.old_end = tuple(end_circle.get_offsets()[0])
                # Existing code for dragging a circle
                self.update_arrow(event)
                

            elif self.start_point and self.flag:
                pass
            elif self.start_point and not self.flag:
                end_point = (event.xdata, event.ydata)
                if self.temp_arrow:
                    self.temp_arrow.remove()
                self.temp_arrow = self.ax.annotate(
                    "",
                    xy=end_point,
                    xytext=self.start_point,
                    arrowprops=dict(arrowstyle="->", color=LINE_COLOR, linewidth=LINE_WIDTH),
                )
                self.canvas.draw_idle()
                # self.flag=False
                return
    
    def reset_selected_arrow(self):
        if self.arrowButtonActivated:
            if self.selected_arrow:
                _, start_circle, end_circle = self.selected_arrow
                start_circle.set_edgecolor(ARROW_MARKER_COLOR)  # Reset color to yellow
                end_circle.set_edgecolor(ARROW_MARKER_COLOR)
                start_circle.set_facecolor(ARROW_MARKER_COLOR)  # Reset color to yellow
                end_circle.set_facecolor(ARROW_MARKER_COLOR)  # Reset color to yellow
                start_circle.set_visible(False)  # Hide the circle
                end_circle.set_visible(False)  # Hide the circle
                self.selected_arrow = None
            self.canvas.draw_idle()
   
    def updateArrowInStorageByCoords(self, old_start, old_end, new_start, new_end):
    # Iterate over the arrowStorageDict
        for patientID, seriesDict in self.arrowStorageDict.items():
            for seriesName, canvasDict in seriesDict.items():
                for canvasId, imageDict in canvasDict.items():
                    for imageIndex, arrowsList in imageDict.items():
                        for arrow_info in arrowsList:
                            # Match the arrow by old coordinates
                            start_circle = arrow_info["startcircle"]
                            end_circle = arrow_info["endcircle"]
                            if (tuple(start_circle.get_offsets()[0]) == old_start and
                                tuple(end_circle.get_offsets()[0]) == old_end):
                                # Update coordinates
                                start_circle.set_offsets([new_start])
                                end_circle.set_offsets([new_end])
                                arrow_info["arrow"].xytext = new_start
                                arrow_info["arrow"].xy = new_end
                                return 
    
    def on_release(self, event):
        self.imageIndex = self.getimageIndex()
        self.canvasIndex = self.getCanvaIndex()
        if self.arrowButtonActivated:
            self.dragging_arrow = None
            self.dragging_circle = None

            if self.dragging_whole_arrow:
                self.dragging_whole_arrow = False
            elif not self.start_point or event.inaxes != self.ax:
                return

            # If an arrow was previously selected and we release on it, keep the circles red
            if self.selected_arrow:
                arrow, start_circle, end_circle = self.selected_arrow
                if self.is_close_to_arrow(event, arrow):
                    start_circle.set_visible(True)
                    end_circle.set_visible(True)
                    self.canvas.draw_idle()
                    # return  # Keep the selected arrow's state and exit the method
            # if self.selected_arrow:
                    arrow, start_circle, end_circle = self.selected_arrow
                    new_start = tuple(start_circle.get_offsets()[0])
                    new_end = tuple(end_circle.get_offsets()[0])

                    # Update the storage with the new arrow details based on old coordinates
                    self.updateArrowInStorageByCoords(self.old_start, self.old_end, new_start, new_end)
                    return
                
            # Remove the temporary arrow (if it exists)
            if self.temp_arrow:
                self.temp_arrow.remove()
                self.temp_arrow = None

            self.reset_selected_arrow()

            # Create a new arrow and circles if we are not clicking on an existing arrow
            end_point = (event.xdata, event.ydata)
            arrow = self.ax.annotate(
                "",
                xy=end_point,
                xytext=self.start_point,
                arrowprops=dict(arrowstyle="->", color=LINE_COLOR, linewidth=LINE_WIDTH),
            )

            start_circle = self.ax.scatter(
                [self.start_point[0]],
                [self.start_point[1]],
                s=MARKER_SIZE,
                color=ARROW_MARKER_COLOR,
                zorder=5,
                visible=False,
            )
            end_circle = self.ax.scatter(
                [end_point[0]],
                [end_point[1]],
                s=MARKER_SIZE,
                color=ARROW_MARKER_COLOR,
                zorder=5,
                visible=False,
            )
            self.arrows.append([arrow, start_circle, end_circle,self.imageIndex,self.canvasIndex])
    
            self.uid=uuid.uuid4() # 4     
            conn = self.dbConnection()
            cur = conn.cursor()
            query = "SELECT EXISTS(SELECT 1 FROM arrowData WHERE uuid = ?)"
            # Execute the query, replacing '?' with the new_uuid
            cur.execute(query, (str(self.uid),))
            # Fetch the result
            exists = cur.fetchone()[0] 
            if self.uid == exists:
                self.uid = uuid.uuid4()
            else :
                pass
             
            self.arrowStorage(arrow, start_circle, end_circle)
            self.arrow_id+=1
            self.last_drawn_arrow = arrow  # Update the last drawn arrow
            self.start_point = None
            self.flag = False
            self.canvas.draw_idle()

    def on_hover(self, event):
        # if self.arrowButtonActivated:
        isArrowHover = False

        # globalArrowHover(False)
        for arrow, start_circle, end_circle,imageindex,canvasindex in self.arrows:
            # Skip the hover effect for the selected arrow
            if self.selected_arrow and arrow == self.selected_arrow[0]:
                continue

            if self.is_close_to_arrow(event, arrow):
                start_circle.set_visible(True)
                end_circle.set_visible(True)
                # Ensure the hover effect uses yellow color for non-selected arrows
                if (arrow, start_circle, end_circle) != self.selected_arrow:
                    start_circle.set_edgecolor(ARROW_MARKER_COLOR)
                    end_circle.set_edgecolor(ARROW_MARKER_COLOR)
                    start_circle.set_facecolor(ARROW_MARKER_COLOR)
                    end_circle.set_facecolor(ARROW_MARKER_COLOR)
                    isArrowHover = not isArrowHover

                    # globalArrowHover(True)

            else:
                # Hide the circles only if they are not part of the selected arrow
                if (arrow, start_circle, end_circle) != self.selected_arrow:
                    start_circle.set_visible(False)
                    end_circle.set_visible(False)

        # self.canvas.mpl_connect("button_press_event", self.on_press)
        # self.canvas.mpl_connect("motion_notify_event", self.on_move)
        # self.canvas.mpl_connect("key_press_event", self.keyPressEvent)
        self.canvas.draw_idle()

    def update_arrow(self, event):
        if self.arrowButtonActivated:
            if not self.dragging_arrow or not self.dragging_circle:
                return

            end_point = (event.xdata, event.ydata)
            if self.dragging_circle == self.selected_arrow[1]:  # start_circle
                self.selected_arrow[0].set_position(end_point)
                new_start = end_point
                new_end = tuple(self.selected_arrow[2].get_offsets()[0]) 
            else:  # end_circle
                self.selected_arrow[0].xy = end_point
                new_start = tuple(self.selected_arrow[1].get_offsets()[0])  # Keep start circle's position
                new_end = end_point

            self.dragging_circle.set_offsets(end_point)
            self.canvas.draw_idle()
            self.updateArrowInStorageByCoords(self.old_start, self.old_end, new_start, new_end) 

    def is_close_to_arrow(self, event, arrow):
        if self.arrowButtonActivated:
            # Check if the event occurred within the plot area
            if event.xdata is None or event.ydata is None:
                return False  # Event is outside the plot area

            x0, y0 = arrow.get_position()
            x1, y1 = arrow.xy
            px, py = event.xdata, event.ydata

            # Check if the point is within the bounding box extended by hover_threshold
            if not (
                min(x0, x1) - self.hover_threshold
                <= px
                <= max(x0, x1) + self.hover_threshold
                and min(y0, y1) - self.hover_threshold
                <= py
                <= max(y0, y1) + self.hover_threshold
            ):
                return False  # The point is outside the extended bounding box of the arrow line

            # Calculate the distance from the point to the line
            line_length = np.hypot(x1 - x0, y1 - y0)
            if line_length == 0:
                return False  # The arrow is a point and cannot be selected by moving close to it

            # Calculate the projection of the point onto the line (dot product)
            projection_length = (
                (px - x0) * (x1 - x0) + (py - y0) * (y1 - y0)
            ) / line_length
            if projection_length < 0 or projection_length > line_length:
                return (
                    False  # The projection of the point is not within the line segment
                )

            # Calculate the distance from the point to the line segment
            distance = abs((px - x0) * (y1 - y0) - (py - y0) * (x1 - x0)) / line_length
            return distance < self.hover_threshold

    def point_line_distance(self, point, start, end):
        if self.arrowButtonActivated:
            px, py = point
            x1, y1 = start
            x2, y2 = end
            normal_length = np.hypot(x2 - x1, y2 - y1)
            if normal_length == 0:
                return np.inf
            distance = (
                abs((px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)) / normal_length
            )
            return distance

    def arrowStorage(self, arrow, start_circle, end_circle, uid=None):
        self.imageIndex = self.getimageIndex()
        self.patientID = self.getPatientID()
        self.patientSeriesName = self.getPatientSeriesName()
        self.canvasIndex = self.getCanvaIndex()

        
        if uid is None:
        
            arrow_info={
                "id":self.arrow_id,
                "arrow":arrow,
                "startcircle":start_circle,
                "endcircle":end_circle,
                "uuid":self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        else:
            arrow_info={
                "id":self.arrow_id,
                "arrow":arrow,
                "startcircle":start_circle,
                "endcircle":end_circle,
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        if uid is None:
        
            arrow_info_original={
                "id":self.arrow_id,
                "arrow":arrow,
                "startcircle":start_circle,
                "endcircle":end_circle,
                "uuid":self.uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        else:
            arrow_info_original={
                "id":self.arrow_id,
                "arrow":arrow,
                "startcircle":start_circle,
                "endcircle":end_circle,
                "uuid":uid,
                "image_index":self.imageIndex,
                "canvas_index":self.canvasIndex
            }

        # Ensure the patient ID level exists
        if self.patientID not in self.arrowStorageDict:
            self.arrowStorageDict[self.patientID] = {}

        # Ensure the patient series name level exists
        if self.patientSeriesName not in self.arrowStorageDict[self.patientID]:
            self.arrowStorageDict[self.patientID][self.patientSeriesName] = {}

        # Ensure the image index level exists
        if self.canvasIndex not in self.arrowStorageDict[self.patientID][self.patientSeriesName]:
            self.arrowStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex] = {}

        if self.imageIndex not in self.arrowStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.arrowStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []
        # Now that we've ensured all levels exist, append the arrow information
        self.arrowStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(arrow_info)

        self.creatingOriginalArrowDict(arrow_info_original)
    
    def creatingOriginalArrowDict(self,arrow_info_original):
         # Ensure the patient ID level exists
        if self.patientID not in self.arrowStorageDictOriginal:
            self.arrowStorageDictOriginal[self.patientID] = {}

        # Ensure the patient series name level exists
        if self.patientSeriesName not in self.arrowStorageDictOriginal[self.patientID]:
            self.arrowStorageDictOriginal[self.patientID][self.patientSeriesName] = {}

        # Ensure the image index level exists
        if self.canvasIndex not in self.arrowStorageDictOriginal[self.patientID][self.patientSeriesName]:
            self.arrowStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex] = {}

        if self.imageIndex not in self.arrowStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.arrowStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []
        # Now that we've ensured all levels exist, append the arrow information
        self.arrowStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(arrow_info_original)
    
    def giveArrowStorageDict(self):
        return self.arrowStorageDict
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
    def getArrowActivation(self):
        return  self.mainWindow.giveArrowActivation()
    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     image_path = "case1_008.dcm"
#     main = ArrowTool(image_path)  # You can adjust this value
#     sys.exit(app.exec_())