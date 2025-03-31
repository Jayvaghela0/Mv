import io
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)  # CORS इनेबल करना

def sharpen_image(img):
    """70% more sharp, 50% less soft"""
    img_np = np.array(img.convert("RGB"))
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # Sharpening parameters
    smoothed = cv2.bilateralFilter(img_cv, d=7, sigmaColor=50, sigmaSpace=50)
    kernel = np.array([[0,-0.25,0], [-0.25,2.2,-0.25], [0,-0.25,0]])
    sharpened = cv2.filter2D(smoothed, -1, kernel)
    result = cv2.addWeighted(smoothed, 0.3, sharpened, 0.7, 0)
    
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))

@app.route('/sharpen', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    try:
        file = request.files['image']
        img = Image.open(file.stream)
        
        # Process image
        if max(img.size) > 1600:
            img.thumbnail((1600, 1600))
        sharpened = sharpen_image(img)
        
        # Create download link
        img_io = io.BytesIO()
        sharpened.save(img_io, 'JPEG', quality=90)
        img_io.seek(0)
        download_link = f"data:image/jpeg;base64,{base64.b64encode(img_io.getvalue()).decode()}"
        
        # Create preview
        preview_io = io.BytesIO()
        sharpened.save(preview_io, 'JPEG', quality=70)
        preview_io.seek(0)
        preview_img = f"data:image/jpeg;base64,{base64.b64encode(preview_io.getvalue()).decode()}"
        
        return jsonify({
            'preview': preview_img,
            'download': download_link,
            'filename': file.filename
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
