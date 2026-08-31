---
title: "1인 개발자를 위한 안티그라비티(Antigravity) 룰 세팅법: AGENTS.md로 AI에게 영구 기억 심기"
description: "AI 페어 프로그래밍 시 발생하는 컨텍스트 유실과 코딩 스타일 붕괴를 원천 방어하기 위해 AGENTS.md를 설계하고 운영하는 실전 가이드를 Q&A 형식으로 정리합니다."
category: "devlog"
pubDate: "2026-08-06T14:00:00+09:00"
heroImage: "../../assets/ai_assistant_workflow.jpg"
---

Lumen Insights 시스템을 개발하며 수많은 AI 코딩 어시스턴트를 활용해 왔습니다.  
처음에는 빠른 코드 작성 능력에 감탄하지만, 대화가 조금만 길어지면 "왜 이 모델은 어제 정한 코딩 규칙을 오늘 또 잊어버리는 걸까?"라는 깊은 피로감에 직면하곤 했습니다.  

우리가 안티그라비티(Antigravity) 2.0 생태계에 정착한 가장 결정적인 이유는, 에이전트에게 확고한 '정체성'과 '영구 기억'을 부여할 수 있는 메커니즘 때문이었습니다.  
1인 창업가가 AI를 단순한 챗봇이 아니라 깐깐한 시니어 풀스택 엔지니어로 훈련시키는 **`AGENTS.md` 룰 세팅법**을 핵심 문답 형식으로 풀어봅니다.  

## Q1. AI가 자꾸 엉뚱한 코드를 짜거나 어제 합의한 규칙을 무시합니다. 근본 원인이 무엇인가요?

일반적인 챗봇 인터페이스는 '현재 열려 있는 단일 대화 세션' 안에서만 단기 기억을 유지합니다.  
작업이 진행되어 토큰이 수만 개를 넘어가면 초기에 주입했던 시스템 프롬프트가 컨텍스트 윈도우 밖으로 밀려나게 됩니다.  

이 문제를 해결하려면 에이전트가 매 턴마다 자동으로 읽고 실행해야 하는 **물리적 규약 문서(`AGENTS.md`)**를 작업 공간 최상단에 배치하는 것이 효과적입니다.  
Antigravity는 파일 시스템을 인식하므로, 이 문서를 단일 진실 공급원(SSOT)으로 삼아 모델이 임의로 규칙을 왜곡하지 못하도록 강제합니다.  

| 에이전트 운영 방식 | 일반 대화창 프롬프팅 | `AGENTS.md` 기반 통제 아키텍처 |
|---|---|---|
| 규칙 지속성 | 대화가 길어지면 100% 망각 발생 | 매 실행 시 영구 룰셋 자동 참조 |
| 코딩 스타일 일관성 | 모델 기분에 따라 라이브러리 파편화 | 지정된 디자인 토큰 및 SQL 규칙 강제 |
| 보안 통제력 | 민감 키 노출 및 평문 저장 위험 | 플레이스홀더 및 암호화 헬퍼 의무화 |

## Q2. `AGENTS.md`에는 구체적으로 어떤 내용을 명시해야 하나요?

"좋은 코드를 짜줘" 같은 모호한 문장은 아무런 효과가 없습니다.  
우리는 과거 개발 일지에서 실제로 터졌던 버그와 보안 사고를 바탕으로, 다음의 **5대 실전 규약**을 명문화했습니다.  

```markdown
# AGENTS.md 핵심 헌법 규약 예시

## 1. 보안 및 민감 정보 보호
- SQL 쿼리는 반드시 $1 플레이스홀더 사용 (문자열 보간 절대 금지)
- 암호화 대상 컬럼은 cryptoHelper.encrypt()를 거쳐 저장

## 2. 데이터베이스 규약 (Supabase 500MB)
- DELETE 쿼리 실행 후 반드시 VACUUM 루틴 연동 고려
- 7일 경과 데이터는 슬라이딩 윈도우 정책에 따라 자동 정리

## 3. UI 및 디자인 시스템
- 모든 input 태그에 autocomplete="off", spellcheck="false" 필수 적용
- 다크 글래스모피즘 테마를 위해 시스템 이모지 하드코딩 엄격 금지 (Lucide 단색 SVG 사용)
```

## Q3. 프롬프트가 길어지면 에이전트가 느려지거나 규칙을 헷갈리지 않나요?

매우 날카로운 질문입니다.  
규칙이 수백 줄로 늘어나면 모델의 인지 부하(Attention Load)가 발생합니다.  
이를 방지하기 위해 우리는 문서를 계층화했습니다.  

1. **`AGENTS.md`**: 전역 보안 및 코딩 규약 (상시 적용)  
2. **`PROJECT_PLAN.md`**: 현재 세션의 마일스톤 및 체크리스트 (실시간 갱신)  
3. **`nuance.md`**: 보이스 톤, 금지어 및 E-E-A-T 품질 기준 (글쓰기/UI 전용)  

역할별로 문서를 분리하고 필요한 컨텍스트만 정밀하게 로드하도록 파이프라인을 구성함으로써, 모델은 불필요한 토큰 낭비 없이 최고 속도로 작업할 수 있게 되었습니다.  

## AI는 프롬프트가 아니라 시스템으로 완성된다

AI 페어 프로그래밍의 완성도는 화려한 수식어에 있지 않습니다.  
과거의 시행착오를 문서로 박제하고, 그 문서를 에이전트가 스스로 검증하게 만드는 구조적 장치를 만드는 것.  
이것이 1인 개발자가 거대한 개발팀 부럽지 않은 생산성을 내는 가장 확실한 엔지니어링 비결입니다.  

---

**참고 자료:**
- [Anthropic — System Prompts and Model Context Protocol (MCP)](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts)
- [Google Cloud — Designing Effective Prompts for Gemini Agents](https://cloud.google.com/vertex-ai/docs/generative-ai/text/prompt-guidelines)
- [Martin Fowler — Specification by Example and Living Documentation](https://martinfowler.com/bliki/SpecificationByExample.html)
