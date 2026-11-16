// Focused subset: vertical ascent, five-light framing and replay across screens.
process.argv.push('--homecoming-only');
await import('./verify.mjs');
