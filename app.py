import os
import io
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import cv2

app = Flask(__name__)
CORS(app)

def apply_esrgan_style_enhancement(image):
    """Balanced enhancement mimicking ESRGAN results without AI"""
    # Convert to OpenCV format (BGR)
    img_np = np.array(image.convert("RGB"))
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # 1. LAB Color Space Processing for Natural Enhancement
    lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Contrast Limited Adaptive Histogram Equalization (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8,8))
    l = clahe.apply(l)
    
    # Slight color boost (5-10%)
    a = cv2.multiply(a, 1.05)
    b = cv2.multiply(b, 1.05)
    
    lab = cv2.merge((l, a, b))
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # 2. Smart Sharpening (ESRGAN-style)
    kernel = np.array([[0, -0.2, 0],
                      [-0.2, 1.8, -0.2],
                      [0, -0.2, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # 3. Final Mixing (70% enhanced, 30% sharpened)
    result = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
    
    # Convert back to PIL Image
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    return Image.fromarray(result_rgb)

@app.route("/")
def home():
    return jsonify({"message": "Welcome to ESRGAN-style Image Enhancement API (Lightweight)"})

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        # Read and validate image
        file = request.files["image"]
        img = Image.open(file.stream)
        
        # Limit input size for Render free tier
        if max(img.size) > 1600:
            img.thumbnail((1600, 1600))
        
        # Apply enhancement
        enhanced_img = apply_esrgan_style_enhancement(img)
        
        # Prepare response
        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=90)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
