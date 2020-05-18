# RideSafeAPI

<img src="https://p-qKFgO2.t2.n0.cdn.getcloudapp.com/items/5zu1Rr6v/Image%202020-05-18%20at%205.00.35%20PM.png?v=dfd7fc30e235275f44caf3b5a5fb3284" width="100" height="100">


Mobile Application backend/homepage for RideSafe.

`flapi` is written mostly in python using flask, the frontend uses mostly html with some javascript.
The app is fully integrated with Datadog and will require an agent deployed alongside flapi & redis to function.

### `flapi` has the following features enabled by default:

- APM
- Custom metrics
- Log collection
- RUM
- Browser Logs
- Profiling

`flapi` can be found on docker hub, and in general the tag `latest` will be fully up to date with this repo.
Flapi supports X86/x64 systems at this time only, however can be builr to run on ARM devices.
Find flapi [here](https://hub.docker.com/repository/docker/monganai/flapi) on docker hub!



### Kubernetes setup:

- Create a new deployment (minikube etc)
- `kubectl create  -f datadog-agent.yaml` 
- `kubectl create -f redis.yaml`
- Add your `API key`, `client token` and `Application_id` as seen in the sample flapi deplyment file`
- `kubectl apply -f flapi-deploy.yaml`

Flapi will be exposed via port 8080 & nodePort 30000

Note: RidesafeAPI is currently hosted locally in microk8s, the daemonset for the Datadog Agent is modified in order to work in this environment and wont work elsewhere.

View the site running live [here!](http://www.ridesafe.duckdns.org:30000/)

![service_map](https://p-qKFgO2.t2.n0.cdn.getcloudapp.com/items/eDu6bXpY/Image%202020-05-18%20at%204.58.59%20PM.png?v=8b17c2957978dcbe67eb10c1d8df38ee)


