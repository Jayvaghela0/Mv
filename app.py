import io
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageFilter
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

def enhance_image(image):
    """Apply sharpening with slight softness"""
    # Convert to numpy array
    img_array = np.array(image)
    
    # Convert RGB to BGR for OpenCV
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Stronger sharpening kernel (increased center value)
    kernel = np.array([[0, -1.2, 0],
                      [-1.2, 6.2, -1.2],
                      [0, -1.2, 0]])
    sharpened = cv2.filter2D(img_array, -1, kernel)
    
    # Slight softness (reduced sigma values)
    sharpened = cv2.edgePreservingFilter(sharpened, flags=1, sigma_s=15, sigma_r=0.3)
    
    # Convert back to RGB
    sharpened = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
    result = Image.fromarray(sharpened)
    
    # Final tiny softness touch
    return result.filter(ImageFilter.SMOOTH_MORE)

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        file = request.files["image"]
        img = Image.open(file.stream).convert("RGB")
        
        # Process image
        enhanced_img = enhance_image(img)
        
        # Save to buffer
        img_buffer = io.BytesIO()
        enhanced_img.save(img_buffer, format='JPEG', quality=98)
        img_buffer.seek(0)
        
        # Create base64 for display
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            "image": f"data:image/jpeg;base64,{img_base64}",
            "download_url": f"data:image/jpeg;base64,{img_base64}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
