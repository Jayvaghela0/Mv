from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import subprocess
import os
import io
from PIL import Image
import numpy as np

def download_model():
    if not os.path.exists("realesrgan-ncnn-vulkan"):  # Check if model is already downloaded
        subprocess.run(["git", "clone", "https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan.git"])
        os.chdir("Real-ESRGAN-ncnn-vulkan")
        subprocess.run(["chmod", "+x", "realesrgan-ncnn-vulkan"])
        os.chdir("..")

def enhance_image(image):
    input_path = "input.jpg"
    output_path = "output.jpg"
    image.save(input_path, format="JPEG")
    
    subprocess.run(["./Real-ESRGAN-ncnn-vulkan/realesrgan-ncnn-vulkan", "-i", input_path, "-o", output_path, "-n", "realesrgan-x4plus-anime"], check=True)
    
    enhanced_img = Image.open(output_path)
    return enhanced_img

app = Flask(__name__)
CORS(app, origins=["https://your-blogger-site.blogspot.com"])  # Replace with your Blogger domain

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    img = Image.open(file.stream)
    
    enhanced_img = enhance_image(img)
    
    img_io = io.BytesIO()
    enhanced_img.save(img_io, format='JPEG', quality=100)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    download_model()
    app.run(host='0.0.0.0', port=5000)
