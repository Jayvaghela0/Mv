from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Cloudflare Bypass Scraper
scraper = cloudscraper.create_scraper()

# 🔍 Function: Get Search Results
def get_search_results(movie_name):
    search_url = f"https://hdhub4u.soccer/?s={movie_name.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://hdhub4u.soccer/",
    }

    response = scraper.get(search_url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    # Extract multiple movies from search results
    for post in soup.find_all("div", class_="result-item"):  # Class name को confirm करें
        movie_link = post.find("a")["href"]
        movie_title = post.find("h2").text.strip()
        results.append({"title": movie_title, "link": movie_link})

    return results if results else None

# 🎯 Function: Extract Direct Download Link
def extract_download_link(movie_page_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://hdhub4u.soccer/",
    }
    response = scraper.get(movie_page_url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    download_links = [a["href"] for a in soup.find_all("a") if "download" in a.get("href", "")]
    return download_links if download_links else None

# 🟢 API Route: Search Movies
@app.route('/search', methods=['GET'])
def search_movie():
    movie_name = request.args.get('name')
    if not movie_name:
        return jsonify({"error": "Movie name required"}), 400

    results = get_search_results(movie_name)
    if results:
        return jsonify({"movies": results})
    else:
        return jsonify({"error": "No movie found"}), 404

# 🔵 API Route: Get Direct Download Link
@app.route('/get_download', methods=['GET'])
def get_download():
    movie_url = request.args.get('url')
    if not movie_url:
        return jsonify({"error": "Movie page URL required"}), 400

    direct_links = extract_download_link(movie_url)
    if direct_links:
        return jsonify({"download_links": direct_links})
    else:
        return jsonify({"error": "No download link found"}), 404

# 🔴 Auto Redirect for Direct Download
@app.route('/download', methods=['GET'])
def auto_download():
    movie_url = request.args.get('url')
    if not movie_url:
        return jsonify({"error": "Movie download URL required"}), 400

    return redirect(movie_url, code=302)

if __name__ == '__main__':
    app.run(debug=True)
