from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

BASE_URL = "https://www.mp4moviez.family"

# Function to search movie and get its page URL
def search_movie(movie_name):
    search_url = f"{BASE_URL}/search/{movie_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    movie_links = []
    
    for link in soup.find_all("a", href=True):
        if "/movie/" in link["href"]:
            movie_links.append(BASE_URL + link["href"])
    
    return movie_links[0] if movie_links else None

# Function to get direct download links and image
def get_download_links(movie_page_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(movie_page_url, headers=headers)
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    download_links = []
    image_url = ""
    
    # Get movie image
    img_tag = soup.find("img")
    if img_tag and "src" in img_tag.attrs:
        image_url = BASE_URL + img_tag["src"]
    
    # Get all download links
    for link in soup.find_all("a", href=True):
        if "/download/" in link["href"]:
            download_links.append(BASE_URL + link["href"])
    
    return {"image": image_url, "download_links": download_links}

@app.route('/get_movie', methods=['GET'])
def get_movie():
    movie_name = request.args.get('name')
    if not movie_name:
        return jsonify({"error": "Movie name required"}), 400
    
    movie_page_url = search_movie(movie_name)
    if not movie_page_url:
        return jsonify({"error": "Movie not found"}), 404
    
    movie_data = get_download_links(movie_page_url)
    if not movie_data or not movie_data["download_links"]:
        return jsonify({"error": "Download links not found"}), 404
    
    return jsonify(movie_data)

if __name__ == '__main__':
    app.run(debug=True)
