from flask import Flask, request, jsonify
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup
from fuzzywuzzy import process

app = Flask(__name__)
CORS(app)

scraper = cloudscraper.create_scraper()
BASE_URL = "https://vegamovies.cr/?s="

# Fetch movie search results
def search_movie(movie_name):
    search_url = f"{BASE_URL}{movie_name.replace(' ', '+')}"
    response = scraper.get(search_url)
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for post in soup.find_all("div", class_="result-item"):  # Update class accordingly
        title = post.find("h2").text.strip()
        link = post.find("a")["href"]
        img = post.find("img")["src"]
        results.append({"title": title, "link": link, "img": img})
    
    return results

# Extract direct download links
def get_download_links(movie_page_url):
    response = scraper.get(movie_page_url)
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if "download" in href:
            links.append(href)
    return links

@app.route('/search', methods=['GET'])
def search():
    movie_name = request.args.get('name')
    if not movie_name:
        return jsonify({"error": "Movie name required"}), 400
    
    results = search_movie(movie_name)
    if not results:
        return jsonify({"error": "No movie found"}), 404
    
    best_match = process.extractOne(movie_name, [r["title"] for r in results])
    if best_match and best_match[1] > 70:
        selected_movie = next(r for r in results if r["title"] == best_match[0])
        download_links = get_download_links(selected_movie["link"])
        selected_movie["download_links"] = download_links
        return jsonify(selected_movie)
    else:
        return jsonify({"error": "No exact match found, showing alternatives", "suggestions": results}), 200

if __name__ == '__main__':
    app.run(debug=True)
