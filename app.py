import os
import io
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageEnhance
import cv2

app = Flask(__name__)
CORS(app)

def natural_enhancement(image):
    """Balanced enhancement without over-sharpening"""
    img = image.convert("RGB")
    img_np = np.array(img)
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # 1. Gentle Contrast Enhancement
    lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge((l,a,b))
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # 2. Subtle Sharpening (Reduced intensity)
    kernel = np.array([[0, -0.5, 0], 
                      [-0.5, 3, -0.5], 
                      [0, -0.5, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # 3. Color Preservation
    sharpened = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
    
    # Convert back to PIL
    result = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
    final_image = Image.fromarray(result)
    
    # Mild Sharpening
    enhancer = ImageEnhance.Sharpness(final_image)
    final_image = enhancer.enhance(1.3)  # Reduced from 2.0 to 1.3
    
    return final_image

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
        
        enhanced_img = natural_enhancement(img)
        
        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=90)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
