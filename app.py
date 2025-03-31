import os
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

def enhanced_sharpening(image):
    """Sharpen image with 70% intensity and 50% less softness"""
    img_np = np.array(image.convert("RGB"))
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # 1. Reduced smoothing (50% less softness)
    smoothed = cv2.bilateralFilter(img_cv, d=7, sigmaColor=50, sigmaSpace=50)  # Reduced from 75
    
    # 2. Stronger sharpening kernel (70% more intense)
    kernel = np.array([
        [0,  -0.25,  0],
        [-0.25, 2.2, -0.25],  # Increased center from 1.6 to 2.2
        [0,  -0.25,  0]
    ])
    sharpened = cv2.filter2D(smoothed, -1, kernel)
    
    # 3. Adjusted blending (70% sharpening effect)
    result = cv2.addWeighted(smoothed, 0.3, sharpened, 0.7, 0)  # Changed from 85/15 to 30/70
    
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    return Image.fromarray(result_rgb)

@app.route('/sharpen', methods=['POST'])
def sharpen_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    try:
        file = request.files['image']
        img = Image.open(file.stream)
        
        if max(img.size) > 1600:
            img.thumbnail((1600, 1600))
        
        sharpened_img = enhanced_sharpening(img)
        
        img_io = io.BytesIO()
        sharpened_img.save(img_io, 'JPEG', quality=90)
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='sharpened_image.jpg'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
