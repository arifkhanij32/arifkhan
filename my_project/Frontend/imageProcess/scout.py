import numpy as np

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
        main_direction = "transverse"
    #print(main_index)
    return main_direction

def frame_cond(scrDcm,dstDcm):
    if scrDcm.FrameOfReferenceUID == dstDcm.FrameOfReferenceUID:
        return True
    else:
        return False

def orientaion_cond(scrDcm,dstDcm):
    scrDirection = identify_orientation(scrDcm)
    dstDirection = identify_orientation(dstDcm)
    if scrDirection == dstDirection:
        return False # "Images are parallel"
    else:
        return True # "Images are localisable" #draw_scout(scrDcm,dstDcm)
    
def is_orthogonal(scrDcm,dstDcm):
    is_ortho = orientaion_cond(scrDcm,dstDcm)
    is_frame = frame_cond(scrDcm,dstDcm)
    #print("Ortho:"+str(is_ortho))
    #print("Frame:"+str(is_frame))

    if is_ortho and is_frame is True:
        return True    
    else:
        return False
    

def matrix_inversion(originalImage):
    transformed = np.linalg.inv(originalImage)
    return transformed


def transformPatientPointToImage(patientToImageSpace,patientPoint):
    patientVector = np.array([patientPoint[0],patientPoint[1],patientPoint[2],1])
    transformed = np.dot(patientToImageSpace,patientVector)
    return transformed[0,0],transformed[0,1]


def intersection_localizer_method(scrDcm,dstDcm):
    "Intersection Localizer method"
    scrRowDircosX,scrRowDircosY,scrRowDircosZ = scrDcm.ImageOrientationPatient[:3]
    scrColDircosX,scrColDircosY,scrColDircosZ = scrDcm.ImageOrientationPatient[3:]

    scrRows = scrDcm.Rows
    scrCols = scrDcm.Columns

    scrRowSpacing,scrColSpacing = scrDcm.PixelSpacing
    dstRowSpacing,dstColSpacing = dstDcm.PixelSpacing
    
    dstPosX,dstPosY,dstPosZ = dstDcm.ImagePositionPatient
    dstRowDircosX,dstRowDircosY,dstRowDircosZ = dstDcm.ImageOrientationPatient[:3]
    dstColDircosX,dstColDircosY,dstColDircosZ = dstDcm.ImageOrientationPatient[3:]

    dstNrmDircosX = dstRowDircosY * dstColDircosZ - dstRowDircosZ * dstColDircosY
    dstNrmDircosY = dstRowDircosZ * dstColDircosX - dstRowDircosX * dstColDircosZ 
    dstNrmDircosZ = dstRowDircosX * dstColDircosY - dstRowDircosY * dstColDircosX 

    imageToPatientSpace = np.matrix([
        [dstRowDircosX*dstRowSpacing,dstColDircosX*dstColSpacing,dstNrmDircosX,dstPosX],
        [dstRowDircosY*dstRowSpacing,dstRowDircosY*dstColSpacing,dstNrmDircosY,dstPosY],
        [dstRowDircosZ*dstRowSpacing,dstRowDircosZ*dstColSpacing,dstNrmDircosZ,dstPosZ],
        [0, 0, 0, 1],
    ])

    patientToImageSpace = matrix_inversion(imageToPatientSpace)


    dstPointTopLeftX = dstDcm.ImagePositionPatient[0]
    dstPointTopLeftY = dstDcm.ImagePositionPatient[1]
    dstPointTopLeftZ = dstDcm.ImagePositionPatient[2]
           
    scrPointTopLeftX = scrDcm.ImagePositionPatient[0]
    scrPointTopLeftY = scrDcm.ImagePositionPatient[1]
    scrPointTopLeftZ = scrDcm.ImagePositionPatient[2]

    scrPointTopRightX = scrPointTopLeftX + scrRowDircosX *scrRowSpacing*scrRows
    scrPointTopRightY = scrPointTopLeftY + scrRowDircosY *scrRowSpacing*scrRows
    scrPointTopRightZ = scrPointTopLeftZ + scrRowDircosZ *scrRowSpacing*scrRows

    scrPointBottomLeftX = scrPointTopLeftX + scrColDircosX * scrColSpacing*scrCols
    scrPointBottomLeftY = scrPointTopLeftY + scrColDircosY * scrColSpacing*scrCols
    scrPointBottomLeftZ = scrPointTopLeftZ + scrColDircosZ * scrColSpacing*scrCols

    scrPointBottomRightX = scrPointBottomLeftX + scrRowDircosX *scrRowSpacing*scrRows
    scrPointBottomRightY = scrPointBottomLeftY + scrRowDircosY *scrRowSpacing*scrRows
    scrPointBottomRightZ = scrPointBottomLeftZ + scrRowDircosZ *scrRowSpacing*scrRows

    nPX = dstNrmDircosX * dstPointTopLeftX
    nPY = dstNrmDircosY * dstPointTopLeftY
    nPZ = dstNrmDircosZ * dstPointTopLeftZ

    nAX = round(dstNrmDircosX * scrPointTopLeftX,2)  
    nAY = round(dstNrmDircosY * scrPointTopLeftY,2) 
    nAZ = round(dstNrmDircosZ * scrPointTopLeftZ,2) 

    nBX = round(dstNrmDircosX * scrPointTopRightX,2) 
    nBY = round(dstNrmDircosY * scrPointTopRightY,2) 
    nBZ = round(dstNrmDircosZ * scrPointTopRightZ,2) 

    nCX = round(dstNrmDircosX * scrPointBottomRightX,2) 
    nCY = round(dstNrmDircosY * scrPointBottomRightY,2) 
    nCZ = round(dstNrmDircosZ * scrPointBottomRightZ,2) 

    nDX = round(dstNrmDircosX * scrPointBottomLeftX,2)
    nDY = round(dstNrmDircosY * scrPointBottomLeftY,2)
    nDZ = round(dstNrmDircosZ * scrPointBottomLeftZ,2)

    epsilon = 1e-10
    lst_proj = []

    # Segment AB
    if abs(nBX - nAX) > epsilon or (nBY - nAY)>epsilon:
        tX = (nPX - nAX) / (nBX - nAX)
        tY = (nPY - nAY) / (nBY - nAY)
        tZ = (nPZ - nAZ) / (nBZ - nAZ)

        xAB = scrPointTopLeftX + tX * (scrPointTopRightX - scrPointTopLeftX)
        yAB = scrPointTopLeftY  + tY * (scrPointTopRightY - scrPointTopLeftY)
        zAB = scrPointTopLeftZ  + tZ * (scrPointTopRightZ - scrPointTopLeftZ)

        lst_proj.append((round(xAB,2), round(yAB,2), round(zAB,2)))

    # Segment BC            
    if abs(nCX - nBX) >epsilon or (nCY - nBY)>epsilon:
        
        tX = (nPX - nBX) / (nCX - nBX)
        tY = (nPY - nBY) / (nCY - nBY)
        tZ = (nPZ - nBZ) / (nCZ - nBZ)


        xBC = scrPointTopRightX + tX * (scrPointBottomRightX - scrPointTopRightX)
        yBC = scrPointTopRightY + tY * (scrPointBottomRightY - scrPointTopRightY)
        zBC = scrPointTopRightZ + tZ * (scrPointBottomRightZ - scrPointTopRightZ)

        lst_proj.append((round(xBC,2),round(yBC,2), round(zBC,2)))

    # Segment CD
    if abs(nDX - nCX) >epsilon or (nDY - nCY)>epsilon:

        tX = (nPX - nCX) / (nDX - nCX)
        tY = (nPY - nCY) / (nDY - nCY)
        tZ = (nPZ - nCZ) / (nDZ - nCZ)


        xCD = scrPointBottomRightX + tX * (scrPointBottomLeftX - scrPointBottomRightX)
        yCD = scrPointBottomRightY + tY * (scrPointBottomLeftY - scrPointBottomRightY)
        zCD = scrPointBottomRightZ + tZ * (scrPointBottomLeftZ - scrPointBottomRightZ)

        lst_proj.append((round(xCD,2), round(yCD,2), round(zCD,2)))    

    # Segment DA
    if abs(nAX - nDX) >epsilon or (nAY - nDY)>epsilon:
        tX = (nPX - nDX) / (nAX - nDX)
        tY = (nPY - nDY) / (nAY - nDY)
        tZ = (nPZ - nDZ) / (nAZ - nDZ)


        xDA = scrPointBottomLeftX + tX * (scrPointTopLeftX - scrPointBottomLeftX)
        yDA = scrPointBottomLeftY + tY * (scrPointTopLeftY - scrPointBottomLeftY)
        zDA = scrPointBottomLeftZ + tZ * (scrPointTopLeftZ - scrPointBottomLeftZ)

        lst_proj.append((round(xDA,2), round(yDA,2), round(zDA,2)))  

    points = []
    for i in range(0,len(lst_proj)):
        points.append(transformPatientPointToImage(patientToImageSpace,lst_proj[i]))

    startPoint = transformPatientPointToImage(patientToImageSpace,lst_proj[0])
    endPoint = transformPatientPointToImage(patientToImageSpace,lst_proj[1])
    return startPoint,endPoint


def rotate(dst_row_dircos_x, dst_row_dircos_y, dst_row_dircos_z,
           dst_col_dircos_x, dst_col_dircos_y, dst_col_dircos_z,
           dst_nrm_dircos_x, dst_nrm_dircos_y, dst_nrm_dircos_z,
           src_pos_x, src_pos_y, src_pos_z):
    dst_pos_x = (dst_row_dircos_x * src_pos_x +
                 dst_row_dircos_y * src_pos_y +
                 dst_row_dircos_z * src_pos_z)
    
    dst_pos_y = (dst_col_dircos_x * src_pos_x +
                 dst_col_dircos_y * src_pos_y +
                 dst_col_dircos_z * src_pos_z)
    
    dst_pos_z = (dst_nrm_dircos_x * src_pos_x +
                 dst_nrm_dircos_y * src_pos_y +
                 dst_nrm_dircos_z * src_pos_z)
        
    return dst_pos_x, dst_pos_y, dst_pos_z


def draw_scout(scrDcm,dstDcm):
    """
    1. Source frame is dataset of the frame, that is viewed by the user
    2. Destination frame is dataset of the scout frame, where the localizer line should be drawn on it
    3. Localizer point contains the points of the localizer rectangle in terms of pixels on destinationFrame
    This is Projection Localiser method Reference: Mc Clunie
    """
    scrPosX,scrPosY,scrPosZ = scrDcm.ImagePositionPatient
    scrRowDircosX,scrRowDircosY,scrRowDircosZ = scrDcm.ImageOrientationPatient[:3]
    scrColDircosX,scrColDircosY,scrColDircosZ = scrDcm.ImageOrientationPatient[3:]

    scrRows = scrDcm.Rows
    scrCols = scrDcm.Columns

    scrRowSpacing,scrColSpacing = scrDcm.PixelSpacing

    srcRowLength = scrRows * scrRowSpacing
    srcColLength = scrCols * scrColSpacing

    dstRowSpacing,dstColSpacing = dstDcm.PixelSpacing
    
    dstPosX,dstPosY,dstPosZ = dstDcm.ImagePositionPatient
    dstRowDircosX,dstRowDircosY,dstRowDircosZ = dstDcm.ImageOrientationPatient[:3]
    dstColDircosX,dstColDircosY,dstColDircosZ = dstDcm.ImageOrientationPatient[3:]

    dstNrmDircosX = dstRowDircosY * dstColDircosZ - dstRowDircosZ * dstColDircosY
    dstNrmDircosY = dstRowDircosZ * dstColDircosX - dstRowDircosX * dstColDircosZ 
    dstNrmDircosZ = dstRowDircosX * dstColDircosY - dstRowDircosY * dstColDircosX 

    # Build a square to project with 4 corners TLHC, TRHC, BRHC, BLHC ...

   
    posX = np.zeros(4,dtype = float)
    posY = np.zeros(4,dtype = float)
    posZ = np.zeros(4,dtype = float)

    # TLHC
    posX[0]=scrPosX
    posY[0]=scrPosY
    posZ[0]=scrPosZ

    # # TRHC

    posX[1]=scrPosX + scrRowDircosX* (srcRowLength)
    posY[1]=scrPosY + scrRowDircosY*(srcRowLength)
    posZ[1]=scrPosZ + scrRowDircosZ*(srcRowLength)

    # # BRHC

    posX[2]=scrPosX + scrRowDircosX*(srcRowLength) + scrColDircosX*(srcColLength)
    posY[2]=scrPosY + scrRowDircosY*(srcRowLength) + scrColDircosY*(srcColLength)
    posZ[2]=scrPosZ + scrRowDircosZ*(srcRowLength) + scrColDircosZ*(srcColLength)

    # #BLHC

    posX[3]=scrPosX + scrColDircosX*(srcColLength)
    posY[3]=scrPosY + scrColDircosY*(srcColLength)
    posZ[3]=scrPosZ + scrColDircosZ*(srcColLength)

    rowPixel = np.zeros(4,dtype = int)
    colPixel = np.zeros(4,dtype = int)
    # To view the source slice from the "point of view" of
	# the target localizer, i.e. a parallel projection of the source
	# onto the target

	# do this by imaging that the target localizer is a view port
	# into a relocated and rotated co-ordinate space, where the
	# viewport has a row vector of +X, col vector of +Y and normal +Z,
	# then the X and Y values of the projected target correspond to
	# row and col offsets in mm from the TLHC of the localizer image!

	# move everything to origin of target
    for i in range(0,4):
        posX[i] -= dstPosX
        posY[i] -= dstPosY
        posZ[i] -= dstPosZ

        # To rotate the row, col and normal vectors
        posX[i], posY[i], posZ[i] = rotate(dstRowDircosX, dstRowDircosY, dstRowDircosZ,
                                         dstColDircosX, dstColDircosY, dstColDircosZ,
                                         dstNrmDircosX, dstNrmDircosY, dstNrmDircosZ,
                                         posX[i], posY[i], posZ[i])
        

        colPixel[i] = int(posX[i]/dstColSpacing + 0.5)
        rowPixel[i] = int(posY[i]/dstRowSpacing + 0.5)


    points = []
    for i in range(0,len(rowPixel)):
        points.append((colPixel[i],rowPixel[i]))

    if np.std(colPixel)> np.std(rowPixel):
        sorted_points = sorted(points, key=lambda point: point[0])
        set_1 = np.array(sorted_points[:2])
        set_2 = np.array(sorted_points[2:])
        startPoint = np.mean(set_1,axis = 0)
        endPoint = np.mean(set_2,axis = 0)
    else:
        sorted_points = sorted(points, key=lambda point: point[1])
        set_1 = np.array(sorted_points[:2])
        set_2 = np.array(sorted_points[2:])
        startPoint = np.mean(set_1,axis = 0)
        endPoint = np.mean(set_2,axis = 0)
   
    return startPoint,endPoint