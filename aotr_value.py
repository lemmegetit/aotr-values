#!/usr/bin/env python3
"""
AOTR value lookup: an item's value in Emperor's Keys, Memory Scrolls and Vizard's Masks.

  python3 aotr_value.py third eye
  python3 aotr_value.py 2x toji attire --discord

Needs aotr_values.json next to this file (made by import_list.py).
--discord posts the answer to the webhook in DISCORD_WEBHOOK_URL.
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
    q, items = norm(query), DATA["items"]
    same = lambda name: [i for i in items if norm(i["name"]) == norm(name)]
    if same(q):
        return same(q)
    part = [i for i in items if q in norm(i["name"])]
    if part:
        return same(min(part, key=lambda i: len(i["name"]))["name"])
    close = difflib.get_close_matches(q, {norm(i["name"]) for i in items}, n=1, cutoff=0.6)
    return same(close[0]) if close else []


def block(item, qty):
    title = (f"{qty}x " if qty > 1 else "") + item["name"] + (f" ({item['category']})" if item.get("category") else "")
    k = item.get("keys")
    if k is None:
        lines = ["No listed value (N/A or O/C)"]
    else:
        k *= qty
        lines = [f"Keys: {fmt(k)}", f"Scrolls: {fmt(k / R['scroll'])}", f"Vizard’s Masks: {fmt(k / R['vizard'])}"]
    extra = []
    if item.get("demand"):
        extra.append(f"demand {item['demand']}/10")
    if item.get("status"):
        extra.append(item["status"].lower())
    tax = item.get("tax", item.get("gem_tax"))
    if tax:
        extra.append(f"{item.get('tax_type') or 'gem'} tax {fmt(tax)}")
    return title, lines, extra


def send(embed):
    url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not url.startswith("https://"):
        sys.exit("Set DISCORD_WEBHOOK_URL first.")
    req = urllib.request.Request(url, json.dumps({"embeds": [embed]}).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "aotr-value/2.0"})
    urllib.request.urlopen(req, timeout=15)


def main():
    args = [a for a in sys.argv[1:] if a != "--discord"]
    if not args:
        sys.exit(__doc__)
    text = " ".join(args)
    m = re.match(r"^(\d+)\s*x?\s+(.*)$", text, re.I)
    qty, name = (int(m.group(1)), m.group(2)) if m else (1, text)
    hits = find(name)
    if not hits:
        msg = f"No item like '{name}' in aotr_values.json."
        if "--discord" in sys.argv:
            send({"title": "No match", "description": msg, "color": 0xE74C3C})
        sys.exit(msg)
    blocks = [block(h, qty) for h in hits[:6]]
    for title, lines, extra in blocks:
        print(title)
        print("  " + " | ".join(lines))
        if extra:
            print("  " + " · ".join(extra))
    print(f"  Values from {DATA['updated']}")
    if "--discord" in sys.argv:
        body = "\n\n".join(f"**{t}**\n" + "\n".join(l) + (f"\n{' · '.join(e)}" if e else "") for t, l, e in blocks)
        send({"title": blocks[0][0] if len(blocks) == 1 else f"Matches for “{name}”",
              "description": body[:4000] if len(blocks) > 1 else "\n".join(blocks[0][1]),
              "color": 0x8B5CF6,
              "footer": {"text": f"AOTR values • {DATA['updated']}" + (f" • {' · '.join(blocks[0][2])}" if len(blocks) == 1 and blocks[0][2] else "")}})
        print("Sent to Discord.")


main()
