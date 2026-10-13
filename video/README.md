# 「소꿉장난 같은 날」 영상

- 완성본: `소꿉장난_같은_날.mp4` (1920×1080, 약 7분 58초, 한국어 자막 번인)
- 자막 파일: `subs.srt` (별도 업로드용), `subs.ass`
- 출처: `CREDITS.md`

## 제작 파이프라인
- 음성: Supertonic 3 (sherpa-onnx, 오프라인 신경망 TTS, 화자 sid=5, 속도 0.95) → `narrate.py`
- 자막: `subs.py`
- 그래픽: `cards.py`(데이터 카드), `cards2.py`(인용 카드·일러스트) — 모두 직접 제작
- 사진: CC0 / 퍼블릭 도메인 5장(`img/`) — 위키미디어 공용
- 배경음악: `music.py` (직접 합성)
- 렌더: `python3 render.py timeline.json plan.json subs.ass narration.wav out.mp4 music.wav`
