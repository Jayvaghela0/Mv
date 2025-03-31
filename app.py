import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
from PIL import Image, ImageEnhance
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

def enhance_image(image):
    """Non-AI image enhancement using traditional CV techniques"""
    img = image.convert("RGB")
    
    # Convert to OpenCV format
    img_cv = np.array(img)
    img_cv = img_cv[:, :, ::-1].copy()  # RGB to BGR
    
    # 1. Contrast Limited Adaptive Histogram Equalization (CLAHE)
    lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl,a,b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    
    # 2. Sharpening
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    enhanced = cv2.filter2D(enhanced, -1, kernel)
    
    # 3. Color correction
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(enhanced)
    
    # 4. Pillow-based enhancements
    enhancer = ImageEnhance.Contrast(img_pil)
    img_pil = enhancer.enhance(1.2)
    
    enhancer = ImageEnhance.Sharpness(img_pil)
    img_pil = enhancer.enhance(1.5)
    
    return img_pil

@app.route("/")
def home():
    return jsonify({"message": "Welcome to Image Enhancement API!"})

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        file = request.files["image"]
        img = Image.open(file.stream)
        
        # Limit input size for free tier
        if img.size[0] > 1024 or img.size[1] > 1024:
            img.thumbnail((1024, 1024))
        
        enhanced_img = enhance_image(img)
        
        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
