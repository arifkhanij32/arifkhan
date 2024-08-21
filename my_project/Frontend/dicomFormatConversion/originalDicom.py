import os
import pydicom
from PyQt5.QtCore import QTimer
import collections



def DicomToOriginal(self,dicom_path, output_folder):
    #self.progressBar.setMaximum(len(dicom_path))
    #self.cdProgressBar.setMaximum(len(dicom_path))
    # current_progress = 0
    try:
        folderName = dicom_path[0].split("/")[-1].split("\\")[-2]
    except:
        folderName = dicom_path.split("/")[-1].split("\\")[-2]

    # print(folderName)
    output_subfolder = os.path.join(output_folder, folderName)
    # print(output_subfolder)
    os.makedirs(output_subfolder, exist_ok=True)
    try:
        for path in dicom_path:
            # current_progress += 1
            #self.progressBar.setValue(current_progress)
            #self.cdProgressBar.setValue(current_progress)
            fileName = path.split("\\")[-1]
            ds = pydicom.dcmread(path)
            path = os.path.join(output_subfolder, f"{fileName}")
            ds.save_as(path, write_like_original=False)
    except:

        fileName = dicom_path.split("\\")[-1]
        ds = pydicom.dcmread(dicom_path)
        path = os.path.join(output_subfolder, f"{fileName}")
        ds.save_as(path, write_like_original=False)
    
    #self.progressBar.setValue(0)
    #self.cdProgressBar.setValue(0)
    #QTimer.singleShot(0, lambda: self.progressBar.setValue(0))
    #QTimer.singleShot(0, lambda: self.cdProgressBar.setValue(0))
    # QTimer.singleShot(0, self.exportCompleteMessage)
     # self.exportCompleteMessage()
        
