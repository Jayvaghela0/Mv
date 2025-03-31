import io
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from PIL import Image, ImageFilter
import cv2
import numpy as np
import os

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def apply_gentle_sharpening(image):
    """Apply sharpening with softness to avoid artifacts"""
    # Convert to numpy array for processing
    img_array = np.array(image)
    
    # 1. Gentle Unsharp Masking with controlled parameters
    blurred = cv2.GaussianBlur(img_array, (0, 0), 2.0)
    sharpened = cv2.addWeighted(img_array, 1.3, blurred, -0.3, 0)
    
    # 2. Edge-preserving smoothing to reduce artifacts
    sharpened = cv2.edgePreservingFilter(sharpened, flags=1, sigma_s=50, sigma_r=0.4)
    
    # 3. Convert back to PIL Image
    result = Image.fromarray(cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB))
    
    # 4. Apply subtle softness
    result = result.filter(ImageFilter.SMOOTH_MORE)
    
    return result

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        file = request.files["image"]
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        # Save original image
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], 'original.jpg')
        file.save(original_path)
        
        img = Image.open(original_path).convert("RGB")
        
        # Apply gentle sharpening
        enhanced_img = apply_gentle_sharpening(img)
        
        # Save enhanced image
        enhanced_path = os.path.join(app.config['UPLOAD_FOLDER'], 'enhanced.jpg')
        enhanced_img.save(enhanced_path, format='JPEG', quality=98, subsampling=0)
        
        # Return both images for comparison
        return render_template('result.html', 
                             original_image='original.jpg',
                             enhanced_image='enhanced.jpg')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<filename>')
def send_image(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
