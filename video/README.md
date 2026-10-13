# 「소꿉장난 같은 날」 영상 제작 파이프라인 (작업 중)

- 음성: Supertonic 3 (sherpa-onnx, 오프라인 신경망 TTS, 화자 sid=5, 속도 0.95) → `narrate.py`
- 자막: `subs.py` → `subs.ass`(영상 번인), `subs.srt`(별도 업로드용)
- 데이터 카드: `cards.py` (직접 제작, 외부 이미지 없음)
- 배경음악: `music.py` (직접 합성한 앰비언트 패드)
- 렌더: `render.py timeline.json plan.json subs.ass narration.wav out.mp4 music.wav`

남은 작업: 위키미디어 공용(퍼블릭 도메인/CC) 실사 이미지 수집 → `plan.json` 작성 → 렌더 → 출처 표기(CREDITS).
