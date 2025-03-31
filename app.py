import os
import io
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter
import cv2

app = Flask(__name__)
CORS(app)

def esrgan_style_sharpening(image):
    """Advanced sharpening mimicking ESRGAN results"""
    img = image.convert("RGB")
    
    # Convert to numpy array (OpenCV format)
    img_np = np.array(img)
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # 1. High Pass Filter for Edge Enhancement
    kernel_size = 5
    gaussian = cv2.GaussianBlur(img_cv, (kernel_size, kernel_size), 0)
    high_pass = cv2.addWeighted(img_cv, 1.5, gaussian, -0.5, 0)
    
    # 2. Unsharp Masking (Advanced Version)
    blurred = cv2.GaussianBlur(high_pass, (0, 0), 3)
    unsharp_image = cv2.addWeighted(high_pass, 1.7, blurred, -0.7, 0)
    
    # 3. Detail Enhancement
    lab = cv2.cvtColor(unsharp_image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl,a,b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    
    # 4. Final Sharpening Kernel
    kernel = np.array([[-1,-1,-1], 
                      [-1, 9,-1],
                      [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # Convert back to PIL Image
    sharpened_rgb = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
    final_image = Image.fromarray(sharpened_rgb)
    
    # Additional Pillow-based sharpening
    enhancer = ImageEnhance.Sharpness(final_image)
    final_image = enhancer.enhance(2.0)  # Aggressive sharpening
    
    return final_image

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        file = request.files["image"]
        img = Image.open(file.stream)
        
        # Limit input size for performance
        if max(img.size) > 2048:
            img.thumbnail((2048, 2048))
        
        enhanced_img = esrgan_style_sharpening(img)
        
        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=92)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
