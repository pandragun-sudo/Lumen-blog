---
title: "100MB짜리 폭탄: 외부 보안 감사가 발견한 Private 저장소의 진짜 위험"
description: "Private 저장소라는 이유로 안심하다가, 외부 감사를 통해 평문 OAuth 토큰과 실제 회원 데이터가 담긴 DB 덤프가 커밋 이력에 남아있던 것을 발견했습니다. 이 사고를 통해 배운 보안의 기초를 공유합니다."
category: "devlog"
pubDate: "2026-08-04T07:30:00Z"
heroImage: "../../assets/saas_security_breach.jpg"
---
식은땀이 등줄기를 타고 흐른다는 게 어떤 기분인지 이제 안다. 미들웨어로 API 엔드포인트마다 인증 가드를 세우고 에러 스택 트레이스를 마스킹하면서 혼자 완벽하다고 취해있었다. 코드를 까보지도 않고 레드팀은 정확히 30분 만에 내 목줄을 쥐었다. `git log --all --full-history -- "*.sql"`. 터미널에 찍힌 이 명령어 한 줄이 모든 걸 무너뜨렸다.

몇 달 전 로컬 백업을 하다가 gitignore를 빠져나간 83MB짜리 운영 DB 덤프와 100MB짜리 소스코드 압축본. 깃허브는 지독하게도 모든 과거를 기억한다. 파일을 지웠다고 안심한 게 멍청했다. 실제 회원 이메일, 평문으로 저장된 OAuth 토큰, 세션 테이블 전체가 그 안에 고스란히 남아있었다. Private 저장소라는 알량한 방어선은 외부인을 초대하는 순간 모래성처럼 무너져 내렸다.

급하게 구글 OAuth 앱 시크릿을 날리고 DB 비밀번호를 강제 교체했다. `git filter-branch`로 커밋 이력을 박박 긁어내며 헛구역질이 났다. AI는 코드의 흐름은 귀신같이 읽으면서도 폴더 구석에 처박힌 100MB짜리 폭탄은 보지 못한다. 아니, 볼 생각도 안 한다. 결국 감시자는 인간이어야 한다. 화려한 프론트엔드 뒤에서 내 시스템은 썩어 들어가고 있었다. [Lumen Insights](https://app.lumeninsights.kr/?utm_source=lumen_blog&utm_medium=blog_post&utm_campaign=auto_generated_post) V2 배포는 전면 중단됐다.