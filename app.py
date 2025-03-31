from flask import Flask, request, send_file
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io

app = Flask(__name__)
CORS(app)

def enhance_image(img, sharpness=2.0, smoothness=0.5, contrast=1.2, saturation=1.1):
    # Convert to PIL Image
    if isinstance(img, np.ndarray):
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    
    # Apply smoothness (bilateral filter)
    if smoothness > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=smoothness))
    
    # Apply sharpening (unsharp mask)
    if sharpness > 1:
        img = img.filter(ImageFilter.UnsharpMask(
            radius=2,
            percent=int(150 * sharpness),
            threshold=3
        ))
    
    # Adjust contrast and saturation
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast)
    
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(saturation)
    
    return img

def upscale_hd(img, scale=2.0):
    # Convert to numpy array if PIL Image
    if isinstance(img, Image.Image):
        img = np.array(img)
    
    # Smart upscaling with sharpening
    height, width = img.shape[:2]
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Use Lanczos interpolation for better quality
    upscaled = cv2.resize(img, (new_width, new_height), 
                         interpolation=cv2.INTER_LANCZOS4)
    
    # Edge-preserving sharpening
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    upscaled = cv2.filter2D(upscaled, -1, kernel)
    
    return upscaled

@app.route('/enhance', methods=['POST'])
def enhance():
    if 'image' not in request.files:
        return {"error": "No image provided"}, 400
    
    file = request.files['image']
    img = Image.open(file.stream)
    
    # Get enhancement parameters
    sharpness = float(request.form.get('sharpness', 1.5))
    smoothness = float(request.form.get('smoothness', 0.3))
    contrast = float(request.form.get('contrast', 1.2))
    saturation = float(request.form.get('saturation', 1.1))
    upscale = float(request.form.get('upscale', 1.5))
    
    # Process image
    enhanced = enhance_image(img, sharpness, smoothness, contrast, saturation)
    
    # Upscale if needed
    if upscale > 1:
        enhanced = upscale_hd(enhanced, upscale)
    
    # Convert to bytes
    img_io = io.BytesIO()
    if isinstance(enhanced, np.ndarray):
        enhanced = Image.fromarray(enhanced)
    enhanced.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
