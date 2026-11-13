#!/usr/bin/env python3
"""
Turns the copied Vaulted Values X page text into aotr_values.json.

  python3 import_list.py aotr-list.txt
"""
import json, re, sys
from datetime import date
from pathlib import Path


def num(s):
    m = re.fullmatch(r"([\d.]+)\s*([KMBT]?)", s.strip().replace(",", ""), re.I)
    return float(m[1]) * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[m[2].upper()] if m else None


def parse(text):
    lines = [l.strip() for l in text.replace("\r", "").split("\n")]
    items = []
    for i, line in enumerate(lines):
        if line != "Value" or not lines[i + 1].startswith("Keys"):
            continue
        back = [l for l in lines[:i] if l][-2:]
        if len(back) < 2:
            continue
        item = {"name": back[0], "category": back[1], "keys": num(lines[i + 1][4:]),
                "tax_type": None, "tax": None, "demand": None, "status": None}
        rest = [l for l in lines[i + 2:i + 16] if l]
        k = 0
        while k + 1 < len(rest):
            lab, val = rest[k], rest[k + 1]
            if lab in ("Gem Tax", "Gold Tax"):
                item["tax_type"], item["tax"] = lab.split()[0].lower(), num(val)
            elif lab == "Demand":
                item["demand"] = int(val) if val.isdigit() else None
            elif lab == "Status":
                item["status"] = val
                break
            else:
                break
            k += 2
        items.append(item)
    return items


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    items = parse(text)
    header = re.search(r"Showing (\d+) of (\d+) matching", text)
    keys = {i["name"]: i["keys"] for i in items if i["keys"]}
    rates = {"scroll": keys.get("Memory Scroll", 4), "vizard": keys.get("Vizard's Mask", 900)}
    Path("aotr_values.json").write_text(json.dumps(
        {"updated": date.today().isoformat(), "source": "aotr.vaultedvaluesx.com value list",
         "rates": rates, "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    novalue = sum(1 for i in items if i["keys"] is None)
    print(f"Parsed {len(items)} items ({novalue} without a numeric value). Rates: {rates}")
    if header:
        shown, total = header.groups()
        print(f"The page said: showing {shown} of {total}.")
        if int(shown) != int(total) or len(items) != int(total):
            print("WARNING: the counts do not match. Click Load more items until everything shows, copy again.")
    else:
        print("No 'Showing X of Y' line found, so I can't confirm the list is complete.")


main()
