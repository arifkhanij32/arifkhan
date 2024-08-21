import numpy as np
import pydicom

def load_dicom_metadata(dicom_file):
    ds = pydicom.dcmread(dicom_file)
    position = np.array(ds.ImagePositionPatient, dtype=np.float64)
    orientation = np.array(ds.ImageOrientationPatient, dtype=np.float64)
    pixel_spacing = np.array(ds.PixelSpacing, dtype=np.float64)
    image_number = ds.InstanceNumber
    return position, orientation, pixel_spacing,image_number

def patient_coordinate(x, y, position, orientation, pixel_spacing): # verified correction
    row_cosines = orientation[:3]
    col_cosines = orientation[3:]
    patient_coord = position + x * pixel_spacing[0] * row_cosines + y * pixel_spacing[1] * col_cosines
    return patient_coord

def image_to_patient_space_matrix(iop,pxl_spacing,ipp,delta_x,delta_y,delta_z ):
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


def ipp_vector(dicom_series):
    positions = []

    for dicom_file in dicom_series:
        position, orientation, pixel_spacing,image_number = load_dicom_metadata(dicom_file)
        positions.append(position)

    # Convert the positions list to a NumPy array for vectorized operations
    positions = np.array(positions, dtype=np.float64)

    delta_positions = np.diff(positions, axis=0)# Calculate the differences (deltas) along each axis

    rounded_deltas = np.round(delta_positions, 2)# Round the differences to 2 decimal places

    all_equal_deltas = np.all(rounded_deltas == rounded_deltas[0], axis=0)

    if all_equal_deltas.all():
        return delta_positions[0],True  # Return the consistent delta vector
    else:
        return delta_positions[0],False  # Indicate inconsistency in position deltas
   

def invert_matrix(affine):
    return np.linalg.inv(affine)


def find_correspond_slice(src_patient_coord, dicom_series_dst):
    ipp_vector_output, condition = ipp_vector(dicom_series_dst)
    if not condition:
        print("IPP vector is inconsistent")
        return

    for dicom_file in dicom_series_dst:
        position, orientation, pixel_spacing, image_number = load_dicom_metadata(dicom_file)
        delta_x, delta_y, delta_z = ipp_vector_output
        i2p_matrix = image_to_patient_space_matrix(orientation, pixel_spacing, position, delta_x, delta_y, delta_z)

        p2i_matrix = invert_matrix(i2p_matrix)
        final_output = p2i_matrix @ np.append(src_patient_coord, 1)  # Using @ for matrix multiplication
        print(f"Image Number: {image_number}, Transformed Coord: {final_output}")
        #estimated_image_index = np.round(final_output[2])
        #print(f"Estimated Image Index (rounded): {estimated_image_index}")


def src_pxl_space(src_series, x, y):
    ipp_vector_output, condition = ipp_vector(src_series)  
    
    if condition:
        for src_dicom_file in src_series:
            position, orientation, pixel_spacing, image_number = load_dicom_metadata(src_dicom_file)
            pt_coord_src = patient_coordinate(x, y, position, orientation, pixel_spacing)
            return pt_coord_src, True
    return None, False

src_series = ['sunview_workstation//frontend//measurements//ASRAF ALI/COR.dcm','sunview_workstation//frontend//measurements//ASRAF ALI/COR1.dcm']
dst_series = ['sunview_workstation//frontend//measurements//ASRAF ALI/SAG1.dcm','sunview_workstation//frontend//measurements//ASRAF ALI/SAG2.dcm','sunview_workstation//frontend//measurements//ASRAF ALI/SAG3.dcm','sunview_workstation//frontend//measurements//ASRAF ALI/SAG4.dcm']

x, y = 102, 151  # example pixel coordinates
pt_coord_src,ipp  = src_pxl_space(src_series,x,y)

find_correspond_slice(pt_coord_src,dst_series)
