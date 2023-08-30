import cv2
import numpy as np

def getCompressedJpgToGreyArr(compressedJpgPath):
    img = cv2.imread(compressedJpgPath)
    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Threshold the image to create a binary mask
    _, thresh = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # invert the image
    # thresh = 1 - thresh
    arr = np.asarray(thresh)
    return arr






