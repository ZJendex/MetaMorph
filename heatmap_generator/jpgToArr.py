import cv2
import numpy as np

def getCompressedJpgToGreyArr(compressedJpgPath):
    img = cv2.imread(compressedJpgPath)
    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Threshold the image to create a binary mask
    _, thresh = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    arr = np.asarray(thresh)
    return arr

# Load the image
img = cv2.imread('IMG_74CD2F752CE5-1.jpeg')

# Resize the image to a smaller size of 100x100
resized = cv2.resize(img, (1000, 1000))

# Save the compressed image
cv2.imwrite('compressed_image2.jpg', resized)

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# Threshold the image to create a binary mask
_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

# Convert the binary mask to a 2D NumPy array
arr = np.asarray(thresh)

# print(arr.shape)
# arr = arr[:arr.shape[0], :arr.shape[0]]
# print(arr.shape)
# for ar in arr:
#     for a in ar:
#         if a != 0:
#             print(a)




