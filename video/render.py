# Usage: render.py timeline.json plan.json subs.ass narration.wav out.mp4 [music.wav]
import sys, json, subprocess, random, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
TL,PLAN,ASS,WAV,OUT=sys.argv[1:6]
tl=json.load(open(TL)); plan=json.load(open(PLAN))
W,H,FPS,XF=1920,1080,30,1.0
total=tl["total"]; items=tl["items"]
secs=[i for i in items if i["type"]=="section"]
# --- build shot list: plan[key] = [[line_idx, src, opts], ...]
shots=[]
for si,s in enumerate(secs):
    lines=[i for i in items if i["type"]=="line" and i["section"]==s["key"]]
    send=secs[si+1]["start"] if si+1<len(secs) else total
    entries=plan[s["key"]]
    for k,(li,src,*o) in enumerate(entries):
        st=s["start"]+3.0 if k==0 else lines[li]["start"]-0.4
        en=send if k==len(entries)-1 else lines[entries[k+1][0]]["start"]-0.4
        shots.append(dict(src=src,start=st,end=en,opt=(o[0] if o else {}),sec=si))
    s["bg"]=entries[0][1]
cache={}
def load(src):
    if src in cache: return cache[src]
    im=Image.open(src).convert("RGB"); r=max(W*1.12/im.width,H*1.12/im.height)
    im=im.resize((round(im.width*r),round(im.height*r)),Image.LANCZOS)
    cache[src]=im; return im
rng=random.Random(7)
for s in shots:
    o=s["opt"]; card=s["src"].split("/")[-1].startswith("card_")
    z=o.get("zoom",[1.0,1.04] if card else rng.choice([[1.0,1.12],[1.12,1.0],[1.04,1.10]]))
    p=o.get("pan",[[0.5,0.5],[0.5,0.5]] if card else [[rng.uniform(.3,.7),rng.uniform(.35,.65)],[rng.uniform(.3,.7),rng.uniform(.35,.65)]])
    s["z"],s["p"]=z,p
def ease(t): return t*t*(3-2*t)
def shot_frame(s,t):
    im=load(s["src"]); u=ease(min(1,max(0,(t-s["start"])/max(.1,s["end"]-s["start"]))))
    z=s["z"][0]+(s["z"][1]-s["z"][0])*u
    cw,ch=im.width/ (z*im.width/W*min(im.width/W,im.height/H)/(im.width/W)) ,0
    # crop window: size = (W,H) scaled so that z=1 covers the whole 'cover' area
    base=min(im.width/W, im.height/H); cw,ch=W*base/z, H*base/z
    px=s["p"][0][0]+(s["p"][1][0]-s["p"][0][0])*u; py=s["p"][0][1]+(s["p"][1][1]-s["p"][0][1])*u
    x=(im.width-cw)*px; y=(im.height-ch)*py
    return np.asarray(im.transform((W,H),Image.EXTENT,(x,y,x+cw,y+ch),Image.BILINEAR),dtype=np.float32)
# vignette + bottom gradient for subtitle legibility
yy,xx=np.mgrid[0:H,0:W]; vig=1-0.38*(((xx-W/2)/(W/1.6))**2+((yy-H/2)/(H/1.4))**2)
grad=np.clip((yy-H*0.62)/(H*0.38),0,1)*0.45; shade=(np.clip(vig,0,1)*(1-grad))[...,None].astype(np.float32)
# title cards
TF=ImageFont.truetype("/root/.fonts/GowunBatang-Bold.ttf",76); SF=ImageFont.truetype("/root/.fonts/GowunBatang-Regular.ttf",40)
titlecache={}
def title_img(si):
    if si in titlecache: return titlecache[si]
    s=secs[si]; im=load(s["bg"]).resize((W,H)).filter(ImageFilter.GaussianBlur(18))
    a=np.asarray(im,dtype=np.float32)*0.28; im=Image.fromarray(a.astype(np.uint8)); d=ImageDraw.Draw(im)
    t=s["title"]; parts=[p.strip() for p in t.split("—")]
    head=parts[0]; sub=parts[1] if len(parts)>1 else ""
    if "·" in head: num,name=[p.strip() for p in head.split("·",1)]
    else: num,name="",head
    y=H/2-(40 if sub else 0)
    if num: d.text((W/2,y-95),num,font=SF,fill=(214,170,120),anchor="mm")
    d.text((W/2,y),name,font=TF,fill=(240,236,228),anchor="mm")
    if sub: d.line([(W/2-60,y+62),(W/2+60,y+62)],fill=(214,170,120),width=2); d.text((W/2,y+120),sub,font=SF,fill=(200,198,192),anchor="mm")
    titlecache[si]=np.asarray(im,dtype=np.float32); return titlecache[si]
def frame(t):
    act=[s for s in shots if s["start"]-XF/2<=t<s["end"]+XF/2]
    img=None
    for s in act:
        f=shot_frame(s,t); a=min(1,(t-(s["start"]-XF/2))/XF) if img is not None else 1
        img=f if img is None else img*(1-a)+f*a
    if img is None: img=np.zeros((H,W,3),np.float32)
    img=img*shade
    for si,s in enumerate(secs):
        st=s["start"]; en=st+3.0
        if st-0.6<=t<en+0.6:
            a=min(1,(t-(st-0.6))/0.6,(en+0.6-t)/0.6); img=img*(1-a)+title_img(si)*a
    if t<1.0: img*=t
    if t>total-2.0: img*=max(0,(total-t)/2.0)
    return np.clip(img,0,255).astype(np.uint8)
vf=f"ass={ASS}"
cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",WAV]
if len(sys.argv)>6: cmd+=["-i",sys.argv[6],"-filter_complex","[1:a][2:a]amix=inputs=2:duration=first:normalize=0[a]","-map","0:v","-map","[a]"]
else: cmd+=["-map","0:v","-map","1:a"]
cmd+=["-vf",vf,"-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest",OUT]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
import os; N=int(float(os.environ.get("LIMIT",total))*FPS)
for n in range(N):
    p.stdin.write(frame(n/FPS).tobytes())
    if n%900==0: print(f"{n/FPS:.0f}s/{total:.0f}s",flush=True)
p.stdin.close(); p.wait(); print("done",p.returncode)
