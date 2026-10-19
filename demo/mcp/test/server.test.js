const assert = require('node:assert/strict');
const test = require('node:test');
const { assertService, dependencyServices, lokiQuery, prometheusQuery, queries, tools, validateWindow } = require('../server');

test('accepts only known demo services', () => {
  assert.doesNotThrow(() => assertService('payments'));
  assert.throws(() => assertService('admin'));
});

test('bounds evidence windows to one hour', () => {
  assert.deepEqual(validateWindow('2026-09-24T08:00:00Z', '2026-09-24T08:30:00Z'), {
    start: '2026-09-24T08:00:00.000Z',
    end: '2026-09-24T08:30:00.000Z',
  });
  assert.throws(() => validateWindow('2026-09-24T08:00:00Z', '2026-09-24T09:01:00Z'));
});

test('constructs fixed read-only source queries', () => {
  const metrics = new URL(prometheusQuery(queries.service_health('orders')));
  const logs = new URL(lokiQuery(queries.top_error_signatures('payments'), '2026-09-24T08:00:00Z', '2026-09-24T08:30:00Z'));
  assert.equal(metrics.pathname, '/api/v1/query');
  assert.match(metrics.searchParams.get('query'), /service="orders"/);
  assert.equal(logs.pathname, '/loki/api/v1/query_range');
  assert.equal(logs.searchParams.get('limit'), '20');
});

test('uses the fixed demo dependency graph', () => {
  assert.deepEqual(dependencyServices('checkout'), ['orders', 'payments']);
  assert.deepEqual(dependencyServices('orders'), ['payments']);
});

test('does not provide mutation or arbitrary query tools', () => {
  assert.equal(tools.some((tool) => /delete|patch|apply|restart|query/i.test(tool.name)), false);
  assert.equal(tools.every((tool) => tool.inputSchema.additionalProperties === false), true);
});
