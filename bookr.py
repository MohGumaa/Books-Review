import requests
res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "xC8CXDYwBlxBLMxmOHjyJw", "isbns": "9781632168146"}).json()["books"][0]

ratings_count = res['work_ratings_count']
print(ratings_count)
