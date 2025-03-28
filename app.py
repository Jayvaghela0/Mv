from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Function to Bypass Ads & Extract Direct Download Link
def get_real_download_link(movie_page_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://hdhub4u.tube/"  # असली वेबसाइट को रेफरर सेट करें
    }

    # 1️⃣ Send request to get the movie page HTML
    response = requests.get(movie_page_url, headers=headers)
    if response.status_code != 200:
        return None

    # 2️⃣ Extract direct download link
    soup = BeautifulSoup(response.text, "html.parser")
    direct_link = None

    # Find the link which has 'download' in it
    for link in soup.find_all("a"):
        href = link.get("href")
        if "download" in href:
            direct_link = href
            break

    return direct_link

# API to Get Direct Download Link
@app.route('/get_movie', methods=['GET'])
def get_movie():
    movie_page_url = request.args.get('url')
    if not movie_page_url:
        return jsonify({"error": "Movie URL required"}), 400

    # Get direct download link
    direct_link = get_real_download_link(movie_page_url)
    
    if direct_link:
        return jsonify({"direct_download_link": direct_link})
    else:
        return jsonify({"error": "Failed to fetch download link"}), 500

# API to Redirect to Download Link
@app.route('/download', methods=['GET'])
def auto_download():
    movie_url = request.args.get('url')
    if not movie_url:
        return jsonify({"error": "Movie download URL required"}), 400

    return redirect(movie_url, code=302)

if __name__ == '__main__':
    app.run(debug=True)
