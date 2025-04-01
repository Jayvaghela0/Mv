import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import cv2
import numpy as np
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

def apply_sharpening(image):
    """Apply sharpening only without any softness"""
    # Convert to numpy array
    img_array = np.array(image)
    
    # Convert RGB to BGR for OpenCV
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Sharpening kernel - stronger center value for more pronounced sharpening
    kernel = np.array([[0, -1, 0], 
                      [-1, 5, -1], 
                      [0, -1, 0]])
    
    # Apply sharpening
    sharpened = cv2.filter2D(img_array, -1, kernel)
    
    # Convert back to RGB
    sharpened = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
    return Image.fromarray(sharpened)

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        file = request.files["image"]
        
        # Open and convert image
        img = Image.open(file.stream).convert("RGB")
        
        # Apply sharpening only
        enhanced_img = apply_sharpening(img)
        
        # Create in-memory file
        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=100)  # Maximum quality
        img_io.seek(0)
        
        # Return the enhanced image
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name='sharpened.jpg'
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
