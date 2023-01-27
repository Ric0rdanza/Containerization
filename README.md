# Containerization

## Prerequesities

Add `127.0.0.1 my.container.local` into host (`/etc/hosts` on macOS)
Make your computer trust certificate authority in `/certificate/ca.crt`
open up a terminal, command `sudo kubectl port-forward svc/nginx-service 443:5000 --address 127.0.0.1` to start port forwarding.
also run `minikube tunnel` if using minikube on macOS.

`brew install minikube`
`minikube start --nodes 4` startup a cluster with 4 nodes (1 master, 3 worker)
`kubectl apply -f database_config/postgres-config.yaml`
`kubectl apply -f database_config/postgres-secret.yaml`
`kubectl apply` all the .yaml file in services/*
`kubectl get pods` to check if pods startup correctly
check website at 127.0.0.1:5000