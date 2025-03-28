from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# Function to search movies on HDHub4u
def search_movie(movie_name):
    search_url = f"https://hdhub4u.tube/?s={movie_name.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    movie_links = []

    for post in soup.find_all("div", class_="result-item"):
        link = post.find("a")["href"]
        title = post.find("h2").text.strip()
        movie_links.append({"title": title, "link": link})

    return movie_links

# Function to get direct download link
def get_direct_download(movie_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://hdhub4u.tube/"
    }

    response = requests.get(movie_url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    download_link = None

    for link in soup.find_all("a"):
        href = link.get("href")
        if "download" in href:
            download_link = href
            break

    return download_link

# API to Search Movies
@app.route('/search', methods=['GET'])
def search():
    movie_name = request.args.get('name')
    if not movie_name:
        return jsonify({"error": "Movie name required"}), 400

    movie_results = search_movie(movie_name)
    
    if movie_results:
        return jsonify({"movies": movie_results})
    else:
        return jsonify({"error": "No movies found"}), 404

# API to Get Direct Download Link
@app.route('/get_download', methods=['GET'])
def get_download():
    movie_url = request.args.get('url')
    if not movie_url:
        return jsonify({"error": "Movie URL required"}), 400

    direct_link = get_direct_download(movie_url)
    
    if direct_link:
        return jsonify({"direct_download_link": direct_link})
    else:
        return jsonify({"error": "Failed to fetch download link"}), 500

if __name__ == '__main__':
    app.run(debug=True)
