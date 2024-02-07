## Kustomized Helm Chart - Cloudbees CD Ro

- CDRO kustomized helm chart 를 ArgoCD 통해 EKS 에 배포하기 위한 예제 Repo 입니다.
- [아키텍처](https://docs.cloudbees.com/docs/cloudbees-cd/latest/horizontal-scalability/architecture)

### 단계 1 > 백업

업그레이드 전에 반드시 [백업](https://docs.bitnami.com/tutorials/backup-restore-data-mariadb-galera-kubernetes/)을 수행하세요:
- Velero를 사용하여 Persistent Volume을 백업합니다.
- 선택적으로, 수동으로 데이터베이스(DB) 백업을 수행합니다.

```bash
<doSometing>
```

### 단계 2 >  테스트 전 준비사항

- Cert Manager (첨부된 파일은 v1.5.4 버전 ) 
- ingress-nginx  (첨부된 파일은 v1.8.2 버전)
- kube-state-metrics (https://github.com/kubernetes/kube-state-metrics/tree/main)  
- EKS 를 사용하는 경우 additional_resources.yaml 의 storage class 의 fileSystemID 변경

```bash 
$ kubectl apply -f cert-manager.crds.yaml
$ kubectl apply -f cert-manager.yaml
$ kubectl apply -f ingress-nginx.yaml
$ kubectl apply -f kube-state-metrics.yaml  
```

### 단계 3 >  CloudBees CDRO 차트 변경 확인 

CloudBees CDRO의 최신 버전을 확인합니다.

```bash
$ helm repo add cb https://public-charts.artifacts.cloudbees.com/repository/public/
$ helm repo update cb
$ helm search repo cb/cloudbees-flow --versions                   
NAME                            CHART VERSION   APP VERSION     DESCRIPTION
cb/cloudbees-flow       2.28.0          2023.12.0.171596        A Helm chart for CloudBees Flow
cb/cloudbees-flow       2.27.0          2023.10.0.169425        A Helm chart for CloudBees Flow
cb/cloudbees-flow       2.26.0          2023.08.0.167214        A Helm chart for CloudBees Flow
cb/cloudbees-flow       2.25.1          2023.06.1.165376        A Helm chart for CloudBees Flow
cb/cloudbees-flow       2.25.0          2023.06.0.164409        A Helm chart for CloudBees Flow
...

```

업그레이드 버전의 values.yaml 을 얻습니다.

```bash
# 풀소스 
$ helm pull cb/cloudbees-flow --version 2.28.0

# 신규 Values.yaml 다운로드
$ helm inspect values cb/cloudbees-flow --version  2.28.0   > cdro-values-new.yaml
```

이전 values.yaml 과 신규 values.yaml 을 비교하여  cdro-values.yaml 에 신규 값을 업데이트 합니다.

```yaml

# 추가된 내용 반영
...
## Custom Labels for CDRO workload pods
customLabels:
  product: cdro

```

kustomize 빌드하여 적용되려는 매니페스트를 얻고 이전 매니페스트(cdro-kust.bk) 와 비교합니다. 이때 반드시 매니페스트에 kustomization.yaml 의 패치값을 적용해도 문제 없을지 검토합니다.

```bash
$ kustomize build --enable-helm  > cdro-kust-new.bk

# kustomizaiton 의 patch 의 내용이 아래와 같다면 cdro-kust-new.bk 에 flow-ingress 가 있는지 확인하고 apiVersion 을 바꿔도 될지 확인
patches:
  - target:
      kind: Ingress
      name: flow-ingress
    patch: |
      - op: replace
        path: /apiVersion
        value: networking.k8s.io/v1

```

### 단계 4 > 변경 분을 확인하고 Tagging 하여 신규 Tag 로 Application 배포

kustomization.yaml 에서 chart 버전을 수정합니다.

```yaml
- name: cloudbees-flow
  namespace: cdro
  valuesFile : ./cdro-values.yaml
  repo: https://public-charts.artifacts.cloudbees.com/repository/public
  version: 2.28.0
  releaseName: cdro 
  IncludeCRDs: true
```

application.yaml 에서 ArgoCD Application 의 targetRevision 을 신규 태그명으로 수정합니다.

```yaml
# application.yaml
...
spec: 
  project: default
  source:
    repoURL: 'https://github.com/daeung0921/kust-cdro-install.git'
    path: .
    targetRevision: v2.0

...
```

변경 사항을 Commit 하고 Tagging 합니다.

```bash
$ git add .
$ git commit -m 'v2.0'
$ git push -u origin main
$ git tag v2.0
$ git push origin v2.0 

```

Application.yaml 을 배포한 뒤 ArgoCD 에서 OutOfSync 상태에서 Diff 를 확인하여 변경 정보를 확인 후 문제 없으면 Manual Sync 를 수행합니다.

```bash
 
# ArgoCD 에 배포후 Manual Sync
$ kubectl apply -f application.yaml

``` 

업그레이드 후 문제가 없는지 확인합니다.

### 단계 5 > 롤백

문제가 있는 경우 ArgoCD 에서 Application.yaml 의 targetRevision 을 이전 Tag 를 사용하여 재배포하여 복구를 시도합니다.

```bash
#  application.yaml 에서 ArgoCD Application 의 targetRevision 을 이전 태그명으로 수정
spec: 
  project: default
  source:
    repoURL: 'https://github.com/daeung0921/kust-cdro-install.git'
    path: .
    targetRevision: v1.0

# ArgoCD 에 배포
$ kubectl apply -f application.yaml

# Diff 확인 후 문제가 없으면 Manual Sync
$ argocd login argo.idtplateer.com:443 --insecure
$ argocd app list --grpc-web
$ argocd app sync cdro --grpc-web
```

이전 버전으로 돌아가도 문제가 개선되지 않는 경우 ArgoCD Application 을 삭제합니다.

```bash
$ argocd login argo.idtplateer.com:443 --insecure
$ argocd app delete cdro
```

Velero 를 사용해 Volume 을 복원하고 DB 는 Dump 뜬것을 이용해 복원합니다.

```bash
<doSometing>
```

Application.yaml 의 targetRevision 을 이전 Tag 를 사용하여 재배포하고 Sync 합니다.

```YAML
#  application.yaml 에서 ArgoCD Application 의 targetRevision 을 이전 태그명으로 수정
spec: 
  project: default
  source:
    repoURL: 'https://github.com/daeung0921/kust-cdro-install.git'
    path: .
    targetRevision: v1.0

# ArgoCD 에 이전 버전 배포후 Manual Sync
$ kubectl apply -f application.yaml
$ argocd login argo.idtplateer.com:443 --insecure
$ argocd app list --grpc-web
$ argocd app sync cdro --grpc-web
```

### 옵션 > EKS 구축

- 로그 컬랙션 테스트용으로 elasticsearch 와 kibana 를 구성중에 있습니다. 
- application 배포 완료 후 elasticserach pod 에서 아래 명령으로 superuser 롤의 User 를 생성하여 kb.idtplateer.com 으로 접근할 수 있습니다.

```bash
$ elasticsearch-users list 
$ elasticsearch-users useradd test -p password -r superuser
```

### 옵션 > 액세스 포인트

- [CDRO Server](https://cdro.idtplateer.com)
- [Anaytic Server ](https://dois.idtplateer.com:9200/)
- [Anaytic Server Kibana](https://doik.idtplateer.com/)
- [Test 용 Kibana](https://kb.idtplateer.com:5601)
- [Test 용 Elasticsearch](https://es.idtplateer.com:9200)

### 옵션 > 리소스 정리

```bash
$ kubectl delete -f application.yaml 
$ kubectl delete -f cert-manager.yaml 
$ kubectl delete -f ingress-nginx.yaml
```