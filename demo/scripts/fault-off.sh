#!/usr/bin/env sh
set -eu
kubectl -n rca-demo create configmap payment-fault --from-file=fault.json=demo/manifests/fault.normal.json --dry-run=client -o yaml | kubectl apply -f -
kubectl -n rca-demo rollout restart deployment/payments
kubectl -n rca-demo rollout status deployment/payments --timeout=120s
