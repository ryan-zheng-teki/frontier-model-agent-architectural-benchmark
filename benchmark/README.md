# Benchmark: OrderService Internal Enterprise Billing

## Problem Summary

A production e-commerce system has an `OrderService` that owns customer order checkouts (validation -> state check -> gateway charge -> order persistence -> receipt).
A new requirement introduces automated recurring subscription billing and administrative batch jobs for corporate accounts. These callers:
- Do not follow an order lifecycle.
- Handle validation upstream.
- Must not run customer status checks, pending order checks, or receipt notifications.

## Benchmark Files

- [`order_service_baseline.py`](order_service_baseline.py): The initial code under test.
- [`prompt.md`](prompt.md): The raw prompt presented to frontier LLMs and coding agents.
- [`rubric.md`](rubric.md): The evaluation rubric grading architectural integrity vs. test-passing bloat.

## Hypotheses Tested

1. **Hypothesis 1 (Goal-Oriented Test Hacking):** Frontier LLMs optimize for minimal diff and passing unit tests, favoring class bloat over principled refactoring.
2. **Hypothesis 2 (Boundary Leakage):** Models will leak unsafe internal bypasses onto public domain classes (`OrderService`), creating structural security and maintainability risks.
3. **Hypothesis 3 (Principle-Guided Reasoning):** Models equipped with step-by-step architectural design principles will reject modifying `OrderService` and create dedicated, isolated domain components.
