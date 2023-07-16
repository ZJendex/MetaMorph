import skimage.io

# Load the image
img = skimage.io.imread('floorPlan.jpg')
from skimage.segmentation import clear_border, mark_boundaries
from skimage.measure import label, regionprops
from skimage.color import label2rgb
from skimage.filters import threshold_otsu
import numpy as np
from skimage.util import crop
from skimage.transform import resize
from skimage.morphology import erosion, dilation, square
from skimage.measure import find_contours

# Convert the image to grayscale
gray = skimage.color.rgb2gray(img)

# Threshold the image to create a binary mask
thresh = threshold_otsu(gray)
binary = gray <= thresh

'''
Remove the Artifacts
'''
# Remove artifacts connected to image border
cleared = clear_border(binary)

# Label image regions
label_image = label(cleared)

# Get properties of labeled regions
regions = regionprops(label_image)

# Select the relevant region(s) based on their properties
relevant_regions = []
for region in regions:
    if region.area > 1000 and region.eccentricity < 0.9:
        relevant_regions.append(region)

# Create a mask for the relevant regions
relevant_mask = np.zeros_like(label_image)
for region in relevant_regions:
    relevant_mask += (label_image == region.label)

max_area = 0
max_region = None
for region in regions:
    if region.area > max_area:
        max_area = region.area
        max_region = region
relevant_mask2 = (label_image == max_region.label)

# Overlay the mask on the original image to visualize the selected regions
overlay = mark_boundaries(img, relevant_mask)


'''
crop the image to square
'''
# Select a square region from the center of the image
# cleared = relevant_mask
# min_size = min(cleared.shape)
# center = [s // 2 for s in cleared.shape]
# cropped = crop(cleared, ((center[0] - min_size // 2, center[0] + min_size // 2),
#                          (center[1] - min_size // 2, center[1] + min_size // 2)))

# Resize the cropped image to a smaller size of 1000x1000
# resized = resize(cropped, (1000, 1000), anti_aliasing=True)

# skimage.io.imsave("saved.jpg", relevant_mask)
# skimage.io.imsave("saved2.jpg", relevant_mask2)


