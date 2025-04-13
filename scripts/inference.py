
import numpy as np
from tensorflow.keras.models import load_model
from scripts.preprocessing import preprocess_image

# Load the trained model
model = load_model("dyslexia_handwriting_cnn.h5")

def predict_image(image_path):
    image = preprocess_image(image_path)
    image = image / 255.0
    image = np.expand_dims(image, axis=(0, -1))  # Shape: (1, 128, 128, 1)
    prediction = model.predict(image)
    class_label = "Dyslexic" if prediction[0][0] > 0.5 else "Non-Dyslexic"
    confidence = float(prediction[0][0]) if class_label == "Dyslexic" else 1 - float(prediction[0][0])
    return class_label, round(confidence * 100, 2)
