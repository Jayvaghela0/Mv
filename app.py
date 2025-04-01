import io
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

# Reduce memory usage by limiting image size
MAX_WIDTH = 1024
MAX_HEIGHT = 1024
JPEG_QUALITY = 90  # Slightly reduced for memory efficiency

def resize_image(img):
    """Downsample large images to stay within memory limits"""
    if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT))
    return img

def sharpen_image(img):
    """Memory-efficient sharpening"""
    # Smallest possible data types
    img_array = np.array(img, dtype=np.uint8)
    
    # Process in BGR space (OpenCV default)
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Lightweight sharpening kernel
    kernel = np.array([[0, -0.5, 0],
                       [-0.5, 3, -0.5],
                       [0, -0.5, 0]], dtype=np.float32)
    
    sharpened = cv2.filter2D(img_array, -1, kernel)
    
    # Convert back to RGB
    return cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        # Process image in chunks to save memory
        file = request.files["image"]
        img = Image.open(file.stream)
        img = resize_image(img.convert("RGB"))
        
        # Process and encode in memory-efficient way
        with io.BytesIO() as output_buffer:
            sharpened_array = sharpen_image(img)
            result_img = Image.fromarray(sharpened_array)
            result_img.save(output_buffer, format='JPEG', quality=JPEG_QUALITY)
            output_buffer.seek(0)
            img_data = output_buffer.getvalue()
        
        return jsonify({
            "status": "success",
            "message": "Image processed within memory limits"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
