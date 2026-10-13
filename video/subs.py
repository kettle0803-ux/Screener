import json, sys, re
tl=json.load(open(sys.argv[1])); out=sys.argv[2]; MAX=24
def split(t):
    if len(t)<=MAX: return [t]
    # candidate break points after punctuation, else spaces
    best=None
    for i,ch in enumerate(t):
        if ch==" " and 8<=i<=len(t)-6:
            score=abs(i-len(t)/2) - (12 if t[i-1] in ",.?”’" else 0)
            if best is None or score<best[0]: best=(score,i)
    if not best: return [t]
    return split(t[:best[1]].strip())+split(t[best[1]:].strip())
def ts(s):
    h=int(s//3600); m=int(s%3600//60); return f"{h}:{m:02d}:{s%60:05.2f}"
ev=[]
for it in tl["items"]:
    if it["type"]!="line": continue
    parts=split(it["text"]); n=sum(len(p) for p in parts); t=it["start"]; dur=it["end"]-it["start"]
    for p in parts:
        d=dur*len(p)/n; ev.append((t,t+d,p)); t+=d
# extend each event slightly into the following gap (no overlap)
res=[]
for i,(a,b,p) in enumerate(ev):
    nxt=ev[i+1][0] if i+1<len(ev) else b+1
    res.append((a,min(b+0.35,nxt-0.02),p))
hdr="""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Noto Sans KR Medium,58,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,3,1.5,2,120,120,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with open(out,"w",encoding="utf-8") as f:
    f.write(hdr)
    for a,b,p in res: f.write(f"Dialogue: 0,{ts(a)},{ts(b)},Sub,,0,0,0,,{{\\fad(120,120)}}{p}\n")
# also SRT
with open(out.replace(".ass",".srt"),"w",encoding="utf-8") as f:
    def st(s): return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int(s*1000%1000):03d}"
    for i,(a,b,p) in enumerate(res,1): f.write(f"{i}\n{st(a)} --> {st(b)}\n{p}\n\n")
print(len(res), max(len(p) for _,_,p in res))
