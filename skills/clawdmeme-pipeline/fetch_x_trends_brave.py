import os, re, json, sys, time, random
import requests

UA = {"User-Agent": "Mozilla/5.0"}

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY") or os.getenv("BRAVE_SEARCH_API_KEY")
if not BRAVE_API_KEY:
    raise SystemExit("Missing BRAVE_API_KEY (or BRAVE_SEARCH_API_KEY) in env.")

def brave_search(q: str, count: int = 20, max_retries: int = 6):
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
        **UA
    }
    params = {"q": q, "count": count}

    backoff = 2.0
    for _ in range(max_retries):
        r = requests.get(url, headers=headers, params=params, timeout=30)

        if r.status_code == 200:
            # Free plan: stay under rate limit
            time.sleep(random.uniform(1.2, 1.6))
            return r.json(), None

        if r.status_code == 429:
            ra = r.headers.get("Retry-After")
            wait = float(ra) if (ra and ra.isdigit()) else backoff
            wait = min(wait, 30.0)
            time.sleep(wait + random.uniform(0.2, 0.8))
            backoff = min(backoff * 2, 30.0)
            continue

        return None, {"status": r.status_code, "body": r.text[:300]}

    return None, {"status": 429, "body": "Rate-limited: max retries exceeded"}

def extract_urls(data):
    urls = []
    for item in (data.get("web", {}) or {}).get("results", []) or []:
        u = item.get("url")
        if u:
            urls.append(u)
    # dedupe preserve order
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def is_x_status_url(u: str) -> bool:
    return ("x.com/" in u or "twitter.com/" in u) and ("/status/" in u)

def extract_tweet_id(url: str):
    m = re.search(r"/status/(\d+)", url)
    return m.group(1) if m else None

def fetch_x_metrics(tweet_id: str):
    api = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en"
    r = requests.get(api, headers=UA, timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    likes = data.get("favorite_count") or data.get("favoriteCount") or data.get("like_count") or 0
    reposts = data.get("retweet_count") or data.get("retweetCount") or data.get("repost_count") or 0
    replies = data.get("reply_count") or data.get("replyCount") or data.get("conversation_count") or 0
    return {"likes": int(likes), "reposts": int(reposts), "replies": int(replies), "source": api}

def main():
    # Content-shape queries (not crypto keywords)
    queries = [
        # Iconic / PFP / mascot
        'site:x.com (pfp OR mascot) ("caption this" OR meme) status',
        'site:x.com ("new pfp" OR "this is my pfp") (meme OR pfp) status',
        'site:x.com (dog OR cat OR frog OR shark) (meme OR pfp) status',

        # Templateable
        'site:x.com ("caption this" OR "make this a meme") status',
        'site:x.com ("X is inevitable" OR "we are so back") status',

        # Us vs them / rebellion
        'site:x.com ("retail" OR "community") ("VC" OR suits) (meme OR pfp) status',
        'site:x.com ("they don\'t get it" OR "we don\'t care") meme status',

        # Quest / rallying cry
        'site:x.com ("send it" OR "get this to") meme status',
        'site:x.com ("change his pfp" OR "make him change") status',

        # Event parasite
        'site:x.com ("breaking:" OR "just happened" OR "today\'s episode") meme status',
    ]

    want_metrics = True  # keep metrics best-effort

    items = []
    errors = []

    for q in queries:
        data, err = brave_search(q, count=20)
        if err:
            errors.append({"query": q, **err})
            continue

        for u in extract_urls(data):
            if not is_x_status_url(u):
                continue
            u = u.replace("twitter.com", "x.com")
            tid = extract_tweet_id(u)

            m = fetch_x_metrics(tid) if (want_metrics and tid) else None
            items.append({"url": u, "tweetId": tid, "metrics": m, "fromQuery": q})

        # extra spacing between queries
        time.sleep(1.0 + random.uniform(0.3, 0.8))

    # dedupe by url
    seen, uniq = set(), []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        uniq.append(it)

    out = {
        "generatedAt": int(time.time()),
        "count": len(uniq),
        "items": uniq[:80],   # return up to 80 urls
        "errors": errors
    }
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
