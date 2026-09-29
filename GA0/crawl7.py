import re, urllib.parse, urllib.request

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

crawl(START)                      # <-- this call was missing

names = [u.rstrip("/").split("/")[-1] for u in files]
bn = [n for n in names if "b" <= n[0].lower() <= "n"]
print("pages visited:", len(seen))
print("total html files:", len(files))
print("B to N (counting duplicates in different folders):", len(bn))
print("B to N (unique filenames):", len(set(n.lower() for n in bn)))