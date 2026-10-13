import sys, json, urllib.request, urllib.parse, re
UA={"User-Agent":"EssayVideoBot/1.0 (https://github.com/kettle0803-ux/Screener; personal non-commercial video) python-urllib"}
OK=re.compile(r"^(cc0|public domain|pd|cc by(-sa)? ?[1-4]\.0|cc by(-sa)? ?2\.5|cc by(-sa)? 3\.0)",re.I)
def api(p):
    p.update(format="json"); u="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(p)
    return json.loads(get(u))
import time
def get(u):
    for k in range(10):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code==429:
                ra=e.headers.get("Retry-After"); time.sleep(min(120,int(ra)) if ra and ra.isdigit() else 15*(k+1)); continue
            raise
    raise RuntimeError("429 "+u)
def search(q,n=12):
    r=api(dict(action="query",generator="search",gsrsearch=f"filetype:bitmap {q}",gsrnamespace=6,gsrlimit=n,
        prop="imageinfo",iiprop="url|size|extmetadata",iiurlwidth=500))
    out=[]
    for p in sorted(r.get("query",{}).get("pages",{}).values(),key=lambda x:x.get("index",0)):
        ii=p["imageinfo"][0]; m=ii.get("extmetadata",{})
        lic=m.get("LicenseShortName",{}).get("value","")
        art=re.sub("<[^>]+>","",m.get("Artist",{}).get("value",""))[:60].strip()
        if not OK.match(lic) or ii["width"]<1200: continue
        out.append(dict(title=p["title"],w=ii["width"],h=ii["height"],lic=lic,artist=art,thumb=ii.get("thumburl",ii["url"]).split("?")[0].replace("thumb.wikimedia.org","upload.wikimedia.org"),url=ii["url"],page=ii["descriptionurl"]))
    return out
def sheet(q,out,n=12):
    from PIL import Image, ImageDraw, ImageFont
    import io
    res=search(q,n); W=480; cols=4; rows=(len(res)+cols-1)//cols or 1
    im=Image.new("RGB",(W*cols,300*rows),(0,0,0)); d=ImageDraw.Draw(im); f=ImageFont.truetype("/root/.fonts/NotoSansKR%5Bwght%5D.ttf",28)
    for i,x in enumerate(res):
        try: t=Image.open(io.BytesIO(get(x["thumb"]))).convert("RGB")
        except Exception as e: continue
        t.thumbnail((W-6,294)); im.paste(t,((i%cols)*W+3,(i//cols)*300+3)); d.text(((i%cols)*W+10,(i//cols)*300+8),str(i),font=f,fill=(255,255,0),stroke_width=3,stroke_fill=(0,0,0))
        time.sleep(0.3)
    im.save(out,quality=80); json.dump(res,open(out+".json","w"),ensure_ascii=False,indent=1)
if __name__=="__main__" and sys.argv[1]=="sheet":
    import os
    for i,q in enumerate(sys.argv[3:]):
        sheet(q,f"{sys.argv[2]}/s_{re.sub('[^a-z0-9]+','_',q.lower())[:40]}.jpg"); print("done",q,flush=True); time.sleep(1)
    sys.exit()
if __name__=="__main__":
    for q in sys.argv[1:]:
        print("##",q)
        for x in search(q): print(f"  {x['w']}x{x['h']} | {x['lic']} | {x['artist'][:30]} | {x['title'][5:80]}")
