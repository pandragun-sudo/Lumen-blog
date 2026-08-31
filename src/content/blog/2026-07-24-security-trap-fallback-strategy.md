---
title: "보안 패치가 서비스를 마비시킨 날: SameSite 쿠키 설정이 부른 OAuth 로그인 전면 장애"
description: "개인정보 보호를 강화하려는 선의의 보안 패치가 구글 로그인 전체를 마비시켰습니다. SameSite=Strict가 OAuth 리다이렉트에서 왜 치명적인 함정이 되는지, 그리고 폴백 전략으로 시스템 강건성을 확보하는 방법을 공개합니다."
category: "devlog"
pubDate: "2026-07-24T20:45:00Z"
heroImage: "../../assets/security_trap_thumbnail.jpg"
---

"로그인이 안 됩니다."  

Lumen Insights V2 런칭을 불과 며칠 앞둔 시점에 들어온 이 메시지를 받았을 때, 저는 처음에는 대수롭지 않게 여겼습니다.  
브라우저 캐시 문제거나 일시적인 네트워크 오류일 거라고 생각했습니다.  
그런데 확인해보니 구글 OAuth 로그인이 **모든 사용자, 모든 환경에서** 완전히 작동하지 않고 있었습니다.  

원인을 찾는 데 4시간이 걸렸습니다.  
범인은 보안을 강화하기 위해 적용했던 `SameSite=Strict` 쿠키 설정이었습니다.  

## SameSite 쿠키 속성의 함정

`SameSite` 속성은 쿠키가 어떤 요청에 포함될지를 제어하는 보안 설정입니다.  
세 가지 값이 있습니다.  

| SameSite 값 | 쿠키 전송 조건 | OAuth 호환성 |
|---|---|---|
| `None` | 모든 요청에 전송 (HTTPS 필수) | 완벽히 호환 |
| `Lax` | 같은 사이트 + GET 방식 최상위 탐색 | 대부분 호환 |
| `Strict` | 오직 같은 사이트 요청에만 전송 | OAuth에서 치명적 문제 |

이전 보안 감사에서 "쿠키 보안을 최대로 강화하라"는 권고에 따라 `SameSite=Strict`로 설정을 변경했습니다.  
표면적으로는 완벽한 보안 강화였습니다.  

하지만 구글 OAuth의 작동 방식을 이해하면 이것이 왜 재앙인지 알 수 있습니다.  

## OAuth 리다이렉트 흐름과 SameSite의 충돌

구글 OAuth 로그인의 흐름은 다음과 같습니다.  

```
1. 사용자가 "구글로 로그인" 클릭
2. 우리 서버가 OAuth state 값을 세션 쿠키에 저장
3. 사용자를 accounts.google.com으로 리다이렉트
4. 구글에서 인증 완료 후 우리 서버로 리다이렉트
5. 우리 서버가 세션 쿠키에서 state 값을 읽어 검증
```

3번에서 4번으로 넘어오는 순간이 문제입니다.  
`accounts.google.com`에서 `app.lumeninsights.kr`로의 리다이렉트는 브라우저 입장에서 **크로스 도메인 탐색(Cross-site Navigation)**입니다.  

`SameSite=Strict`는 이 크로스 도메인 탐색에서 쿠키를 절대 전송하지 않습니다.  
즉, 4번 단계에서 우리 서버는 세션 쿠키를 받지 못하고, state 값을 확인할 수 없어 "OAuth 상태 불일치" 오류를 던지며 로그인을 거부했습니다.  

사용자 입장에서는 아무런 오류 메시지도 없이 로그인 페이지로 다시 튕겨나갈 뿐이었습니다.  

## 해결: SameSite=Lax로의 롤백과 추가 방어선 구축

해결책은 단순했습니다.  
`SameSite=Strict` → `SameSite=Lax`로 롤백.  

`Lax`는 최상위 탐색(Top-level Navigation)에서는 쿠키를 전송하기 때문에, OAuth 리다이렉트 흐름에서 세션 쿠키가 정상적으로 전달됩니다.  
보안 수준이 `Strict`보다는 낮지만, OAuth를 사용하는 서비스에서는 `Lax`가 실질적인 표준입니다.  

하지만 여기서 멈추지 않았습니다.  
이 사고가 가르쳐준 더 중요한 교훈은 **"보안 설정 하나가 핵심 기능 전체를 마비시킬 수 있다"**는 사실이었습니다.  
이러한 단일 장애점(Single Point of Failure)을 막기 위한 폴백 전략이 필요했습니다.  

## 폴백 전략: 연쇄 장애를 막는 방어선 설계

소프트웨어 시스템에서 폴백(Fallback)이란 주된 방법이 실패했을 때 자동으로 대안으로 전환되는 메커니즘입니다.  

Lumen Insights에서는 이 사고 이후 다음 폴백 전략들을 추가했습니다.  

**OAuth 폴백**: 구글 로그인 실패 시 사용자에게 명확한 오류 메시지와 함께 "이메일로 다시 시도" 안내  
**API 폴백**: YouTube API 쿼터 소진 시 DB 캐시 데이터로 자동 전환, 캐시 없으면 "데이터 수집 중" 상태 표시  
**DB 폴백**: DB 연결 실패 시 읽기 전용 캐시 레이어에서 마지막 성공 데이터 제공  

폴백을 설계할 때의 핵심 원칙은 하나입니다.  
**사용자는 내부에서 무슨 일이 벌어지고 있든 명확한 상태를 알아야 한다.**  
조용히 실패하는 시스템은 시스템이 없는 것보다 더 위험합니다.  
사용자는 작동하고 있다고 생각하지만 실제로는 아무 일도 일어나지 않는 상태가 가장 신뢰도를 무너뜨립니다.  

## 선의의 패치가 가르쳐준 것

이 장애는 "보안을 강화하면 무조건 좋다"는 단순한 생각이 얼마나 위험한지 보여주었습니다.  
모든 보안 설정에는 트레이드오프가 있습니다.  
`SameSite=Strict`는 CSRF 공격에 대한 완벽한 방어선이지만, OAuth 흐름을 끊어버립니다.  

이후 저는 모든 보안 패치를 적용하기 전에 반드시 이 질문을 먼저 합니다.  
"이 변경이 핵심 사용자 여정(Login → Dashboard → 핵심 기능)을 방해하지는 않는가?"  

Lumen Insights는 이 장애를 통해 더 단단해졌습니다.  
완벽한 보안이란 없지만, 장애가 발생했을 때 빠르게 감지하고 폴백으로 전환하는 시스템은 만들 수 있습니다.  
선의로 시작한 패치가 예상치 못한 방식으로 돌아오는 경험 — 이것이 1인 개발자가 혼자 감당해야 하는 가장 힘든 종류의 배움입니다.

---

**참고 자료:**
- [MDN Web Docs — Understanding SameSite Cookie Policies and Cross-Site Contexts](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
- [IETF RFC 6265bis — Cookies: HTTP State Management Mechanism](https://datatracker.ietf.org/doc/html/rfc6265bis)
- [OWASP Foundation — Cross-Site Request Forgery (CSRF) Prevention Cheat Sheet](https://owasp.org/www-community/attacks/Cross-Site_Request_Forgery)
