---
title: "Next.js URL-Driven 모달 아키텍처와 좀비 파라미터(Zombie Param) 퇴치기"
description: "브라우저 히스토리와 URL 쿼리 파라미터로 모달 상태를 동기화하는 과정에서 발생한 Stale Closure 및 좀비 파라미터 버그를 완벽히 디버깅한 실전 아키텍처를 공유합니다."
category: "devlog"
pubDate: "2026-08-03T16:00:00+09:00"
heroImage: "../../assets/scrapbook_routing_architecture.jpg"
---

모던 웹 애플리케이션에서 모달(Modal)은 사용자 경험을 결정짓는 핵심 요소입니다.  
사용자가 특정 숏폼 영상이나 채널 상세 정보를 클릭했을 때, 새 페이지로 튕겨 나가지 않고 현재 대시보드 위에서 상세 정보를 오버레이로 보여주는 방식은 작업 흐름을 유지하는 데 탁월합니다.  

하지만 단순한 React `useState(isOpen)` 방식의 모달은 브라우저의 '뒤로 가기' 버튼을 누르면 모달만 닫히는 것이 아니라 아예 이전 사이트로 이탈해 버리는 치명적인 결함을 낳습니다.  
이를 극복하기 위해 도입한 **URL 기반 모달(URL-Driven Modal)** 아키텍처와, 그 과정에서 마주했던 교묘한 버그들을 해결한 과정을 정리합니다.  

## URL-Driven 모달의 원리와 장점

우리가 설계한 모달 아키텍처의 핵심은 **"모든 모달의 상태는 오직 URL 쿼리 파라미터(`?modal=shorts_player&videoId=xyz`)가 결정한다"**는 원칙이었습니다.  

이 방식은 다음과 같은 강력한 이점을 제공합니다.  
1. **공유 가능한 딥링크(Deep Linking)**: 특정 영상 분석 모달이 열린 상태의 URL을 그대로 복사해 공유할 수 있습니다.  
2. **자연스러운 브라우저 히스토리 지원**: 뒤로 가기(Back) 버튼을 누르면 모달만 닫히고 원래 대시보드 상태로 부드럽게 복귀합니다.  
3. **단일 모달 컨트롤러**: 전역 `ModalController` 컴포넌트 하나가 URL 파라미터를 구독하고 알맞은 모달을 조건부 렌더링합니다.  

## 모달 겹침과 좀비 URL 파라미터(Zombie Param)의 습격

그러나 실제 운영 환경에서 예상치 못한 엣지 케이스 버그가 터져 나왔습니다.  
쇼츠 플레이어 모달 안에서 '채널 상세 보기' 버튼을 클릭한 뒤 ESC 키를 눌러 모달을 닫았을 때, 화면에는 아무 모달도 없는데 URL에는 여전히 `?channelTitle=숏영드` 파라미터가 유령처럼 남아있는 현상이었습니다.  

더 심각한 것은, 사용자가 다른 채널의 영상을 클릭해도 이 잔존 파라미터가 렌더링 우선순위를 가로채며 계속 이전 채널의 정보를 노출하는 '좀비 데이터 오염'이 발생했다는 점입니다.  

| 버그 증상 | 근본 원인 | 해결 조치 |
|---|---|---|
| ESC 닫기 후 파라미터 잔존 | `useEffect` 내 `handleClose` 클로저의 의존성 배열 누락 (Stale Closure) | `useCallback` 메모이제이션 및 `searchParams`, `router` 의존성 주입 |
| 이전 채널명 고정 렌더링 | URL 파라미터가 DB 실제 데이터보다 높은 우선순위 점유 | SWR 데이터 최우선 렌더링으로 역전 + 라우팅 시 `params.delete()` 강제 집행 |
| 모달 이중 렌더링 | 인라인 모달 래퍼와 전역 컨트롤러의 중복 마운트 | 모든 모달 렌더링 책임을 `ModalController`로 단일화 |

```typescript
// Stale Closure를 방어하고 좀비 파라미터를 제거하는 모달 닫기 훅
export function useModalCloser() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const closeModal = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    // 등록된 모든 모달 관련 파라미터 일괄 청소
    params.delete('modal');
    params.delete('videoId');
    params.delete('channelId');
    params.delete('channelTitle');

    const newQuery = params.toString();
    const targetUrl = newQuery ? `${pathname}?${newQuery}` : pathname;
    router.replace(targetUrl, { scroll: false });
  }, [router, searchParams, pathname]);

  return { closeModal };
}
```

## 구조적 버원칙의 타협에서 발생한다

이 디버깅 경험은 상태 관리가 URL과 결합할 때 얼마나 엄격한 생명주기 관리가 필요한지를 일깨워주었습니다.  
편의를 위해 컴포넌트 내부에서 URL 파라미터를 임의로 주입하던 레거시 코드를 모두 걷어내고, SWR을 통한 DB 실제 데이터 직접 바인딩으로 데이터 흐름을 정돈했습니다.  

URL-Driven 아키텍처는 강력하지만, 클로저의 상태 동기화와 파라미터 정리 규약이 전제되지 않으면 시스템을 복잡하게 만듭니다.  
우아한 사용자 경험은 보이지 않는 라우팅 파이프라인의 엄격함에서 완성됩니다.  

---

**참고 자료:**
- [Next.js Documentation — Routing: Query Parameters and Shallow Routing](https://nextjs.org/docs/app/building-your-application/routing)
- [React Documentation — Synchronizing with Effects and Preventing Stale Closures](https://react.dev/learn/synchronizing-with-effects)
- [Nielsen Norman Group — Modal vs Modeless Dialog Design Guidelines](https://www.nngroup.com/articles/modal-nonmodal-dialog/)
