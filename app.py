import os
import io
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import cv2

app = Flask(__name__)
CORS(app)

def apply_enhancement(image, saturation_factor=0.9):  # Default to 10% reduction
    """Enhanced image with adjustable saturation"""
    img_np = np.array(image.convert("RGB"))
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # Convert to HSV for saturation control
    hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
    
    # Reduce saturation (H:0-179, S:0-255, V:0-255)
    hsv[:,:,1] = cv2.multiply(hsv[:,:,1], saturation_factor)
    
    # Convert back to BGR
    img_cv = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    # Continue with other enhancements
    lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # Smart sharpening
    kernel = np.array([[0, -0.2, 0],
                     [-0.2, 1.8, -0.2],
                     [0, -0.2, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    result = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    return Image.fromarray(result_rgb)

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        file = request.files["image"]
        img = Image.open(file.stream)
        
        # Get saturation factor from request (default 0.9)
        saturation = float(request.form.get('saturation', 0.9))
        
        # Validate saturation (0-1.5 range)
        saturation = max(0.0, min(1.5, saturation))
        
        if max(img.size) > 1600:
            img.thumbnail((1600, 1600))
        
        enhanced_img = apply_enhancement(img, saturation)
        
        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=90)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
