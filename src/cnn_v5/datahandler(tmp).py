#!/usr/bin/env python3
import sh
import os
import random
import numpy as np
import cv2
#np.set_printoptions(threshold=np.nan)

data_path = "../../dataset/human-action-dataset"

images_list = open("small-train-copy.txt", "r").read().split("\n")

classes = 4
out_depth = (5+classes)

def create(input_size, flip=1, crop=0.9, angle=10, color = 0.05):
    image_name = random.choice(images_list)
    image_path = os.path.join(data_path, image_name)
    label_name = image_name.split(".")[0] + ".txt"
    label_path = os.path.join(data_path, label_name)

    #image
    im = cv2.imread(image_path).astype(np.float)
    h, w, _ = im.shape
        #resize to inputsize
    image = cv2.resize(im, (input_size, input_size), interpolation = cv2.INTER_CUBIC)
    image = image.reshape((1, input_size, input_size, 3))


    #label

    label = []
    if os.path.exists(label_path):
        with open(label_path, "r") as f:
            labeltxt = f.read()
        for objtxt in labeltxt.split("\n"):
            if objtxt == "": continue
            cls, x0, y0, w0, h0 = objtxt.split(" ")
            cls = int(cls)
            x0   = float(x0)
            y0   = float(y0)
            w0   = float(w0)
            h0   = float(h0)
            label.append((cls, x0, y0, w0, h0))
    return image, label

def IoU(box1, box2):
    w1, h1 = box1
    w2, h2 = box2
    iou = min(w1, w2) * min(h1, h2)
    return iou

def which_anchor(box):
    anchor = (1,1)
    dist = []
    dist.append(IoU(anchor, box))
    i = dist.index(max(dist))
    return i

def create_array(input_size):
    image, label = create(input_size)
    _, height, width, depth = image.shape
    out_height = height//32
    out_width = width//32
    
    X = image
    Y1 = np.random.random((1, out_height, out_width, out_depth))
    #Y2 = np.random.random((1, 2*out_height, 2*out_width, out_depth))
    #for i in range(1):
    Y1[:, :, :, 0] = 1
        #Y2[:, :, :, i*(out_depth)] = 1
    #convert label to array
    for obj in label:
        cls, x0, y0, w0, h0 = obj
        if x0<0 or x0>=1 or y0<0 or y0>=1: continue
        box = (w0, h0)
        #i = which_anchor(box)
        #if (1):
        x = int(out_width*x0)
        y = int(out_height*y0)
        Y1[0, y, x, 0] = 1
        Y1[0, y, x, 1] = x0
        Y1[0, y, x, 2] = y0
        Y1[0, y, x, 3] = w0
        Y1[0, y, x, 4] = h0
        Y1[0, y, x, 5:out_depth] = 0
        Y1[0, y, x, 5+cls] = 1
    X[X<1e-37] = 1e-37
    Y1[Y1<1e-37] = 1e-37
    #Y2[Y2<1e-37] = 1e-37
 
    return X, Y1

def create_many_arrays(batch_size, input_size):
    X = []
    Y1 = []
    #Y2 = []
    for i in range(batch_size):
        x, y1 = create_array(input_size)
        X.append(x)
        Y1.append(y1)
        #Y2.append(y2)
    X = np.vstack(X)
    Y1 = np.vstack(Y1)
    #Y2 = np.vstack(Y2)   

    return X, Y1

def shuffle(batch_size, input_size):
    step = 0
    while (1):
        if (step == 0):
            yield step, None, None
        else:
            yield step, X, Y1
            del X
            del Y1
            #del Y2
        step += 1
        X, Y1 = create_many_arrays(batch_size, input_size)

if __name__ == "__main__":
    image, label = create(416)
    image = image.astype(np.int32).reshape(416,416,3)
    print(image.shape)
    for obj in label:
        cls, x0, y0, w0, h0 = obj
        x1 = int((x0 - w0/2)*416)
        x2 = int((x0 + w0/2)*416)
        y1 = int((y0 - h0/2)*416)
        y2 = int((y0 + h0/2)*416)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0,0,0),2)

    cv2.imwrite("temp.jpg", image)
    sh.eog("temp.jpg")
    sh.rm("temp.jpg")                                            