# dl.py credits.json outdir key=File:Title ...
import cs, sys, json, os, time, re, urllib.parse
cred=json.load(open(sys.argv[1])) if os.path.exists(sys.argv[1]) else {}
out=sys.argv[2]
for arg in sys.argv[3:]:
    key,title=arg.split("=",1)
    if key in cred and os.path.exists(f"{out}/{key}.jpg"): continue
    r=cs.api(dict(action="query",titles=title,prop="imageinfo",iiprop="url|size|extmetadata",iiurlwidth=1920))
    p=list(r["query"]["pages"].values())[0]; ii=p["imageinfo"][0]; m=ii["extmetadata"]
    url=ii["thumburl"].split("?")[0] if "thumburl" in ii else ii["url"]
    try: data=cs.get(url)
    except Exception as e: print('FAIL',key,e,flush=True); time.sleep(30); continue
    open(f"{out}/{key}.jpg","wb").write(data)
    g=lambda k: re.sub(r"\s+"," ",re.sub("<[^>]+>","",m.get(k,{}).get("value",""))).strip()
    cred[key]=dict(title=title,page=ii["descriptionurl"],license=g("LicenseShortName"),license_url=g("LicenseUrl"),artist=g("Artist")[:120],credit=g("Credit")[:120])
    print(key, cred[key]["license"], cred[key]["artist"][:40], len(data), flush=True)
    json.dump(cred,open(sys.argv[1],"w"),ensure_ascii=False,indent=1); time.sleep(8)
