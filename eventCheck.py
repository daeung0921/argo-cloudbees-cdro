# pip install kubernetes
# pip install elasticsearch

from kubernetes import client, config

# Kubernetes 클러스터 구성 로드 (이 예제에서는 ~/.kube/config를 사용)
config.load_kube_config()

# Kubernetes API 클라이언트 설정
v1 = client.CoreV1Api()

# 가져올 이벤트의 네임스페이스 지정
namespace = 'cdro'

# 가져올 이벤트의 포드 이름 지정
pod_name = 'cdro-remote-agent-flow-agent-0'

# 특정 네임스페이스의 특정 포드에 대한 이벤트 목록 가져오기
events = v1.list_namespaced_event(namespace, field_selector=f'involvedObject.name={pod_name}').items

# 각 이벤트에 대한 출력
for event in events:
    print("Namespace: %s, Message: %s" % (event.metadata.namespace, event.message))
