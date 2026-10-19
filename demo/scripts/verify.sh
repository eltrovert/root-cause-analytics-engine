#!/usr/bin/env sh
set -eu
kubectl -n rca-demo rollout status deployment/checkout --timeout=120s
kubectl -n rca-demo rollout status deployment/orders --timeout=120s
kubectl -n rca-demo rollout status deployment/payments --timeout=120s
kubectl -n rca-demo rollout status deployment/prometheus --timeout=120s
kubectl -n rca-demo rollout status deployment/grafana --timeout=120s
kubectl -n rca-demo rollout status deployment/loki --timeout=120s
kubectl -n rca-demo rollout status daemonset/promtail --timeout=120s
kubectl -n rca-demo get pods
printf '%s\n' 'Open Grafana with: kubectl -n rca-demo port-forward service/grafana 3001:3000'
printf '%s\n' 'Query Prometheus with: kubectl -n rca-demo port-forward service/prometheus 9090:9090'
printf '%s\n' 'Query Loki with: kubectl -n rca-demo port-forward service/loki 3100:3100'
