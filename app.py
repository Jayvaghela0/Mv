from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Cloudflare Bypass Scraper
scraper = cloudscraper.create_scraper()

# Movie Search Function
def get_movie_download_link(movie_name):
    search_url = f"https://hdhub4u.soccer/?s={movie_name.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://hdhub4u.tube/",
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = scraper.get(search_url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    first_result = soup.find("div", class_="post")
    if not first_result:
        return None

    movie_page_url = first_result.find("a")["href"]
    return extract_download_link(movie_page_url)

# Extract Direct Download Link
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
    return download_links[0] if download_links else None

@app.route('/search', methods=['GET'])
def search_movie():
    movie_name = request.args.get('name')
    if not movie_name:
        return jsonify({"error": "Movie name required"}), 400

    direct_link = get_movie_download_link(movie_name)
    if direct_link:
        return jsonify({"direct_download_link": direct_link})
    else:
        return jsonify({"error": "No movie found"}), 404

@app.route('/download', methods=['GET'])
def auto_download():
    movie_url = request.args.get('url')
    if not movie_url:
        return jsonify({"error": "Movie download URL required"}), 400

    return redirect(movie_url, code=302)

if __name__ == '__main__':
    app.run(debug=True)
