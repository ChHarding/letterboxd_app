# imports for RSS parsing, API requests, data storage, and date handling
import feedparser
OMDB_API_KEY = "60ab2584"
import requests
import pandas as pd
import os
from datetime import datetime, timedelta

#this is hard coded so that you can see good results. It will say input() in the real version.
username = "protocrone" 

# build the RSS feed URL and fetch it using the username
url = "https://letterboxd.com/" + username + "/rss/"
feed = feedparser.parse(url)

# loop through each entry in the feed and pull out just the fields we need
# using .get() instead of dot notation so missing fields return None instead of crashing
def get_diary_entries(feed):
    entries = []
    for entry in feed.entries:
        film = {}
        film["title"] = entry.get("letterboxd_filmtitle")
        film["year"] = entry.get("letterboxd_filmyear")
        film["rating"] = entry.get("letterboxd_memberrating")
        film["watched_date"] = entry.get("letterboxd_watcheddate")
        film["rewatch"] = entry.get("letterboxd_rewatch")
        entries.append(film)
    return entries

# send a request to OMDb using the film title and return the fields we need 
# if OMDb can't find the film or something goes wrong, return None
# TODO: title matching isn't perfect, a film with a similar name could return wrong results
def get_omdb_data(title):
    url = "https://www.omdbapi.com/"
    params = {
        "t": title,
        "apikey": OMDB_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("Response") == "True":
        return {
            "genre": data.get("Genre"),
            "director": data.get("Director"),
            "runtime": data.get("Runtime"),
            "imdb_rating": data.get("imdbRating")
        }
    else:
        return None

# loop through diary entries and query OMDb for each film
# if a film has no title or OMDb can't find it, fill missing fields with None
# TODO: check CSV first so we only query OMDb for films we haven't seen before
def build_film_list(diary):
    films = []
    for film in diary:
        if film["title"] is None:
            continue
        omdb = get_omdb_data(film["title"])
        if omdb is not None:
            film["genre"] = omdb["genre"]
            film["director"] = omdb["director"]
            film["runtime"] = omdb["runtime"]
            film["imdb_rating"] = omdb["imdb_rating"]
        else:
            film["genre"] = None
            film["director"] = None
            film["runtime"] = None
            film["imdb_rating"] = None
        films.append(film)
    return films

# convert the list of film dictionaries into a dataframe and save it as a CSV
def save_to_csv(films, username):
    df = pd.DataFrame(films)
    df.to_csv(username + ".csv", index=False)
    print("Saved", len(films), "films to", username + ".csv")

# snapshot section (last 30 days)
def get_snapshot(films):
    today = datetime.today()
    thirty_days_ago = today - timedelta(days=30)

    # convert the watched_date string to a date object so we can compare it to today  
    # number of films watched
    recent_films = []
    for film in films:
        if film["watched_date"] is not None:
            watched = datetime.strptime(str(film["watched_date"]), "%Y-%m-%d")
            if watched >= thirty_days_ago:
                recent_films.append(film)

    # strip the "min" text out of the runtime string and add it to the total  
    # count up total hours watched
    total_minutes = 0
    for film in recent_films:
        if film["runtime"] is not None:
            runtime_str = str(film["runtime"])
            if "min" in runtime_str:
                minutes = int(runtime_str.replace(" min", ""))
                total_minutes += minutes
    total_hours = round(total_minutes / 60, 1)
    
    # find most watched genre
    # split genre strings since OMDb returns them comma separated (e.g. "Action, Drama")
    genre_counts = {}
    for film in recent_films:
        if film["genre"] is not None:
            genres = str(film["genre"]).split(", ")
            for genre in genres:
                if genre in genre_counts:
                    genre_counts[genre] += 1
                else:
                    genre_counts[genre] = 1
    
    if genre_counts:
        top_genre = max(genre_counts, key=genre_counts.get)
    else:
        top_genre = "N/A"
    
    print("--- Snapshot: Your Last 30 Days ---")
    print("Films watched:", len(recent_films))
    print("Hours watched:", total_hours)
    print("Most watched genre:", top_genre)

# variety section
def get_variety(films):
    # count unique genres
    # split genre strings and add any we haven't seen yet to the list
    all_genres = []
    for film in films:
        if film["genre"] is not None:
            genres = str(film["genre"]).split(", ")
            for genre in genres:
                if genre not in all_genres:
                    all_genres.append(genre)
    
    # count unique directors
    # same approach for directors, splitting on comma since some films have multiple
    all_directors = []
    for film in films:
        if film["director"] is not None:
            directors = str(film["director"]).split(", ")
            for director in directors:
                if director not in all_directors:
                    all_directors.append(director)
    
    # find oldest and newest film by release year
    years = []
    for film in films:
        if film["year"] is not None:
            years.append(int(film["year"]))
    
    oldest = min(years) if years else "N/A"
    newest = max(years) if years else "N/A"
    
    # output
    print("--- Variety ---")
    print("Unique genres watched:", len(all_genres))
    print("Unique directors watched:", len(all_directors))
    print("Oldest film release year:", oldest)
    print("Newest film release year:", newest)

def get_rating_breakdown(films):
    # average rating by genre
    genre_ratings = {}
    genre_counts = {}
    for film in films:
        if film["genre"] is not None and film["rating"] is not None:
            genres = str(film["genre"]).split(", ")
            for genre in genres:
                if genre not in genre_ratings:
                    genre_ratings[genre] = 0
                    genre_counts[genre] = 0
                genre_ratings[genre] += float(film["rating"])
                genre_counts[genre] += 1
    
    print("--- Rating Breakdown ---")
    print("Average rating by genre (min. 3 films):")
    for genre in genre_ratings:
        if genre_counts[genre] >= 3:
            avg = round(genre_ratings[genre] / genre_counts[genre], 2)
            print(" ", genre + ":", avg)
    
    # average rating by director
    director_ratings = {}
    director_counts = {}
    for film in films:
        if film["director"] is not None and film["rating"] is not None:
            directors = str(film["director"]).split(", ")
            for director in directors:
                if director not in director_ratings:
                    director_ratings[director] = 0
                    director_counts[director] = 0
                director_ratings[director] += float(film["rating"])
                director_counts[director] += 1
    
    print("Average rating by director (min. 3 films):")
    for director in director_ratings:
        if director_counts[director] >= 3:
            avg = round(director_ratings[director] / director_counts[director], 2)
            print(" ", director + ":", avg)

    # average rating by decade
    decade_ratings = {}
    decade_counts = {}
    for film in films:
        if film["year"] is not None and film["rating"] is not None:
            decade = (int(film["year"]) // 10) * 10
            decade_str = str(decade) + "s"
            if decade_str not in decade_ratings:
                decade_ratings[decade_str] = 0
                decade_counts[decade_str] = 0
            decade_ratings[decade_str] += float(film["rating"])
            decade_counts[decade_str] += 1
    
    print("Average rating by decade (min. 3 films):")
    for decade in sorted(decade_ratings):
        if decade_counts[decade] >= 3:
            avg = round(decade_ratings[decade] / decade_counts[decade], 2)
            print(" ", decade + ":", avg)
    
    # average difference between user rating and imdb rating
    differences = []
    for film in films:
        if film["rating"] is not None and film["imdb_rating"] is not None:
            user_rating = float(film["rating"])
            imdb_rating = float(film["imdb_rating"])
            # convert imdb rating from 10 point scale to 5 point scale
            imdb_converted = imdb_rating / 2
            diff = round(user_rating - imdb_converted, 2)
            differences.append(diff)
    
    print("Your ratings vs IMDb:")
    if differences:
        avg_diff = round(sum(differences) / len(differences), 2)
        if avg_diff > 0:
            print("On average, you rate films", avg_diff, "stars higher than IMDb")
        elif avg_diff < 0:
            print("On average, you rate films", abs(avg_diff), "stars lower than IMDb")
        else:
            print("Woah! Your average ratings match IMDb EXACTLY!")

    # most controversial opinion
    biggest_diff = 0
    controversial_film = None
    for film in films:
        if film["rating"] is not None and film["imdb_rating"] is not None:
            user_rating = float(film["rating"])
            imdb_converted = float(film["imdb_rating"]) / 2
            diff = abs(user_rating - imdb_converted)
            if diff > biggest_diff:
                biggest_diff = diff
                controversial_film = film
    
    if controversial_film is not None:
        user = float(controversial_film["rating"])
        imdb = round(float(controversial_film["imdb_rating"]) / 2, 2)
        print("Most controversial opinion:", controversial_film["title"])
        print("  You rated it:", user, "| IMDb average:", imdb)

# ratings graph
def get_rating_histogram(films):
    # count how many films got each star rating
    ratings = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    counts = {}
    for r in ratings:
        counts[r] = 0
    
    for film in films:
        if film["rating"] is not None:
            r = float(film["rating"])
            if r in counts:
                counts[r] += 1
    
    print("--- Rating Graph ---")
    for r in ratings:
        print(" ", r, "stars:", counts[r])

diary = get_diary_entries(feed)

# if a CSV exists for this user, load it instead of hitting the OMDb API again
# TODO: only query OMDb for films not already in the CSV instead of skipping entirely
if os.path.exists(username + ".csv"):
    df = pd.read_csv(username + ".csv")
    films = df.to_dict("records")
    print("Loaded existing data for", username)
else:
    films = build_film_list(diary)
    save_to_csv(films, username)

get_snapshot(films)
get_variety(films)
get_rating_breakdown(films)
get_rating_histogram(films)