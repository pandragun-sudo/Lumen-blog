---
title: "Claude와 함께 Remotion으로 설명 영상 만들기: 대본부터 렌더까지 제작 순서 (2026)"
description: "5분 50초짜리 설명 영상을 만든 순서를 그대로 적었습니다. 대본과 음성은 사람이, 장면 데이터와 Remotion 코드는 Claude가 맡았고, 자막 타이밍은 음성 인식 결과를 썼습니다."
pubDate: 2026-10-07T03:00:00+09:00
category: "guide"
---

최근에 5분 50초짜리 설명 영상을 한 편 만들었습니다.\
[쇼츠 성장 방법: 137편 실제 데이터로 본 길이·평균 조회율·업로드 빈도 기준 (2026)](/blog/2026-10-06-shorts-growth-137-videos-length-retention-frequency/) 글을 영상으로 옮긴 것입니다.

이번 영상은 코드와 장면 데이터를 Claude(Anthropic의 AI)가 쓰는 방식으로 만들었습니다.\
이 글은 그 순서를 기록한 것입니다. 누가 무엇을 했는지가 핵심이라 먼저 표로 정리합니다.

## 누가 무엇을 했나

| 단계 | 맡은 쪽 | 사용한 것 |
|---|---|---|
| 방향 정하기, 대본 확정 | 사람 | |
| 대본 초안 | Claude | |
| 음성 생성 | 사람 | ElevenLabs |
| 단어별 시각 추출 | 직접 만든 도구 | Whisper 기반 음성 인식 |
| 장면 데이터 정리, 영상 코드 작성 | Claude | scenes.json, Remotion |
| 렌더, 프레임 점검 | Claude | Remotion |
| 효과음 합성, 음량 맞춤 | 스크립트 | ffmpeg |
| 최종 확인, 업로드 | 사람 | |

Claude가 맡은 일은 코드와 데이터를 쓰는 부분입니다.\
무엇을 말할지, 어떤 목소리로 읽을지, 올려도 되는지는 사람이 정합니다.

## 대본과 음성은 사람이 정합니다

대본은 제가 방향을 정하고 Claude가 초안을 씁니다.\
확정은 제가 합니다.

음성은 외부 도구인 ElevenLabs로 직접 만듭니다.\
영상 코드가 음성을 만드는 것이 아니라, 이미 만들어진 음성 파일을 받아서 쓰는 구조입니다.

## 음성에서 단어별 시각을 뽑습니다

음성이 나오면 직접 만든 음성 인식 도구로 단어마다 몇 초에 나오는지를 뽑습니다.\
이 도구는 [Whisper](https://github.com/openai/whisper) 기반입니다.\
처음에는 자막이 없는 영상에 자막을 만들려고 바이브 코딩으로 만든 앱이었습니다.

Whisper는 모델에 따라 속도와 인식률이 갈립니다.\
turbo 모델은 빠르지만 인식률이 낮습니다.\
medium이나 large 모델은 인식률이 높은 대신 많이 느립니다.

정확히 재 둔 값은 아니지만 기억으로는 2시간짜리 영상 전체 자막을 뽑는 데 30분이 넘게 걸렸습니다.\
CPU와 GPU로 돌리다 보니 지금 쓰는 맥 미니에서는 속도가 느려서 불편했고, 최적화를 했는데도 인식 오류는 남았습니다.\
그래서 만들어 놓고도 잘 쓰지 않았습니다.

지금은 사정이 다릅니다.\
대본이 이미 있어서 단어가 나오는 시각만 뽑으면 되니, 인식률이 조금 낮아도 문제가 되지 않습니다.\
원래 용도로는 잘 쓰지 않던 도구가 이번 제작에서는 잘 맞았습니다.

자막 문구는 대본에서 가져오고, 인식 결과에서는 타이밍만 씁니다.\
인식 오류가 화면에 나오지 않게 하려는 규칙입니다.

자막 타이밍을 직접 맞추면 어긋남이 생겼습니다.\
그래서 이후에는 음성에서 단어별 시각을 뽑아 자막에 씁니다.

자막 데이터는 이런 모양입니다.

```json
{ "s": 5.06, "e": 5.96, "t": "제목이 별로였나?" }
```

시작 초, 끝 초, 문구가 한 줄입니다.\
이 영상의 번인 자막은 142줄이고, 글꼴은 Pretendard Bold입니다.

## 장면 데이터는 scenes.json으로 정리합니다

Claude는 단어별 시각을 장면 데이터로 정리합니다.\
장면마다 id, 시작과 끝, 효과가 시작되는 시점이 들어갑니다. 이 영상은 장면이 12개입니다.

```json
{ "id": "S03", "label": "CONCENTRATION", "bg": "ink", "start": 39.92, "end": 64.62,
  "cues": { "ghost": 39.92, "grid": 40.3, "top20": 42.04, "top42": 46.62 } }
```

위는 실제 파일의 한 장면에서 일부 항목을 줄여 옮긴 것입니다.\
`cues`는 효과가 시작되는 시각이고, 이름은 장면 안에서 그 효과를 가리키는 말입니다.

Remotion 코드는 이 시각을 장면 시작 기준의 프레임으로 바꿔서 애니메이션의 시작점으로 씁니다.\
실제 코드의 핵심은 몇 줄입니다.

```typescript
export const FPS = 60;
export const T = (s: number) => Math.round(s * FPS);          // 초 -> 프레임
const L = (s: number) => T(s) - T(scene.start);               // 장면 시작 기준 프레임

// 큐 이름 -> 진행도(0~1)
export const useCue = (name: string, dur = 26, ease = EXPO) => {
  const f = useCurrentFrame();
  const { L, c } = useScene();
  return prog(f, L(c[name]), dur, ease);
};
```

`prog`는 Remotion의 [interpolate](https://www.remotion.dev/docs/interpolate)로 시작 프레임부터 지정한 길이 동안 0에서 1로 올라가는 값을 만듭니다.\
장면 안의 컴포넌트는 `useCue("top20")`처럼 큐 이름으로 이 값을 받아서 투명도나 위치에 씁니다.

## 렌더하고 점검합니다

Claude가 영상을 렌더한 뒤 프레임을 점검합니다.\
최종 확인과 업로드는 제가 합니다.

화면 사양은 1920x1080, 60fps이고, 총 21,012프레임입니다.

효과음 합성과 음량 맞춤(-16 LUFS)은 ffmpeg 스크립트로 처리했습니다.\
이 영상은 프리미어 같은 편집 툴에서 후작업 없이 Remotion 렌더 결과를 그대로 올렸습니다.

## 같은 데이터에서 나온 것들

같은 컴포넌트와 데이터에서 썸네일 2종, 커뮤니티용 카드뉴스 8장, 세로 쇼츠 3편도 만들었습니다.

## 사람이 맡는 일

Claude가 코드를 써도 방향을 정하고, 음성을 만들고, 마지막에 확인하는 일은 사람의 몫입니다.\
영상이 저절로 나오는 구조는 아닙니다.

제가 이 방식에서 얻은 것은 반복되는 수정을 코드와 데이터 한 곳에서 끝낼 수 있다는 점입니다.

이전에 Remotion으로 영상을 만든 기록은 [프리미어 대신 React(Remotion) 코드로 만든 이유](/blog/2026-09-30-react-remotion-motion-graphics-youtube-automation/)에 있습니다.

---

참고 자료:
- [Remotion: Make videos programmatically](https://www.remotion.dev/)
- [Remotion interpolate()](https://www.remotion.dev/docs/interpolate)
- [OpenAI Whisper](https://github.com/openai/whisper)
