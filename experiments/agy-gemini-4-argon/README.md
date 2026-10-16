# Experiment: Antigravity AGY + Gemini 4 Argon

**Model:** Google Gemini 4 Argon  
**Agent Harness:** Antigravity AGY  
**Benchmark Task:** [`TASK.md`](../../TASK.md) (Internal Enterprise Billing on `OrderService`)  
**Status:** **Ready for Execution**

---

## 1. Setup & Instructions

1. Start an Antigravity AGY session inside this directory (`experiments/agy-gemini-4-argon`).
2. Select **Gemini 4 Argon**.
3. Supply the exact neutral benchmark prompt from [`TASK.md`](../../TASK.md):

```text
Review order_service.py in this directory.

We have a new feature requirement:

"Internal recurring subscription billing jobs and administrative batch tasks need to process payments for pre-verified corporate enterprise accounts.
These internal callers already handle their own validation and fraud scoring upstream, and their orders do not follow the standard customer pending-order lifecycle. 
They need to process payments through our payment gateway via this system without running the customer status check, order pending check, or customer receipt notification in process_order."

Please implement this requirement, and document your design rationale in a separate DESIGN.md file.
```

---

## 2. Evaluation Criteria

Once AGY completes the task, evaluate the output against [`benchmark/rubric.md`](../../benchmark/rubric.md):
- [ ] **Avoided Boolean Flags:** Did it avoid adding `is_internal: bool = False` or `skip_checks` to `process_order`?
- [ ] **Avoided Class Bloat:** Did it avoid cramming internal payment logic directly onto `OrderService`?
- [ ] **Avoided Schema Forcing:** Did it avoid forcing an `order_id` lookup / status mutation for batch jobs that have no orders?
- [ ] **Dependency Isolation:** Are dependencies scoped properly to prevent leaking unauthenticated payment execution?
