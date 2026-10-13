# Self-made data cards (no third-party imagery). Figures are as stated in the narration script.
from PIL import Image, ImageDraw, ImageFont
import sys
OUT=sys.argv[1]; W,H=2208,1242
F=lambda n,s: ImageFont.truetype(f"/root/.fonts/{n}",s)
SANS="NotoSansKR%5Bwght%5D.ttf"; SER="GowunBatang-Bold.ttf"
BG=(18,22,28); FG=(236,232,224); MUTE=(150,156,164); ACC=(226,120,72); ACC2=(96,160,200)
def base():
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    for i in range(0,W,96): d.line([(i,0),(i,H)],fill=(26,31,38))
    for j in range(0,H,96): d.line([(0,j),(W,j)],fill=(26,31,38))
    return im,d
def sans(s,w=500):
    f=F(SANS,s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def txt(d,xy,t,f,fill=FG,anchor="la"): d.text(xy,t,font=f,fill=fill,anchor=anchor)
# 1) Seoul apartments 86 weeks
im,d=base(); x0,y0,x1,y1=260,330,1950,960
txt(d,(260,190),"서울 아파트값",sans(54,500),MUTE); txt(d,(260,250),"86주 연속 상승",sans(92,800))
import math
pts=[]; v=100
for k in range(87):
    v*=1+0.00182+0.0009*math.sin(k/7); pts.append(v)
lo,hi=98,max(pts)+1
P=[(x0+(x1-x0)*k/86, y1-(y1-y0)*(p-lo)/(hi-lo)) for k,p in enumerate(pts)]
d.line([(x0,y1),(x1,y1)],fill=(70,76,84),width=3)
d.polygon(P+[(x1,y1),(x0,y1)],fill=(60,40,34)); d.line(P,fill=ACC,width=8)
d.ellipse([P[-1][0]-14,P[-1][1]-14,P[-1][0]+14,P[-1][1]+14],fill=ACC)
txt(d,(x1,P[-1][1]-40),"누적 +17% 이상",sans(60,700),ACC,"rb")
txt(d,(x0,y1+30),"지난해 2월",sans(40),MUTE); txt(d,(x1,y1+30),"86주째",sans(40),MUTE,"ra")
txt(d,(260,1020),"통계 작성 이래 최장 연속 상승  ·  그래프는 추세를 나타낸 예시입니다",sans(34),MUTE)
im.save(f"{OUT}/card_apt.png")
# 2) KOSPI
im,d=base()
txt(d,(260,190),"코스피",sans(54,500),MUTE); txt(d,(260,250),"사상 첫 6,000선 돌파",sans(92,800))
for i,(lab,val,col) in enumerate([("6,000",6000,MUTE),("6,900",6900,ACC)]):
    y=520+i*230; w=int(1500*val/7000)
    d.rounded_rectangle([260,y,260+w,y+150],18,fill=col)
    txt(d,(290+w,y+75),lab,sans(84,800),FG,"lm")
txt(d,(260,470),"올해 처음 돌파",sans(40),MUTE); txt(d,(260,700),"5월 고점",sans(40),MUTE)
txt(d,(260,1020),"단위: 포인트",sans(34),MUTE)
im.save(f"{OUT}/card_kospi.png")
# 3) Youth jobs
im,d=base()
txt(d,(260,190),"한국은행 분석 · 2022년부터 4년간",sans(54,500),MUTE)
txt(d,(260,250),"청년 일자리",sans(92,800))
txt(d,(260,560),"−28만 5천 개",sans(190,800),ACC2,"lm")
cx,cy,r=1700,700,300
d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(44,50,58))
d.pieslice([cx-r,cy-r,cx+r,cy+r],-90,-90+360*0.94,fill=ACC)
d.ellipse([cx-185,cy-185,cx+185,cy+185],fill=BG)
txt(d,(cx,cy-10),"94%",sans(120,800),FG,"mm")
txt(d,(260,780),"감소분 중 94%가",sans(60,600)); txt(d,(260,870),"인공지능 노출도가 높은 업종",sans(60,600),ACC)
im.save(f"{OUT}/card_jobs.png")
print("ok")
