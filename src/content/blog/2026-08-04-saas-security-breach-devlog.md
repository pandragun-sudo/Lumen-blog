---
title: "100MB짜리 폭탄: 외부 보안 감사가 발견한 Private 저장소의 진짜 위험"
description: "Private 저장소라는 이유로 안심하다가, 외부 감사를 통해 평문 OAuth 토큰과 실제 회원 데이터가 담긴 DB 덤프가 커밋 이력에 남아있던 것을 발견했습니다. 이 사고를 통해 배운 보안의 기초를 공유합니다."
category: "devlog"
pubDate: "2026-08-04T07:30:00Z"
heroImage: "../../assets/saas_security_breach.jpg"
---

모든 것이 완벽하다고 생각했습니다.  
Next.js 미들웨어로 인증 가드를 세웠고, API 엔드포인트마다 권한 검사를 달았으며, 글로벌 에러 핸들러는 프로덕션 환경에서 스택 트레이스를 노출하지 않도록 마스킹 처리했습니다.  
저는 Lumen Insights V2의 런칭을 앞두고, 코드베이스가 충분히 안전하다고 확신했습니다.  

그 확신이 산산조각 난 것은 외부 개발자의 크로스 체크(Red Teaming)가 시작된 지 불과 30분 만이었습니다.  

## 발견된 폭탄: 커밋 이력 속에 잠들어 있던 100MB의 진실

외부 개발자가 가장 먼저 확인한 것은 코드가 아니었습니다.  
**깃허브 커밋 이력**이었습니다.  

```bash
git log --all --full-history -- "*.sql"
git log --all --full-history -- "*.zip"
```

이 두 명령어가 뱉어낸 결과물은 충격이었습니다.  
수개월 전, 로컬 환경에서 백업 작업을 하던 중 실수로 `.gitignore` 필터링을 빠져나간 두 개의 파일이 커밋 이력 깊숙이 묻혀 있었습니다.  

- `aiven_dump.sql` (83MB): 운영 데이터베이스 전체 덤프
- `yt-shorts-mvp-source.zip` (101MB): 소스코드 압축본

이 파일들 안에는 다음 내용이 포함되어 있었습니다.  

| 데이터 종류 | 상태 | 위험도 |
|---|---|---|
| 실제 회원 이메일, 전화번호, 생년월일 | 평문 저장 | 매우 높음 |
| YouTube OAuth Access Token 5건 | 평문 저장 | 매우 높음 |
| YouTube Refresh Token 1건 | 평문 저장 | 매우 높음 |
| `session` 테이블 전체 | 평문 저장 | 높음 |
| `dist/.env`의 운영 API 키 | 평문 저장 | 매우 높음 |

가장 두려운 사실은, 파일 자체를 삭제해도 소용없다는 점이었습니다.  
**깃허브는 커밋 이력을 영구 보관합니다.**  
`git rm`으로 파일을 지워도, `git log`로 과거 커밋을 체크아웃하면 그 파일을 완전히 복원할 수 있습니다.  
저장소가 Private이라는 것이 유일한 방어선이었는데, 그 저장소에 외주 개발자를 초대하는 순간 이 모든 데이터가 노출될 수 있었습니다.  

## AI가 놓친 이유: 사각지대의 본질

이 대목에서 저는 스스로에게 가혹한 질문을 던졌습니다.  
"왜 AI 비서는 이 문제를 발견하지 못했는가?"  

답은 명확했습니다.  
AI는 주어진 컨텍스트, 즉 현재 열려있는 코드베이스의 논리적 흐름 안에서는 경이로운 통찰력을 발휘합니다.  
하지만 그 범위를 벗어난 **형태 없는 위험** — 저장소 전체의 물리적 상태, 과거의 커밋 이력, 6개월 전에 올라간 파일 — 앞에서는 완전히 맹목적입니다.  

이것은 AI의 결함이 아닙니다.  
코드를 짠 당사자도, 그 코드를 함께 작성한 AI도 자신의 작업물을 완벽하게 객관적으로 감사할 수 없다는 소프트웨어 공학의 오래된 불문율입니다.  
그래서 외부 감사, 즉 Red Teaming이 필요합니다.  

## 즉각 조치와 재발 방지 시스템

발견 즉시 다음 순서로 긴급 조치를 수행했습니다.  

**1단계 (당일)**: 노출된 모든 크리덴셜 즉시 폐기
- Google OAuth 앱 시크릿 리셋 (기존 토큰 전체 무효화)
- 데이터베이스 비밀번호 강제 변경
- YouTube API 키 Revoke 후 재발급 (IP 제한 추가)

**2단계 (당일)**: 커밋 이력에서 민감 파일 완전 제거
```bash
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch aiven_dump.sql yt-shorts-mvp-source.zip' \
  --prune-empty --tag-name-filter cat -- --all
git push origin --force --all  # 이 경우에만 예외적으로 force push 허용
```

**3단계 (다음 날)**: 재발 방지 규칙을 `AGENTS.md`에 하드코딩

이후 AI 비서에게 강제 주입된 불변 규칙은 다음과 같습니다.  
- `.env`, `*.sql`, `*.zip`, `*.dump`, `*.sqlite` 파일은 어떤 이유로도 `git add` 금지
- 10MB를 초과하는 파일은 반드시 사전에 대표에게 확인
- 커밋 전 `git status`로 민감 파일이 스테이징 되었는지 항상 검사
- `git push --force`는 크리덴셜 노출 사고 복구 시에만 허용

## 1인 창업가를 위한 저장소 보안 체크리스트

이 사고를 겪고 나서, 저는 모든 새로운 프로젝트를 시작할 때 다음 체크리스트를 반드시 먼저 실행합니다.  

```bash
# 1. .gitignore 상태 확인
cat .gitignore | grep -E "\.env|\.sql|\.zip|\.dump"

# 2. 이미 트래킹 중인 민감 파일 확인
git ls-files | grep -E "\.env|\.sql|\.zip|\.dump|\.key|\.pem"

# 3. 커밋 이력에서 민감 파일 존재 여부 확인
git log --all --full-history -- "*.sql" "*.env" "*.zip" "*.dump"
```

이 세 가지 명령어를 처음 실행하는 데 1분도 걸리지 않습니다.  
하지만 이것을 확인하지 않아 발생하는 사고는 수개월간의 대응 비용과 신뢰 손실로 이어집니다.  

Lumen Insights는 이 사고를 계기로 인프라 보안을 기능 개발보다 우선순위에 두는 운영 원칙을 확립했습니다.  
화려한 UI 뒤에 아무도 모르게 쌓이고 있는 위험을 직접 경험한 창업가로서, 이 글을 읽고 계신 모든 분들이 지금 당장 `git log`를 열어보시기를 권합니다.

---

**참고 자료:**
- [GitHub Docs — Best Practices for Preventing Secret and Token Leaks](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [OWASP Foundation — Top 10 Web Application Security Risks](https://owasp.org/www-project-top-ten/)
- [The Twelve-Factor App — Config: Store Config in the Environment](https://12factor.net/config)
