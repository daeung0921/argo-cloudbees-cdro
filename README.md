## Kustomized Helm Chart - Cloudbees CD Ro

CDRO kustomized helm chart 를 ArgoCD 통해 배포하기 위한 예제 Repo

### Step 1 > 백업

업그레이드를 진행하기 전에 Backup 한다.
- [Velero 를 통해 Persistent Volume 을 백업하고 수동으로 DB 백업](https://docs.bitnami.com/tutorials/backup-restore-data-mariadb-galera-kubernetes/)

### Step 2 > Cloudbees CDRO Chart 변경분 확인

먼저 아래와 같이 Cloudbees CDRO 에서 신규 버전을 확인하고 Values.yaml 및 Chart 파일이 구성이 어디가 변경되었는지 확인한다.
- Release Note 를 통해 신규 버전과 이전 버전의 차이를 확인한다.
- values-origin.yaml, values-new.yaml 의 변경된 사항을 확인한다.
- values-new.yaml 내용이 values-origin.yaml 과 비교하여 많이 변경이 된 경우는 chart 전체에서 어떤 수정이 일어났는지도 확인한다.

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

# 풀소스 
$ helm pull cb/cloudbees-flow --version 2.28.0 # 신규 적용 버전

# 신규 Values.yaml 다운로드
$ helm inspect values cb/cloudbees-flow --version  2.28.0   > cdro-values-new.yaml

```

### Step 3 > 변경 분을 확인하고 Tagging 하여 신규 Tag 로 Application 배포

1. cdro-values.yaml, cdro-values-new.yaml 두 값을 비교하여 차이점을 cdro-values.yaml 에 반영한다.
2. cdro-values.yaml 을 수정한 상태에서 kustomize build 를 사용하여 실제 배포할 매니페스트를 얻는다.
3. cdro-kust.bk, cdro-kust-new.bk 두 값을 비교하여 차이가 있는 점을 확인한다.
4. cdro-kust.bk 를 신규 컨텐츠로 변경한다.
5. 필요시 kustomization.yaml 을 수정한다.
6. Application.yaml 에 신규 태그명을 넣는다.
7. Tagging 한다.
8. Application.yaml 을 배포하여 ArgoCD 에서 OutOfSync 상태에서 Diff 를 확인하여 변경 정보를 확인 후 문제 없으면 Sync 한다.

```bash
# cdro-kust.bk, cdro-kust-new.bk 두 값을 비교하여 차이가 있는 점을 확인
$ kustomize build --enable-helm  > kust_result_new.bk

# application.yaml 에서 ArgoCD Application 의 targetRevision 을 신규 태그명으로 수정
spec: 
  project: default
  source:
    repoURL: 'https://github.com/daeung0921/kust-cdro-install.git'
    path: .
    targetRevision: v2.0

# Tagging 하여 저장
$ git add .
$ git commit -m 'v2.0'
$ git push -u origin main
$ git tag v2.0
$ git push origin v2.0 

# ArgoCD 에 배포후 Manual Sync
$ kubectl apply -f application.yaml

``` 

### Step 4 > 롤백

문제가 있는 경우 아래와 같이 롤백한다.

1.  ArgoCD 에서 Application.yaml 의 targetRevision 을 이전 Tag 를 사용하여 재배포하여 복구한다.
2.  문제가 없이 롤백되면 그대로 사용한다.
3.  문제가 있는 경우 ArgoCD Application 을 삭제한다.
4.  Velero 와 DB 를 Backup 을 이용해 복원한다.
5.  Application.yaml 의 targetRevision 을 이전 Tag 를 사용하여 재배포한다.

```YAML
#  application.yaml 에서 ArgoCD Application 의 targetRevision 을 이전 태그명으로 수정
spec: 
  project: default
  source:
    repoURL: 'https://github.com/daeung0921/kust-cdro-install.git'
    path: .
    targetRevision: v1.0

# ArgoCD 에 배포후 Manual Sync
$ kubectl apply -f application.yaml
```