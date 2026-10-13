# Original illustrations & quote cards (drawn in code; no third-party imagery)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys, math, random
OUT=sys.argv[1]; W,H=2208,1242
SANS="/root/.fonts/NotoSansKR%5Bwght%5D.ttf"; SER="/root/.fonts/GowunBatang-Bold.ttf"; SERR="/root/.fonts/GowunBatang-Regular.ttf"
def sans(s,w=500):
    f=ImageFont.truetype(SANS,s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
ser=lambda s: ImageFont.truetype(SER,s); serr=lambda s: ImageFont.truetype(SERR,s)
BG=(18,22,28); FG=(236,232,224); MUTE=(150,156,164); ACC=(226,120,72); GOLD=(214,170,120); ACC2=(96,160,200)
def base(top=(18,22,28),bot=(10,12,16)):
    im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H; d.line([(0,y),(W,y)],fill=tuple(int(top[i]*(1-t)+bot[i]*t) for i in range(3)))
    return im,ImageDraw.Draw(im)
def grain(im,a=10):
    rnd=random.Random(1); n=Image.effect_noise((W,H),a).convert("RGB")
    return Image.blend(im,n,0.04)
def ctext(d,y,t,f,fill=FG,sp=0): d.text((W/2,y),t,font=f,fill=fill,anchor="mm")
def quote(name,lines,src,sub=None,size=78):
    im,d=base(); d.text((W/2,330),"“",font=ser(220),fill=GOLD,anchor="mm")
    y=520-(len(lines)-1)*size*0.65
    for l in lines: ctext(d,y,l,ser(size)); y+=size*1.35
    d.line([(W/2-60,y+20),(W/2+60,y+20)],fill=GOLD,width=3)
    ctext(d,y+80,src,serr(44),MUTE)
    if sub: ctext(d,y+140,sub,serr(34),(110,116,124))
    grain(im).save(f"{OUT}/{name}.png")
def sky(top,mid,bot,horizon=0.72):
    im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/(H*horizon)
        if t<=1:
            c=[top[i]*(1-t)+mid[i]*t for i in range(3)] if t<0.6 else [mid[i]*(1-(t-.6)/.4)+bot[i]*((t-.6)/.4) for i in range(3)]
        else: c=[x*0.25 for x in bot]
        d.line([(0,y),(W,y)],fill=tuple(int(v) for v in c))
    return im,d
SIL=(14,12,16)
# --- playground at dusk
def playground(name,sun=True,kids=0):
    im,d=sky((40,46,84),(214,120,90),(250,196,120))
    gy=int(H*0.72)
    if sun:
        g=Image.new("L",(W,H)); gd=ImageDraw.Draw(g); gd.ellipse([1500,gy-260,1800,gy+40],fill=255); g=g.filter(ImageFilter.GaussianBlur(40))
        im.paste((255,214,150),mask=g); d=ImageDraw.Draw(im); d.ellipse([1560,gy-200,1740,gy-20],fill=(255,226,170))
    d.rectangle([0,gy,W,H],fill=SIL)
    # swing set
    x0=380; d.line([(x0,gy),(x0+120,gy-420)],fill=SIL,width=16); d.line([(x0+240,gy),(x0+120,gy-420)],fill=SIL,width=16)
    x1=1080; d.line([(x1,gy),(x1-120,gy-420)],fill=SIL,width=16); d.line([(x1-240,gy),(x1-120,gy-420)],fill=SIL,width=16)
    d.line([(x0+120,gy-420),(x1-120,gy-420)],fill=SIL,width=18)
    for sx in (620,840):
        d.line([(sx,gy-420),(sx,gy-120)],fill=SIL,width=4); d.line([(sx+90,gy-420),(sx+90,gy-120)],fill=SIL,width=4)
        d.rectangle([sx-10,gy-128,sx+100,gy-112],fill=SIL)
    # slide
    d.polygon([(1250,gy),(1290,gy),(1290,gy-300),(1250,gy-300)],fill=SIL)
    d.line([(1290,gy-300),(1560,gy)],fill=SIL,width=22); d.line([(1250,gy-300),(1250,gy-360)],fill=SIL,width=8); d.line([(1290,gy-300),(1290,gy-360)],fill=SIL,width=8)
    for i in range(6): d.line([(1250,gy-50*i),(1290,gy-50*i)],fill=SIL,width=6)
    # sandbox
    d.rectangle([1700,gy-40,2050,gy],fill=SIL)
    for k in range(kids):
        cx=1830+k*110-(kids-1)*55; h=150+(k%2)*30
        d.ellipse([cx-24,gy-h-48,cx+24,gy-h],fill=SIL); d.rounded_rectangle([cx-30,gy-h,cx+30,gy-60],14,fill=SIL)
        d.line([(cx-14,gy-62),(cx-20,gy)],fill=SIL,width=16); d.line([(cx+14,gy-62),(cx+20,gy)],fill=SIL,width=16)
    grain(im).save(f"{OUT}/{name}.png")
playground("ill_playground_dusk",kids=0); playground("ill_playground_kids",kids=3)
# --- Sisyphus hill
def sisyphus(name,descend=False):
    im,d=sky((22,26,44),(70,64,96),(170,120,110),0.9)
    pts=[(0,H)]+[(x,H-120-680*(x/W)**1.3) for x in range(0,W+1,8)]+[(W,H)]
    d.polygon(pts,fill=SIL)
    def hy(x): return H-120-680*(x/W)**1.3
    if not descend:
        bx=1500; by=hy(bx); r=120
        d.ellipse([bx-r+40,by-2*r+10,bx+r+40,by+10],fill=(40,36,44))
        px=bx-110; py=hy(px)
        d.ellipse([px-28,py-250,px+28,py-194],fill=SIL)
        d.line([(px,py-194),(px+70,py-110)],fill=SIL,width=30); d.line([(px+70,py-110),(px-30,py)],fill=SIL,width=20); d.line([(px+60,py-110),(px+60,py)],fill=SIL,width=20)
        d.line([(px+10,py-180),(bx-60,by-140)],fill=SIL,width=16)
    else:
        bx=420; by=hy(bx); r=110; d.ellipse([bx-r,by-2*r+10,bx+r,by+10],fill=(40,36,44))
        px=1900; py=hy(px)
        d.ellipse([px-26,py-250,px+26,py-198],fill=SIL); d.line([(px,py-198),(px-8,py-100)],fill=SIL,width=30)
        d.line([(px-8,py-100),(px-50,py)],fill=SIL,width=20); d.line([(px-8,py-100),(px+30,py)],fill=SIL,width=20)
    grain(im).save(f"{OUT}/{name}.png")
sisyphus("ill_sisyphus_up"); sisyphus("ill_sisyphus_down",True)
# --- magic circle
im,d=base((22,20,18),(12,10,10))
cx,cy,r=W/2,560,430
for k in range(10): d.ellipse([cx-r-k,cy-r-k,cx+r+k,cy+r+k],outline=(200,170,120,),width=1) if k%3==0 else None
d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=GOLD,width=6)
ctext(d,cy-60,"마법의 원",ser(96)); ctext(d,cy+40,"모래는 밥이 되고, 나뭇잎은 돈이 된다",serr(44),MUTE)
ctext(d,cy+r+70,"요한 하위징아 『호모 루덴스』(1938)",serr(40),MUTE)
grain(im).save(f"{OUT}/ill_circle.png")
# --- leaves & sand money
im,d=base((40,34,24),(20,16,12)); rnd=random.Random(3)
for i in range(4000): x=rnd.random()*W; y=rnd.random()*H; c=rnd.randint(150,200); d.point((x,y),fill=(c,c-30,c-80))
for i in range(14):
    x=rnd.uniform(200,W-200); y=rnd.uniform(150,H-350); a=rnd.uniform(0,6.28); L=rnd.uniform(70,120)
    pts=[(x+L*math.cos(a+t)*(1 if t<3.14 else .45)*math.cos(t)-0,y+L*math.sin(a+t)*abs(math.sin(t))*0.6) for t in [i*0.2 for i in range(32)]]
    col=rnd.choice([(170,120,40),(190,80,40),(120,140,50),(200,150,60)])
    d.ellipse([x-L,y-L*0.45,x+L,y+L*0.45],fill=col); d.line([(x-L,y),(x+L,y)],fill=(90,60,30),width=4)
for cx,cy in [(700,700),(1500,620)]:
    d.ellipse([cx-150,cy-60,cx+150,cy+60],fill=(230,226,214)); d.ellipse([cx-120,cy-80,cx+120,cy+10],fill=(196,170,120))
grain(im).save(f"{OUT}/ill_leaves_sand.png")
# --- quotes / text cards
quote("q_play",["너는 아빠 해, 나는 엄마 할게.","이건 밥이고, 이건 돈이야."],"놀이터에서",size=84)
quote("q_newton",["나는 천체의 움직임은 계산할 수 있지만,","사람들의 광기는 계산할 수 없다."],"아이작 뉴턴 (전해지는 말)",size=72)
quote("q_camus",["우리는 행복한 시지프를","상상해야 한다."],"알베르 카뮈 『시지프 신화』",size=88)
def title_card(name,kicker,lines,foot=None,col=FG,size=96):
    im,d=base(); ctext(d,330,kicker,sans(46,500),GOLD); y=470
    for l in lines: ctext(d,y,l,sans(size,800),col); y+=size*1.3
    if foot: ctext(d,y+40,foot,sans(40,400),MUTE)
    grain(im).save(f"{OUT}/{name}.png")
title_card("t_meme","미국 · 몇 년 전",["‘밈 주식’"],"개인 투자자들이 게시판에 모여 주가를 수십 배로 — 놀이이자 시위")
title_card("t_ai","지금, 전 세계 경제면",["버블인가, 혁명인가"],"인공지능 기업가치를 둘러싼 논쟁")
title_card("t_common","공통점",["가치는 실물보다","기대와 이야기로 움직인다"],"그리고 그 기대는 게임처럼 점수로 표시된다",size=84)
title_card("t_late","차이",["미국: ‘참여’한다","한국: ‘늦었다’"],"판이 이미 깔린 뒤 놀이터에 도착한 아이처럼",size=88)
title_card("t_harari","유발 하라리",["상상의 질서"],"국가 · 회사 · 화폐 — 함께 믿기 때문에 작동한다")
title_card("t_simul","장 보드리야르",["시뮬라크르"],"지도가 영토보다 먼저 존재하는 세계")
title_card("t_two","원이 흔들릴 때",["원 밖에서 냉소하거나,","원 안에서 더 크게 베팅하거나"],None,size=80)
title_card("t_1","이번엔 무엇이 다른가 · 첫째",["점수판이 손안에 있다"],"하루 한 번 보던 숫자를, 이제는 하루 수십 번")
title_card("t_2","둘째",["사람이 아닌 참여자"],"인공지능이 거래하고, 일자리를 대신한다")
title_card("t_3","셋째",["새로 들어오는 아이가 적다"],"늦게 온 아이가 자리를 찾지 못하는 놀이는 오래가지 못한다")
title_card("t_end","",["지금 우리가 하는 놀이의 원은","누구에게 열려 있을까"],None,size=84)
# --- South Sea: share price ~10x in half a year (illustrative)
im,d=base(); d.text((260,250),"1720년 런던 · 남해회사",font=sans(54,500),fill=MUTE); d.text((260,310),"반년 사이 주가 약 10배",font=sans(92,800),fill=FG)
x0,y0,x1,y1=260,480,1950,960; d.line([(x0,y1),(x1,y1)],fill=(70,76,84),width=3)
P=[]; 
for k in range(101):
    t=k/100; v=1+9*(t**2.6) if t<0.8 else 10-8*((t-0.8)/0.2)**0.7
    P.append((x0+(x1-x0)*t, y1-(y1-y0)*(v-1)/9))
d.line(P[:81],fill=ACC,width=8); d.line(P[80:],fill=(120,70,60),width=8)
d.text((x0,y1+24),"1720년 초",font=sans(40),fill=MUTE); d.text((P[80][0],y1+24),"정점",font=sans(40),fill=MUTE,anchor="ma"); d.text((x1,y1+24),"붕괴",font=sans(40),fill=MUTE,anchor="ra")
grain(im).save(f"{OUT}/c_southsea.png")
# --- triptych
im,d=base()
for i,(yr,city) in enumerate([("1720","런던"),("1980년대","도쿄"),("지금","서울")]):
    cx=W/2+(i-1)*600; d.rounded_rectangle([cx-250,330,cx+250,860],24,outline=(70,76,84),width=3)
    ctext(d,520,yr,sans(96,800),ACC if i==2 else FG) if False else d.text((cx,520),yr,font=sans(92,800),fill=ACC if i==2 else FG,anchor="mm")
    d.text((cx,660),city,font=ser(80),fill=GOLD,anchor="mm")
ctext(d,980,"숫자와 실물 사이의 거리가 멀어질 때",sans(48,500),MUTE)
grain(im).save(f"{OUT}/c_three.png")
# --- Tokyo
title_card("t_tokyo","1980년대 후반 · 도쿄",["왕궁 부지의 땅값","= 캘리포니아 전체?"],"모두가 믿는 동안에는 그 숫자가 현실이었다",size=90)
print("ok")
