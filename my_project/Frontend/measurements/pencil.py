from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt
from .constants import *
import sqlite3
import uuid
import copy


class PencilTool(QMainWindow):
    def __init__(self, freeHandButtonActivated, canvas, ax, figure, imgDCM,parent):
        super().__init__()

        self.freeHandButtonActivated = freeHandButtonActivated
        self.canvas = canvas
        self.ax = ax
        self.figure = figure
        self.dicom_image = imgDCM
        self.py, self.px = self.dicom_image.PixelSpacing
        self.pixel_data = self.dicom_image.pixel_array
        self.mainWindow=parent
        self.freeHandStorageDict = {}
        self.freeHandStorageDictOriginal = {}

        self.delDbList=[]
        self.is_drawing = False
        self.hovered_line = None
        self.clicked_line = None  # Store the currently hovered line
        self.xs = list()
        self.ys = list()
        
        self.selectedFreeHandIndex = None
        self.selecteduid=None
        self.freeHandId=0
        self.setupEventConnections()

    def setupEventConnections(self):
        try:
            # Connect key press event
            self.canvas.mpl_connect("key_press_event", self.DeletePressEvent)
        except:
            pass






        # self.canvas.mpl_connect("button_press_event", self.on_press)
        # self.canvas.mpl_connect("motion_notify_event", self.on_move)
        # self.canvas.mpl_connect("key_press_event", self.DeletePressEvent)

        # Connect the mouse events to the drawing functions
        # self.cidpress = self.canvas.mpl_connect('button_press_event', self.on_press)
        # self.cidrelease = self.canvas.mpl_connect('button_release_event', self.on_release)
        # self.cidmotion = self.canvas.mpl_connect('motion_notify_event', self.on_move)
        # self.cidKeyPress = self.canvas.mpl_connect("key_press_event", self.DeletePressEvent)

        
    def dbConnection(self):
            mydb = sqlite3.connect("mainApplication.db")
            return mydb
    
    def on_press(self, event):
        self.freeHandButtonActivated=self.getFreeHandActivation()
        self.selectedFreeHandIndex = None
        self.selecteduid=None
        self.is_drawing = False
        self.xs = list()
        self.ys = list()
        (self.line,) = self.ax.plot(
            [], [], "-", color=LINE_COLOR,linewidth=LINE_WIDTH
        )  # Initialize an empty line
        self.hovered_line = None
        self.clicked_line = None  # Store the currently hovered line
        if self.freeHandButtonActivated:
            if event.button == Qt.LeftButton:
                self.ax=self.getAxes()
                self.canvas=self.getCanvas()
                self.imageIndex = self.getimageIndex()
                self.patientID = self.getPatientID()
                self.patientSeriesName = self.getPatientSeriesName()
                if event.inaxes != self.ax:
                    return
                self.is_drawing = True
                clicked_line = None

                # Check if the click point is inside any line
                for line in self.ax.lines:
                    contains, _ = line.contains(event)
                    if contains:
                        self.clicked_line = line
                        break
                if self.clicked_line:
                    # Change the color of the clicked line to red
                    self.clicked_line.set_color(CLICKED_LINE_COLOR)
                    self.hovered_line = None  # Reset the hovered line
                    self.canvas.draw_idle()
                    # print("1234",self.freeHandStorageDict)
                    for idx, drawing in enumerate(self.freeHandStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex]):
                        if drawing['xs'] == self.clicked_line.get_xdata().tolist() and drawing['ys'] == self.clicked_line.get_ydata().tolist():
                            self.selectedFreeHandIndex = idx
                            self.selecteduid=drawing["uuid"]
                            # print("self.clicked_line",self.selecteduid)
                            break
                else:
                    # Start drawing a new line
                    self.xs.append(event.xdata)
                    self.ys.append(event.ydata)

    def on_move(self, event):
        if self.freeHandButtonActivated:
            if event.inaxes != self.ax:
                return
            if self.is_drawing:
                self.xs.append(event.xdata)
                self.ys.append(event.ydata)
                self.line.set_data(self.xs, self.ys)
                self.canvas.draw()
            else:
                # Check if the mouse is over any line and change its color to yellow
                for line in self.ax.lines:
                    contains, _ = line.contains(event)
                    if contains:
                        if self.hovered_line is not None and self.hovered_line != line:
                            self.hovered_line.set_color(LINE_COLOR)
                        line.set_color(HOVER_LINE_COLOR)
                        self.hovered_line = line
                        self.canvas.draw_idle()
                        return
                # If no line is hovered, set color back to lime
                if self.hovered_line is not None:
                    self.hovered_line.set_color(LINE_COLOR)
                    self.canvas.draw_idle()
                    self.hovered_line = None
        

    def DeletePressEvent(self, event):
        if type(event.key) == str:
            if event.key.lower().strip() == "delete".lower().strip():
                event.key = 16777223
        else:
            pass
        # print("int(Qt.Key_Delete):",Qt.Key_Delete)
        # print("(event.key():",type(event.key())
        if str(event.key) == str(Qt.Key_Delete):
            if self.clicked_line:
                self.remove_arrow(self.clicked_line)
                self.remove_freeHand_from_storage(self.selectedFreeHandIndex,self.selecteduid)

    def remove_arrow(self, drawing):
        if self.freeHandButtonActivated:
            try:
                drawing.remove()
                self.canvas.draw_idle()
            except Exception as ex:
                pass

    def remove_freeHand_from_storage(self, index,uid):
        # print("index",index)
        # print("uid",uid)
        # Remove the freehand drawing at the given index
        try:
            self.delDbList.append(uid)
            # print("self.delDbList=[]",self.delDbList)
            del self.freeHandStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex][index]
            # print("self.delDbList",self.delDbList)
            self.selectedFreeHandIndex = None
            self.selecteduid=None
            return True
        except (IndexError, KeyError):
            return False
        
    def on_release(self, event):
        if self.freeHandButtonActivated:
            if event.inaxes != self.ax:
                return
            self.is_drawing = False
            # Add the line to the Axes and reset the line data
            self.ax.plot(self.xs, self.ys, "-", color=LINE_COLOR,linewidth=LINE_WIDTH)

            self.uid=uuid.uuid4() # 4     
            conn = self.dbConnection()
            cur = conn.cursor()
            query = "SELECT EXISTS(SELECT 1 FROM pencilData WHERE uuid = ?)"
            # Execute the query, replacing '?' with the new_uuid
            cur.execute(query, (str(self.uid),))
            # Fetch the result
            exists = cur.fetchone()[0] 
            # self.text_id+=1
            if self.uid == exists:
                self.uid = uuid.uuid4()
            else :
                pass
            
            self.freeHandStorage(self.xs, self.ys)
            self.freeHandId+=1
            self.line.set_data([], [])
            self.xs, self.ys = [], []  # Clear the points lists
            self.canvas.draw_idle()


    def freeHandStorage(self, xs, ys, uid=None):
            self.imageIndex = self.getimageIndex()
            self.patientID = self.getPatientID()
            self.patientSeriesName = self.getPatientSeriesName()
            self.canvasIndex = self.getCanvaIndex()


            if uid is None:
                freeHand_info = {
                        "index": self.freeHandId,  # Unique index for the freehand diagram
                        "xs": xs,
                        "ys": ys,
                        "uuid":self.uid
                    }

            else:
                freeHand_info = {
                            "index": self.freeHandId,  # Unique index for the freehand diagram
                            "xs": xs,
                            "ys": ys,
                            "uuid":uid
                    }
            
            if uid is None:
                freeHand_info_original = {
                        "index": self.freeHandId,  # Unique index for the freehand diagram
                        "xs": copy.deepcopy(xs),
                        "ys": copy.deepcopy(ys),
                        "uuid":self.uid
                    }

            else:
                freeHand_info_original = {
                            "index": self.freeHandId,  # Unique index for the freehand diagram
                            "xs": copy.deepcopy(xs),
                            "ys": copy.deepcopy(ys),
                            "uuid":uid
                    }
                
            # Ensure the patient ID level exists
            if self.patientID not in self.freeHandStorageDict:
                self.freeHandStorageDict[self.patientID] = {}
            
            # Ensure the patient series name level exists
            if self.patientSeriesName not in self.freeHandStorageDict[self.patientID]:
                self.freeHandStorageDict[self.patientID][self.patientSeriesName] = {}

            if self.canvasIndex not in self.freeHandStorageDict[self.patientID][self.patientSeriesName]:
                self.freeHandStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
            
            # Ensure the image index level exists
            if self.imageIndex not in self.freeHandStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex]:
                self.freeHandStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []

            
            self.freeHandStorageDict[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(freeHand_info)
            
                
            self.creatingFreeHandOriginalDict(freeHand_info_original)

    def creatingFreeHandOriginalDict(self,freeHand_info_original)        :
        if self.patientID not in self.freeHandStorageDictOriginal:
            self.freeHandStorageDictOriginal[self.patientID] = {}
        
        # Ensure the patient series name level exists
        if self.patientSeriesName not in self.freeHandStorageDictOriginal[self.patientID]:
            self.freeHandStorageDictOriginal[self.patientID][self.patientSeriesName] = {}

        if self.canvasIndex not in self.freeHandStorageDictOriginal[self.patientID][self.patientSeriesName]:
            self.freeHandStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex] = {}
        
        # Ensure the image index level exists
        if self.imageIndex not in self.freeHandStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex]:
            self.freeHandStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex] = []

        
        self.freeHandStorageDictOriginal[self.patientID][self.patientSeriesName][self.canvasIndex][self.imageIndex].append(freeHand_info_original)
               
        
            # print("self.freeHandStorageDict",self.freeHandStorageDict)
           
        

    def giveFreeHandStorageDict(self):
        return self.freeHandStorageDict
    
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
    def getFreeHandActivation(self):
        return  self.mainWindow.giveFreeHandActivation()
    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()