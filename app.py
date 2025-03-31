import os
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for API endpoints

def professional_sharpening(image):
    """
    Advanced image sharpening without artifacts
    Returns: PIL Image
    """
    # Convert to OpenCV format
    img_np = np.array(image.convert("RGB"))
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # 1. Edge-preserving smoothing
    smoothed = cv2.bilateralFilter(img_cv, d=9, sigmaColor=75, sigmaSpace=75)
    
    # 2. Custom soft-sharpening kernel
    kernel = np.array([
        [ 0,  -0.15,  0 ],
        [-0.15, 1.6, -0.15],
        [ 0,  -0.15,  0 ]
    ])
    sharpened = cv2.filter2D(smoothed, -1, kernel)
    
    # 3. Smart blending (85% smoothed + 15% sharpened)
    result = cv2.addWeighted(smoothed, 0.85, sharpened, 0.15, 0)
    
    # Convert back to PIL Image
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    return Image.fromarray(result_rgb)

@app.route('/enhance', methods=['POST'])
def enhance_image():
    """API endpoint for image enhancement"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    try:
        # Read input image
        file = request.files['image']
        img = Image.open(file.stream)
        
        # Limit size for processing
        if max(img.size) > 1600:
            img.thumbnail((1600, 1600))
        
        # Apply professional sharpening
        enhanced_img = professional_sharpening(img)
        
        # Prepare response
        img_io = io.BytesIO()
        enhanced_img.save(img_io, 'JPEG', quality=92)
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='enhanced_image.jpg'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
