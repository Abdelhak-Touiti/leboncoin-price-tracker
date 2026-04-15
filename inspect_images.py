import json, sys

with open("debug_nextdata.json", encoding="utf-8") as f:
    data = json.load(f)

def find_ads(obj, depth=0):
    if depth > 6: return None
    if isinstance(obj, list) and len(obj) > 0:
        first = obj[0]
        if isinstance(first, dict) and any(k in first for k in ("list_id","subject","price")):
            return obj
    if isinstance(obj, dict):
        for v in obj.values():
            found = find_ads(v, depth+1)
            if found: return found
    return None

props = data.get("props",{}).get("pageProps",{})
ads = find_ads(props) or find_ads(data) or []

if not ads:
    print("No ads found in JSON!")
    sys.exit(1)

first = ads[0]
print("=== Top-level keys ===")
print(list(first.keys()))
print()
print("=== images field ===")
print(json.dumps(first.get("images", "NOT FOUND"), indent=2))
print()
print("=== image field ===")
print(first.get("image","NOT FOUND"))
