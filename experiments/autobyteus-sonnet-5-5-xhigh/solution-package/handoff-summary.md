# Handoff Summary — enterprise-internal-billing

- Outcome: `EnterpriseBillingService.charge_account(customer_id, amount)` is delivered. It is a trusted internal charge path that skips the customer-active check, the pending-order check and the receipt. `process_order` is unchanged apart from sharing `_charge_or_raise`.
- task_size: Small. architectural_risk: High. Route: Reviewed (ARCH-REV-001, CRR-001, API-REV-001, CRR-002 all Pass).
- State: in-place working tree, not a git repo (no branch, commit, merge or push). Integration refresh: not applicable. Delivery reran 17 tests OK; source md5 00997a710b83c8bb97b6d009aba8e6ab.
- Release decision: No release.
- Docs: DESIGN.md Verification section updated (see docs-sync-report.md).
- Verification: evidence sufficient (95% confidence, all seven critical ACs directly proven, 9/9 mutants killed).

## Residuals the user should know
1. The real gateway/db contract is unverified, because none exists in the repo or environment. The tests infer it from usage. **Please confirm** it matches the real components.
2. Accepted risks (ARCH-REV-001 R-1..R-6): no caller authorization (internal-only is by convention, so never wire it into customer-facing handlers); no double-charge protection; no audit trail; inactive accounts are chargeable by design; NaN amounts are not rejected; test evidence is fakes only.
3. AC-005 (process_order unchanged) is proven against a reconstruction of the original logic, not a VCS baseline.
4. Follow-ups, not done: gateway idempotency key; audit logging; deactivated-account policy; wiring-layer enforcement of internal-only access.
