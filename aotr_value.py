#!/usr/bin/env python3
"""
AOTR value lookup: shows an item's value in Emperor's Keys, Memory Scrolls and Vizard's Masks.

  python3 aotr_value.py third eye
  python3 aotr_value.py 2x toji attire
  python3 aotr_value.py third eye --discord     # also sends it to your webhook

Needs aotr_values.json next to this file. --discord uses DISCORD_WEBHOOK_URL.
"""
import difflib, json, os, re, sys, urllib.request
from pathlib import Path

DATA = json.loads(Path(__file__).with_name("aotr_values.json").read_text(encoding="utf-8"))
R = DATA["rates"]
norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[’'`]", "", s.lower())).strip()


def fmt(n):
    a = abs(n)
    for limit, div, suf in ((1e9, 1e9, "B"), (1e6, 1e6, "M"), (1e4, 1e3, "K")):
        if a >= limit:
            return f"{n / div:.2f}".rstrip("0").rstrip(".") + suf
    return f"{n:,.0f}" if a >= 100 else f"{n:,.2f}".rstrip("0").rstrip(".")


def find(query):
    q = norm(query)
    items = {norm(i["name"]): i for i in DATA["items"]}
    if q in items:
        return items[q]
    hits = [k for k in items if q in k]
    if hits:
        return items[min(hits, key=len)]
    close = difflib.get_close_matches(q, items, n=1, cutoff=0.6)
    return items[close[0]] if close else None


def send(embed):
    url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not url.startswith("https://"):
        sys.exit("Set DISCORD_WEBHOOK_URL first.")
    req = urllib.request.Request(url, json.dumps({"embeds": [embed]}).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "aotr-value/1.0"})
    urllib.request.urlopen(req, timeout=15)


def main():
    args = [a for a in sys.argv[1:] if a != "--discord"]
    if not args:
        sys.exit(__doc__)
    text = " ".join(args)
    m = re.match(r"^(\d+)\s*x?\s+(.*)$", text, re.I)
    qty, name = (int(m.group(1)), m.group(2)) if m else (1, text)
    item = find(name)
    if not item:
        msg = f"No item like '{name}' in aotr_values.json yet."
        if "--discord" in sys.argv:
            send({"title": "No match", "description": msg, "color": 0xE74C3C})
        sys.exit(msg)
    k = item["keys"] * qty
    title = f"{qty}x {item['name']}" if qty > 1 else item["name"]
    lines = [f"Keys: {fmt(k)}", f"Scrolls: {fmt(k / R['scroll'])}", f"Vizard’s Masks: {fmt(k / R['vizard'])}"]
    extra = [x for x in (f"demand {item['demand']}/10" if item.get("demand") else "", f"gem tax {fmt(item['gem_tax'])}" if item.get("gem_tax") else "") if x]
    print(title + (f" ({item['category']})" if item.get("category") else ""))
    print("  " + " | ".join(lines))
    if extra:
        print("  " + " · ".join(extra))
    print(f"  Values from {DATA['updated']}")
    if "--discord" in sys.argv:
        send({"title": title, "color": 0x8B5CF6, "description": "\n".join(lines),
              "footer": {"text": f"AOTR values • {DATA['updated']}" + (f" • {' · '.join(extra)}" if extra else "")}})
        print("Sent to Discord.")


main()
