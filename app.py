from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import os

app = Flask(__name__)
CORS(app)  # CORS Enable for Frontend Access

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Image Processing Functions
def upscale_image(image):
    return cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)

def sharpen_image(image):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(image, -1, kernel)

def denoise_image(image):
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

def deblur_image(image):
    kernel = np.array([[1, 1, 1], [1, -7, 1], [1, 1, 1]])
    return cv2.filter2D(image, -1, kernel)

@app.route('/enhance', methods=['POST'])
def enhance_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    image = cv2.imread(filepath)
    
    if image is None:
        return jsonify({"error": "Invalid image"}), 400

    enhanced = upscale_image(image)  # Upscale 2x
    enhanced = sharpen_image(enhanced)  # Sharpen
    enhanced = denoise_image(enhanced)  # Denoise
    enhanced = deblur_image(enhanced)  # Deblur

    output_path = os.path.join(OUTPUT_FOLDER, "enhanced_" + file.filename)
    cv2.imwrite(output_path, enhanced)

    return jsonify({"preview_url": f"/download/{'enhanced_' + file.filename}"})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
