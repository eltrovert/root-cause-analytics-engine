#!/usr/bin/env node
const readline = require('node:readline');

const prometheusURL = process.env.PROMETHEUS_URL || 'http://localhost:9090';
const lokiURL = process.env.LOKI_URL || 'http://localhost:3100';
const services = ['checkout', 'orders', 'payments'];
const maxWindowMs = 60 * 60 * 1000;

const queries = {
  alert_context: 'ALERTS{alertstate="firing"}',
  service_health: (service) => `service:http_error_ratio:rate5m{service="${service}"} or service:http_p95_latency_seconds:rate5m{service="${service}"}`,
  dependency_health: (service) => `service:http_error_ratio:rate5m{service=~"${dependencyServices(service).join('|')}"}`,
  top_error_signatures: (service) => `{service="${service}"} |= "\\\"status\\\":5"`,
};

function assertService(service) {
  if (!services.includes(service)) throw new Error(`service must be ${services.join(', ')}`);
}

function dependencyServices(service) {
  assertService(service);
  return { checkout: ['orders', 'payments'], orders: ['payments'], payments: ['payments'] }[service];
}

function validateWindow(start, end) {
  const startMs = Date.parse(start);
  const endMs = Date.parse(end);
  if (!Number.isFinite(startMs) || !Number.isFinite(endMs) || endMs <= startMs) {
    throw new Error('start and end must be increasing ISO-8601 timestamps');
  }
  if (endMs - startMs > maxWindowMs) throw new Error('time range must not exceed 60 minutes');
  return { start: new Date(startMs).toISOString(), end: new Date(endMs).toISOString() };
}

function prometheusQuery(query, time) {
  const url = new URL('/api/v1/query', prometheusURL);
  url.searchParams.set('query', query);
  if (time) url.searchParams.set('time', time);
  return url.toString();
}

function lokiQuery(query, start, end) {
  const url = new URL('/loki/api/v1/query_range', lokiURL);
  url.searchParams.set('query', query);
  url.searchParams.set('start', String(Date.parse(start) * 1_000_000));
  url.searchParams.set('end', String(Date.parse(end) * 1_000_000));
  url.searchParams.set('limit', '20');
  url.searchParams.set('direction', 'BACKWARD');
  return url.toString();
}

async function queryJSON(url, source) {
  const response = await fetch(url, { signal: AbortSignal.timeout(5000) });
  if (!response.ok) throw new Error(`${source} returned ${response.status}`);
  const payload = await response.json();
  if (payload.status !== 'success') throw new Error(payload.error || `${source} query failed`);
  return payload.data;
}

async function queryPrometheus(query, time) {
  return queryJSON(prometheusQuery(query, time), 'Prometheus');
}

async function queryLoki(query, start, end) {
  return queryJSON(lokiQuery(query, start, end), 'Loki');
}

function evidence({ source, tool, service, window, queryTemplate, result, limitations = [] }) {
  const count = Array.isArray(result?.result) ? result.result.length : Array.isArray(result) ? result.length : 0;
  return {
    source,
    tool,
    service: service || null,
    time_range: window,
    query_template: queryTemplate,
    query_reference: `${source}:${queryTemplate}`,
    summary: `${count} result series returned`,
    confidence: count > 0 ? 0.8 : 0.2,
    evidence_grade: count > 0 ? 'direct' : 'missing',
    limitations,
    result,
  };
}

async function collectEvidence(name, args = {}) {
  const window = validateWindow(args.start, args.end);
  switch (name) {
    case 'alert_context':
      return evidence({
        source: 'prometheus', tool: name, window, queryTemplate: 'alert_context_v1',
        result: await queryPrometheus(queries.alert_context, window.end),
        limitations: ['Firing alerts provide context, not proof of root cause.'],
      });
    case 'service_health':
    case 'dependency_health': {
      assertService(args.service);
      return evidence({
        source: 'prometheus', tool: name, service: args.service, window,
        queryTemplate: `${name}_v1`, result: await queryPrometheus(queries[name](args.service), window.end),
        limitations: ['Recording rules establish correlation, not causation.'],
      });
    }
    case 'top_error_signatures':
      assertService(args.service);
      return evidence({
        source: 'loki', tool: name, service: args.service, window,
        queryTemplate: 'top_error_signatures_v1', result: await queryLoki(queries.top_error_signatures(args.service), window.start, window.end),
        limitations: ['Only structured application logs from rca-demo are searched.'],
      });
    default:
      throw new Error(`unknown tool: ${name}`);
  }
}

function textResult(value) {
  return { content: [{ type: 'text', text: JSON.stringify(value, null, 2) }] };
}

const timeWindow = {
  start: { type: 'string', format: 'date-time' },
  end: { type: 'string', format: 'date-time' },
};
const serviceWindow = {
  type: 'object',
  properties: { ...timeWindow, service: { type: 'string', enum: services } },
  required: ['service', 'start', 'end'],
  additionalProperties: false,
};
const tools = [
  { name: 'alert_context', description: 'Returns firing alert context for a bounded interval. Read-only.', inputSchema: { type: 'object', properties: timeWindow, required: ['start', 'end'], additionalProperties: false } },
  { name: 'service_health', description: 'Returns recording-rule health for one service and bounded interval. Read-only.', inputSchema: serviceWindow },
  { name: 'dependency_health', description: 'Returns bounded health for known downstream dependencies. Read-only.', inputSchema: serviceWindow },
  { name: 'top_error_signatures', description: 'Returns bounded structured error logs for one service. Read-only.', inputSchema: serviceWindow },
];

async function callTool(name, args = {}) {
  return textResult(await collectEvidence(name, args));
}

function send(message) {
  process.stdout.write(`${JSON.stringify(message)}\n`);
}

async function handle(message) {
  if (message.method === 'notifications/initialized') return;
  if (message.method === 'initialize') {
    return send({ jsonrpc: '2.0', id: message.id, result: { protocolVersion: '2024-11-05', capabilities: { tools: {} }, serverInfo: { name: 'rca-grafana-evidence', version: '0.2.0' } } });
  }
  if (message.method === 'tools/list') return send({ jsonrpc: '2.0', id: message.id, result: { tools } });
  if (message.method === 'tools/call') {
    try {
      return send({ jsonrpc: '2.0', id: message.id, result: await callTool(message.params.name, message.params.arguments) });
    } catch (error) {
      return send({ jsonrpc: '2.0', id: message.id, result: { content: [{ type: 'text', text: error.message }], isError: true } });
    }
  }
  send({ jsonrpc: '2.0', id: message.id, error: { code: -32601, message: 'Method not found' } });
}

if (require.main === module) {
  readline.createInterface({ input: process.stdin, crlfDelay: Infinity }).on('line', (line) => {
    try { handle(JSON.parse(line)); } catch { send({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } }); }
  });
}

module.exports = { assertService, collectEvidence, dependencyServices, lokiQuery, prometheusQuery, queries, services, tools, validateWindow };
