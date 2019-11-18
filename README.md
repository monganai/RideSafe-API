
Kubernetes setup:

-Create a new deployment (minikube etc)
-kubectl create  -f datadog-agent.yaml 
-kubectl apply -f flapi-deploy.yaml
-kubectl port-forward deployment/flapi 8080:8080



Docker setup:

comment out the current tracer settings and uncomment out the other settings in api.py

Pull either build the image using the dockerfile or pull the latest build from here: https://hub.docker.com/repository/docker/monganai/flapi


Host setup:
EXPORT_FLASK_APP = api.py
flask run

Dont install requirements.text without a venv - the list isn't exactly accurate :)
