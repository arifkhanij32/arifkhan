import pydicom
from pydicom.pixel_data_handlers import util


def windowParameterChoose(windowParameter):
    if type(windowParameter) == pydicom.multival.MultiValue:
        return int(windowParameter[0])
    else:
        return int(windowParameter)


def imageProcess(dicom_image):
    media_class = dicom_image.file_meta.MediaStorageSOPClassUID
    # print(media_class_file)
    temp = pydicom.uid.UID_dictionary
    modality = dicom_image.Modality
    media_class_name = temp[media_class][0]

    if media_class_name == "Secondary Capture Image Storage":
        image = dicom_image.pixel_array

    if modality == "CT" and media_class_name == "CT Image Storage":
        slope = dicom_image.RescaleSlope
        intercept = dicom_image.RescaleIntercept
        level = windowParameterChoose(dicom_image.WindowCenter)
        window = windowParameterChoose(dicom_image.WindowWidth)
        vmin = level - window / 2
        vmax = level + window / 2
        image = dicom_image.pixel_array
        image = image * slope + intercept
        image[image < vmin] = vmin
        image[image > vmax] = vmax

    if modality == "MRI" or modality == "MR":
        arr = dicom_image.pixel_array
        # Apply rescale operation (if required, otherwise returns arr unchanged)
        rescaled_arr = util.apply_modality_lut(arr, dicom_image)
        # Apply windowing operation (if required, otherwise returns arr unchanged)
        image = util.apply_voi_lut(rescaled_arr, dicom_image, index=0)
    return image


def onHover(x, y, dcm):
    # x, y = int(event.xdata), int(event.ydata)
    pixel_array = dcm.pixel_array
    value = pixel_array[x, y]
    # print(value)
    slope = dcm.RescaleSlope
    intercept = dcm.RescaleIntercept

    hu = transform_hu(value, slope, intercept)
    organ = identify_organ(hu)
    # print(f"HU={hu}, Tissue: {organ}")
    # statusBar().showMessage(f"HU: {hu}, Organ: {organ}")
    return organ
    


def transform_hu(dicom_image, slope, intercept):
    hu = dicom_image * slope + intercept
    return hu


def identify_organ(hu):
    """
    Reference:
    1. Porosity Estimation from High Resolution CT SCAN Images of Rock Samples by Using Housfield Unit Nguyen Lam Quoc Cuong et al
    2. Einstein, A., B. Podolsky, and N. Rosen, 1935, “Can quantum-mechanical description of physical reality be considered complete?”, Phys. Rev. 47, 777-780.
    """
    if hu == -1000:
        organ = "Air"
    elif hu == -500:
        organ = "Lung"
    elif hu == 0:
        organ = "Water"
    elif hu == 15:
        organ = "CSF"
    elif hu == 30:
        organ = "Kidney"
    elif hu > -100 and hu < -50:
        organ = "Fat"
    elif hu > 30 and hu < 45:
        organ = "Blood"
    elif hu > 10 and hu < 40:
        organ = "Muscle"
    elif hu > 37 and hu < 45:
        organ = "Grey Matter"
    elif hu > 20 and hu < 30:
        organ = "White Matter"
    # elif hu > 40 and hu < 60:
    #     organ = "Liver"
    elif hu > 100 and hu < 300:
        organ = "Soft Tissue"
    elif hu > 700 and hu < 3000:
        organ = "Cancellous bone"
    elif hu > 3000:
        organ = "Dense bone"
    else:
        organ = " "
    return organ


# dicom_image = pydicom.dcmread('C:/Dicom images/Dicom/brain')
# slope = dicom_image.RescaleSlope
# intercept = dicom_image.RescaleIntercept
# image_display = imageProcess(dicom_image)
# plt.imshow(image_display, cmap=plt.cm.gray)
# fig = plt.gcf()
# cid = fig.canvas.mpl_connect('button_press_event', onclick)

# plt.show()
