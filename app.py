import io
import base64
import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageEnhance

app = Flask(__name__)
CORS(app)

def enhance_image(img, sharpen=True, denoise=True, contrast=True, hdr=True):
    img_np = np.array(img.convert("RGB"))
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # 1️⃣ **Sharpening**
    if sharpen:
        kernel = np.array([[0,-0.25,0], [-0.25,2.2,-0.25], [0,-0.25,0]])
        img_cv = cv2.filter2D(img_cv, -1, kernel)

    # 2️⃣ **Denoising (Removing Blur & Noise)**
    if denoise:
        img_cv = cv2.fastNlMeansDenoisingColored(img_cv, None, 10, 10, 7, 21)

    # 3️⃣ **Contrast & Brightness Adjustment**
    if contrast:
        img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Contrast(img_pil)
        img_pil = enhancer.enhance(1.5)  # Contrast Increase
        enhancer = ImageEnhance.Brightness(img_pil)
        img_pil = enhancer.enhance(1.2)  # Brightness Increase
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    # 4️⃣ **HDR Effect (Color Correction)**
    if hdr:
        lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = cv2.equalizeHist(l)
        lab = cv2.merge((l, a, b))
        img_cv = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

@app.route('/enhance', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    try:
        file = request.files['image']
        img = Image.open(file.stream)

        # Image Processing
        enhanced_img = enhance_image(img)

        # Create Download Link
        img_io = io.BytesIO()
        enhanced_img.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        download_link = f"data:image/jpeg;base64,{base64.b64encode(img_io.getvalue()).decode()}"

        # Create Preview
        preview_io = io.BytesIO()
        enhanced_img.save(preview_io, 'JPEG', quality=70)
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
