// Focused subset of the same browser assertions used by npm test.
process.argv.push('--arrivals-only');
await import('./verify.mjs');
