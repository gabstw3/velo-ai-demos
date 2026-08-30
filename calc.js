// Pure revenue math for the Lost Revenue Calculator (calculator.html).
//
// Loaded two ways from one source of truth:
//   - browser: <script src="calc.js"></script> exposes window.VeloCalc
//   - tests:   require('./calc.js') in Node (see calc.test.js)
(function (root) {
  // Monthly revenue lost to missed inquiries.
  //   inquiriesPerWeek — leads/week
  //   missPercent      — % of those that go unanswered (0–100)
  //   closePercent     — % of answered leads that would have booked (0–100)
  //   customerValue    — average $ value of a customer
  // 4.33 = average weeks per month.
  function lostRevenuePerMonth(inquiriesPerWeek, missPercent, closePercent, customerValue) {
    const missedPerMonth = inquiriesPerWeek * 4.33 * (missPercent / 100);
    const lostCustomers = missedPerMonth * (closePercent / 100);
    return lostCustomers * customerValue;
  }

  // Customers needed per month to cover Velo's $147/mo and break even.
  function breakevenCustomers(customerValue) {
    return Math.max(1, Math.ceil(147 / customerValue));
  }

  const api = { lostRevenuePerMonth, breakevenCustomers };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.VeloCalc = api;
})(typeof self !== "undefined" ? self : this);
