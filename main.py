import requests
from dotenv import load_dotenv
import os
from datetime import datetime
import json

# Load environment variables from .env file
load_dotenv()

API_URL = os.getenv("API_URL")
GREEN_API_INSTANCE_ID = os.getenv("GREEN_API_INSTANCE_ID")
GREEN_API_API_TOKEN = os.getenv("GREEN_API_API_TOKEN")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")  # WhatsApp number to send the notification to (with country code)
TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # TMDB API key
LOG_FILE = "notified_movies.log"  # Log file to store notified movie IDs
HUMAN_FRIENDLY_LOG_FILE = "movie_notifier.log"  # Human-friendly log file

def fetch_genres():
    """Fetch the genres from the TMDB API."""
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        genres = {genre["id"]: genre["name"] for genre in data["genres"]}
        return genres
    except requests.RequestException as e:
        print(f"Error fetching genres: {e}")
        return {}

def fetch_latest_movies_and_tv_shows():
    """Fetch the latest movies and TV shows from the TMDB API."""
    url_movie = f"https://api.themoviedb.org/3/movie/latest?api_key={TMDB_API_KEY}&language=en-US"
    url_tv = f"https://api.themoviedb.org/3/tv/latest?api_key={TMDB_API_KEY}&language=en-US"
    
    try:
        # Fetch the latest movie and TV show
        response_movie = requests.get(url_movie)
        response_tv = requests.get(url_tv)
        
        response_movie.raise_for_status()
        response_tv.raise_for_status()

        movie_data = response_movie.json()
        tv_data = response_tv.json()

        # Fetch genres for mapping
        genres = fetch_genres()

        # Process movie
        latest_content = []
        
        # Process Movie
        title = movie_data.get("title")
        release_date = movie_data.get("release_date")
        description = movie_data.get("overview", "No description available.")
        poster_path = movie_data.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""  # Fixed image size (w500)
        movie_id = movie_data.get("id")
        genre_ids = movie_data.get("genre_ids", [])
        movie_genres = [genres.get(genre_id, "Unknown") for genre_id in genre_ids]
        genres_str = ", ".join(movie_genres)

        latest_content.append({
            "id": movie_id,
            "type": "movie",
            "title": title,
            "release_date": release_date,
            "description": description,
            "poster_url": poster_url,  # Using same size for all images
            "genres": genres_str
        })

        # Process TV Show
        title = tv_data.get("name")
        release_date = tv_data.get("first_air_date")
        description = tv_data.get("overview", "No description available.")
        poster_path = tv_data.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""  # Fixed image size (w500)
        tv_id = tv_data.get("id")
        genre_ids = tv_data.get("genre_ids", [])
        tv_genres = [genres.get(genre_id, "Unknown") for genre_id in genre_ids]
        genres_str = ", ".join(tv_genres)

        latest_content.append({
            "id": tv_id,
            "type": "tv",
            "title": title,
            "release_date": release_date,
            "description": description,
            "poster_url": poster_url,  # Using same size for all images
            "genres": genres_str
        })

        return latest_content
    
    except requests.RequestException as e:
        print(f"Error fetching latest content: {e}")
        return []

def format_date(date_str):
    """Format the date to be more human-readable."""
    if not date_str:
        return "Release date not available"  # Handle missing or empty dates
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")  # Return formatted date
    except ValueError:
        return "Invalid date format"  # Handle invalid date formats


def load_notified_movies():
    """Load the list of notified movies from the log file."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as file:
            return json.load(file)
    else:
        return []

def save_notified_movies(notified_movies):
    """Save the list of notified movies to the log file."""
    with open(LOG_FILE, "w") as file:
        json.dump(notified_movies, file)

def create_human_friendly_log(content, action):
    """Create a human-friendly log entry."""
    log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {action} - {content['title']}\n"
    
    # Open the log file with UTF-8 encoding to handle special characters
    with open(HUMAN_FRIENDLY_LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)


def send_whatsapp_notification(latest_content, notified_movies):
    """Send a WhatsApp message with details about the latest movies and TV shows."""
    if not latest_content:
        print("No latest content to notify.")
        return
    
    for content in latest_content:
        if content['id'] in notified_movies:
            print(f"Content {content['title']} already notified, skipping.")
            continue

        # Create the message with content details using the new format
        message = f"🎬 *Latest Update: New Releases!*\n\n"
        message += f"📌 *Title*: {content['title']}\n"
        message += f"📅 *Release Date*: {format_date(content['release_date'])}\n"  # Use the updated format_date function
        message += f"🎥 *Type*: {content['type'].capitalize()}\n"  # Capitalize the type (movie or TV show)
        message += f"📝 *Description*: {content['description']}\n\n"
        message += f"🎭 *Genres*: {content['genres']}\n"
        message += f"🔗 *Watch Now*: [Link to Content](https://www.themoviedb.org/{content['type']}/{content['id']})\n"

        # Send the same image size (w500) for all notifications
        image_url = content['poster_url']

        if image_url:
            payload = {
                "chatId": f"{WHATSAPP_NUMBER}@g.us",  # WhatsApp group id
                "urlFile": image_url,
                "fileName": f"{content['title']}_poster.jpg",
                "caption": message
            }
            url = f"{API_URL}/waInstance{GREEN_API_INSTANCE_ID}/sendFileByUrl/{GREEN_API_API_TOKEN}"
            headers = {
                'Content-Type': 'application/json'
            }
            try:
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                print(f"WhatsApp notification with poster sent successfully for {content['title']}!")

                # After sending the notification, add the content ID to the notified list
                notified_movies.append(content['id'])
                create_human_friendly_log(content, "Notified")
            except requests.exceptions.RequestException as e:
                print(f"Failed to send WhatsApp notification with poster for {content['title']}: {e}")

def main():
    """Main function to fetch latest content and send notifications."""
    print("Fetching the latest movies and TV shows...")
    latest_content = fetch_latest_movies_and_tv_shows()

    notified_movies = load_notified_movies()

    if latest_content:
        print("Latest content found! Sending WhatsApp notification...")
        send_whatsapp_notification(latest_content, notified_movies)
        # Save the updated list of notified movies
        save_notified_movies(notified_movies)
    else:
        print("No latest content available at the moment.")

if __name__ == "__main__":
    main()
