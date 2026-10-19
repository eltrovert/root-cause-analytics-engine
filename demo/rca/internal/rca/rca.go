package rca

import (
	"context"
	"crypto/rand"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sync"
	"time"
)

type State string

const (
	Received               State = "received"
	Planned                State = "planned"
	CollectingEvidence     State = "collecting_evidence"
	Synthesizing           State = "synthesizing"
	AwaitingOnCallDecision State = "awaiting_on_call_decision"
	ManuallyMitigated      State = "manually_mitigated"
	Validating             State = "validating"
	Resolved               State = "resolved"
	RCADraftReady          State = "rca_draft_ready"
	maxEvidenceWindow            = time.Hour
	evidenceTaskTimeout          = 5 * time.Second
)

var services = []string{"checkout", "orders", "payments"}
var incidentIDPattern = regexp.MustCompile(`^inc_[a-zA-Z0-9_-]+$`)
var transitions = map[State][]State{
	Received:               {Planned},
	Planned:                {CollectingEvidence},
	CollectingEvidence:     {Synthesizing},
	Synthesizing:           {AwaitingOnCallDecision},
	AwaitingOnCallDecision: {Planned, ManuallyMitigated},
	ManuallyMitigated:      {Validating},
	Validating:             {Resolved},
	Resolved:               {RCADraftReady},
}

type Window struct {
	Start time.Time `json:"start"`
	End   time.Time `json:"end"`
}

type Plan struct {
	Alert            string    `json:"alert"`
	Service          string    `json:"service"`
	FiredAt          time.Time `json:"fired_at"`
	Window           Window    `json:"window"`
	Services         []string  `json:"services"`
	AllowedSources   []string  `json:"allowed_sources"`
	MaxParallelTasks int       `json:"max_parallel_tasks"`
	QueryBudget      int       `json:"query_budget"`
}

type Finding struct {
	Source         string          `json:"source"`
	Tool           string          `json:"tool"`
	Service        string          `json:"service,omitempty"`
	TimeRange      Window          `json:"time_range"`
	QueryTemplate  string          `json:"query_template"`
	QueryReference string          `json:"query_reference"`
	Summary        string          `json:"summary"`
	Confidence     float64         `json:"confidence"`
	EvidenceGrade  string          `json:"evidence_grade"`
	Limitations    []string        `json:"limitations"`
	Result         json.RawMessage `json:"result"`
}

type Synthesis struct {
	LikelyCause        string   `json:"likely_cause,omitempty"`
	Confidence         string   `json:"confidence"`
	SupportingEvidence []string `json:"supporting_evidence"`
	Alternative        string   `json:"alternative"`
	Limitations        []string `json:"limitations"`
	Proposal           string   `json:"proposal"`
}

type Mitigation struct {
	At    time.Time `json:"at"`
	Actor string    `json:"actor"`
	Note  string    `json:"note"`
}

type AuditEvent struct {
	At       time.Time       `json:"at"`
	Type     string          `json:"type"`
	Actor    string          `json:"actor"`
	Previous State           `json:"previous,omitempty"`
	Next     State           `json:"next,omitempty"`
	Detail   json.RawMessage `json:"detail,omitempty"`
}

type Incident struct {
	ID         string       `json:"id"`
	State      State        `json:"state"`
	Plan       Plan         `json:"plan"`
	Evidence   []Finding    `json:"evidence"`
	Synthesis  *Synthesis   `json:"synthesis,omitempty"`
	Mitigation *Mitigation  `json:"mitigation,omitempty"`
	Audit      []AuditEvent `json:"audit"`
}

type Collector interface {
	Collect(context.Context, string, string, Window) (Finding, error)
}

type HTTPCollector struct {
	PrometheusURL string
	LokiURL       string
	Client        *http.Client
}

func NewHTTPCollector(prometheusURL, lokiURL string) *HTTPCollector {
	return &HTTPCollector{PrometheusURL: prometheusURL, LokiURL: lokiURL, Client: &http.Client{Timeout: evidenceTaskTimeout}}
}

func KnownService(service string) error {
	for _, known := range services {
		if service == known {
			return nil
		}
	}
	return fmt.Errorf("service must be checkout, orders, or payments")
}

func ValidateWindow(window Window) error {
	if !window.End.After(window.Start) {
		return errors.New("end must be after start")
	}
	if window.End.Sub(window.Start) > maxEvidenceWindow {
		return errors.New("time range must not exceed 60 minutes")
	}
	return nil
}

func WindowAround(firedAt time.Time) Window {
	return Window{Start: firedAt.Add(-30 * time.Minute), End: firedAt.Add(30 * time.Minute)}
}

func NewIncident(alert, service, actor string, firedAt time.Time) (*Incident, error) {
	if err := KnownService(service); err != nil {
		return nil, err
	}
	if firedAt.IsZero() {
		firedAt = time.Now().UTC()
	}
	bytes := make([]byte, 4)
	if _, err := rand.Read(bytes); err != nil {
		return nil, fmt.Errorf("generate incident id: %w", err)
	}
	incident := &Incident{
		ID:    fmt.Sprintf("inc_%x_%x", firedAt.UnixMilli(), bytes),
		State: Received,
		Plan:  Plan{Alert: alert, Service: service, FiredAt: firedAt, Window: WindowAround(firedAt), Services: append([]string(nil), services...), AllowedSources: []string{"prometheus", "loki"}, MaxParallelTasks: 4, QueryBudget: 8},
	}
	incident.AppendAudit("incident_created", actor, map[string]string{"alert": alert, "service": service})
	if err := incident.Transition(Planned, actor, nil); err != nil {
		return nil, err
	}
	return incident, nil
}

func (incident *Incident) AppendAudit(kind, actor string, detail any) {
	var encoded json.RawMessage
	if detail != nil {
		encoded, _ = json.Marshal(detail)
	}
	incident.Audit = append(incident.Audit, AuditEvent{At: time.Now().UTC(), Type: kind, Actor: actor, Detail: encoded})
}

func (incident *Incident) Transition(next State, actor string, detail any) error {
	allowed := false
	for _, candidate := range transitions[incident.State] {
		if candidate == next {
			allowed = true
			break
		}
	}
	if !allowed {
		return fmt.Errorf("cannot transition from %s to %s", incident.State, next)
	}
	previous := incident.State
	incident.State = next
	var encoded json.RawMessage
	if detail != nil {
		encoded, _ = json.Marshal(detail)
	}
	incident.Audit = append(incident.Audit, AuditEvent{At: time.Now().UTC(), Type: "state_transition", Actor: actor, Previous: previous, Next: next, Detail: encoded})
	return nil
}

func dependencyServices(service string) ([]string, error) {
	if err := KnownService(service); err != nil {
		return nil, err
	}
	return map[string][]string{"checkout": {"orders", "payments"}, "orders": {"payments"}, "payments": {"payments"}}[service], nil
}

func (collector *HTTPCollector) Collect(ctx context.Context, tool, service string, window Window) (Finding, error) {
	if err := ValidateWindow(window); err != nil {
		return Finding{}, err
	}
	var source, template, query string
	var limitations []string
	switch tool {
	case "alert_context":
		source, template, query = "prometheus", "alert_context_v1", `ALERTS{alertstate="firing"}`
		limitations = []string{"Firing alerts provide context, not proof of root cause."}
	case "service_health":
		if err := KnownService(service); err != nil {
			return Finding{}, err
		}
		source, template = "prometheus", "service_health_v1"
		query = fmt.Sprintf(`service:http_error_ratio:rate5m{service=%q} or service:http_p95_latency_seconds:rate5m{service=%q}`, service, service)
		limitations = []string{"Recording rules establish correlation, not causation."}
	case "dependency_health":
		dependencies, err := dependencyServices(service)
		if err != nil {
			return Finding{}, err
		}
		source, template = "prometheus", "dependency_health_v1"
		query = fmt.Sprintf(`service:http_error_ratio:rate5m{service=~%q}`, joinRegex(dependencies))
		limitations = []string{"Dependency health is limited to the fixed local graph."}
	case "top_error_signatures":
		if err := KnownService(service); err != nil {
			return Finding{}, err
		}
		source, template, query = "loki", "top_error_signatures_v1", fmt.Sprintf(`{service=%q} |= "\\\"status\\\":5"`, service)
		limitations = []string{"Only structured application logs from rca-demo are searched."}
	default:
		return Finding{}, fmt.Errorf("unknown tool: %s", tool)
	}

	result, err := collector.query(ctx, source, query, window)
	if err != nil {
		return Finding{}, err
	}
	count := resultCount(result)
	grade, confidence := "missing", 0.2
	if count > 0 {
		grade, confidence = "direct", 0.8
	}
	return Finding{Source: source, Tool: tool, Service: service, TimeRange: window, QueryTemplate: template, QueryReference: source + ":" + template, Summary: fmt.Sprintf("%d result series returned", count), Confidence: confidence, EvidenceGrade: grade, Limitations: limitations, Result: result}, nil
}

func (collector *HTTPCollector) query(ctx context.Context, source, query string, window Window) (json.RawMessage, error) {
	base := collector.PrometheusURL
	endpoint := "/api/v1/query"
	values := url.Values{"query": {query}, "time": {window.End.Format(time.RFC3339Nano)}}
	if source == "loki" {
		base, endpoint = collector.LokiURL, "/loki/api/v1/query_range"
		values = url.Values{"query": {query}, "start": {fmt.Sprintf("%d", window.Start.UnixNano())}, "end": {fmt.Sprintf("%d", window.End.UnixNano())}, "limit": {"20"}, "direction": {"BACKWARD"}}
	}
	requestURL, err := url.Parse(base)
	if err != nil {
		return nil, fmt.Errorf("invalid %s URL: %w", source, err)
	}
	requestURL.Path = endpoint
	requestURL.RawQuery = values.Encode()
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, requestURL.String(), nil)
	if err != nil {
		return nil, err
	}
	response, err := collector.Client.Do(request)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	body, err := io.ReadAll(io.LimitReader(response.Body, 1<<20))
	if err != nil {
		return nil, err
	}
	if response.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("%s returned %s", source, response.Status)
	}
	var envelope struct {
		Status string          `json:"status"`
		Data   json.RawMessage `json:"data"`
		Error  string          `json:"error"`
	}
	if err := json.Unmarshal(body, &envelope); err != nil {
		return nil, err
	}
	if envelope.Status != "success" {
		return nil, errors.New(envelope.Error)
	}
	return envelope.Data, nil
}

func joinRegex(values []string) string {
	result := ""
	for index, value := range values {
		if index > 0 {
			result += "|"
		}
		result += value
	}
	return result
}

func resultCount(raw json.RawMessage) int {
	var payload struct {
		Result []json.RawMessage `json:"result"`
	}
	if json.Unmarshal(raw, &payload) != nil {
		return 0
	}
	return len(payload.Result)
}

func Synthesize(findings []Finding) Synthesis {
	var metrics, logs *Finding
	for index := range findings {
		finding := &findings[index]
		if finding.Tool == "service_health" && finding.Service == "payments" {
			metrics = finding
		}
		if finding.Tool == "top_error_signatures" && finding.Service == "payments" {
			logs = finding
		}
	}
	if metrics != nil && logs != nil && resultCount(metrics.Result) > 0 && resultCount(logs.Result) > 0 {
		return Synthesis{LikelyCause: "payments dependency degradation", Confidence: "medium-high", SupportingEvidence: []string{metrics.QueryReference, logs.QueryReference}, Alternative: "downstream propagation from checkout or orders", Limitations: []string{"The synthetic demo correlates fixed metrics and logs; it does not prove causation."}, Proposal: "Validate payment pod state, then have an operator disable the contained fault manually."}
	}
	references := make([]string, 0, len(findings))
	for _, finding := range findings {
		references = append(references, finding.QueryReference)
	}
	return Synthesis{Confidence: "low", SupportingEvidence: references, Alternative: "Insufficient evidence to distinguish services.", Limitations: []string{"Collect another explicitly approved hypothesis with a fresh bounded plan."}, Proposal: "Do not remediate automatically."}
}

func (incident *Incident) Investigate(ctx context.Context, collector Collector, actor string) error {
	if err := incident.Transition(CollectingEvidence, actor, nil); err != nil {
		return err
	}
	tasks := []struct{ tool, service string }{{"alert_context", ""}}
	for _, service := range incident.Plan.Services {
		tasks = append(tasks, struct{ tool, service string }{"service_health", service})
	}
	tasks = append(tasks, struct{ tool, service string }{"dependency_health", incident.Plan.Service}, struct{ tool, service string }{"top_error_signatures", incident.Plan.Service})
	if len(tasks) > incident.Plan.QueryBudget {
		return errors.New("investigation plan exceeds query budget")
	}

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	findings := make([]Finding, len(tasks))
	errorsByTask := make(chan error, len(tasks))
	jobs := make(chan int)
	var workers sync.WaitGroup
	for worker := 0; worker < incident.Plan.MaxParallelTasks; worker++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for index := range jobs {
				taskCtx, stop := context.WithTimeout(ctx, evidenceTaskTimeout)
				finding, err := collector.Collect(taskCtx, tasks[index].tool, tasks[index].service, incident.Plan.Window)
				stop()
				if err != nil {
					errorsByTask <- err
					cancel()
					return
				}
				findings[index] = finding
			}
		}()
	}
	for index := range tasks {
		if ctx.Err() != nil {
			break
		}
		jobs <- index
	}
	close(jobs)
	workers.Wait()
	select {
	case err := <-errorsByTask:
		return fmt.Errorf("collect evidence: %w", err)
	default:
	}
	if ctx.Err() != nil {
		return ctx.Err()
	}
	incident.Evidence = append(incident.Evidence, findings...)
	for _, finding := range findings {
		incident.AppendAudit("evidence_collected", actor, map[string]string{"source": finding.Source, "tool": finding.Tool, "query_reference": finding.QueryReference})
	}
	if err := incident.Transition(Synthesizing, actor, nil); err != nil {
		return err
	}
	synthesis := Synthesize(incident.Evidence)
	incident.Synthesis = &synthesis
	incident.AppendAudit("synthesis_created", actor, map[string]string{"confidence": synthesis.Confidence})
	return incident.Transition(AwaitingOnCallDecision, actor, nil)
}

func StateDir() string {
	if directory := os.Getenv("RCA_STATE_DIR"); directory != "" {
		return directory
	}
	return "state"
}

func incidentPath(id string) (string, error) {
	if !incidentIDPattern.MatchString(id) {
		return "", errors.New("invalid incident id")
	}
	return filepath.Join(StateDir(), id, "incident.json"), nil
}

func Save(incident *Incident) error {
	file, err := incidentPath(incident.ID)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(file), 0o755); err != nil {
		return err
	}
	payload, err := json.MarshalIndent(incident, "", "  ")
	if err != nil {
		return err
	}
	temporary := fmt.Sprintf("%s.%d.tmp", file, os.Getpid())
	if err := os.WriteFile(temporary, append(payload, '\n'), 0o600); err != nil {
		return err
	}
	return os.Rename(temporary, file)
}

func Load(id string) (*Incident, error) {
	file, err := incidentPath(id)
	if err != nil {
		return nil, err
	}
	payload, err := os.ReadFile(file)
	if err != nil {
		return nil, err
	}
	var incident Incident
	if err := json.Unmarshal(payload, &incident); err != nil {
		return nil, err
	}
	return &incident, nil
}

func ApproveMitigation(incident *Incident, note, actor string) error {
	if err := incident.Transition(ManuallyMitigated, actor, map[string]string{"note": note}); err != nil {
		return err
	}
	incident.Mitigation = &Mitigation{At: time.Now().UTC(), Actor: actor, Note: note}
	return nil
}

func Validate(incident *Incident, actor string) error {
	if err := incident.Transition(Validating, actor, nil); err != nil {
		return err
	}
	incident.AppendAudit("validation_requested", actor, map[string]string{"limitation": "The demo records approval; the operator runs fault-off manually."})
	return nil
}

func Resolve(incident *Incident, actor string) error {
	return incident.Transition(Resolved, actor, nil)
}

func Reinvestigate(incident *Incident, actor string) error {
	return incident.Transition(Planned, actor, map[string]string{"reason": "explicit operator request"})
}

func DraftRCA(incident *Incident, actor string) (string, error) {
	if err := incident.Transition(RCADraftReady, actor, nil); err != nil {
		return "", err
	}
	file, err := incidentPath(incident.ID)
	if err != nil {
		return "", err
	}
	draft := filepath.Join(filepath.Dir(file), "rca-draft.md")
	content := fmt.Sprintf("# RCA draft: %s\n\n## Alert and plan\n- Alert: %s\n- Service: %s\n- Window: %s to %s\n- Candidate services: %s\n\n## Evidence\n", incident.ID, incident.Plan.Alert, incident.Plan.Service, incident.Plan.Window.Start.Format(time.RFC3339), incident.Plan.Window.End.Format(time.RFC3339), joinComma(incident.Plan.Services))
	for _, finding := range incident.Evidence {
		content += fmt.Sprintf("- %s/%s: %s (%s)\n", finding.Source, finding.Tool, finding.QueryReference, finding.EvidenceGrade)
	}
	content += fmt.Sprintf("\n## Assessment\n- Likely cause: %s\n- Confidence: %s\n- Proposal: %s\n\n## Human action\n- %s\n\n## Review status\nDraft only. A human must review before distribution.\n", incident.Synthesis.LikelyCause, incident.Synthesis.Confidence, incident.Synthesis.Proposal, mitigationNote(incident.Mitigation))
	if err := os.WriteFile(draft, []byte(content), 0o600); err != nil {
		return "", err
	}
	incident.AppendAudit("rca_draft_created", actor, map[string]string{"draft": draft})
	return draft, nil
}

func mitigationNote(mitigation *Mitigation) string {
	if mitigation == nil {
		return "No mitigation recorded."
	}
	return mitigation.Note
}

func joinComma(values []string) string {
	result := ""
	for index, value := range values {
		if index > 0 {
			result += ", "
		}
		result += value
	}
	return result
}
