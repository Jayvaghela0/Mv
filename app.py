import io
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

def enhance_image(img):
    """Original look maintain रखते हुए हल्का sharpen और softness add करना"""
    img_np = np.array(img.convert("RGB"))
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # हल्का soft effect (Gaussian Blur)
    soft = cv2.GaussianBlur(img_cv, (5,5), 1.5)
    
    # हल्का sharpening kernel (sharpness कम किया)
    kernel = np.array([[0,-0.1,0], [-0.1,1.5,-0.1], [0,-0.1,0]])
    sharpened = cv2.filter2D(soft, -1, kernel)
    
    # Smooth blending (original look बनाए रखने के लिए)
    result = cv2.addWeighted(soft, 0.4, sharpened, 0.6, 0)

    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))

@app.route('/enhance', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    try:
        file = request.files['image']
        img = Image.open(file.stream)
        
        # अगर image बहुत बड़ी है तो resize करें
        if max(img.size) > 1600:
            img.thumbnail((1600, 1600))
            
        enhanced = enhance_image(img)
        
        # Create download link
        img_io = io.BytesIO()
        enhanced.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        download_link = f"data:image/jpeg;base64,{base64.b64encode(img_io.getvalue()).decode()}"
        
        # Create preview
        preview_io = io.BytesIO()
        enhanced.save(preview_io, 'JPEG', quality=75)
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
