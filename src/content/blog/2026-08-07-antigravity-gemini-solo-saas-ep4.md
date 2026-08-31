---
title: "에피소드 4: 길을 잃지 않는 법, 프로젝트 플랜 관리와 컨텍스트 엔지니어링"
description: "AI 에이전트와의 수십 번 세션 전환 속에서도 아키텍처 일관성을 유지하는 프로젝트 플랜 관리법과 옵시디언(Obsidian) 개발 일지 자동화 시스템을 해부합니다."
category: "devlog"
pubDate: "2026-08-07T08:29:07Z"
heroImage: "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80"
---

1인 개발자에게 가장 두려운 순간은 컴파일 에러나 데이터베이스 충돌을 만날 때가 아닙니다. 수백 개의 소스 코드 파일과 복잡하게 얽힌 컴포넌트 구조 속에서, "내가 지금 대체 무엇을 만들고 있었는가?"라며 프로젝트의 거대한 방향성을 상실할 때입니다.

특히 Antigravity나 Gemini 같은 고성능 LLM 에이전트와 페어 프로그래밍을 진행하다 보면, 초당 수십 줄의 코드가 빠르게 쏟아지는 속도감에 압도되어 오히려 아키텍처의 균형을 잃어버리는 현상이 발생합니다. 속도가 빨라질수록 방향을 잃었을 때 치러야 하는 대가는 기하급수적으로 커집니다.

오늘은 Lumen Insights 개발 초기, 컨텍스트 유실로 인해 겪었던 뼈아픈 시행착오와 이를 극복하기 위해 구축한 `PROJECT_PLAN.md` 기반의 컨텍스트 앵커링(Context Anchoring) 시스템을 공유합니다.

## 파편화된 코드와 새 세션마다 리셋되는 기억들

Lumen Insights 초기 버전 개발 당시, 저는 눈앞의 기능 구현에만 매몰되어 시스템 전체의 상태 머신을 체계화하지 못했습니다. LLM의 컨텍스트 윈도우 한계로 인해 채팅 세션이 길어지면 토큰 비용이 급증하고 응답 지연이 발생했기에, 30~40턴마다 새로운 세션으로 대화를 전환해야 했습니다.

하지만 세션이 전환될 때마다 AI는 이전 세션에서 합의했던 핵심 설계 원칙과 우선순위를 완전히 잊어버렸습니다.

```
[과거의 세션 전환 실패 패턴]
세션 1: "Supabase DB 용량 한계를 고려해 슬라이딩 윈도우 60일 컷오프를 적용하자." (합의 완료)
  ↓ (세션 리셋)
세션 2: "전체 기간 통계를 뽑아야 하니 모든 히스토리 데이터를 무제한 적재하겠습니다." (원칙 붕괴)
  ↓ (세션 리셋)
세션 3: "지난 세션의 쿼리가 느리니 인덱스를 10개 더 추가하겠습니다." (용량 한도 초과 위기)
```

어제 확정한 라우팅 규칙을 오늘 완전히 새로운 라이브러리로 대체하려 하거나, 이미 최적화를 마친 쿼리를 엉뚱한 방식으로 롤백하는 일이 반복되었습니다. 머릿속에만 존재하는 암묵지(Tacit Knowledge)는 AI 에이전트에게 전달될 수 없다는 사실을 절감했습니다.

| 구분 | 비정형 세션 방식 (과거) | 구조화된 플랜 앵커링 (현재) |
|---|---|---|
| 컨텍스트 유지 | 대화 히스토리에 의존 (세션 리셋 시 소멸) | `PROJECT_PLAN.md` 단일 진실 공급원(SSOT) |
| 작업 착수 방식 | 프롬프트로 과거 상황 장황하게 설명 | 에이전트가 플랜 파일을 읽고 스스로 위치 파악 |
| 완료 판정 기준 | 주관적 "잘 작동합니다" 보고 | 체크리스트 기반 단위 테스트 및 룰 검증 |
| 지식 누적 | 메신저나 메모장에 산발적 파편화 | 옵시디언(Obsidian) 개발 일지 자동 아카이빙 |

## PROJECT_PLAN.md: AI와 인간이 공유하는 단일 진실 공급원 (SSOT)

이 혼란을 종식시키기 위해 도입한 도구가 바로 프로젝트 루트의 `PROJECT_PLAN.md`입니다. 이 문서는 단순한 할 일 목록(To-Do List)이 아니라, 시스템의 현재 상태(Current State), 다음 마일스톤, 기술적 제약 사항이 실시간으로 기록되는 **동적 상태 저장소**입니다.

새로운 세션이 시작되면, 에이전트는 규칙(Rule)에 따라 다른 어떤 코드도 건드리기 전에 반드시 `PROJECT_PLAN.md`를 가장 먼저 읽습니다.

```markdown
# Lumen Insights - Project Plan

## 현재 컨텍스트
* **작업 단계:** [v2.3.7] 블로그 E-E-A-T 전수 검증 및 고위험 포스팅 클린업 진행 중.
* **현재 우선 과제:**
  1. [x] MFA 오인 위험 포스팅 삭제 및 301 리다이렉트 매핑
  2. [ ] 42편 전 포스팅 외부 권위 출처 링크 2~3건 결합
  3. [ ] Astro 빌드 검증 및 사이트맵 최신화
* **기술적 제약:** Supabase 무료 티어 500MB 엄수 (무기한 데이터 적재 금지).
```

에이전트는 이 파일을 읽는 순간 "지금은 데이터베이스 튜닝이 아니라 블로그 E-E-A-T 검증 단계이며, 500MB DB 제약을 위반하면 안 된다"는 맥락을 1초 만에 복원합니다. 작업이 완료되면 에이전트가 직접 완료 항목을 체크하고 다음 우선순위를 갱신합니다.

## 지식 자산화: 옵시디언(Obsidian) 개발 일지 자동 아카이빙

플랜 관리가 '현재와 미래의 좌표'를 잡아준다면, 과거의 시행착오를 자산으로 바꾸는 것은 **옵시디언 개발 일지 자동 아카이빙 시스템**입니다.

1인 개발에서 동일한 유형의 버그(예: KST 타임존 오차, 조회수 쉼표 파싱 실패)를 두 번 디버깅하는 것은 치명적인 시간 낭비입니다. Lumen Insights의 에이전트 규약에는 복잡한 트러블슈팅이나 아키텍처 결정이 있을 때마다 `obsidian_notes/Lumen_Insights_개발일지.md`에 의사결정 기록(ADR, Architecture Decision Record)을 자동으로 덧붙이도록(Append-Only) 정의되어 있습니다.

```
[시행착오 발생] → [원인 분석 및 3가지 대안 평가] → [최종 채택안 도출] → [개발 일지 최상단 자동 기록]
```

이 기록은 마크다운 형식의 영구적인 로컬 지식 베이스로 축적되어, 다음번 유사한 문제를 마주했을 때 AI가 과거의 해결책을 즉각 참조할 수 있는 사내 위키(Internal Wiki) 역할을 수행합니다.

문서화는 코딩이 끝난 뒤 억지로 작성하는 부차적 행위가 아닙니다. AI 에이전트와의 협업에서 문서화는 컨텍스트의 왜곡을 막고 복리(Compound Effect)로 성장하는 엔지니어링 자산을 구축하는 핵심 메커니즘입니다.

---

**참고 자료:**
- [Martin Fowler — Architecture Decision Records (ADRs)](https://martinfowler.com/articles/scaling-architecture-conversationally.html#ArchitectureDecisionRecords)
- [GitHub Documentation — About READMEs and Project Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
- [Google Search Central — Creating Helpful, Reliable, People-First Content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
