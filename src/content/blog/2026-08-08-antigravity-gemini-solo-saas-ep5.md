---
title: "Supabase 500MB 무료 티어 한계 극복기: PostgreSQL Dead Tuples와 VACUUM 자동화"
description: "DELETE 쿼리만으로는 줄어들지 않는 PostgreSQL 디스크 공간의 원리를 분석하고, 7일 슬라이딩 윈도우와 cronJobs.js 자동 VACUUM 파이프라인으로 500MB DB를 무결점으로 유지한 엔지니어링 기록입니다."
category: "devlog"
pubDate: "2026-08-08T14:00:00+09:00"
heroImage: "../../assets/images/blog/ep5_servers.jpg"
---

1인 소프트웨어 엔지니어에게 인프라 비용 최적화는 생존을 위한 필수 과제입니다.  
수십만 건의 유튜브 숏폼 메트릭을 매일 수집하는 데이터 파이프라인을 운영하면서, Supabase 무료 티어의 500MB 디스크 용량 한계는 언제 터질지 모르는 가장 큰 위험 요인이었습니다.  

많은 개발자들이 데이터베이스에서 `DELETE FROM table WHERE date < ...` 쿼리를 실행하면 디스크 용량이 즉시 확보될 것이라 생각합니다.  
하지만 실제 프로덕션 환경에서 수만 건의 레코드를 삭제했음에도 불구하고 DB 용량 게이지는 단 1MB도 줄어들지 않았습니다.  
PostgreSQL의 MVCC(다중 버전 동시성 제어) 엔진이 작동하는 원리를 이해하지 못해 겪었던 위기와 이를 해결한 자동화 아키텍처를 공유합니다.  

## DELETE 쿼리의 함정과 데드 튜플(Dead Tuples)

PostgreSQL은 데이터 수정과 삭제 시 성능을 유지하기 위해 기존 디스크 블록을 즉시 비우지 않습니다.  
레코드를 삭제하면 해당 행을 '사용하지 않음(Dead Tuple)'으로 마킹만 해두고 물리적 디스크 공간은 그대로 점유합니다.  

1MIN DRAMA 벤치마킹을 위해 수집하던 `video_daily_stats` 테이블에서 29,689건의 레코드를 DELETE 쿼리로 지웠지만, 디스크 사용량은 여전히 400MB(80%)에 머물러 있었습니다.  
이 데드 튜플들을 청소하고 공간을 OS 및 데이터베이스에 실제로 반환하려면 반드시 **`VACUUM`** 명령이 수행되어야 합니다.  

| 정리 방식 | 물리 디스크 반환 여부 | 테이블 락(Lock) 영향 | 적용 적합성 |
|---|---|---|---|
| 단순 `DELETE` 실행 | 반환 안 됨 (Dead Tuple 누적) | 락 없음 | 데이터 삭제 플래그 처리 |
| 표준 `VACUUM table` | 여유 공간 재사용 가능 (OS 반환은 제한적) | 서비스 무중단 (비동기 처리) | **일일 정기 유지보수 (권장)** |
| `VACUUM FULL table` | 디스크 공간 100% 즉시 반환 | **테이블 전체 배타적 락 (서비스 정지)** | 긴급 수동 작업 시에만 제한적 사용 |

## 주의: `VACUUM FULL`의 함정과 락(Lock) 리스크

디스크 공간을 완전히 반환하겠다는 생각으로 `VACUUM FULL`을 일상적인 크론잡에 넣는 것은 매우 위험합니다.  
`VACUUM FULL`은 실행되는 동안 테이블 전체에 배타적 락(Exclusive Lock)을 걸어 모든 읽기/쓰기 쿼리를 중단시키며, 작업 중 원본 테이블 크기만큼의 임시 추가 디스크 용량을 요구합니다.  
500MB 한도에 아슬아슬하게 걸려 있는 상황에서 `VACUUM FULL`을 돌리면 오히려 용량 부족으로 작업이 실패하고 서비스가 멈추는 대참사가 일어납니다.  

## 7일 슬라이딩 윈도우와 자정 크론잡 자동화

우리는 안전한 표준 `VACUUM`과 7일 슬라이딩 윈도우 보존 정책을 결합한 백엔드 자동화 파이프라인을 구축했습니다.  

```javascript
// services/cronJobs.js 내부의 데이터 자정 청소 루틴
async function pruneDatabase() {
  const client = await pool.connect();
  try {
    console.log("[DB Prune] 7일 경과 통계 데이터 정리 시작...");
    
    // 1. 7일이 지난 일일 통계 레코드 삭제
    await client.query(`
      DELETE FROM video_daily_stats 
      WHERE record_date < CURRENT_DATE - INTERVAL '7 days'
    `);
    
    // 2. 표준 VACUUM을 통한 공간 회수 (무중단)
    await client.query(`VACUUM video_daily_stats`);
    await client.query(`VACUUM channel_daily_stats`);
    
    console.log("[DB Prune] 데이터베이스 정기 청소 및 공간 회수 완료");
  } catch (err) {
    console.error("[DB Prune Error] 데이터베이스 청소 실패:", err);
  } finally {
    client.release();
  }
}
```

이 루틴을 매일 새벽 3시에 자동 실행하도록 등록한 이후, 데이터베이스 용량은 수십만 건의 트래픽 데이터 수집에도 불구하고 **330MB~350MB의 안정적인 평형 상태**를 유지하고 있습니다.  

한정된 자원을 다루는 엔지니어링의 본질은 무한정 리소스를 증설하는 것이 아니라, 시스템이 스스로를 정화하는 순환 고리를 만드는 데 있습니다.  

---

**참고 자료:**
- [PostgreSQL Official Documentation — Routine Vacuuming and Dead Tuples Management](https://www.postgresql.org/docs/current/routine-vacuuming.html)
- [Supabase Documentation — Database Optimization and Storage Best Practices](https://supabase.com/docs/guides/database/managing-storage)
- [Martin Fowler — Database Administration and Scheduled Maintenance](https://martinfowler.com/articles/evodb.html)
