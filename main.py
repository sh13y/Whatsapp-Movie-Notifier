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

# Fetch genres for movies and TV shows
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

# Fetch top movies for the week (using 'top_rated' or 'now_playing' endpoint)
def fetch_top_movies():
    """Fetch the top movies for the week from the TMDB API."""
    url = f"https://api.themoviedb.org/3/movie/top_rated?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Debugging: Print the API response
        print("Top Movies:", data)

    except requests.RequestException as e:
        print(f"Error fetching top movies: {e}")
        return []

    top_movies = []
    genres = fetch_genres()  # Fetch genre names

    for movie in data.get("results", []):
        title = movie.get("title")
        release_date = movie.get("release_date")
        description = movie.get("overview", "No description available.")
        poster_path = movie.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
        movie_id = movie.get("id")  # Unique ID to track which movies have been notified
        genre_ids = movie.get("genre_ids", [])
        
        # Map genre IDs to genre names
        movie_genres = [genres.get(genre_id, "Unknown") for genre_id in genre_ids]
        genres_str = ", ".join(movie_genres)  # Genres as comma-separated string

        # Add movie to the top_movies list
        top_movies.append({
            "id": movie_id,
            "title": title,
            "release_date": release_date,
            "description": description,
            "poster_url": poster_url,
            "genres": genres_str
        })

    return top_movies

# Fetch top TV shows for the week (using 'top_rated' or 'airing_today' endpoint)
def fetch_top_tv_shows():
    """Fetch the top TV shows for the week from the TMDB API."""
    url = f"https://api.themoviedb.org/3/tv/top_rated?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Debugging: Print the API response
        print("Top TV Shows:", data)

    except requests.RequestException as e:
        print(f"Error fetching top TV shows: {e}")
        return []

    top_tv_shows = []
    genres = fetch_genres()  # Fetch genre names

    for tv_show in data.get("results", []):
        title = tv_show.get("name")
        first_air_date = tv_show.get("first_air_date")
        description = tv_show.get("overview", "No description available.")
        poster_path = tv_show.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
        tv_show_id = tv_show.get("id")  # Unique ID to track which shows have been notified
        genre_ids = tv_show.get("genre_ids", [])
        
        # Map genre IDs to genre names
        tv_show_genres = [genres.get(genre_id, "Unknown") for genre_id in genre_ids]
        genres_str = ", ".join(tv_show_genres)  # Genres as comma-separated string

        # Add TV show to the top_tv_shows list
        top_tv_shows.append({
            "id": tv_show_id,
            "title": title,
            "release_date": first_air_date,
            "description": description,
            "poster_url": poster_url,
            "genres": genres_str
        })

    return top_tv_shows

# Format the date to a human-readable format
def format_date(date_str):
    """Format the date to be more human-readable."""
    if date_str:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    return "Unknown"

# Load the list of notified movies and TV shows
def load_notified_movies():
    """Load the list of notified movies from the log file."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as file:
            return json.load(file)
    else:
        return []

# Save the list of notified movies and TV shows
def save_notified_movies(notified_movies):
    """Save the list of notified movies to the log file."""
    with open(LOG_FILE, "w") as file:
        json.dump(notified_movies, file)

# Create a human-friendly log entry
def create_human_friendly_log(content, action):
    """Create a human-friendly log entry."""
    log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {action} - {content['title']}\n"
    with open(HUMAN_FRIENDLY_LOG_FILE, "a", encoding='utf-8') as log_file:
        log_file.write(log_entry)

# Send a WhatsApp notification
def send_whatsapp_notification(content_list, notified_movies, content_type):
    """Send a WhatsApp message with details about the top content (movies or TV shows)."""
    if not content_list:
        print(f"No {content_type} content to notify.")
        return
    
    for content in content_list:
        if content['id'] in notified_movies:
            print(f"Content {content['title']} already notified, skipping.")
            continue

        # Create the message with content details
        message = f"🎬 *Top {content_type.capitalize()} for the Week!*\n\n"
        message += f"📌 *{content['title']}*\n"
        message += f"📅 *Release Date*: {format_date(content['release_date'])}\n"
        message += f"💬 {content['description']}\n"
        message += f"🎥 *Genres*: {content['genres']}\n"
        
        # Standardize image size to 500x750 pixels
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
                print(f"Failed to send WhatsApp notification for {content['title']}: {e}")

# Main function to fetch top movies and TV shows for the week and send notifications
def main():
    """Main function to fetch top movies and TV shows for the week and send notifications."""
    print("Fetching top movies for the week...")
    top_movies = fetch_top_movies()

    # Notify about top movies
    notified_movies = load_notified_movies()
    if top_movies:
        print("Top movies found! Sending WhatsApp notifications...")
        send_whatsapp_notification(top_movies, notified_movies, "movie")
        save_notified_movies(notified_movies)
    else:
        print("No top movies found.")

    # Now fetch and notify about top TV shows
    print("Fetching top TV shows for the week...")
    top_tv_shows = fetch_top_tv_shows()

    # Notify about top TV shows
    if top_tv_shows:
        print("Top TV shows found! Sending WhatsApp notifications...")
        send_whatsapp_notification(top_tv_shows, notified_movies, "tv")
        save_notified_movies(notified_movies)
    else:
        print("No top TV shows found.")

if __name__ == "__main__":
    main()
