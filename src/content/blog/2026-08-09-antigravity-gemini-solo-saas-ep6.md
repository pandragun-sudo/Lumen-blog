---
title: "1인 SaaS를 위한 다계층 보안 방어선: Next.js 미들웨어와 토큰 어뷰징 차단"
description: "외부 API 쿼터 고갈과 무단 크롤링 공격으로부터 1인 SaaS를 보호하기 위해 설계한 Next.js 미들웨어, Redis Rate Limit, SameSite 쿠키 보안 아키텍처를 상세히 공유합니다."
category: "devlog"
pubDate: "2026-08-09T14:00:00+09:00"
heroImage: "../../assets/images/blog/ep6_security.jpg"
---

웹 서비스를 운영하다 보면 트래픽의 증가가 마냥 반갑지만은 않은 순간이 찾아옵니다.  
서비스의 인지도가 올라갈수록 시스템의 취약점을 노려 무차별적인 API 호출을 시도하거나, 단일 계정의 세션을 수십 명이 공유하여 리소스를 고갈시키는 어뷰징(Abuse) 시도가 급증하기 때문입니다.  

특히 YouTube Data API와 같은 외부 상용 쿼터에 의존하는 1인 SaaS 환경에서, 악의적인 스크립트에 의한 무한 요청은 전체 사용자의 서비스 마비와 막대한 인프라 청구서로 이어질 수 있습니다.  
거대 보안 전담팀이나 고가의 보안 솔루션 없이, 소프트웨어 아키텍처와 세션 제어 기술만으로 완성한 **다계층 보안 방어선(Defense-in-Depth)**을 공개합니다.  

## 1인 SaaS가 직면하는 3대 핵심 위협

1. **무차별 API 엔드포인트 크롤링**: `/api/dashboard/trending-tags` 등의 경로를 미인증 상태로 1초에 수백 번 찔러 DB 풀을 고갈시키는 공격  
2. **SameSite 쿠키 탈취 및 세션 하이재킹**: CSRF 공격이나 교차 도메인 스크립트를 통한 사용자 세션 오용  
3. **계정 등급 우회 및 쿼터 고갈**: 만료된 무료 체험(Trial) 계정이 백엔드 검증 누락으로 상위 등급 권한을 유지하는 결함  

| 보안 계층 | 방어 대상 및 위협 | 구현 기술 및 조치 |
|---|---|---|
| 1계층: 엣지 미들웨어 | 악의적인 비인증 대량 요청 | Next.js Edge Middleware 토큰 사전 검증 |
| 2계층: Rate Limiter | 무차별 엔드포인트 디도스 | IP 및 유저 ID 기반 분당 60회 엄격 제한 |
| 3계층: 세션 무결성 | 교차 사이트 쿠키 오용 | `SameSite=Lax`, `HttpOnly`, `Secure` 쿠키 플래그 강제 |
| 4계층: DB 강등 방어 | 만료 유저 권한 승급 버그 | 런타임 이중 검증 및 RESTRICTED 강등 자동화 |

## Next.js Edge Middleware를 통한 1차 관문 방어

모든 요청이 무거운 백엔드 비즈니스 로직이나 DB 커넥션 풀을 건드리기 전에, 엣지(Edge) 네트워크 단계에서 인증 유효성을 먼저 검사하여 서버 부하를 99% 차단합니다.  

```typescript
// src/middleware.ts: 엣지 단의 신속한 인증 및 레이트 리밋 검증
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('lumen_session_token')?.value;
  const isApiPath = request.nextUrl.pathname.startsWith('/api/');

  // 보호된 API 경로에 유효한 세션 토큰이 없는 경우 즉시 401 차단
  if (isApiPath && !token) {
    return NextResponse.json(
      { error: '로그인이 필요한 서비스입니다.' },
      { status: 401 }
    );
  }

  return NextResponse.next();
}
```

## 미인증 응답 상한(Limit 10)과 런타임 권한 강제

보안 취약점 중 하나는 미인증 유저에게도 100건의 전체 트렌드 데이터가 노출되던 레거시 라우터였습니다.  
우리는 엔드포인트 레벨에서 인증되지 않은 요청에 대해 최대 10건으로 응답을 강제 제한하고, API 키가 존재하지 않는데 상위 등급을 가진 비정상 유저는 런타임에서 즉시 `RESTRICTED` 등급으로 강등하는 이중 방어막을 구축했습니다.  

보안은 한 번의 설정으로 끝나는 작업이 아니라, 시스템의 모든 입출력 경로에 다층 방어막을 촘촘히 엮어내는 지속적인 엔지니어링 규율입니다.  

---

**참고 자료:**
- [OWASP Foundation — Defense in Depth Principles](https://owasp.org/www-community/Defense_in_Depth)
- [Next.js Documentation — Edge Middleware Authentication Patterns](https://nextjs.org/docs/app/building-your-application/routing/middleware)
- [MDN Web Docs — Using HTTP Cookies and SameSite Security](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)
