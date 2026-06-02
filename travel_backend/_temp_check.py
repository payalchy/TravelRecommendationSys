import sqlite3

conn = sqlite3.connect(r"c:\Users\Zeeya Shrestha\Desktop\smart_travel\TravelRecommendationSys\travel_backend\db.sqlite3")
cur = conn.cursor()
print(cur.execute("SELECT id, user_id, budget, preferred_duration, preferred_season, preferred_provinces FROM users_userprofile ORDER BY id DESC LIMIT 5").fetchall())
print(cur.execute("SELECT id, user_id, search_payload FROM users_searchhistory ORDER BY id DESC LIMIT 5").fetchall())
