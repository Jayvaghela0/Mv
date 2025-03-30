import os
import requests
from flask import Flask, request, jsonify, send_file
import torch
import torchvision.transforms as transforms
from PIL import Image
import io
import numpy as np
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

app = Flask(__name__)

# Auto-Download ESRGAN Model
MODEL_PATH = "ESRGAN_x4.pth"
MODEL_URL = "https://drive.google.com/uc?export=download&id=1lZVx0Pw2yTnS5t2-vdlcQ03AjrEpXFgk
"

if not os.path.exists(MODEL_PATH):
    print("🔄 Downloading ESRGAN Model...")
    response = requests.get(MODEL_URL, stream=True)
    with open(MODEL_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
    print("✅ Model Downloaded Successfully!")

# Load ESRGAN Model at Runtime
def load_model():
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    upscaler = RealESRGANer(scale=4, model_path=MODEL_PATH, model=model, pre_pad=10, half=True)
    return upscaler

upscaler = load_model()

def enhance_image(image):
    img = image.convert("RGB")
    img_np = np.array(img)
    output, _ = upscaler.enhance(img_np, outscale=4)
    enhanced_img = Image.fromarray(output)
    return enhanced_img

@app.route("/")
def home():
    return jsonify({"message": "Welcome to ESRGAN API!"})

@app.route("/enhance", methods=["POST"])
def enhance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    img = Image.open(file.stream)
    enhanced_img = enhance_image(img)

    img_io = io.BytesIO()
    enhanced_img.save(img_io, format='JPEG', quality=100)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
