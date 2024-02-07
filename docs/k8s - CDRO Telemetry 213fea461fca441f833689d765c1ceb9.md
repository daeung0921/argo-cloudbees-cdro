# k8s - CDRO Telemetry

Agent 죽는 현상 , Server 관련 Job Pending 현상 관련하여 원인 규명을 위하여 K8S 환경에서 추적을 위한 환경 구성이 필요합니다. 관련 이슈는 아래와 같습니다.

- cd-flow-agent replica 2 개 이상일 때 job abort
- cb-fow-server replica 2 개 이상일 때 job pending

---

**K8S 환경에서 CDRO 텔레메트리** 

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled.png)

- 로깅
    - CDRO 로그 모니터링을 위해서는  server, agent, repository, zookeeper, devops-insight 서버의 log 에 대한 추적이 필요합니다.
    - 모비스에서 이미 Elastic 스택을 사용중인 것으로 보이므로 filebeat 를 통해 추적이 가능합니다.
- 메트릭
    - Metricbeat 의 kubernetes 모듈을 통해 Elastic 스택에서 확인이 가능해 보입니다.
        - [kube_state_metrics](https://medium.com/finda-tech/kube-state-metrics%EC%97%90-%EB%8C%80%ED%95%B4%EC%84%9C-1303b10fb8f8) 설치가 필요합니다.
        - metricbeat.values.yaml 에 [kubernetes 모듈](https://www.elastic.co/guide/en/beats/metricbeat/current/metricbeat-module-kubernetes.html) 구성이 필요합니다.

---

**k8s 메트릭 확인 및 이벤트 로깅**

 

저는 테스트로 metricbeat 를 사용하여 구성할 예정이고 구성을 위해 관련 도큐먼트를 확인중에 있습니다.  현재 구성은 아래와 같고 아직 kubernetes module 사용 방법에 대해 파악중입니다.

- kube_state_metrics 설치 참고 →  [소스](https://github.com/daeung0921/argo-cloudbees-cdro/blob/main/kube-state-metrics.yaml)
- metricbeat 의 values.yaml 참고 → [소스](https://github.com/daeung0921/argo-cloudbees-cdro/blob/main/es-metricbeat-value.yaml)

**`결과확인`**

Observability →  Metrics

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%201.png)

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%202.png)

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%203.png)

---

**cdro 로깅** 

 ****

제가 작성한 filebeat 의 values.yaml 은 [소스](https://github.com/daeung0921/argo-cloudbees-cdro/blob/main/es-filebeat-value.yaml)와 같고 아직 zookeeper 와 insight 서버 로깅은 부분은 아직 작업 진행중입니다.

[https://kb.idtplateer.com:5601/](https://kb.idtplateer.com:5601/)  (admin/changeme) 로 접근 가능합니다.

**`로그형태`** 

Flow 에서 관리되는 로그 형태 관련하여 확인할 수 있는 [레퍼런스](https://docs.cloudbees.com/docs/cloudbees-cd-kb/latest/cloudbees-cd-kb/kbec-00173-default-locations-and-use-scenarios-for-flow-log-files) 문서의 하단에 로그 형태를 확인하실 수 있습니다.

**`로그파싱`** 

[autodiscover 의 kubernetes provider](https://www.elastic.co/guide/en/beats/filebeat/7.17/configuration-autodiscover.html) 를 사용하면 컨테이너 로그를 검색하여 정규 표현식으로 필터링한 결과를 Elasticsearch 로 인덱스를 만들어 보낼 수 있습니다. 

**`멀티라인`** 

autodiscover 멀티라인 관련하여 사용하는 옵션은 `negate=true, match=after` 인데 이 옵션을 사용하면 아래와 같이 메시지를 파싱합니다.

```go
true   2024-02-06T21:58:25.282 | INFO  | qtp1444930323-2474             |  ...

**true   2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |          |                                      |                                                                             | ApiServletImpl                 | servletRequestContext[id=5535,on 127.0.0.1:8443,from 10.0.2.84:48398,bytes=214]:
false   <?xml version="1.0" encoding="UTF-8"?>
false   <requests version="2.2" timeout="5">
false     <request requestId="1">
false       <getServerStatus>
false         <serverStateOnly>1</serverStateOnly>
false       </getServerStatus>
false     </request>
false   </requests>**

true   2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |      
```

관련하여 Elasic 메뉴얼에서 [멀티라인 처리](https://www.elastic.co/guide/en/beats/filebeat/current/multiline-examples.html) 정보를 확인해 보실수 있습니다.

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%204.png)

**`로그 파싱 테스트`** 

filebeat 를 통해 로그 파싱시에는 go 의 정규 표현식를 사용하게 되는데 [https://go.dev/play/](https://go.dev/play/) 에서 간단히 코드를 통해 사전 테스트 가능합니다. 

단순히 정규 표현식만 테스트 하는 경우는 [https://www.regextester.com/97259](https://www.regextester.com/97259) 사이트에서 테스트 할 수 있습니다.

```go
package main

import (
	"fmt"
	"regexp"
	"strings"
)

var negate = false
var pattern = `^\d\d\d\d(-\d\d){2}T\d\d(:\d\d){2}\.\d\d\d`
var content = `
2024-02-06T21:57:56.073 | INFO  | messageTrigger                 |          |                                      | messageTrigger                                                              | HibernateStatistics            | 1 queries executed in 1 (ms)
2024-02-06T21:57:56.073 | INFO  | messageTrigger                 |          |                                      | messageTrigger                                                              | HibernateStatistics            | Longest running query: FROM     Message WHERE    completed = :completed          AND processed = :processed ORDER BY createDate.time ASC; executed in 1 (ms)
2024-02-06T21:57:56.073 | DEBUG | messageTrigger                 |          |                                      | messageTrigger                                                              | OperationTimingAspect          | messageTrigger.perform: Thread CPU Usage:0%, Duration:3 ms
2024-02-06T21:57:56.073 | DEBUG | messageTrigger                 |          |                                      |                                                                             | DeadlineTriggerSupport         | operationDeadlineTrigger[name=messageTrigger]: accepted new deadline 2024-02-06T21:58:56.072
2024-02-06T21:58:00.498 | DEBUG | HikariCP-001                   |          |                                      |                                                                             | HikariPool                     | CloudBees CD - Before cleanup stats (total=7, active=1, idle=6, waiting=0)
2024-02-06T21:58:00.498 | DEBUG | HikariCP-001                   |          |                                      |                                                                             | HikariPool                     | CloudBees CD - After cleanup  stats (total=7, active=1, idle=6, waiting=0)
2024-02-06T21:58:00.498 | DEBUG | HikariCP-001                   |          |                                      |                                                                             | HikariPool                     | CloudBees CD - Fill pool skipped, pool has sufficient level or currently being filled (queueDepth=0).
2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |          |                                      | findSession                                                                 | HibernateStatisticsAspect      | findSession: queries: 0 entityInserts: 0 entityFetches: 0 entityLoads: 0 entityUpdates: 0 entityDeletes: 0 collectionFetches: 0 collectionLoads: 0 flushes: 0 transactions: 1 optimisticFailures: 0
2024-02-06T21:58:25.282 | INFO  | qtp1444930323-2474             |          |                                      | findSession                                                                 | HibernateStatistics            | 0 queries executed in 0 (ms)
2024-02-06T21:58:25.282 | INFO  | qtp1444930323-2474             |          |                                      | findSession                                                                 | HibernateStatistics            | Longest running query: null; executed in 0 (ms)
2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |          |                                      | findSession                                                                 | OperationTimingAspect          | findSession.perform: Thread CPU Usage:0%, Duration:1 ms
2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |          |                                      |                                                                             | ApiServletImpl                 | servletRequestContext[id=5535,on 127.0.0.1:8443,from 10.0.2.84:48398,bytes=214]:
<?xml version="1.0" encoding="UTF-8"?>
<requests version="2.2" timeout="5">
  <request requestId="1">
    <getServerStatus>
      <serverStateOnly>1</serverStateOnly>
    </getServerStatus>
  </request>
</requests>
2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |          |                                      |                                                                             | ExecuteQueueImpl               | operationCallable[context[op=dispatchApi#0,id=35210],id=13929] submitted to executeQueue[name=Dispatch,serviceState=running,threads=4,available=4,queued=0]
2024-02-06T21:58:25.283 | DEBUG | Dispatch-002                   |    35210 |                                      | dispatchApi#0 findSession                                                   | HibernateStatisticsAspect      | findSession: queries: 0 entityInserts: 0 entityFetches: 0 entityLoads: 0 entityUpdates: 0 entityDeletes: 0 collectionFetches: 0 collectionLoads: 0 flushes: 0 transactions: 1 optimisticFailures: 0
2024-02-06T21:58:25.283 | INFO  | Dispatch-002                   |    35210 |                                      | dispatchApi#0 findSession                                                   | HibernateStatistics            | 0 queries executed in 0 (ms)
2024-02-06T21:58:25.283 | INFO  | Dispatch-002                   |    35210 |                                      | dispatchApi#0 findSession                                                   | HibernateStatistics            | Longest running query: null; executed in 0 (ms)
2024-02-06T21:58:25.283 | DEBUG | Dispatch-002                   |    35210 |                                      | dispatchApi#0                                                               | ExecuteQueueImpl               | operationCallable[context[op=getServerStatus#,id=35212],id=13930] submitted to executeQueue[name=Api,serviceState=running,threads=6,available=6,queued=0]
2024-02-06T21:58:25.286 | DEBUG | Api-017                        |    35212 |                                      | getServerStatus                                                             | HibernateStatisticsAspect      | getServerStatus: queries: 1 entityInserts: 0 entityFetches: 0 entityLoads: 1 entityUpdates: 0 entityDeletes: 0 collectionFetches: 0 collectionLoads: 0 flushes: 0 transactions: 1 optimisticFailures: 0
2024-02-06T21:58:25.286 | INFO  | Api-017                        |    35212 |                                      | getServerStatus                                                             | HibernateStatistics            | 1 queries executed in 1 (ms)
2024-02-06T21:58:25.286 | INFO  | Api-017                        |    35212 |                                      | getServerStatus                                                             | HibernateStatistics            | Longest running query: FROM  SystemObject WHERE name = :name; executed in 1 (ms)
2024-02-06T21:58:25.286 | DEBUG | Api-017                        |    35212 |                                      | getServerStatus                                                             | OperationTimingAspect          | getServerStatus.perform: Thread CPU Usage:0%, Duration:3 ms
2024-02-06T21:58:25.286 | DEBUG | Api-017                        |    35212 |                                      | getServerStatus                                                             | XmlApiRequestHandler           | Response for id=5535:
<?xml version="1.0" encoding="UTF-8"?>
<responses version="2.3" dispatchId="5535" nodeId="10.0.2.84">
  <response requestId="1" nodeId="10.0.2.84">
    <serverState>running</serverState>
  </response>
</responses>
`

func main() {
	regex, err := regexp.Compile(pattern)
	if err != nil {
		fmt.Println("Failed to compile pattern: ", err)
	}
	lines := strings.Split(content, "\n")
	fmt.Printf("matches\n")
	for _, line := range lines {
		matches := regex.MatchString(line)
		if negate {
			matches = !matches
		}
		fmt.Printf("%v   %v\n", matches, line)
	}
}

// ----------------------------------------------------------------
// 응답 
// ----------------------------------------------------------------
matches 
true   2024-02-06T21:57:56.073 | INFO  | messageTrigger                 |          |                                      | messageTrigger                                                              | HibernateStatistics            | 1 queries executed in 1 (ms)
true   2024-02-06T21:57:56.073 | INFO  | messageTrigger                 |          |                                      | messageTrigger                                                              | HibernateStatistics            | Longest running query: FROM     Message WHERE    completed = :completed          AND processed = :processed ORDER BY createDate.time ASC; executed in 1 (ms)
true   2024-02-06T21:57:56.073 | DEBUG | messageTrigger                 |          |                                      | messageTrigger                                                              | OperationTimingAspect          | messageTrigger.perform: Thread CPU Usage:0%, Duration:3 ms
true   2024-02-06T21:57:56.073 | DEBUG | messageTrigger                 |          |                                      |                                                                             | DeadlineTriggerSupport         | operationDeadlineTrigger[name=messageTrigger]: accepted new deadline 2024-02-06T21:58:56.072
true   2024-02-06T21:58:00.498 | DEBUG | HikariCP-001                   |          |                                      |                                                                             | HikariPool                     | CloudBees CD - Before cleanup stats (total=7, active=1, idle=6, waiting=0)
true   2024-02-06T21:58:00.498 | DEBUG | HikariCP-001                   |          |                                      |                                                                             | HikariPool                     | CloudBees CD - After cleanup  stats (total=7, active=1, idle=6, waiting=0)
true   2024-02-06T21:58:00.498 | DEBUG | HikariCP-001                   |          |                                      |                                                                             | HikariPool                     | CloudBees CD - Fill pool skipped, pool has sufficient level or currently being filled (queueDepth=0).
true   2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |          |                                      | findSession                                                                 | HibernateStatisticsAspect      | findSession: queries: 0 entityInserts: 0 entityFetches: 0 entityLoads: 0 entityUpdates: 0 entityDeletes: 0 collectionFetches: 0 collectionLoads: 0 flushes: 0 transactions: 1 optimisticFailures: 0
true   2024-02-06T21:58:25.282 | INFO  | qtp1444930323-2474             |          |                                      | findSession                                                                 | HibernateStatistics            | 0 queries executed in 0 (ms)
true   2024-02-06T21:58:25.282 | INFO  | qtp1444930323-2474             |          |                                      | findSession                                                                 | HibernateStatistics            | Longest running query: null; executed in 0 (ms)
true   2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |          |                                      | findSession                                                                 | OperationTimingAspect          | findSession.perform: Thread CPU Usage:0%, Duration:1 ms
**true   2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |          |                                      |                                                                             | ApiServletImpl                 | servletRequestContext[id=5535,on 127.0.0.1:8443,from 10.0.2.84:48398,bytes=214]:
false   <?xml version="1.0" encoding="UTF-8"?>
false   <requests version="2.2" timeout="5">
false     <request requestId="1">
false       <getServerStatus>
false         <serverStateOnly>1</serverStateOnly>
false       </getServerStatus>
false     </request>
false   </requests>**
true   2024-02-06T21:58:25.282 | DEBUG | qtp1444930323-2474             |          |                                      |                                                                             | ExecuteQueueImpl               | operationCallable[context[op=dispatchApi#0,id=35210],id=13929] submitted to executeQueue[name=Dispatch,serviceState=running,threads=4,available=4,queued=0]
true   2024-02-06T21:58:25.283 | DEBUG | Dispatch-002                   |    35210 |                                      | dispatchApi#0 findSession                                                   | HibernateStatisticsAspect      | findSession: queries: 0 entityInserts: 0 entityFetches: 0 entityLoads: 0 entityUpdates: 0 entityDeletes: 0 collectionFetches: 0 collectionLoads: 0 flushes: 0 transactions: 1 optimisticFailures: 0
true   2024-02-06T21:58:25.283 | INFO  | Dispatch-002                   |    35210 |                                      | dispatchApi#0 findSession                                                   | HibernateStatistics            | 0 queries executed in 0 (ms)
true   2024-02-06T21:58:25.283 | INFO  | Dispatch-002                   |    35210 |                                      | dispatchApi#0 findSession                                                   | HibernateStatistics            | Longest running query: null; executed in 0 (ms)
true   2024-02-06T21:58:25.283 | DEBUG | Dispatch-002                   |    35210 |                                      | dispatchApi#0                                                               | ExecuteQueueImpl               | operationCallable[context[op=getServerStatus#,id=35212],id=13930] submitted to executeQueue[name=Api,serviceState=running,threads=6,available=6,queued=0]
true   2024-02-06T21:58:25.286 | DEBUG | Api-017                        |    35212 |                                      | getServerStatus                                                             | HibernateStatisticsAspect      | getServerStatus: queries: 1 entityInserts: 0 entityFetches: 0 entityLoads: 1 entityUpdates: 0 entityDeletes: 0 collectionFetches: 0 collectionLoads: 0 flushes: 0 transactions: 1 optimisticFailures: 0
true   2024-02-06T21:58:25.286 | INFO  | Api-017                        |    35212 |                                      | getServerStatus                                                             | HibernateStatistics            | 1 queries executed in 1 (ms)
true   2024-02-06T21:58:25.286 | INFO  | Api-017                        |    35212 |                                      | getServerStatus                                                             | HibernateStatistics            | Longest running query: FROM  SystemObject WHERE name = :name; executed in 1 (ms)
true   2024-02-06T21:58:25.286 | DEBUG | Api-017                        |    35212 |                                      | getServerStatus                                                             | OperationTimingAspect          | getServerStatus.perform: Thread CPU Usage:0%, Duration:3 ms
true   2024-02-06T21:58:25.286 | DEBUG | Api-017                        |    35212 |                                      | getServerStatus                                                             | XmlApiRequestHandler           | Response for id=5535:
false   <?xml version="1.0" encoding="UTF-8"?>
false   <responses version="2.3" dispatchId="5535" nodeId="10.0.2.84">
false     <response requestId="1" nodeId="10.0.2.84">
false       <serverState>running</serverState>
false     </response>
false   </responses>
false
```

**`Logging 처리 확인`** 

결과는 간단히 Devtools 에서 조회하실수 있습니다.

```bash
GET _cat/indices
 
GET /cbf-server-*/_search
{
  "query": {
    "match_all": {}  
  },
  "_source": ["log"]  
}

# log 구성부 확인
GET /cbf-web-*/_search
{
  "query": {
    "match_all": {}  
  },
  "_source": ["log"]  
}

# GET /cbf-web-*/_search 응답
{
  "took" : 1,
  "timed_out" : false,
  "_shards" : {
    "total" : 1,
    "successful" : 1,
    "skipped" : 0,
    "failed" : 0
  },
  "hits" : {
    "total" : {
      "value" : 8864,
      "relation" : "eq"
    },
    "max_score" : 1.0,
    "hits" : [
      {
        "_index" : "cbf-web-2024.02.06",
        "_type" : "_doc",
        "_id" : "UZ_Ff40BtGY2GINZZc_o",
        "_score" : 1.0,
        "_source" : {
          "log" : {
            "file" : {
              "path" : "/var/log/containers/flow-web-57fc95f855-zb94t_cdro_flow-web-dd2a367d6bcf26e289010d31330c1a7570b46617bcb5c152f6363c499a9e21ef.log"
            },
            "address" : "10.0.102.200",
            "offset" : 2220240,
            "level" : "INFO",
            "message" : "\"GET /auth/ HTTP/1.1\" 200 178556 24937 - 7f89d8005b80",
            "user" : "-",
            "timestamp" : "2024-02-06 18:54:13.511262"
          }
        }
      },
...

GET /cbf-repository-*/_search
{
  "query": {
    "match_all": {}  
  },
  "_source": ["log"]  
}

 
# 맵핑정보 확인
GET /cbf-server-*/_mapping
GET /cbf-web-*/_mapping
GET /cbf-repository-*/_mapping
```

구성후 Kibana 에서 Index Pattern 을 만들어 결과를 Anlytics→Discover 를 통해 확인하실수 있습니다. 

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%205.png)

Management→Index managements 에서 인덱스 맵핑이나 설정 정보를 확인할 수 있습니다.

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%206.png)

---

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%207.png)
