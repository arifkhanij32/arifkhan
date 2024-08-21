import pydicom
from pydicom.pixel_data_handlers import util
import numpy as np
import traceback

def windowParameterChoose(windowParameter):
    if type(windowParameter) == pydicom.multival.MultiValue:
        return int(windowParameter[0])
    else:
        return int(windowParameter)


def imageDisplay(dicom_image=None,data=None,level=None,width=None):
    # print("inside image processinggggggg")
    # print (dicom_image)
    # print("image processing")
    try:
        media_class = dicom_image.file_meta.MediaStorageSOPClassUID
        # print(media_class_file)

        temp = pydicom.uid.UID_dictionary
        modality = dicom_image.Modality

        media_class_name = temp[media_class][0]
        if data is None:
            # print("noneee")
            if media_class_name == "Secondary Capture Image Storage":
                image = dicom_image.pixel_array
            if modality == "CT" and media_class_name == "CT Image Storage":
                slope = dicom_image.RescaleSlope
                # print(slope)
                intercept = dicom_image.RescaleIntercept
                # print(intercept)
                
                level = windowParameterChoose(dicom_image.WindowCenter)
                window = windowParameterChoose(dicom_image.WindowWidth)
                vmin = level - window / 2
                vmax = level + window / 2
                image = dicom_image.pixel_array
                image = image * slope + intercept
                image[image < vmin] = vmin
                image[image > vmax] = vmax

            if dicom_image.PhotometricInterpretation=='MONOCHROME1':
                dimage= dicom_image.pixel_array
                image=(np.max(dimage) - dimage)
                return image       
            
            if modality == "MRI" or "MR":
                arr = dicom_image.pixel_array
                # Apply rescale operation (if required, otherwise returns arr unchanged)
                rescaled_arr = util.apply_modality_lut(arr, dicom_image)
                # Apply windowing operation (if required, otherwise returns arr unchanged)
                image = util.apply_voi_lut(rescaled_arr, dicom_image, index=0)
            return image
        else:
            # print("not noneeeee")
            if media_class_name == "Secondary Capture Image Storage":
                image = data
            if modality == "CT" and media_class_name == "CT Image Storage":
                slope = dicom_image.RescaleSlope
                # print(slope)
                intercept = dicom_image.RescaleIntercept
                # print(intercept)
                if level is None :
                    level = windowParameterChoose(dicom_image.WindowCenter)
                else:
                    level=level
                if width is None:
                    window = windowParameterChoose(dicom_image.WindowWidth)
                else:
                    window=width
                # print("level,width",level,window)
                vmin = level - window / 2
                vmax = level + window / 2
                image = data
                image = image * slope + intercept
                image[image < vmin] = vmin
                image[image > vmax] = vmax

            if dicom_image.PhotometricInterpretation=='MONOCHROME1':
                dimage= data
                image=(np.max(dimage) - dimage)
                return image       
            
            if modality == "MRI" or "MR":
                # print("mrrrrrr")
                arr = data
                # Apply rescale operation (if required, otherwise returns arr unchanged)
                rescaled_arr = util.apply_modality_lut(arr, dicom_image)
                # Apply windowing operation (if required, otherwise returns arr unchanged)
                image = util.apply_voi_lut(rescaled_arr, dicom_image, index=0)
            
            return image
    except:
        print("image prcessing traceback",traceback.format_exc())
    
def adjust_brightness(image, levelB, widthB):
    img_min = levelB - widthB // 2  # minimum HU level
    img_max = levelB + widthB // 2  # maximum HU level
    image[image < img_min] = img_min  # set img_min for all HU levels less than minimum HU level
    image[image > img_max] = img_max  # set img_max for all HU levels higher than maximum HU level
    image = (image - img_min) / (img_max - img_min) * 255.0
    return image

def identify_orientation(dcm):
        image_ori = dcm.ImageOrientationPatient
        image_y = np.array([image_ori[0], image_ori[1], image_ori[2]])
        image_x = np.array([image_ori[3], image_ori[4], image_ori[5]])
        image_z = np.cross(image_x, image_y)
        abs_image_z = abs(image_z)
        main_index = list(abs_image_z).index(max(abs_image_z))
        if main_index == 0:
            main_direction = "sagittal"
        elif main_index == 1:
            main_direction = "coronal"
        else:
            main_direction = "axial"
        return main_direction
    
def check_orthogonal(dcm1,dcm2):
    dcm1_orientation = identify_orientation(dcm1)
    dcm2_orientation = identify_orientation(dcm2)
    if dcm1_orientation == dcm2_orientation:
        return True
    else:
        return False
    
def windowing(levelP,widthP,image):
    vmin = int(levelP) - int(widthP) / 2
    vmax = int(levelP) + int(widthP) / 2

    image[image < vmin] = vmin
    image[image > vmax] = vmax

    return image

# def isInversionButtonClicked(shouldReset, inversionOn, shouldResetRotation,rows, cols, event = None ):
#         self.shouldReset=False
#         self.inversionOn = not self.inversionOn

#         try:
#             self.shouldResetRotation[self.index] = False
#             if self.rows == 1 and self.cols == 1:
#                 if self.isMaximized==False:
#                     self.new_index= self.widget.currentIndex
#                     a = self.widget
#                     b = self.processedSeriesDicom
#                     for i in self.selected_images.keys():
#                         self.inversionDict[i] = True
#                         if self.inversionDict[i]:
#                             b[i] = np.max(b[i]) - b[i]
#                 else:
#                     self.new_index= self.selectedWidget.currentIndex                      
#                     a = self.selectedWidget
#                     b = self.psdListDict[self.index]
#                     for i in self.selected_subplots[self.index].keys():
#                         self.inversionDict[i] = True
#                         if self.inversionDict[i]:
#                             b[i] = np.max(b[i]) - b[i]
#                 a.show_image_by_index(self.new_index)
#             else:
#                 if not self.singleSeriesLayoutBool:
#                     self.new_index= self.selectedWidget.currentIndex
#                     a = self.selectedWidget
#                     b = self.psdListDict[self.index]
#                     for i in self.selected_subplots[self.index].keys():
#                         self.inversionDict[i] = True
#                         if self.inversionDict[i]:
#                             b[i] = np.max(b[i]) - b[i]
#                     a.show_image_by_index(self.new_index)

#                 else:
#                     self.new_index= self.selectedWidget.fourIndex
#                     a = self.selectedWidget
#                     b = self.processedSeriesDicom
                    

#                     # 
#                     for i in self.selected_images.keys():
#                         # 
#                         # 
#                         # self.inversionDict[self.ii] = True
#                         # if self.inversionDict[self.ii]:
#                         b[i] = np.max(b[i]) - b[i]

#                     # for i , w in enumerate(self.subplotWidget):
#                     #     self.selectedWidget.show_image_by_index(self.ii, loadInd = i )

#                     # for i, widget in enumerate(self.subplotWidget):
#                     #     # self.selectWidget(widget)
#                     #     self.selectedWidget.show_image_by_index(self.ii,fourIndex =i,loadInd = i)
#                     #     widget.update()
#                     #     widget.repaint()
#                     if self.wheelEventBool == False:


#                         for i,wid in enumerate(self.subplotWidget):
#                             wid.show_image_by_index(0,loadInd = i,fourIndex=i)
#                     else:
#                         for i,widget in enumerate(self.subplotWidget):
#                             self.selectWidget(widget)
#                             widget.show_image_by_index(self.selectedWidget.currentIndex)
#                             widget.update()
#                             widget.repaint()

#                         for i, wid in enumerate(self.subplotWidget): 
#                             wid.show_image_by_index(self.ii-self.index , i)
#         except:
#             print("traceback", traceback.format_exc())