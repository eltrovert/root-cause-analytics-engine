const http = require('node:http');
const fs = require('node:fs');
const { performance } = require('node:perf_hooks');

const service = process.env.SERVICE_NAME || 'checkout';
const port = Number(process.env.PORT || 8080);
const downstream = process.env.DOWNSTREAM_URL;
let paymentRequests = 0;
const metrics = new Map();

function observe(route, status, seconds) {
  const key = `${route}|${status}`;
  const entry = metrics.get(key) || { count: 0, sum: 0, buckets: [0, 0, 0, 0, 0] };
  entry.count += 1;
  entry.sum += seconds;
  for (const [index, boundary] of [0.05, 0.1, 0.25, 0.5, 1].entries()) {
    if (seconds <= boundary) entry.buckets[index] += 1;
  }
  metrics.set(key, entry);
}

function renderMetrics() {
  const lines = [
    '# HELP http_requests_total HTTP requests handled by the demo service.',
    '# TYPE http_requests_total counter',
    '# HELP http_request_duration_seconds HTTP request duration handled by the demo service.',
    '# TYPE http_request_duration_seconds histogram',
  ];
  for (const [key, value] of metrics) {
    const [route, status] = key.split('|');
    const labels = `service="${service}",route="${route}",status="${status}"`;
    lines.push(`http_requests_total{${labels}} ${value.count}`);
    for (const [index, boundary] of [0.05, 0.1, 0.25, 0.5, 1].entries()) {
      lines.push(`http_request_duration_seconds_bucket{${labels},le="${boundary}"} ${value.buckets[index]}`);
    }
    lines.push(`http_request_duration_seconds_bucket{${labels},le="+Inf"} ${value.count}`);
    lines.push(`http_request_duration_seconds_sum{${labels}} ${value.sum}`);
    lines.push(`http_request_duration_seconds_count{${labels}} ${value.count}`);
  }
  return `${lines.join('\n')}\n`;
}

function faultMode() {
  try {
    return JSON.parse(fs.readFileSync('/config/fault.json', 'utf8'));
  } catch {
    return { delayMs: 0, failEvery: 0 };
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function callDownstream() {
  if (!downstream) return { status: 200, body: { approved: true } };
  const response = await fetch(downstream, { signal: AbortSignal.timeout(2500) });
  return { status: response.status, body: await response.json() };
}

const server = http.createServer(async (request, response) => {
  if (request.url === '/metrics') {
    response.writeHead(200, { 'content-type': 'text/plain; version=0.0.4' });
    return response.end(renderMetrics());
  }
  if (request.url === '/healthz') return response.end('ok');

  const started = performance.now();
  let status = 200;
  let payload = { ok: true, service };
  try {
    if (service === 'payments') {
      const mode = faultMode();
      paymentRequests += 1;
      if (mode.delayMs > 0) await sleep(mode.delayMs);
      if (mode.failEvery > 0 && paymentRequests % mode.failEvery === 0) {
        status = 503;
        payload = { ok: false, dependency: 'payments', reason: 'simulated_processor_error' };
      }
    } else {
      const downstreamResult = await callDownstream();
      status = downstreamResult.status === 200 ? 200 : 502;
      payload = { ok: status === 200, service, downstream: downstreamResult.body };
    }
  } catch (error) {
    status = 502;
    payload = { ok: false, service, error: error.name };
  }
  const seconds = (performance.now() - started) / 1000;
  observe(request.url || '/', status, seconds);
  console.log(JSON.stringify({ service, status, duration_ms: Math.round(seconds * 1000), reason: payload.reason || null }));
  response.writeHead(status, { 'content-type': 'application/json' });
  response.end(JSON.stringify(payload));
});

server.listen(port, () => console.log(`${service} listening on ${port}`));
