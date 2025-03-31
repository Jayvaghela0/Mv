from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io
import os

app = Flask(__name__)
CORS(app)  # CORS enabled for frontend

# Set max upload size (50MB)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  

# Image processing function
def enhance_image(image):
    # Convert PIL image to OpenCV format
    img_cv = np.array(image)
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

    # Sharpening
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(img_cv, -1, kernel)

    # Denoising
    denoised = cv2.fastNlMeansDenoisingColored(sharpened, None, 10, 10, 7, 21)

    # Convert back to PIL
    final_img = cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB)
    enhanced_pil = Image.fromarray(final_img)

    # Contrast Enhancement
    enhancer = ImageEnhance.Contrast(enhanced_pil)
    enhanced_pil = enhancer.enhance(1.5)  # Increase contrast

    # Brightness Adjustment
    brightness = ImageEnhance.Brightness(enhanced_pil)
    enhanced_pil = brightness.enhance(1.2)  # Increase brightness

    # Upscale using bicubic interpolation
    width, height = enhanced_pil.size
    upscale_size = (width * 2, height * 2)  # 2x upscale
    upscaled_img = enhanced_pil.resize(upscale_size, Image.BICUBIC)

    return upscaled_img

# Route for homepage
@app.route("/")
def home():
    return jsonify({"message": "Image Upscaler & Enhancer API is running!"})

# Image enhancement route
@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files["image"]
    image = Image.open(file)

    # Enhance the image
    enhanced_image = enhance_image(image)

    # Save to bytes
    img_io = io.BytesIO()
    enhanced_image.save(img_io, format="PNG")
    img_io.seek(0)

    return send_file(img_io, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
