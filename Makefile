.PHONY: up down fault-on fault-off verify test grafana prometheus loki rca

up:
	kind get clusters | grep -qx rca-demo || kind create cluster --config demo/kind-config.yaml
	kubectl apply -k demo
	$(MAKE) verify

down:
	kind delete cluster --name rca-demo

fault-on:
	sh demo/scripts/fault-on.sh

fault-off:
	sh demo/scripts/fault-off.sh

verify:
	sh demo/scripts/verify.sh

test:
	node --test demo/mcp/test/*.test.js
	cd demo/rca && go test ./...

grafana:
	kubectl -n rca-demo port-forward service/grafana 3001:3000

prometheus:
	kubectl -n rca-demo port-forward service/prometheus 9090:9090

loki:
	kubectl -n rca-demo port-forward service/loki 3100:3100

rca:
	@printf '%s\n' 'Run: cd demo/rca && go run ./cmd/rca create'
