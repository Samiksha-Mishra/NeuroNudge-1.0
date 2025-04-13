import os
import cv2
import numpy as np

def preprocess_image(image_path, size=(128, 128)):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.GaussianBlur(image, (5, 5), 0)
    _, image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    image = cv2.resize(image, size)
    return image

def load_dataset(folder_path, label):
    data, labels = [], []
    for img_name in os.listdir(folder_path):
        try:
            img = preprocess_image(os.path.join(folder_path, img_name))
            data.append(img)
            labels.append(label)
        except:
            continue
    return data, labels
