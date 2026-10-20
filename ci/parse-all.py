import concurrent.futures, json, pathlib, sys
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import parsers

ROOT = pathlib.Path.cwd().resolve()
SKIP_TOP = parsers.STATE_DIRS

def walk():
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file(): continue
        try: top = p.relative_to(ROOT).parts[0]
        except (ValueError, IndexError): continue
        if top in SKIP_TOP: continue
        out.append(p)
    return out

def main():
    files = walk()
    print(f"describing {len(files)} files")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
        for fut in concurrent.futures.as_completed({pool.submit(parsers.describe, f, ROOT): f for f in files}):
            results.append(fut.result())
    results.sort(key=lambda r: r["path"])
    v = Counter(r["verdict"] for r in results)
    c = Counter(r["class"] for r in results)
    out = ROOT/"build"/"stage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"records":results}, indent=2))
    print(f"stage: {len(results)} records, parsed={v['parsed']}, skipped={v['skipped']}, failed={v['failed']}")
    print(f"classes: " + ", ".join(f"{k}={n}" for k,n in sorted(c.items())))
    for r in results:
        if r["verdict"] == "failed":
            print(f"  {r['path']}: [{r['class']}] {r['reason']}")
    return 0 if v["failed"] == 0 else 1

if __name__ == "__main__": sys.exit(main())
