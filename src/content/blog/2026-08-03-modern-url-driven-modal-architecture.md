---
title: "모달 지옥 탈출기: React 로컬 State를 버리고 URL을 믿기로 한 날"
description: "두 개의 모달이 겹치고, 뒤로 가기가 먹히지 않고, 공유 링크가 작동하지 않는 '모달 지옥'을 100% URL 파라미터 기반 아키텍처로 완전히 해결한 실전 리팩토링 과정을 공개합니다."
category: "devlog"
pubDate: "2026-08-03T05:40:00Z"
heroImage: "../../assets/scrapbook_routing_architecture.jpg"
---

"채널 상세 화면에서 X 버튼을 눌렀는데, 이미 닫힌 줄 알았던 이전 모달이 다시 뜨는 버그가 있어요."  

이 메시지를 받았을 때, 저는 처음에 단순한 브라우저 히스토리 문제라고 생각했습니다.  
하지만 2시간의 디버깅 끝에 드러난 진실은 훨씬 충격적이었습니다.  
**화면에는 실제로 모달이 두 겹으로 떠있었던 것입니다.**  

이것은 단순한 버그가 아니었습니다.  
Lumen Insights V2의 모달 시스템 전체가 잘못 설계되어 있었다는 구조적 결함의 증거였습니다.  

## 문제의 진단: 로컬 State라는 시한폭탄

초기 개발 당시, 저는 각 컴포넌트 안에서 독립적으로 모달을 여는 방식을 선택했습니다.  
대시보드의 트렌드 위젯이 클릭되면, 위젯 내부의 `useState`가 모달을 열고, 그 모달 안에서 다른 항목을 클릭하면 `router.push`로 전역 URL이 변경되면서 최상단 `ModalController`가 또 다른 모달을 생성했습니다.  

결과적으로 DOM에는 두 개의 모달이 동시에 존재했습니다.  
하나는 로컬 State가 제어하는 모달, 하나는 URL이 제어하는 모달.  
X 버튼을 눌러 URL을 초기화해도, 로컬 State가 관리하는 모달은 `isOpen: true` 상태 그대로 남아있었던 것입니다.  

여기서 더 심각한 파생 문제들이 연쇄적으로 따라왔습니다.  

| 문제 | 원인 | 사용자 경험 |
|---|---|---|
| 모달 중첩(Stacking) | 로컬 + 전역 모달 동시 렌더링 | 화면이 이상하게 겹쳐 보임 |
| 뒤로가기 오작동 | URL이 모달 상태를 모름 | 모달 대신 이전 페이지로 튕겨남 |
| 공유 불가 | URL에 상태 정보 없음 | 링크 공유 시 빈 화면 |
| ShortsPlayer iframe 충돌 | 여러 iframe 동시 렌더링 | 영상 재생 끊김 |

특히 ShortsPlayer 문제는 치명적이었습니다.  
채널 상세 모달 안에 있는 쇼츠 카드들이 백그라운드에서 렌더링되면서 `<iframe>`을 생성하고 있었고, YouTube iframe이 동시에 여러 개 존재하면 브라우저가 미디어 스트림을 정상적으로 처리하지 못해 재생이 끊기는 현상이 발생했습니다.  

## 해결책: 단일 진실의 원천(Single Source of Truth) - URL

진단이 끝나면 처방은 명확해집니다.  
**모달의 상태를 관리하는 주체를 단 하나로 통일해야 합니다.**  

저는 브라우저의 URL을 그 유일한 주체로 선택했습니다.  
이유는 단순합니다. URL은 브라우저의 네이티브 기능이고, 뒤로가기, 앞으로가기, 복사, 공유를 이미 완벽하게 지원하는 검증된 상태 관리자이기 때문입니다.  

리팩토링의 핵심 규칙은 두 가지였습니다.  

**규칙 1**: 사이트의 어느 곳에서든 영상이나 채널을 클릭하면, 모달을 직접 열지 않고 **URL 파라미터만 변경**한다.  
```
클릭 → router.push('?videoId=xxx')  (모달 직접 렌더링 금지)
```

**규칙 2**: 화면에 모달을 그리는 역할은 최상단의 `ModalController` 컴포넌트 **단 하나**만 담당한다.  
```
URL 변화 감지 → ModalController가 렌더링 결정 (분산 금지)
```

그리고 모달 간의 우선순위를 명확히 하기 위해 **3단계 Tier 시스템**을 도입했습니다.  

```
Tier 1 (최상위): ShortsPlayerModal
  → 열리면 Tier 2, 3 완전 언마운트

Tier 2: ChannelActionModal
  → 열리면 Tier 3 완전 언마운트

Tier 3: MediaDetailModal + GlobalSearchModal
  → 공존 가능, 상태 보존
```

이 구조에서는 절대로 두 개의 모달이 같은 Tier에서 동시에 렌더링되지 않습니다.  
ShortsPlayer가 열리는 순간, 그 아래의 모든 `<iframe>`은 DOM에서 즉시 제거됩니다.  

## 예상치 못한 부작용: 검색 상태 유실 문제

새 아키텍처가 완성된 직후, 또 다른 문제가 보고되었습니다.  
"검색 결과에서 영상을 클릭해서 플레이어를 열었다가 닫으면, 방금 검색한 결과가 다 사라져요."  

Tier 시스템에 따라 ShortsPlayer(Tier 1)가 열리면 GlobalSearchModal(Tier 3)이 DOM에서 언마운트됩니다.  
검색 결과는 컴포넌트의 로컬 `useState`에 저장되어 있었기 때문에, 언마운트와 동시에 사라져버린 것입니다.  

해결책은 우아했습니다.  
검색창에서 다른 모달로 진입할 때 URL에 `&from=search` 꼬리표를 달아주도록 설계했습니다.  
`ModalController`는 이 꼬리표가 존재하면 Tier 1이 열려있더라도 검색 모달을 완전히 언마운트하지 않고, CSS의 `display: none`으로 **화면에서만 숨기도록** 처리했습니다.  

사용자가 플레이어를 닫으면, 검색 모달이 `display: block`으로 돌아오면서 모든 검색 결과가 그대로 살아있는 상태로 복원됩니다.  
0.1초의 지연도, 어떤 로딩도 없이.  

이 경험을 통해 하나의 원칙이 확립되었습니다.  
**아키텍처는 완성되는 순간이 아니라, 엣지 케이스를 하나씩 해결하면서 진화한다.**  

URL 기반 모달 시스템은 Lumen Insights의 핵심 UX 자산이 되었습니다.  
어느 화면에서든 현재 보고 있는 영상이나 채널의 URL을 복사해서 누군가에게 보내면, 그 사람도 정확히 동일한 화면을 바로 볼 수 있습니다.  
이것은 추가 개발 비용 없이 아키텍처 설계에서 자연스럽게 얻어진 딥링킹(Deep Linking) 기능입니다.  
뼈대를 바르게 세우면, 원하지 않았던 혜택까지 따라옵니다.

---

**참고 자료:**
- [React Official Documentation — State Management and URL Synchronization](https://react.dev/reference/react/useState)
- [MDN Web Docs — Manipulating the Browser History and URL State](https://developer.mozilla.org/en-US/docs/Web/API/History_API)
- [W3C WAI-ARIA — Accessible Dialog (Modal) Architecture Standards](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
