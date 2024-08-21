import numpy as np
import nibabel as nib


def anatomy_position(dcm):
    """
    Reference:
    1. https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.2.html#sect_C.7.6.2.1.2
    2. https://dicomiseasy.blogspot.com/2013/06/getting-oriented-using-image-plane.html
    3. https://nipy.org/nibabel/dicom/dicom_orientation.html
    """

    iop = dcm.ImageOrientationPatient  # Image orientation
    sx, sy, sz = dcm.ImagePositionPatient  # Image position
    row_cosine = iop[:3]
    col_cosine = iop[3:]
    if 'PixelSpacing' in dcm:
        # print("inside pixel spacing")
        px = float(dcm.PixelSpacing[0])
        py = float(dcm.PixelSpacing[1])
        if px and py:
            affine = np.matrix(
                [
                    [-row_cosine[0] * px, -col_cosine[0] * py, 0, sx],
                    [-row_cosine[1] * px, -col_cosine[1] * py, 0, sy],
                    [row_cosine[2] * px, col_cosine[2] * py, 0, sz],
                    [0, 0, 0, 1],
                ]
            )
            opposite_labels = {"R": "L", "L": "R", "A": "P", "P": "A", "S": "I", "I": "S"}
            right, bottom, normal = nib.aff2axcodes(affine)
            top = opposite_labels[bottom]
            left = opposite_labels[right]
            return top, bottom, right, left
    else:
        top=""
        bottom=""
        right=""
        left=""
        return top, bottom, right, left

