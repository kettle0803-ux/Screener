import sys, sherpa_onnx, soundfile as sf

def make(D):
    c=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
            duration_predictor=f"{D}/duration_predictor.int8.onnx", text_encoder=f"{D}/text_encoder.int8.onnx",
            vector_estimator=f"{D}/vector_estimator.int8.onnx", vocoder=f"{D}/vocoder.int8.onnx",
            tts_json=f"{D}/tts.json", unicode_indexer=f"{D}/unicode_indexer.bin", voice_style=f"{D}/voice.bin"),
        num_threads=4, provider="cpu"))
    return sherpa_onnx.OfflineTts(c)
def gen(tts, text, out, sid, speed=1.0, steps=16):
    g=sherpa_onnx.GenerationConfig(); g.sid=sid; g.num_steps=steps; g.speed=speed; g.extra["lang"]="ko"
    a=tts.generate(text,g); sf.write(out,a.samples,samplerate=a.sample_rate); return len(a.samples)/a.sample_rate
if __name__=="__main__":
    tts=make(sys.argv[1]); print("speakers",tts.num_speakers)
    t="가끔 그런 날이 있습니다. 회의실에 앉아 있는데, 누군가 화면을 넘기며 이번 분기 목표는요, 하고 말하는 그 장면이 갑자기 아주 멀리서 보이는 날."
    for s in range(tts.num_speakers): print(s, gen(tts,t,f"{sys.argv[2]}/sid{s}.wav",s))
