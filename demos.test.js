// Validates that every Velo AI concierge demo's inline chat script actually
// COMPILES. Catches the recurring "unescaped apostrophe in a single-quoted
// string" bug (and any other JS syntax error) using the real V8 parser via
// node:vm — so, unlike a naive text scanner, it does NOT false-positive on
// apostrophes inside // comments, /regex/ literals, or `template strings`.
//
// A syntax error here means the chat silently fails to load on the live page.
//
// Run:  node --test
"use strict";
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const dir = __dirname;
const htmlFiles = fs.readdirSync(dir).filter((f) => f.endsWith(".html"));

// Inline <script> blocks only (skip ones with a src= like GoatCounter / calc.js).
function inlineScripts(html) {
  const out = [];
  const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    if (/\bsrc\s*=/i.test(m[1])) continue;
    if (m[2].trim()) out.push(m[2]);
  }
  return out;
}

for (const file of htmlFiles) {
  const html = fs.readFileSync(path.join(dir, file), "utf8");
  // Only the AI-concierge demo pages (they all define addBotMessage()).
  if (!html.includes("addBotMessage")) continue;

  test(`${file}: inline chat script compiles`, () => {
    const scripts = inlineScripts(html);
    assert.ok(scripts.length > 0, `${file}: no inline chat script found`);
    for (const src of scripts) {
      assert.doesNotThrow(
        () => new vm.Script(src),
        `Syntax error in ${file} — the chat script would fail to load on the live page`
      );
    }
  });
}
