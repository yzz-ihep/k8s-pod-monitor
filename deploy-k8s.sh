pip freeze > requirements.txt
docker build -t monitor:v0.1 -f Dockerfile .
kubectl delete -f nginx-monitor.yaml
kubectl apply -f nginx-monitor.yaml