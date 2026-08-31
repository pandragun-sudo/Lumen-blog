---
title: "1인 창업가의 기술 부채 전수 조사: 60.5MB의 유령 인덱스를 찾아낸 데이터베이스 감사"
description: "Supabase 500MB 디스크 제한 압박 속에서 중복 인덱스 4개를 발굴하고, 슬라이딩 윈도우 보존 정책으로 60.5MB를 즉각 회수한 데이터베이스 리팩토링 실전기를 공유합니다."
category: "devlog"
pubDate: "2026-07-30T14:00:00+09:00"
heroImage: "../../assets/tech_debt_audit_cover_1785403165549.jpg"
---

1인 소프트웨어 개발자에게 '기술 부채(Technical Debt)'는 소리 없이 다가오는 시한폭탄과 같습니다.  
초기 개발 단계에서는 빠른 기능 완성이 최우선이기 때문에 데이터베이스 인덱스를 중복 생성하거나, 무제한 적재 쿼리를 방치하더라도 당장 눈앞의 기능은 문제없이 돌아갑니다.  

하지만 서비스가 운영 단계에 접어들고 수십만 건의 숏폼 통계 데이터가 누적되기 시작하면, 그동안 쌓아둔 기술 부채가 디스크 용량 초과와 쿼리 타임아웃이라는 가혹한 청구서로 돌아옵니다.  
Supabase 무료 티어의 500MB 디스크 한도에 근접했던 위기 상황에서, 시스템을 전수 감사하여 숨겨진 60.5MB의 낭비 공간을 회수했던 실제 엔지니어링 과정을 정리합니다.  

## 402MB(80.4%) 급증의 충격: 범인은 신규 테이블이 아니었다

매일 45,000여 개 채널의 일일 통계가 쌓이면서 데이터베이스 용량이 순식간에 402MB까지 치솟았습니다.  
처음에는 최근 신설한 `korean_upcoming_content`(방영 예정작) 테이블이 용량을 잡아먹고 있을 것이라 짐작했습니다.  

하지만 PostgreSQL 시스템 카탈로그 쿼리를 실행해 직접 측정한 결과는 완전히 달랐습니다.  
신규 예정작 테이블은 82건, 고작 **128 kB (0.12 MB, 전체의 0.03%)**에 불과했습니다.  
진짜 원인은 과거 개발 과정에서 무심코 생성했던 **완전 중복 인덱스(Duplicate Indexes)**들이었습니다.  

| 테이블명 | 삭제된 중복 인덱스명 | 낭비 용량 | 중복 원인 분석 |
|---|---|---|---|
| `channel_daily_stats` | `idx_channel_daily_stats_channel_date` | 26.0 MB | `UNIQUE(channel_id, record_date)` 제약 인덱스와 100% 일치 |
| `video_daily_stats` | `idx_vds_video_record` | 20.0 MB | `PRIMARY KEY(video_id, record_date)` 복합키와 100% 중복 |
| `channel_daily_stats` | `idx_cds_channel_id` | 7.2 MB | 복합키 prefix가 단일 조회를 완벽히 커버함 |
| `videos` | `idx_videos_video_id` | 7.5 MB | `PRIMARY KEY(video_id)` 인덱스와 동일 컬럼 중복 |

## 무중단 인덱스 회수와 서비스 무결성 검증

중복 인덱스를 삭제할 때는 서비스 가동 상태를 유지하는 무중단 작업이 필수적이었습니다.  
우리는 다음 절차를 거쳐 안전하게 디스크를 정리했습니다.  

1. **커버 제약 조건 검증**: 삭제하려는 단일 인덱스를 복합 기본키 인덱스가 실제로 커버하고 있는지 `EXPLAIN ANALYZE`로 쿼리 실행 계획을 사전에 검증했습니다.  
2. **동시성 삭제(`DROP INDEX CONCURRENTLY`)**: 락(Lock)으로 인한 서비스 멈춤을 방지하기 위해 백그라운드 삭제 명령을 수행했습니다.  
3. **공간 회수 결과**: 4개 중복 인덱스를 제거함으로써 DB 용량은 **402MB에서 341MB로 즉시 60.5MB가 경감**되었습니다.  

```sql
-- 실행 계획 검증 후 안전한 무중단 인덱스 정리
DROP INDEX CONCURRENTLY IF EXISTS idx_channel_daily_stats_channel_date;
DROP INDEX CONCURRENTLY IF EXISTS idx_vds_video_record;
DROP INDEX CONCURRENTLY IF EXISTS idx_cds_channel_id;
DROP INDEX CONCURRENTLY IF EXISTS idx_videos_video_id;
```

## 7일 슬라이딩 윈도우(Sliding Window) 보존 정책 확립

단순히 인덱스를 정리하는 것만으로는 영구적인 용량 방어가 불가능합니다.  
우리는 매일 새벽 3시 크론잡(`cronJobs.js`)에서 7일이 지난 일일 통계 데이터를 자동 정리하고, `VACUUM`을 실행하여 물리 디스크 공간을 즉시 OS에 반환하는 자동 보존 파이프라인을 완성했습니다.  

기술 부채는 방치하면 이자가 붙어 시스템을 무너뜨리지만, 정기적인 감사와 수치화된 데이터로 관리하면 가장 확실한 최적화의 기회가 됩니다.  
1인 빌더일수록 기능 추가보다 데이터베이스의 건강 상태를 먼저 살피는 규율이 필요합니다.  

---

**참고 자료:**
- [PostgreSQL Official Documentation — Indexing Best Practices and Maintenance](https://www.postgresql.org/docs/current/indexes.html)
- [Supabase Documentation — Managing Database Storage and Performance](https://supabase.com/docs/guides/database/managing-storage)
- [Martin Fowler — Technical Debt and Code Quality](https://martinfowler.com/bliki/TechnicalDebt.html)
