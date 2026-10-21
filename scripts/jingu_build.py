#!/usr/bin/env python3
"""明治神宮野球場の公式スケジュールJSONから jingu.json を生成する。"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

SRC = "https://www.jingu-stadium.com/event/json/data.json"
OUT = "jingu.json"
LOOKAHEAD_DAYS = 120
JST = timezone(timedelta(hours=9))

TEAM_FULL = {
    "慶大": "慶應義塾大学", "早大": "早稲田大学", "明大": "明治大学",
    "東大": "東京大学", "法大": "法政大学", "立大": "立教大学",
    "中央大": "中央大学", "亜細亜大": "亜細亜大学", "國學院大": "國學院大学",
    "東洋大": "東洋大学", "立正大": "立正大学", "青学大": "青山学院大学",
    "東京ヤクルト": "ヤクルト", "北海道日本ハム": "日本ハム",
    "千葉ロッテ": "ロッテ", "埼玉西武": "西武", "横浜DeNA": "DeNA",
}


def team_name(raw):
    m = re.search(r"alt=['\"]([^'\"]*)['\"]", raw)
    name = m.group(1) if m else re.sub(r"<[^>]+>", "", raw)
    name = name.strip()
    return TEAM_FULL.get(name, name)


PRO_SHORT = {
    "東京ヤクルト": "ヤクルト", "北海道日本ハム": "日本ハム", "千葉ロッテ": "ロッテ",
    "埼玉西武": "西武", "横浜DeNA": "DeNA",
}
SCORE_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")


def short_team(raw):
    m = re.search(r"alt=['\"]([^'\"]*)['\"]", raw)
    name = (m.group(1) if m else re.sub(r"<[^>]+>", "", raw)).strip()
    return PRO_SHORT.get(name, name)


def build_results(data, today):
    start = datetime(today.year, 9 if today.month >= 8 else 3, 1).date()
    end = today + timedelta(days=30)
    games = []
    for y, m, d, blog_cat, e in iter_events(data):
        try:
            day = datetime(y, m, d).date()
        except ValueError:
            continue
        if not (start <= day <= end):
            continue
        cat = e.get("category", "")
        if blog_cat == "A":
            lg = "npb"
        elif blog_cat == "B" and "六大学" in cat:
            lg = "big6"
        elif blog_cat == "B" and "東都" in cat:
            lg = "tohto"
        else:
            continue
        for g in e.get("value") or []:
            if not (g.get("team1") and g.get("team2")):
                continue
            item = {"d": day.isoformat(), "t": e.get("time") or "", "lg": lg,
                    "a": short_team(g["team1"]), "b": short_team(g["team2"]),
                    "sa": None, "sb": None, "st": "sched"}
            sm = SCORE_RE.match(g.get("result") or "")
            if g.get("cancel") == "true":
                item["st"] = "cancel"
            elif sm:
                item["st"], item["sa"], item["sb"] = "final", int(sm.group(1)), int(sm.group(2))
            games.append(item)
    games.sort(key=lambda x: (x["d"], x["t"] or "99:99"))
    return start.isoformat(), games


def write_if_changed(path, payload, same):
    try:
        with open(path, encoding="utf-8") as f:
            if same(json.load(f)):
                return False
    except (FileNotFoundError, ValueError):
        pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return True


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def iter_events(data):
    for blog in data:
        for block in blog if isinstance(blog, list) else [blog]:
            if not isinstance(block, dict) or "yearData" not in block:
                continue
            for ym in block["yearData"]:
                for md in ym["monthData"]:
                    for e in md["dayData"]:
                        yield block["year"], ym["month"], md["day"], block["blogCategory"], e


def convert_event(blog_cat, e):
    name = e.get("category", "").strip()
    if blog_cat == "A":
        name = "プロ野球"
    time = e.get("time", "") or ""
    games = e.get("value") or []
    if not games:
        return [{"time": time, "name": name, "sub": ""}]
    out = []
    for i, g in enumerate(games):
        if not (g.get("team1") and g.get("team2")):
            continue
        sub = f"{team_name(g['team1'])} vs {team_name(g['team2'])}"
        if g.get("cancel") == "true":
            sub += "（中止）"
        out.append({"time": time if i == 0 else "", "name": name, "sub": sub})
    return out or [{"time": time, "name": name, "sub": ""}]


def main():
    data = fetch()
    today = datetime.now(JST).date()
    last = today + timedelta(days=LOOKAHEAD_DAYS)
    days = {}
    total = 0
    for y, m, d, blog_cat, e in iter_events(data):
        total += 1
        try:
            day = datetime(y, m, d).date()
        except ValueError:
            continue
        if not (today <= day <= last):
            continue
        days.setdefault(day.isoformat(), []).append((e.get("time") or "99:99", len(days.get(day.isoformat(), [])), convert_event(blog_cat, e)))
    if total < 100:
        sys.exit(f"unexpected data: only {total} events in source")
    result_days = {}
    for k in sorted(days):
        items = []
        for _, _, evs in sorted(days[k], key=lambda x: (x[0], x[1])):
            items.extend(evs)
        result_days[k] = items
    now = datetime.now(JST).isoformat(timespec="seconds")
    out = {"source": SRC, "updated": now, "days": result_days}
    a = write_if_changed("jingu.json", out, lambda old: old.get("days") == out["days"])
    season_start, games = build_results(data, today)
    res = {"source": SRC, "updated": now, "season_start": season_start, "games": games}
    b = write_if_changed("results.json", res, lambda old: old.get("games") == games)
    print(f"jingu.json: {'wrote ' + str(len(result_days)) + ' days' if a else 'no change'} / results.json: {'wrote ' + str(len(games)) + ' games' if b else 'no change'}")


if __name__ == "__main__":
    main()
