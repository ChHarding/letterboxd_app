import feedparser
from keys import OMDB_API_KEY

username = "protocrone"

url = "https://letterboxd.com/" + username + "/rss/"
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
feed = feedparser.parse(url)

diary = get_diary_entries(feed)
print(diary[0])
print(diary[1])