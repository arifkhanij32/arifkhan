#   convert explicit big to explicit little###########################################
import os
import pydicom
from pydicom.uid import ExplicitVRLittleEndian, ExplicitVRBigEndian
import numpy as np
from imageProcess.imageProcessing import imageDisplay
from PyQt5.QtCore import QTimer
import collections


def DicomToLittleExplicit(self,dicom_path, output_folder):
    try:
        folderName = dicom_path[0].split("/")[-1].split("\\")[-2]
    except:
        folderName = dicom_path.split("/")[-1].split("\\")[-2]

    output_subfolder = os.path.join(output_folder, folderName)
    os.makedirs(output_subfolder, exist_ok=True)
    try:
        for path in dicom_path:
            fileName = path.split("\\")[-1]
            ds = pydicom.dcmread(path)
            processedPath = imageDisplay(ds)
            image = processedPath
            
            if "PixelData" in ds:
                if ds.file_meta.TransferSyntaxUID == ExplicitVRBigEndian:
                    # Ensure the length of the pixel data is even
                    pixel_data = ds.PixelData
                    if len(pixel_data) % 2 != 0:
                        pixel_data += b"\0"
                    # Use numpy to efficiently swap the bytes
                    pixel_array = np.frombuffer(pixel_data, dtype=np.uint16).copy()
                    pixel_array.byteswap(inplace=True)
                    ds.PixelData = pixel_array.tobytes()

            ds.is_little_endian = True
            ds.is_implicit_VR = False
            ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
            path = os.path.join(output_subfolder, f"{fileName}")
            ds.save_as(path, write_like_original=False)
    except:
        fileName = dicom_path.split("\\")[-1]
        ds = pydicom.dcmread(dicom_path)
        processedPath = imageDisplay(ds)
        image = processedPath
        
        if "PixelData" in ds:
            if ds.file_meta.TransferSyntaxUID == ExplicitVRBigEndian:
                # Ensure the length of the pixel data is even
                pixel_data = ds.PixelData
                if len(pixel_data) % 2 != 0:
                    pixel_data += b"\0"
                # Use numpy to efficiently swap the bytes
                pixel_array = np.frombuffer(pixel_data, dtype=np.uint16).copy()
                pixel_array.byteswap(inplace=True)
                ds.PixelData = pixel_array.tobytes()

        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        path = os.path.join(output_subfolder, f"{fileName}")
        ds.save_as(path, write_like_original=False)
    
        
