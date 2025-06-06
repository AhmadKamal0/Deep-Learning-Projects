import cv2
import os
import random
from scipy.ndimage import rotate
import cvzone
import uuid

def con_to_yolo(x1, y1, w, h, image_w, image_h):
    return [((2*x1 + w)/(2*image_w)) , ((2*y1 + h)/(2*image_h)), w/image_w, h/image_h]

NUMBER_OF_DATASET = 120     # Number of imgs you want for your Dataset ***CHANGE***

flag_path = r"C:\Users\LENOVO\Desktop\Flag_of_the_Army_of_Egypt.svg.png"         # Path of flags or QR codes
desert_path = r"C:\Users\LENOVO\Desktop\suas\SUAS2023\Sample Images\desert"        # Path of desert background
outputDirectory_img = r"C:\Users\LENOVO\Desktop\out\data"  # Output dataset "images" directory ***CHANGE***
outputDirectory_label = r"C:\Users\LENOVO\Desktop\out\labels"  # Output dataset "labels" directory ***CHANGE***

desert_bg = os.listdir(desert_path)                 # Read array of desert imgs
flag = cv2.imread(flag_path,cv2.IMREAD_UNCHANGED)       # Read flag to place it ***CHANGE*** MUST BE PNG

n = 1
while(NUMBER_OF_DATASET > 0):
    for bg in desert_bg:
        img_path = os.path.join(desert_path,bg)
        img = cv2.imread(img_path,1)
        h,w,c = img.shape
        # Resize
        cols = random.randrange(50,90)
        rows = int((cols*25/100)+cols)
        
        dim = (rows,cols)
        resized = cv2.resize(flag,dim,interpolation=cv2.INTER_AREA)

                
        # Rotate
        rate = random.randrange(0,360)
        rotated = rotate(resized , angle=rate, reshape=True)
        (h1,w1)= rotated.shape[:2]
        
        
        # Position
        x_pos = random.randrange(0,w-200)
        y_pos = random.randrange(0,h-200)
        
        final = cvzone.overlayPNG(img,rotated, [x_pos,y_pos])
        X,Y,W,H = con_to_yolo(x_pos,y_pos,w1,h1,w,h)
        item_list = ['Usa', 
                        'Uk',
                        'Germany',
                        'France',
                        'Canada',
                        'Egypt',
                        'Italy',
                        'Spain',
                        'Brazil',
                        'China',
                        'Australia',
                        'Argentine',
                        'Belgium',
                        'Ukarine',
                        'Russia',
                        'Czech' ,
                        'England',
                        'Netherland',
                        'QR',
                        'Injured person'] 

        item = 'Egypt' #change it according to the target
        
        # # Show imgs
        # cv2.imshow("test img",final)
        # cv2.waitKey(0)
        
        # Saving the dataset
        special_key = str(uuid.uuid4()) + ".jpg"
        
        final_output = os.path.join(outputDirectory_img,special_key)
        cv2.imwrite(final_output,final)
        alphanuml = f"{item_list.index(item)} {X} {Y} {W} {H}\n"
        f = open(f"{outputDirectory_label}/{special_key}.txt", 'w')
        f.write(alphanuml)
        f.close()
        n += 1
        NUMBER_OF_DATASET -= 1
        if(NUMBER_OF_DATASET == 0):
            break;
