# Speaker Notes Cheat Sheet: Root Cause Analytics Engine
**Event:** Kubernetes Community Days Indonesia 2026  
**Speaker:** El Muhammad Cholid H. (Founder, DevOps Focus Group)  

---

### Slide 1: Title
- **GOAL:** Frame the talk and set immediate expectations.
- **TALK TRACK:**
  - Welcome everyone. This architecture started at a real fintech client with strict regulatory constraints.
  - Today's demo runs on synthetic data and fits in a public repo you can test on your laptop.
  - Two clear non-goals: this is NOT autonomous remediation, and it does NOT replace on-call engineers.
- **TRANSITION:** "Let's look at what actually happens when an incident wakes you up."

---

### Slide 2: When an alert fires at 3am, the clock starts ticking
- **GOAL:** Connect with the audience's shared pain of on-call triage.
- **TALK TRACK:**
  - Ask the room: who has spent 40 minutes at 3am clicking 12 dashboard tabs while Slack explodes?
  - Typing a kubectl command or applying a patch takes 2 minutes. Finding WHAT to fix takes 40 minutes.
  - Alerts tell you symptoms, never the root cause.
- **TRANSITION:** "The natural reaction today is: why not just hand the logs to an LLM?"

---

### Slide 3: The obvious instinct is to point an LLM at your logs
- **GOAL:** Deconstruct why naive LLM debugging fails in production.
- **TALK TRACK:**
  - Walk through the diagram: alert triggers -> LLM gets broad kubectl access -> dumps gigabytes of logs.
  - Result: 100k tokens burned, context exhausted, and the model confuses cascade noise for the real bug.
  - Worse: giving an unconstrained prompt cluster-admin credentials is a critical security hole.
- **TRANSITION:** "So how do disciplined SREs actually solve this? They bound the evidence first."

---

### Slide 4: Instead of searching blindly, bound the evidence first
- **GOAL:** Explain the strict evidence hierarchy: Metrics -> Traces -> Logs.
- **TALK TRACK:**
  - Step 1: Metrics isolate the anomaly window and narrow candidates. They prove correlation, not causation.
  - Step 2: Traces bound the exact distributed path. Who called who, where did the latency spike?
  - Step 3: Logs are queried last, for confirmation, never discovery. Querying 30 seconds of targeted logs costs nothing.
- **TRANSITION:** "Where do we correlate all three? Grafana."

---

### Slide 5: Grafana is where telemetry turns into correlation
- **GOAL:** Establish Grafana, not the AI, as the center of evidence correlation.
- **TALK TRACK:**
  - Many expect MCP or an LLM to be the core architecture. It isn't.
  - Grafana is already your federation engine: it connects Prometheus, Loki, and Tempo with unified dashboards.
  - MCP is simply a thin read-only interface letting our engine query existing Grafana datasources safely.
- **TRANSITION:** "Here is how we translated this enterprise pattern into an open repo."

---

### Slide 6: Taking an enterprise pattern and making it reproducible
- **GOAL:** Show that the demo retains genuine enterprise design principles.
- **TALK TRACK:**
  - Everything in proprietary production has a 1-to-1 open equivalent in the repo.
  - Client auth proxies become standalone MCP servers; internal telemetry becomes synthetic RED metrics.
  - You get the exact same state machine and validation loops in a simple Docker Compose setup.
- **TRANSITION:** "Now, rule number one for production safety."

---

### Slide 7: Never let an LLM write raw PromQL in production
- **GOAL:** Explain why dynamic PromQL generation is banned.
- **TALK TRACK:**
  - Never give an LLM an open PromQL prompt in production.
  - Why? Complex regex or unindexed label queries can crash your Prometheus cluster right during an active incident.
  - Instead, SREs pre-vetted recording rules. The engine exposes named tools, and the gateway fills parameters into fixed queries.
- **TRANSITION:** "And we enforce this boundary with strict schemas."

---

### Slide 8: Enforce security in schemas, not in prompts
- **GOAL:** Show how JSON Schema provides deterministic policy enforcement.
- **TALK TRACK:**
  - Prompt instructions like 'please do not query broad time windows' fail under pressure.
  - Schemas don't negotiate: 'additionalProperties: false', enum-constrained service names, and bounded duration limits.
  - If an argument doesn't validate, the MCP gateway rejects it before the packet ever hits Grafana.
- **TRANSITION:** "Once tools are safe, how do we structure the investigation flow?"

---

### Slide 9: Every state change must be an auditable human decision
- **GOAL:** Walk the 10-stage auditable state machine.
- **TALK TRACK:**
  - State transitions are persisted records in a database, not internal loops in an agent's memory.
  - Follow the flow: Received -> Planned -> Collecting -> Synthesizing -> Human Gate.
  - Notice node 5: rejecting a hypothesis explicitly returns to planning. Notice 7b: automated patching is disabled by policy.
- **TRANSITION:** "Let's look at how that initial plan is scoped."

---

### Slide 10: The alert builds a shared plan before anyone runs queries
- **GOAL:** Explain why planning happens before execution.
- **TALK TRACK:**
  - When the alert fires, it first builds a visible plan: services in scope, time boundaries, and initial hypotheses.
  - This plan is posted into the incident channel immediately.
  - If an on-call engineer joins 10 minutes late, they read a clear checklist instead of guessing what the bot is doing.
- **TRANSITION:** "Who actually runs the checks? Five narrow workers."

---

### Slide 11: Five focused workers asking five narrow questions
- **GOAL:** Present the division of labor across specialized workers.
- **TALK TRACK:**
  - Instead of one massive agent that does everything, we deploy five bounded workers.
  - Each worker answers one question: Metrics checks RED; Logs checks 3 minutes; Traces checks top 5 spans; Topology checks dependencies; Changes checks recent deploys.
  - None of them has ambient access to explore outside their lane.
- **TRANSITION:** "And what do they return? Structured verdicts."

---

### Slide 12: Ruling out a false lead is just as valuable as finding the bug
- **GOAL:** Highlight that negative evidence stops engineers from wasting time.
- **TALK TRACK:**
  - Proving that the database is healthy is just as valuable as finding an error in the auth pod.
  - Workers return structured JSON verdicts: 'status: rejected', with exact metric proofs.
  - This eliminates circular arguments and prevents people from re-checking components that are operating normally.
- **TRANSITION:** "Here is the complete sequence in motion."

---

### Slide 13: How the entire investigation unfolds end to end
- **GOAL:** Walk the end-to-end timeline smoothly.
- **TALK TRACK:**
  - Walk through the steps: Alert fires -> Coordinator creates incident record -> 5 workers fan out concurrently.
  - Results collect -> Synthesis correlates timeline -> Root cause proposed -> Human approval gate.
  - Total elapsed time: under 45 seconds from initial trigger to actionable verdict.
- **TRANSITION:** "Now let's examine the security boundaries that make this safe."

---

### Slide 14: Architecture enforces trust, not polite prompts
- **GOAL:** Explain why prompt injection cannot compromise cluster infrastructure.
- **TALK TRACK:**
  - Notice how permissions are isolated across all four tiers:
  - The Orchestrator holds no Grafana credentials. The MCP Gateway has zero write endpoints.
  - Even if someone injected malicious text into an application log, the gateway physically cannot execute write commands.
- **TRANSITION:** "What about Slack and Teams interaction? How do chat buttons work?"

---

### Slide 15: Chat buttons request actions, but the backend verifies
- **GOAL:** Explain secure ChatOps button handling.
- **TALK TRACK:**
  - A Slack button click never runs a script directly.
  - It sends an intent payload to the backend server with a single-use cryptographic nonce.
  - The server verifies caller RBAC, ensures the incident is in the correct state, and rejects duplicate or stale clicks.
- **TRANSITION:** "Once mitigation is approved and applied, how do we confirm recovery?"

---

### Slide 16: A human applies the fix, but telemetry proves it worked
- **GOAL:** Describe closed-loop validation after applying a fix.
- **TALK TRACK:**
  - Applying a fix isn't the end of an incident.
  - The engine waits for 3 consecutive evaluation windows (3x 60s) to verify error rates return below SLO thresholds.
  - Only when metrics confirm recovery does the state machine transition to Resolved.
- **TRANSITION:** "And when it resolves, the post-mortem is already finished."

---

### Slide 17: The post-mortem assembles itself while you fix the incident
- **GOAL:** Showcase the immediate practical benefit: zero manual post-mortem writing.
- **TALK TRACK:**
  - Nobody likes writing post-mortems days later when memory fades and metric charts have expired.
  - Because our engine recorded every step as an auditable state transition, the post-mortem compiles automatically upon resolution.
  - All timestamps, rejected hypotheses, and metric proofs are already organized for final human sign-off.
- **TRANSITION:** "Let's summarize the architecture comparison side-by-side."

---

### Slide 18: Why bounding the evidence beats dumping the logs
- **GOAL:** Compare raw log dumping against bounded evidence.
- **TALK TRACK:**
  - Be transparent about the trade-off: this requires building clean telemetry and recording rules.
  - In exchange, you cut token usage from 100k down to 4k tokens, drop query latency from minutes to seconds, and eliminate cluster-admin security risks.
- **TRANSITION:** "And we should be equally honest about what this engine cannot do."

---

### Slide 19: Where this design deliberately stops
- **GOAL:** Earn trust with senior engineers by stating hard limitations plainly.
- **TALK TRACK:**
  - State these upfront: correlation is never causation, and no AI can invent metrics you didn't collect.
  - If your service catalog is outdated or missing RED metrics, the engine cannot help you.
  - Most importantly: this is NOT autonomous remediation. Humans stay in the loop.
- **TRANSITION:** "How can teams start implementing this today?"

---

### Slide 20: How to build this incrementally without boiling the ocean
- **GOAL:** Provide a pragmatic, low-risk adoption path.
- **TALK TRACK:**
  - Do not start by deploying AI agents.
  - Phase 1 and Phase 2 are standard observability engineering: RED recording rules and correlated dashboards.
  - Once human engineers have fast correlation dashboards, adding the MCP gateway and state machine is easy.
- **TRANSITION:** "Here are the three big takeaways to bring home."

---

### Slide 21: Three principles to take back to your team
- **GOAL:** Deliver three clear takeaways slowly and deliberately.
- **TALK TRACK:**
  - 1. Put Grafana at the evidence plane: don't build integrations on raw Prometheus and Loki directly.
  - 2. Never let models write queries: schemas are hard policies that prevent crashes.
  - 3. Persist the plan and the state: keep humans in control with auditable transitions.
- **TRANSITION:** "You can run the entire system on your laptop right now."

---

### Slide 22: Try the entire stack locally on your machine
- **GOAL:** Point audience to the working implementation.
- **TALK TRACK:**
  - Everything shown today is open source: Prometheus configs, Grafana dashboards, and the MCP gateway.
  - Run 'make up' to start the stack, and 'make fault' to simulate a real latency spike.
  - Keep https://github.com/eltrovert/root-cause-analytics-engine on screen for Q&A.
- **TRANSITION:** "Thank you everyone!"

---

### Slide 23: Thank You
- **GOAL:** Close smoothly and open for Q&A.
- **TALK TRACK:**
  - Thank the KCD Indonesia organizers, sponsors, and attendees.
  - Open the floor for questions about Prometheus, MCP, or incident state machines.
