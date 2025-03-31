import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageFilter
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def apply_gentle_sharpening(image):
    """Apply sharpening with softness to avoid artifacts"""
    # Convert to numpy array for processing
    img_array = np.array(image)
    
    # Convert RGB to BGR for OpenCV
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # 1. Gentle Unsharp Masking with controlled parameters
    blurred = cv2.GaussianBlur(img_array, (0, 0), 2.0)
    sharpened = cv2.addWeighted(img_array, 1.3, blurred, -0.3, 0)
    
    # 2. Edge-preserving smoothing to reduce artifacts
    sharpened = cv2.edgePreservingFilter(sharpened, flags=1, sigma_s=50, sigma_r=0.4)
    
    # Convert back to RGB
    sharpened = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
    result = Image.fromarray(sharpened)
    
    # 4. Apply subtle softness
    return result.filter(ImageFilter.SMOOTH_MORE)

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        file = request.files["image"]
        
        # Open and convert image
        img = Image.open(file.stream).convert("RGB")
        
        # Apply gentle sharpening
        enhanced_img = apply_gentle_sharpening(img)
        
        # Create in-memory file
        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=98, subsampling=0)
        img_io.seek(0)
        
        # Return the enhanced image directly
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='enhanced_image.jpg'
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
