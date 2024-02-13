# k8s - CDRO Telemetry

Created: February 6, 2024 10:34 PM
Updated: February 13, 2024 12:39 PM

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

**테스트 서버**

- [https://kb.idtplateer.com:5601/](https://kb.idtplateer.com:5601/)
    - ID : admin
    - PW: changeme
- 소스
    - https://github.com/daeung0921/argo-cloudbees-cdro

---

**filebeat**

cdro server,agent,repository,web 을 한통에서 관리합니다.  

```yaml
$ helm repo add es  https://helm.elastic.co
$ helm repo update es
$ helm search repo es/filebeat  --versions 
 
#-------------------------------------------------------------------
# values/es-filebeat-value.yaml 파일에서 아래 부분에 모비스에 맞게 기입 
#-------------------------------------------------------------------
  extraEnvs:
    - name: ELASTICSEARCH_HOST # Elasticsearch 내부 서비스명
      value: "es-test"
    - name: ELASTICSEARCH_PORT # Elasticsearch 내부 사용포트
      value: "9200"       
    - name: ELASTICSEARCH_USERNAME # Elasticsearch 유저명
      value: "admin"
    - name: ELASTICSEARCH_PASSWORD # Elasticsearch 패스워드
      value: "changeme"
    - name: ELASTICSEARCH_PROTOCOL # Elasticsearch 내부 서비스 프로토콜
      value: "https"
    - name: ELASTICSEARCH_SSL_ENABLED # Elasticsearch 내부 서비스에 SSL 활성화 여부
      value: "true"            
    - name: KIBANA_HOST
      value: "es-kibana"
    - name: KIBANA_PORT
      value: "5601"
    - name: KIBANA_PROTOCOL
      value: "https"
    - name: KIBANA_SSL_ENABLED
      value: "true"
    - name: KUBE_LABLES_APP_FOR_SERVER # server 의 metadata.labels.app 에 설정한 값
      value: "flow-server"
    - name: KUBE_LABLES_APP_FOR_WEB # web server 의 metadata.labels.app 에 설정한 값
      value: "flow-web"
    - name: KUBE_LABLES_APP_FOR_REPO  # repository server 의 metadata.labels.app 에 설정한 값
      value: "flow-repository"
    - name: KUBE_LABLES_APP_FOR_AGENT # agent server 의 metadata.labels.app 에 설정한 값
      value: "cdro-remote-agent-flow-agent"
    - name: KUBE_TARGET_NAMESPACE
      value: "cdro"

#-------------------------------------------------------------------
# 설치
#-------------------------------------------------------------------
$ kubectl create ns cdro
$ helm install esfilebeat es/filebeat --namespace cdro --values  es-filebeat-value.yaml  --version 7.17.1
```

생성된 인덱스를 아래와 같이 확인할 수 있습니다.

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%201.png)

 discover 에서 log.message 로 필터링한 결과는 아래와 같습니다.

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%202.png)

---

**metricbeat**

k8s 매트릭을 수집하며 추가로 kubernetes 모듈에서 이벤트를 수집해줘서 특정 시간대의 이벤트를 확인할 수 있습니다.

[kube-state-metrics](https://github.com/kubernetes/kube-state-metrics) 가 필요합니다.

```yaml
# values/metricbeat.yaml 에서 아래 부분에 모비스에 맞게 수정
      env:
        - name: ELASTICSEARCH_HOST
          value: "es-test"
        - name: ELASTICSEARCH_PORT
          value: "9200"       
        - name: ELASTICSEARCH_USERNAME
          value: "admin"
        - name: ELASTICSEARCH_PASSWORD
          value: "changeme"
        - name: ELASTICSEARCH_PROTOCOL
          value: "https"
        - name: ELASTICSEARCH_SSL_ENABLED
          value: "true"            
        - name: KIBANA_HOST
          value: "es-kibana"
        - name: KIBANA_PORT
          value: "5601"
        - name: KIBANA_PROTOCOL
          value: "https"
        - name: KIBANA_SSL_ENABLED
          value: "true"

$ kubectl apply -f kube-state-metrics.yaml
$ kubectl create ns cdro
$ kubectl apply -f metricbeat.yaml -n cdro
```

매트릭 수집 결과는 아래와 같습니다.

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%203.png)

메트릭중 이벤트만 필터링해 보면 아래와 같습니다.

![Untitled](k8s%20-%20CDRO%20Telemetry%20213fea461fca441f833689d765c1ceb9/Untitled%204.png)

---

**정규표현식 테스트** 

filebeat 를 통해 로그 파싱시에는 go 의 정규 표현식를 사용하게 되는데 [https://go.dev/play/](https://go.dev/play/](https://go.dev/play/](https://go.dev/play/) 에서 간단히 코드를 통해 사전 테스트 가능합니다.  단순히 정규 표현식만 테스트 하는 경우는 [https://www.regextester.com/97259](https://www.regextester.com/97259)  사이트에서 테스트 할 수 있습니다.

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
```

결과는 아래와 같습니다.

```bash
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

---

**로깅 확인**

결과는 간단히 Devtools 에서 조회하실수 있습니다.

```bash
GET _cat/indices
 
# 서버 로그 매치
GET /cbf-server-*/_search
{
  "query": {
    "match_all": {}  
  },
  "_source": ["log"]  
}

# 웹서버 로그 매치
GET /cbf-web-*/_search
{
  "query": {
    "match_all": {}  
  },
  "_source": ["log"]  
}

# 레포지토리 로그 매치 
GET /cbf-repository-*/_search
{
  "query": {
    "match_all": {}  
  },
  "_source": ["log"]  
}
```

 맵핑정보 확인은 아래와 같습니다.

```bash
GET /cbf-server-*/_mapping
GET /cbf-web-*/_mapping
GET /cbf-repository-*/_mapping
```

 생성이 잘 된 것을 확인 하고 이후 Kibana 에서 Index Pattern 을 만들어 결과를 Anlytics→Discover 를 통해 확인하실수 있습니다.
