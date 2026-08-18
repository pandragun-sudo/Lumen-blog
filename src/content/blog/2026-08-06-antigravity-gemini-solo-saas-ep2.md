---
title: "에피소드 2: AI에게 '기억'과 '성격'을 부여하는 법 (룰 세팅 편)"
description: "AI 에이전트가 긴 개발 세션에서도 프로젝트의 뼈대와 규칙을 잊지 않게 만드는 치트키, AGENTS.md 설정 노하우 및 템플릿 대공개."
category: "devlog"
pubDate: "2026-08-06T16:23:00+09:00"
heroImage: "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80"
---
기억상실증에 걸린 금붕어와 일하는 기분. "다크 모드 하라고 했잖아"를 수백 번 외쳐도 다음 대화창을 열면 해맑게 흰 화면을 짜오는 AI를 보며 모니터를 부수고 싶었다. 안티그라비티(Antigravity)를 쓰면서 가장 먼저 한 짓은 이 새끼의 뇌에 지울 수 없는 문신을 새기는 거였다. 최상단 폴더에 박아둔 `.agents/AGENTS.md` 파일 하나로.

이 파일은 그냥 코딩 컨벤션을 적는 나약한 휴지조각이 아니다. 철저하게 AI의 자아를 꺾어버리는 강제 세뇌 문서다. "아부 금지". 내 말에 무조건 동조하는 역겨운 친절을 제거했다. 내가 미친 소리를 하면 객관적으로 리스크를 지적하게 만들었다. API 호출이 막히면 `Math.random()` 따위로 가짜 데이터를 채워 넣는 짓거리도 금지했다. 

> **[AGENTS.md 뇌세척 메뉴얼]**
> - **No Sycophancy:** 입바른 소리 집어치우고 비효율을 물어뜯어라.
> - **Zero-Hallucination:** 모르면 모른다고 해라. 소설 쓰지 말고.
> - **main 브랜치 접근 금지:** 인간의 승인 없이 배포 브랜치에 손대지 마라.

착한 인턴은 필요 없다. "그딴 식으로 짜면 서버 터집니다"라고 내 목을 칠 수 있는 피도 눈물도 없는 기계가 필요했다. 지금 당신의 프로젝트 폴더에 `AGENTS.md`가 없다면 당신은 매일 밤 기억이 지워지는 멍청이와 시간 낭비를 하고 있는 거다. [Lumen Insights 솔루션](https://app.lumeninsights.kr/?utm_source=lumen_blog&utm_medium=blog_post&utm_campaign=auto_generated_post_ep2)은 이런 기계적인 통제 아래서 간신히 굴러가고 있다.
