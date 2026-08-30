// Tests for the Lost Revenue Calculator math (calc.js).
//
// These lock down the formula prospects see on calculator.html — a wrong
// multiplier (e.g. weeks-per-month, or a stray /100) would quietly misquote
// every visitor's "lost revenue" number.
//
// Zero dependencies — uses Node's built-in runner.
// Run with:  node --test
const test = require("node:test");
const assert = require("node:assert/strict");

const { lostRevenuePerMonth, breakevenCustomers } = require("./calc.js");

test("lostRevenuePerMonth: worked example", () => {
  // 10/wk × 4.33 × 30% missed = 12.99 missed/mo
  // × 40% close = 5.196 lost customers × $500 = 2598
  assert.equal(lostRevenuePerMonth(10, 30, 40, 500), 2598);
});

test("lostRevenuePerMonth: zero missed share => no loss", () => {
  assert.equal(lostRevenuePerMonth(20, 0, 50, 400), 0);
});

test("lostRevenuePerMonth: zero inquiries => no loss", () => {
  assert.equal(lostRevenuePerMonth(0, 50, 50, 400), 0);
});

test("lostRevenuePerMonth: zero close rate => no loss", () => {
  assert.equal(lostRevenuePerMonth(20, 50, 0, 400), 0);
});

test("lostRevenuePerMonth: uses 4.33 weeks/month", () => {
  // 100% miss, 100% close, $1 value => exactly inquiries × 4.33.
  assert.ok(Math.abs(lostRevenuePerMonth(1, 100, 100, 1) - 4.33) < 1e-9);
});

test("lostRevenuePerMonth: scales linearly with customer value", () => {
  const a = lostRevenuePerMonth(10, 30, 40, 500);
  const b = lostRevenuePerMonth(10, 30, 40, 1000);
  assert.ok(Math.abs(b - 2 * a) < 1e-9);
});

test("lostRevenuePerMonth: more missed leads => more loss", () => {
  assert.ok(lostRevenuePerMonth(10, 50, 50, 300) > lostRevenuePerMonth(10, 20, 50, 300));
});

test("breakevenCustomers: exactly the $147 price => 1", () => {
  assert.equal(breakevenCustomers(147), 1);
});

test("breakevenCustomers: high-value customer floors at 1", () => {
  assert.equal(breakevenCustomers(1000), 1);
});

test("breakevenCustomers: rounds up partial customers", () => {
  assert.equal(breakevenCustomers(50), 3); // ceil(147/50) = ceil(2.94)
  assert.equal(breakevenCustomers(100), 2); // ceil(1.47)
  assert.equal(breakevenCustomers(10), 15); // ceil(14.7)
});
