import os
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import torch
import numpy as np
import io
from PIL import Image
from torchvision.transforms.functional import to_tensor, to_pil_image
import hashlib
import re

app = Flask(__name__)
CORS(app)

# ESRGAN Model Configuration
MODEL_PATH = "ESRGAN_x4.pth"
GDRIVE_URL = "https://drive.google.com/uc?export=download&id=1lZVx0Pw2yTnS5t2-vdlcQ03AjrEpXFgk"
EXPECTED_SIZE = 67089157  # Expected file size in bytes (for verification)

def get_confirm_token(response):
    """Extract download confirmation token from Google Drive response"""
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def download_file_from_gdrive():
    """Handle Google Drive's virus scan warning and large file downloads"""
    print("🔄 Downloading ESRGAN Model from Google Drive...")
    
    session = requests.Session()
    response = session.get(GDRIVE_URL, stream=True)
    token = get_confirm_token(response)
    
    if token:
        params = {'id': '1lZVx0Pw2yTnS5t2-vdlcQ03AjrEpXFgk', 'confirm': token}
        response = session.get(GDRIVE_URL, params=params, stream=True)
    
    # Save content to file
    with open(MODEL_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    
    # Verify download completed successfully
    actual_size = os.path.getsize(MODEL_PATH)
    if actual_size != EXPECTED_SIZE:
        os.remove(MODEL_PATH)
        raise ValueError(f"Download incomplete. Expected {EXPECTED_SIZE} bytes, got {actual_size} bytes")

    print("✅ Model downloaded successfully!")

# Download model if needed
if not os.path.exists(MODEL_PATH) or os.path.getsize(MODEL_PATH) != EXPECTED_SIZE:
    download_file_from_gdrive()

# Load ESRGAN Model
def load_model():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    try:
        # First try loading as a traced model
        model = torch.jit.load(MODEL_PATH, map_location=device)
    except RuntimeError:
        try:
            # Fallback to state_dict loading
            from torch import nn
            model = nn.Module()
            state_dict = torch.load(MODEL_PATH, map_location=device)
            if 'params' in state_dict:
                model.params = state_dict['params']
            elif 'state_dict' in state_dict:
                model.load_state_dict(state_dict['state_dict'])
            else:
                model.load_state_dict(state_dict)
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")
    
    model.eval()
    return model

model = load_model()

def enhance_image(image):
    img_tensor = to_tensor(image).unsqueeze(0)
    
    if torch.cuda.is_available():
        img_tensor = img_tensor.cuda()
    
    with torch.no_grad():
        output = model(img_tensor)
    
    output = output.squeeze(0).cpu().clamp(0, 1)
    return to_pil_image(output)

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
    app.run(host="0.0.0.0", port=5000, threaded=True)
