import os
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import torch
import numpy as np
import io
from PIL import Image
from torchvision.transforms.functional import to_tensor, to_pil_image

app = Flask(__name__)
CORS(app)

# ESRGAN Model Configuration
MODEL_PATH = "ESRGAN_x4.pth"
MODEL_URL = "https://drive.google.com/uc?export=download&id=1lZVx0Pw2yTnS5t2-vdlcQ03AjrEpXFgk"


# Download ESRGAN model if not exists
if not os.path.exists(MODEL_PATH):
    print("🔄 Downloading ESRGAN Model...")
    response = requests.get(MODEL_URL, stream=True)
    with open(MODEL_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    print("✅ Model Downloaded Successfully!")

# Load ESRGAN Model
def load_model():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = torch.jit.load(MODEL_PATH, map_location=device)
    model.eval()
    return model

model = load_model()

def enhance_image(image):
    # Convert image to tensor
    img_tensor = to_tensor(image).unsqueeze(0)
    
    # Move to GPU if available
    if torch.cuda.is_available():
        img_tensor = img_tensor.cuda()
    
    # Perform super-resolution
    with torch.no_grad():
        output = model(img_tensor)
    
    # Convert back to PIL Image
    output = output.squeeze(0).cpu().clamp(0, 1)
    enhanced_img = to_pil_image(output)
    
    return enhanced_img

@app.route("/")
def home():
    return jsonify({"message": "Welcome to ESRGAN API!"})

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    try:
        img = Image.open(file.stream).convert("RGB")
        enhanced_img = enhance_image(img)

        img_io = io.BytesIO()
        enhanced_img.save(img_io, format='JPEG', quality=95)
        img_io.seek(0)

        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
