"""Q7 Count crawled HTML files: crawl the tdsdata crawl_html site and count HTML files starting with letters FIRST..LAST.

Run: uv run q07_crawl_html.py FIRST LAST   (the letter range in your question, e.g. A K)
"""
import re, sys, urllib.parse, urllib.request

if len(sys.argv) < 3:
    sys.exit(__doc__)
FIRST, LAST = sys.argv[1].lower(), sys.argv[2].lower()
START = "https://sanand0.github.io/tdsdata/crawl_html/"
seen, files = set(), set()

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req).read().decode("utf-8", "ignore")

def crawl(url):
    if url in seen or not url.startswith(START):
        return
    seen.add(url)
    try:
        html = get(url)
    except Exception as e:
        print("skip", url, e)
        return
    for href in re.findall(r'href=["\']([^"\']+)["\']', html):
        nxt = urllib.parse.urljoin(url, href).split("#")[0].split("?")[0]
        if not nxt.startswith(START):
            continue
        if nxt.lower().endswith((".html", ".htm")):
            files.add(nxt)
            crawl(nxt)
        elif nxt.endswith("/"):
            crawl(nxt)

crawl(START)

names = [u.rstrip("/").split("/")[-1] for u in files]
hits = [n for n in names if FIRST <= n[0].lower() <= LAST]
label = f"{FIRST.upper()} to {LAST.upper()}"
print("pages visited:", len(seen))
print("total html files:", len(files))
print(label, "(counting duplicates in different folders):", len(hits))
print(label, "(unique filenames):", len(set(n.lower() for n in hits)))
