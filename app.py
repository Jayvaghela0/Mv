
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageEnhance
import base64

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def apply_enhancements(image, brightness=1.0, contrast=1.0, sharpness=1.0, saturation=1.0):
    """Apply traditional image enhancements"""
    # Convert to PIL Image if it's a numpy array
    if isinstance(image, np.ndarray):
        image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # Apply enhancements
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(brightness)
    
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(contrast)
    
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(sharpness)
    
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(saturation)
    
    return image

def upscale_image(image, scale=2.0):
    """Upscale image using traditional interpolation"""
    if isinstance(image, Image.Image):
        image = np.array(image)
    
    height, width = image.shape[:2]
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Using cv2.INTER_CUBIC for better quality than bilinear
    upscaled = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    # Apply slight sharpening to compensate for interpolation blur
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    upscaled = cv2.filter2D(upscaled, -1, kernel)
    
    return upscaled

@app.route('/enhance', methods=['POST'])
def enhance_image():
    try:
        # Get parameters from request
        brightness = float(request.form.get('brightness', 1.0))
        contrast = float(request.form.get('contrast', 1.0))
        sharpness = float(request.form.get('sharpness', 1.0))
        saturation = float(request.form.get('saturation', 1.0))
        upscale = float(request.form.get('upscale', 1.0))
        
        # Get image file
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': 'No image file provided'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'}), 400
        
        # Open and convert image
        img_stream = file.stream
        img = Image.open(img_stream)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Apply enhancements
        enhanced_img = apply_enhancements(img, brightness, contrast, sharpness, saturation)
        
        # Upscale if needed
        if upscale > 1.0:
            enhanced_img = upscale_image(enhanced_img, upscale)
        
        # Convert to bytes
        img_io = BytesIO()
        if isinstance(enhanced_img, np.ndarray):
            enhanced_img = Image.fromarray(enhanced_img)
        
        # Save as JPEG with high quality
        enhanced_img.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        
        # Create response
        response = send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False
        )
        
        # Add CORS headers
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
