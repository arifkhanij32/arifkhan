import numpy as np
from .constants import *


class SmartPointerPlot:
    def __init__(self, smartPointActivated, canvas, ax,parent,total_widgets):
        super().__init__()
        self.smartPointActivated = smartPointActivated
        self.canvas = canvas
        self.ax = ax
        #self.figure = figure
        #self.dicom_image = imgDCM
                
        self.mainWindow=parent
        self.pointer_pos = None
        self.smart_pointer_elements = []
        self.total_widgets = total_widgets
        # self.image = image
        self.is_dragging = False  # Flag to track when the mouse is being dragged
        
        
        for i in self.mainWindow.subplotCanvases:
            self.cid_click = i.mpl_connect('button_press_event', self.on_Press)
            self.cid_release = i.mpl_connect('button_release_event', self.on_release)
            self.cid_motion = i.mpl_connect('motion_notify_event', self.on_Move)

        
        
    def draw_pointer(self, x, y,i):
        self.clear_smart_pointer()
        gap = 5  # Adjust gap size relative to your data's scale
        line_length = 15  # Adjust line length
        self.ax = self.mainWindow.subplotAxes[i]
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        aspect = self.ax.get_aspect()
        # Drawing smart pointer
        self.lines = [
            self.ax.plot([x - gap - line_length, x - gap], [y, y], color=LINE_COLOR)[0],
            self.ax.plot([x + gap, x + gap + line_length], [y, y], color=LINE_COLOR)[0],
            self.ax.plot([x, x], [y - gap - line_length, y - gap], color=LINE_COLOR)[0],
            self.ax.plot([x, x], [y + gap, y + gap + line_length], color=LINE_COLOR)[0]
        ]
        self.smart_pointer_elements.extend(self.lines)
        self.mainWindow.subplotCanvases[i].draw_idle()
        #self.mainWindow.subplotCanvases[i].blit()
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)
        self.ax.set_aspect(aspect)

    def load_dicom_metadata(self,dicom_file):
        ds = dicom_file
    
        position = np.array(ds.ImagePositionPatient, dtype=np.float64)
        orientation = np.array(ds.ImageOrientationPatient, dtype=np.float64)
        pixel_spacing = np.array(ds.PixelSpacing, dtype=np.float64)
        return position, orientation, pixel_spacing

    def patient_coordinate(self,x, y, position, orientation, pixel_spacing): # verified correction
        row_cosines = orientation[:3]
        col_cosines = orientation[3:]
        patient_coord = position + x * pixel_spacing[0] * row_cosines + y * pixel_spacing[1] * col_cosines
        return patient_coord

    def patient_to_pixel_coordinate(self,patient_coord, position, orientation, pixel_spacing):
        row_cosines = orientation[:3]
        col_cosines = orientation[3:]
        delta = patient_coord - position
        x = np.dot(delta, row_cosines) / pixel_spacing[0]
        y = np.dot(delta, col_cosines) / pixel_spacing[1]
        return int(round(x)), int(round(y))
   
        
    def image_to_patient_space_matrix(self,iop,pxl_spacing,ipp,delta_x,delta_y,delta_z ):
        px = pxl_spacing[0]
        py = pxl_spacing[1]
        row_cosine = iop[:3]
        col_cosine = iop[3:]
        affine = np.matrix(
                    [
                        [row_cosine[0] * px, col_cosine[0] * py, delta_x, ipp[0]],
                        [row_cosine[1] * px, col_cosine[1] * py, delta_y, ipp[1]],
                        [row_cosine[2] * px, col_cosine[2] * py, delta_z, ipp[2]],
                        [0, 0, 0, 1],
                    ]
                )
        return affine
        
    def ipp_vector(self,dicom_series):
        positions = []

        for dicom_file in dicom_series:
            position, orientation, pixel_spacing = self.load_dicom_metadata(dicom_file)
            positions.append(position)

        # Convert the positions list to a NumPy array for vectorized operations
        positions = np.array(positions, dtype=np.float64)

        delta_positions = np.diff(positions, axis=0)# Calculate the differences (deltas) along each axis

        rounded_deltas = np.round(delta_positions, 2)# Round the differences to 2 decimal places

        try:
            all_equal_deltas = np.all(rounded_deltas == rounded_deltas[0], axis=0)
            if all_equal_deltas.all():
                return delta_positions[0], True  # Return the consistent delta vector
            else:
                return delta_positions[0], False  # Indicate inconsistency in position deltas
        except IndexError:
            return None, False

    def invert_matrix(self,affine):
        return np.linalg.inv(affine)
    
    def find_correspond_slice(self,src_patient_coord, dicom_series_dst):
        ipp_vector_output, condition = self.ipp_vector(dicom_series_dst)
        if not condition:
            print("IPP vector is inconsistent")
            return
        
        dicom_dst = dicom_series_dst[0]

        position, orientation, pixel_spacing = self.load_dicom_metadata(dicom_dst)
        delta_x, delta_y, delta_z = ipp_vector_output
        i2p_matrix = self.image_to_patient_space_matrix(orientation, pixel_spacing, position, delta_x, delta_y, delta_z)

        p2i_matrix = self.invert_matrix(i2p_matrix)
        final_output = p2i_matrix @ np.append(src_patient_coord, 1)  # Using @ for matrix multiplication

        return final_output[0]

    def src_pxl_space(self,src_series, x, y):
        #ipp_vector_output, condition = self.ipp_vector(src_series) 
        
        #if condition:
        for src_dicom_file in src_series:
            position, orientation, pixel_spacing = self.load_dicom_metadata(src_dicom_file)
            pt_coord_src = self.patient_coordinate(x, y, position, orientation, pixel_spacing)
            return pt_coord_src, True
        #return None, False

        

    def draw_reference_pointer(self,x,y,i,image_no):
        image_no=int(image_no)

        self.ax = self.mainWindow.subplotAxes[i]
        gap = 5  # Adjust gap size relative to your data's scale
        line_length = 15  # Adjust line length
        self.psdlist=self.getgivepsdListDict()
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        aspect = self.ax.get_aspect()
        try:
            data=self.psdlist[i][image_no]
            data=np.array(data)
            #self.ax.plot(dicom_file)
            self.ax.imshow(data, cmap='gray')
        
            # Drawing smart pointer
            self.plines = [
                self.ax.plot([x - gap - line_length, x - gap], [y, y], color=LINE_COLOR,linestyle="--")[0],
                self.ax.plot([x + gap, x + gap + line_length], [y, y], color=LINE_COLOR,linestyle="--")[0],
                self.ax.plot([x, x], [y - gap - line_length, y - gap], color=LINE_COLOR,linestyle="--")[0],
                self.ax.plot([x, x], [y + gap, y + gap + line_length], color=LINE_COLOR,linestyle="--")[0]
            ]
            self.smart_pointer_elements.extend(self.plines)
            # self.canvas.draw()
            # for can in self.mainWindow.subplotCanvases:
            self.mainWindow.subplotCanvases[i].draw_idle()
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
            self.ax.set_aspect(aspect)

        except IndexError as e:
            pass

        
        
    def clear_smart_pointer(self,restore_background=False):
        for element in self.smart_pointer_elements:
            element.remove()
        self.smart_pointer_elements.clear() 
        
        if restore_background:
            for can in self.mainWindow.subplotCanvases:
                #can.draw()
                can.blit(self.ax.bbox)

        
    def on_Press(self, event):          
        self.ax=self.giveCurrentAxes()
        self.canvas=self.getCanvas()
        self.index = self.getIndex()
        self.index = self.getIndex()
        self.smartPointActivated=self.getSmartPointerActivation()
        self.dicomListDict = self.getgivedicomListDict()       

        if self.smartPointActivated:
            if event.inaxes == self.ax:
                self.is_dragging = True
                self.pointer_pos = (event.xdata, event.ydata)
                selected_image = self.dicomListDict[self.index][self.mainWindow.selectedWidget.currentIndex]
                self.draw_pointer(event.xdata, event.ydata,self.index)

                position, orientation, pixel_spacing = self.load_dicom_metadata(selected_image)
                patient_coord = self.patient_coordinate(event.xdata,event.ydata, position, orientation, pixel_spacing)


                for i in range(self.total_widgets):
                    if i != self.index:
                        unselected_img_series = self.dicomListDict[i] 
                       
                        smt_output = self.find_correspond_slice(patient_coord, unselected_img_series)
                        if smt_output is not None:
                            x = smt_output[0, 0]
                            y = smt_output[0, 1]
                            instanceNo = smt_output[0, 2]
                        
                            self.draw_reference_pointer(int(x), int(y),i,instanceNo)
                        else:
                            print("smt_output is none")
                    
    

    def on_release(self, event):
        self.is_dragging = False

    def on_Move(self, event):
        self.ax = self.giveCurrentAxes()
        self.canvas=self.getCanvas()
        self.index = self.getIndex()
        self.smartPointActivated=self.getSmartPointerActivation()
        self.dicomListDict = self.getgivedicomListDict()
        
        
        #self.ax = self.giveCurrentAxes()
        #self.canvas=self.getCanvas()
        #self.index = self.getIndex()
        #self.smartPointActivated=self.getSmartPointerActivation()
        #self.dicomListDict = self.getgivedicomListDict()
        
        
        if event.inaxes == self.ax:
            if self.is_dragging and event.inaxes == self.ax:

                self.pointer_pos = (event.xdata, event.ydata)
                selected_image = self.dicomListDict[self.index][self.mainWindow.selectedWidget.currentIndex]

                self.draw_pointer(event.xdata, event.ydata,self.index)
                position, orientation, pixel_spacing = self.load_dicom_metadata(selected_image)
                patient_coord = self.patient_coordinate(event.xdata,event.ydata, position, orientation, pixel_spacing)


                for i in range(self.total_widgets):
                    if i != self.index:
                        # unselected_image = self.dicomListDict[i][self.mainWindow.widget.currentIndex] 
                        unselected_img_series = self.dicomListDict[i] 
                        smt_output = self.find_correspond_slice(patient_coord, unselected_img_series)
                        if smt_output is not None:
                            x = smt_output[0, 0]
                            y = smt_output[0, 1]
                            instanceNo = smt_output[0, 2]
                        
                            self.draw_reference_pointer(int(x), int(y),i,instanceNo)
                        else:
                            print("smt_output is none")
    
                self.ax.autoscale(False) 
                
    def giveCurrentAxes(self):
        return self.mainWindow.giveAxes()
    def getCanvas(self):
        return self.mainWindow.giveCanvas()
    
    def getSmartPointerActivation(self):
        return self.mainWindow.giveSmartPointerActivation()
    
    def getCanvaIndex(self):
        return self.mainWindow.giveCurrentCanvas()
    
    def getIndex(self):
        return self.mainWindow.giveIndex()
    
    def getTotalWidget(self):
        return self.mainWindow.giveTotalWidgets()
    
    def getgivedicomListDict(self):
        return self.mainWindow.giveDicomListDict()
    
    def getgivepsdListDict(self):
        return self.mainWindow.givePsdListDict()
