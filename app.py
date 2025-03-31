from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({'message': 'Image Upscaler API is running'}), 200

def upscale_image(image, scale=2):
    width, height = image.size
    new_width, new_height = width * scale, height * scale
    return image.resize((new_width, new_height), Image.LANCZOS)

def enhance_image(image, sharpness=1.5, contrast=1.3, brightness=1.2, denoise=True):
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(sharpness)
    
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(contrast)
    
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(brightness)
    
    if denoise:
        image = np.array(image)
        image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        image = Image.fromarray(image)
    
    return image

@app.route('/enhance', methods=['POST'])
def enhance():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    image = Image.open(file.stream).convert("RGB")
    
    upscale_factor = int(request.form.get('scale', 2))
    image = upscale_image(image, scale=upscale_factor)
    image = enhance_image(image)
    
    img_io = io.BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
