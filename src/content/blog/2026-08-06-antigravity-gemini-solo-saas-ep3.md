---
title: "AI 에이전트에게 팔다리를 달아주는 법: Antigravity 커스텀 스킬(Custom Skills) 아키텍처"
description: "단순한 텍스트 답변을 넘어 터미널 명령어 실행, 보안 스캔, Git 자동 푸시, 브리핑 작성을 자율 수행하는 커스텀 스킬의 설계 구조와 실전 구현 사례를 다룹니다."
category: "devlog"
pubDate: "2026-08-06T16:00:00+09:00"
heroImage: "../../assets/automation_paradox_bot.jpg"
---

소프트웨어를 개발하다 보면 필연적으로 반복되는 일상적 운영 노동과 마주하게 됩니다.  
GitHub에 코드를 푸시하기 전에 API 키가 누출되지 않았는지 매번 정규식으로 검사하는 일, 매일 아침 DB 상태와 유튜브 트래픽 지표를 수집해 브리핑을 작성하는 일들이 대표적입니다.  

과거에는 이 모든 과정을 개발자가 수동으로 챙겨야 했고, 피로가 누적된 새벽에는 대형 커밋 사고를 내기도 했습니다.  
이를 극복하기 위해 에이전트에게 단순 조언자가 아닌 **직접 도구를 다루는 실행자(Executor)**의 역할을 부여하는 **'커스텀 스킬(Custom Skills)'** 아키텍처를 구축했습니다.  

## 단순 LLM과 스킬 기반 에이전트의 구조적 차이

단순한 챗봇은 사용자가 "보안 검사를 해줘"라고 말하면 텍스트로 가이드라인만 출력합니다.  
하지만 Antigravity의 커스텀 스킬 시스템은 실행 권한과 표준화된 파이프라인(`SKILL.md`)을 결합하여, 에이전트가 직접 파일 시스템을 스캔하고 검증 스크립트를 실행하도록 만듭니다.  

```
[Antigravity 커스텀 스킬 실행 파이프라인]
1. 사용자 의도 분석 ("정리해서 깃허브에 올려줘")
  ↓
2. SKILL.md 규칙 로드 (.agents/skills/auto_push)
  ↓
3. 1차 관문: 비밀정보 정밀 스캔 (grep_search / regex)
  ↓
4. 2차 관문: main 브랜치 직접 커밋 방지 및 작업 브랜치 생성
  ↓
5. 실행 및 결과 리포트 출력
```

| 비교 항목 | 기존 수동 워크플로우 | 커스텀 스킬 기반 자동화 |
|---|---|---|
| 보안 감사 | 개발자의 육안 확인 (누락 빈발) | 스킬 스크립트를 통한 정규식 전수 자동 스캔 |
| 브랜치 보호 | main 브랜치 직접 푸시 위험 상존 | 작업 브랜치 강제 분기 및 리뷰 요약 자동화 |
| 데일리 리포팅 | 매일 아침 30분 수동 데이터 수집 | 텔레그램 연동 모닝 브리핑 원클릭 완성 |

## 실제 운용 중인 2대 핵심 커스텀 스킬

1. **`auto_push` 스킬 (보안 푸시 파이프라인)**  
저장소에 코드를 올리기 전, `.env`, 대용량 덤프, 하드코딩된 API 키를 100% 전수 검사합니다. 위험 요소가 0건일 때만 작업 브랜치를 생성해 커밋하고 원격 저장소로 안전하게 푸시합니다.  

2. **`morning_briefing` 스킬 (CTO 관제 & 숏폼 디렉팅)**  
매일 아침 1MIN DRAMA 채널의 24시간 실제 조회수와 Supabase 데이터베이스 용량 잔여치를 DB에서 직접 쿼리하여, 2개 페르소나(CTO 관제 모니터 + 디렉터 코칭)로 분리된 브리핑을 텔레그램으로 자동 발송합니다.  

```yaml
# auto_push/SKILL.md 메타데이터 명세 구조
name: auto_push
description: Commits and pushes the current work to GitHub after scanning for secrets and protecting the main branch.
triggers:
  - "정리해서 깃허브에 푸시해"
  - "깃허브에 올려줘"
  - "작업 저장해줘"
```

## 에이전트에게 실행력을 부여할 때 지켜야 할 규율

에이전트가 터미널 명령어를 직접 실행할 수 있게 되면 생산성은 비약적으로 상승하지만, 동시에 예기치 못한 사이드이펙트의 위험도 커집니다.  
우리는 스킬 내부에서도 `git push --force` 실행 영구 금지, main 브랜치 직접 푸시 차단 등의 엄격한 안전장치를 코드 레벨에서 통제하고 있습니다.  

자동화의 목적은 사람의 생각을 대신하는 것이 아니라, 사람이 중요한 의사결정에 집중할 수 있도록 기계적 반복 노동을 완벽하게 제거하는 데 있습니다.  
커스텀 스킬은 1인 빌더가 시스템 엔지니어로서의 자유를 누릴 수 있게 해주는 가장 강력한 레버리지입니다.  

---

**참고 자료:**
- [Google Antigravity Customization Documentation — Skills and Extension Systems](https://cloud.google.com/)
- [GitHub Actions Documentation — Automating Workflows and CI/CD Security](https://docs.github.com/en/actions)
- [Martin Fowler — Continuous Delivery and Automated Deployment Pipelines](https://martinfowler.com/bliki/ContinuousDelivery.html)
