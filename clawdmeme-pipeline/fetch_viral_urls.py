import re, json, sys, time
import requests

UA = {"User-Agent": "Mozilla/5.0"}

def get(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=30, allow_redirects=True)
    r.raise_for_status()
    return r.text

def nitter_search(query: str, limit: int = 20):
    """
    Use Nitter search HTML (no JS needed). Returns x.com status URLs.
    """
    q = requests.utils.quote(query)
    html = get(f"https://nitter.net/search?f=tweets&q={q}&since=&until=&near=")
    # Nitter tweet links often look like: /username/status/123...
    rel = re.findall(r'href="(/[^"/]+/status/\d+)"', html)
    # convert to x.com
    urls = ["https://x.com" + r for r in rel]
    # dedupe
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
        if len(out) >= limit:
            break
    return out

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

def filter_x(m, min_likes, min_reposts, min_replies):
    return m["likes"] >= min_likes and m["reposts"] >= min_reposts and m["replies"] >= min_replies

def main():
    keywords = sys.argv[1:] or ["solana meme", "pump fun", "meme coin"]
    cfg = {
        "x": {"min_likes": 200, "min_reposts": 20, "min_replies": 10},
        "per_keyword": 20
    }

    items = []
    for kw in keywords:
        urls = nitter_search(kw, limit=cfg["per_keyword"])
        for u in urls:
            tid = extract_tweet_id(u)
            if not tid:
                continue
            m = fetch_x_metrics(tid)
            if not m:
                continue
            if filter_x(m, **cfg["x"]):
                items.append({"platform": "x", "keyword": kw, "url": u, "metrics": m})
            time.sleep(0.2)

    # dedupe
    seen, uniq = set(), []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        uniq.append(it)

    print(json.dumps({"generatedAt": int(time.time()), "items": uniq}, ensure_ascii=False))

if __name__ == "__main__":
    main()
