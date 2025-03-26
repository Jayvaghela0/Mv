from flask import Flask, request, jsonify
from flask_cors import CORS
from telethon.sync import TelegramClient

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Telegram API Credentials
api_id = YOUR_API_ID  # Replace with your Telegram API ID
api_hash = "YOUR_API_HASH"  # Replace with your API Hash
channel_username = "YourMovieChannel"  # Replace with Telegram channel username or ID

client = TelegramClient("session_name", api_id, api_hash)

def generate_download_link(file_id):
    """
    Yeh function Telegram file ka direct download link generate karega.
    """
    return f"https://api.telegram.org/file/bot{api_id}:{api_hash}/{file_id}"

@app.route("/search", methods=["GET"])
def search_movie():
    movie_name = request.args.get("q")
    if not movie_name:
        return jsonify({"error": "Movie name is required"}), 400

    movies = []
    with client:
        for message in client.iter_messages(channel_username, search=movie_name, limit=10):
            if message.document or message.video:
                file_id = message.id
                file_name = message.file.name
                file_size = message.file.size

                # Generate direct download link
                download_link = generate_download_link(file_id)

                movies.append({"name": file_name, "size": file_size, "url": download_link})

    return jsonify({"results": movies})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
