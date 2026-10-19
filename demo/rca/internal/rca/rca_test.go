package rca

import (
	"context"
	"encoding/json"
	"sync"
	"testing"
	"time"
)

type fakeCollector struct {
	mu     sync.Mutex
	active int
	max    int
}

func (collector *fakeCollector) Collect(_ context.Context, tool, service string, window Window) (Finding, error) {
	collector.mu.Lock()
	collector.active++
	if collector.active > collector.max {
		collector.max = collector.active
	}
	collector.active--
	collector.mu.Unlock()
	result, _ := json.Marshal(map[string]any{"result": []any{map[string]string{"service": service}}})
	return Finding{Source: "test", Tool: tool, Service: service, TimeRange: window, QueryReference: "test:" + tool, EvidenceGrade: "direct", Result: result}, nil
}

func TestValidateWindow(t *testing.T) {
	now := time.Now().UTC()
	tests := []struct {
		name    string
		window  Window
		wantErr bool
	}{
		{name: "valid", window: Window{Start: now, End: now.Add(time.Minute)}},
		{name: "too long", window: Window{Start: now, End: now.Add(maxEvidenceWindow + time.Second)}, wantErr: true},
		{name: "backwards", window: Window{Start: now, End: now}, wantErr: true},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if err := ValidateWindow(test.window); (err != nil) != test.wantErr {
				t.Fatalf("ValidateWindow() error = %v, wantErr %t", err, test.wantErr)
			}
		})
	}
}

func TestTransitionsAndLifecycle(t *testing.T) {
	directory := t.TempDir()
	t.Setenv("RCA_STATE_DIR", directory)
	incident, err := NewIncident("CheckoutPaymentDependencyDegraded", "payments", "test", time.Date(2026, 9, 24, 8, 30, 0, 0, time.UTC))
	if err != nil {
		t.Fatal(err)
	}
	if err := Save(incident); err != nil {
		t.Fatal(err)
	}
	collector := &fakeCollector{}
	if err := incident.Investigate(context.Background(), collector, "test"); err != nil {
		t.Fatal(err)
	}
	if incident.State != AwaitingOnCallDecision {
		t.Fatalf("state = %s", incident.State)
	}
	if len(incident.Evidence) != 6 {
		t.Fatalf("evidence = %d, want 6", len(incident.Evidence))
	}
	if collector.max > incident.Plan.MaxParallelTasks {
		t.Fatalf("parallel collectors = %d, limit %d", collector.max, incident.Plan.MaxParallelTasks)
	}
	if incident.Synthesis.LikelyCause != "payments dependency degradation" {
		t.Fatalf("cause = %q", incident.Synthesis.LikelyCause)
	}
	if err := Resolve(incident, "test"); err == nil {
		t.Fatal("Resolve() accepted an unapproved incident")
	}
	if err := ApproveMitigation(incident, "operator will run fault-off", "test"); err != nil {
		t.Fatal(err)
	}
	if err := Validate(incident, "test"); err != nil {
		t.Fatal(err)
	}
	if err := Resolve(incident, "test"); err != nil {
		t.Fatal(err)
	}
	draft, err := DraftRCA(incident, "test")
	if err != nil {
		t.Fatal(err)
	}
	if incident.State != RCADraftReady {
		t.Fatalf("state = %s", incident.State)
	}
	if draft == "" {
		t.Fatal("draft path is empty")
	}
	if len(incident.Audit) < 10 {
		t.Fatalf("audit events = %d", len(incident.Audit))
	}
}

func TestExplicitReinvestigation(t *testing.T) {
	incident, err := NewIncident("alert", "payments", "test", time.Now().UTC())
	if err != nil {
		t.Fatal(err)
	}
	collector := &fakeCollector{}
	if err := incident.Investigate(context.Background(), collector, "test"); err != nil {
		t.Fatal(err)
	}
	if err := Reinvestigate(incident, "test"); err != nil {
		t.Fatal(err)
	}
	if incident.State != Planned {
		t.Fatalf("state = %s", incident.State)
	}
}
