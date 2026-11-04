#!/usr/bin/env python3
"""日本青年館ホール公式サイトの「公演案内」から hall.json を生成する（標準ライブラリのみ）。"""
import html
import json
import re
import sys
import unicodedata
import urllib.request
from datetime import date, datetime, timedelta, timezone

SRC = "https://seinenkan-hall.com/"
JST = timezone(timedelta(hours=9))


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def text(block, cls):
    m = re.search(r'class="performanceCard-%s">(.*?)</(?:div|h3)>' % cls, block, re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip()


def parse_dates(s):
    """'2026年11月17日（火）・18日（水）' / '2026年10月30日(金)〜11月8日(日)' → (開始, 終了, 個別日 or None)"""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[（(][^）)]*[）)]", "", s)
    m = re.match(r"\s*(\d{4})年(\d{1,2})月(\d{1,2})日(.*)$", s)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    start = date(y, mo, d)
    rest = m.group(4)
    if "・" in rest:
        days = [start] + [date(y, mo, int(x)) for x in re.findall(r"(\d{1,2})日", rest)]
        return start, max(days), sorted(days)
    e = re.match(r"\s*[〜～~-]\s*(?:(\d{1,2})月)?(\d{1,2})日", rest)
    if e:
        end = date(y + (1 if e.group(1) and int(e.group(1)) < mo else 0), int(e.group(1) or mo), int(e.group(2)))
        return start, end, None
    return start, start, None


def main():
    h = fetch()
    shows = []
    for m in re.finditer(r'<li class="swiper-slide performanceCard">(.*?)</li>', h, re.S):
        b = m.group(1)
        title, period = text(b, "tit"), text(b, "time")
        parsed = parse_dates(period) if period else None
        if not title or not parsed:
            print(f"skip: {title!r} {period!r}")
            continue
        start, end, days = parsed
        item = {"title": title, "tag": text(b, "tag"), "start": start.isoformat(), "end": end.isoformat()}
        if days:
            item["days"] = [x.isoformat() for x in days]
        shows.append(item)
    if not shows:
        sys.exit("no performances found on " + SRC)
    out = {"source": SRC, "updated": datetime.now(JST).isoformat(timespec="seconds"), "shows": shows}
    try:
        old = json.load(open("hall.json", encoding="utf-8"))
        if old.get("shows") == shows:
            print("hall.json: no change")
            return
    except (OSError, ValueError):
        pass
    with open("hall.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"hall.json: wrote {len(shows)} shows")


if __name__ == "__main__":
    main()
