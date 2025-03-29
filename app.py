from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup
import logging

app = Flask(__name__)
CORS(app)  # Allow frontend access

# Logging setup for debugging
logging.basicConfig(level=logging.DEBUG)

# Cloudflare Bypass Scraper
scraper = cloudscraper.create_scraper()

# Movie Search Function
def get_movie_download_link(movie_name):
    try:
        search_url = f"https://hdhub4u.soccer/?s={movie_name.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Referer": "https://hdhub4u.soccer/",
            "Accept-Language": "en-US,en;q=0.9",
        }

        logging.info(f"Searching movie: {movie_name} at {search_url}")

        response = scraper.get(search_url, headers=headers, timeout=20)
        if response.status_code != 200:
            logging.error(f"Failed to fetch search results. Status: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        movie_posts = soup.find_all("div", class_="result-item")  # Updated class name

        if not movie_posts:
            logging.warning("No movie found in search results.")
            return None

        # Extract first movie link
        first_result = movie_posts[0]
        movie_page_url = first_result.find("a")["href"]

        logging.info(f"Found movie page: {movie_page_url}")
        return extract_download_link(movie_page_url)

    except Exception as e:
        logging.error(f"Error in get_movie_download_link: {str(e)}")
        return None

# Extract Direct Download Link
def extract_download_link(movie_page_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Referer": "https://hdhub4u.soccer/",
        }

        logging.info(f"Fetching download links from: {movie_page_url}")

        response = scraper.get(movie_page_url, headers=headers, timeout=20)
        if response.status_code != 200:
            logging.error(f"Failed to fetch movie page. Status: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        download_links = [a["href"] for a in soup.find_all("a") if "download" in a.get("href", "")]

        if not download_links:
            logging.warning("No download links found on page.")
            return None

        logging.info(f"Direct Download Link Found: {download_links[0]}")
        return download_links[0]

    except Exception as e:
        logging.error(f"Error in extract_download_link: {str(e)}")
        return None

# Movie Search API
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

# Auto Redirect to Direct Download
@app.route('/download', methods=['GET'])
def auto_download():
    movie_url = request.args.get('url')
    if not movie_url:
        return jsonify({"error": "Movie download URL required"}), 400

    return redirect(movie_url, code=302)

if __name__ == '__main__':
    app.run(debug=True)
