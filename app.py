import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageFilter
import numpy as np

app = Flask(__name__)
CORS(app)

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
    result = Image.fromarray(sharpened)
    
    # 4. Apply subtle softness
    result = result.filter(ImageFilter.SMOOTH_MORE)
    
    return result

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        file = request.files["image"]
        img = Image.open(file.stream).convert("RGB")
        
        # Maintain original resolution
        original_size = img.size
        
        # Apply gentle sharpening
        enhanced_img = apply_gentle_sharpening(img)
        
        # Preserve original dimensions
        if enhanced_img.size != original_size:
            enhanced_img = enhanced_img.resize(original_size, Image.LANCZOS)
        
        # Save as high quality JPEG
        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=98, subsampling=0)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
