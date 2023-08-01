SECRET_NAME=$(microk8s kubectl get serviceaccount my-service-account -o jsonpath='{.secrets[0].name}')
BEARER_TOKEN=$(microk8s kubectl get secret $SECRET_NAME -o jsonpath='{.data.token}' | base64 --decode)
curl -H "Authorization: Bearer $BEARER_TOKEN" https://www.aiofauna.com