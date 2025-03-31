import os
import io
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageFilter
import cv2

app = Flask(__name__)
CORS(app)

def apply_natural_enhancement(image):
    """Advanced sharpening with soft edge preservation"""
    img = image.convert("RGB")
    img_np = np.array(img)
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # 1. Soft Contrast Enhancement (LAB Space)
    lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8,8))  # Reduced from 1.2
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # 2. Edge-Preserving Smoothing (Bilateral Filter)
    smoothed = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)
    
    # 3. Gentle Sharpening (Softer Kernel)
    kernel = np.array([[ 0, -0.1,  0],
                      [-0.1, 1.4, -0.1],
                      [ 0, -0.1,  0]])  # Reduced center weight
    sharpened = cv2.filter2D(smoothed, -1, kernel)
    
    # 4. Edge-Aware Mixing (80% smoothed + 20% sharpened)
    final = cv2.addWeighted(smoothed, 0.8, sharpened, 0.2, 0)
    
    # 5. Pillow-Based Softening (Gaussian Blur)
    final_rgb = cv2.cvtColor(final, cv2.COLOR_BGR2RGB)
    final_pil = Image.fromarray(final_rgb)
    final_pil = final_pil.filter(ImageFilter.GaussianBlur(radius=0.7))  # Soft touch
    
    return final_pil

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        file = request.files["image"]
        img = Image.open(file.stream)
        
        # Size limit
        if max(img.size) > 1600:
            img.thumbnail((1600, 1600))
        
        enhanced_img = apply_natural_enhancement(img)
        
        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=90)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
