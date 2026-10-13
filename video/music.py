# Self-synthesized ambient pad (original, no third-party audio)
import numpy as np, soundfile as sf, sys, json
T=json.load(open(sys.argv[1]))["total"]; SR=44100; n=int(T*SR); t=np.arange(n)/SR
chords=[[57,60,64,69],[53,57,60,65],[48,52,55,60],[55,59,62,67]]  # Am F C G
L=16.0; out=np.zeros(n)
hz=lambda m: 440*2**((m-69)/12)
for ci in range(int(T/L)+2):
    st=ci*L; c=chords[ci%4]; a=int(max(0,st-4)*SR); b=min(n,int((st+L+4)*SR))
    if a>=n: break
    tt=t[a:b]-st; env=np.clip((tt+4)/4,0,1)*np.clip((L+4-tt)/4,0,1)
    for m in c:
        f=hz(m-12)
        for det in (-0.6,0.6): out[a:b]+=env*np.sin(2*np.pi*(f+det)*t[a:b])*0.05
        out[a:b]+=env*np.sin(2*np.pi*f*2*t[a:b])*0.012
# soft lowpass via moving average
k=np.ones(40)/40; out=np.convolve(out,k,"same")
out*=0.5+0.5*np.sin(2*np.pi*t/23)**2*0.3+0.35
fade=np.minimum(1,np.minimum(t/4,(T-t)/5)); out*=np.clip(fade,0,1)
out=out/np.max(np.abs(out))*10**(-24/20)
sf.write(sys.argv[2],np.stack([out,out],1).astype(np.float32),SR); print("ok")
