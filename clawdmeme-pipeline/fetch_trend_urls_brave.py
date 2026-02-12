import os, re, json, sys, time
import requests

UA = {"User-Agent": "Mozilla/5.0"}

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY") or os.getenv("BRAVE_SEARCH_API_KEY")
if not BRAVE_API_KEY:
    raise SystemExit("Missing BRAVE_API_KEY or BRAVE_SEARCH_API_KEY in env.")

def brave_search(q: str, count: int = 10):
    # Brave Web Search API
    # Docs vary by plan; this endpoint commonly works:
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
        **UA
    }
    params = {"q": q, "count": count}
    r = requests.get(url, headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        return None, {"status": r.status_code, "body": r.text[:400]}
    return r.json(), None

def extract_urls(result_json):
    urls = []
    web = result_json.get("web", {})
    for item in web.get("results", []) or []:
        u = item.get("url")
        if u:
            urls.append(u)
    # dedupe
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
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

def is_x_url(u: str) -> bool:
    return "x.com/" in u or "twitter.com/" in u

def is_tiktok_url(u: str) -> bool:
    return "tiktok.com/" in u

def main():
    # You can pass queries; if not, we use broad ones.
    queries = sys.argv[1:] or [
        'site:x.com (meme OR "pump.fun" OR solana) status',
        'site:tiktok.com (solana OR "meme coin" OR pump) video'
    ]

    out = {"generatedAt": int(time.time()), "queries": queries, "x": [], "tiktok": [], "errors": []}

    for q in queries:
        data, err = brave_search(q, count=20)
        if err:
            out["errors"].append({"query": q, **err})
            continue
        urls = extract_urls(data)
        for u in urls:
            if is_x_url(u):
                xurl = u.replace("twitter.com", "x.com")
                tid = extract_tweet_id(xurl)
                metrics = fetch_x_metrics(tid) if tid else None
                out["x"].append({"url": xurl, "tweetId": tid, "metrics": metrics, "fromQuery": q})
            elif is_tiktok_url(u):
                out["tiktok"].append({"url": u, "fromQuery": q})

        time.sleep(0.2)

    # dedupe x/tiktok by url
    def dedupe(items):
        seen, res = set(), []
        for it in items:
            if it["url"] in seen: 
                continue
            seen.add(it["url"])
            res.append(it)
        return res

    out["x"] = dedupe(out["x"])
    out["tiktok"] = dedupe(out["tiktok"])

    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
