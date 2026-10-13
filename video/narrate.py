import sys, json, re, numpy as np, soundfile as sf
sys.path.insert(0, sys.argv[1]); from tts import make
D, SCRIPT, OUT = sys.argv[2], sys.argv[3], sys.argv[4]
SID, SPEED = int(sys.argv[5]), float(sys.argv[6])
REPL = [("6,900선","육천구백 선"),("6천 선","육천 선"),("28만 5천 개","이십팔만 오천 개"),("86주","팔십육 주"),("17%","십칠 퍼센트"),
 ("94%","구십사 퍼센트"),("2022년","이천이십이 년"),("4년","사 년"),("1720년","천칠백이십 년"),("1980년대","천구백팔십 년대"),
 ("1938년","천구백삼십팔 년"),("1989년","천구백팔십구 년"),("2월","이월"),("5월","오월"),("—"," "),("·"," ")]
def tts_text(t):
    t=t.replace("(쉼)","")
    for a,b in REPL: t=t.replace(a,b)
    t=re.sub(r"[“”‘’『』]","",t)
    return re.sub(r"\s+"," ",t).strip()
import tts as T
eng=make(D); SR=44100
audio=[]; cur=0.0; tl=[]
def sil(s):
    global cur; audio.append(np.zeros(int(s*SR),dtype=np.float32)); cur+=s
sil(1.0)
for line in open(SCRIPT,encoding="utf-8"):
    line=line.strip()
    if not line: continue
    if line.startswith("#S "):
        key,title=line[3:].split("|",1)
        if tl: sil(1.2)
        tl.append({"type":"section","key":key,"title":title,"start":cur}); sil(3.0); continue
    pause = 1.4 if "(쉼)" in line else 0.55
    T.gen(eng, tts_text(line), "/tmp/_l.wav", SID, SPEED, 16)
    x,sr=sf.read("/tmp/_l.wav",dtype="float32"); assert sr==SR
    # trim leading/trailing near-silence
    idx=np.where(np.abs(x)>0.01)[0]; x=x[max(0,idx[0]-400):idx[-1]+2000] if len(idx) else x
    st=cur; audio.append(x); cur+=len(x)/SR
    tl.append({"type":"line","text":line.replace("(쉼)","").strip(),"start":st,"end":cur,"section":[t for t in tl if t["type"]=="section"][-1]["key"]})
    print(f"{st:7.2f} {cur-st:5.2f} {line[:40]}", flush=True)
    sil(pause)
sil(2.5)
a=np.concatenate(audio); a=a/np.max(np.abs(a))*0.89
sf.write(OUT+"/narration.wav",a,SR); json.dump({"total":cur,"items":tl},open(OUT+"/timeline.json","w"),ensure_ascii=False,indent=1)
print("TOTAL",cur)
