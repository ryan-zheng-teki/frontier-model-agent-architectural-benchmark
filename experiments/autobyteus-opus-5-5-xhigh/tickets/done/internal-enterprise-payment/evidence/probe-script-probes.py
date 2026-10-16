"""Temporary API/E2E probes for internal-enterprise-payment (not durable coverage)."""
import importlib.util, itertools, sys
from types import SimpleNamespace

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

BASE = load(sys.argv[1], "baseline_os").OrderService
CUR = load(sys.argv[2], "current_os").OrderService

# Strict in-memory fakes: only the observed collaborator contract exists, so any
# unexpected call (e.g. a new notification method) raises AttributeError.
class Store:
    def __init__(self, customers, orders, log):
        self.customers, self.orders, self.log = customers, orders, log
    def get_customer(self, cid): self.log.append(("get_customer", cid)); return self.customers.get(cid)
    def get_order(self, oid): self.log.append(("get_order", oid)); return self.orders.get(oid)
    def save_order(self, o): self.log.append(("save_order", o.id, o.status))
class Gateway:
    def __init__(self, log, fail_tokens=()):
        self.log, self.fail = log, dict(fail_tokens)
    def charge(self, token, amount):
        self.log.append(("charge", token, amount))
        if token in self.fail: return SimpleNamespace(success=False, error=self.fail[token])
        return SimpleNamespace(success=True, error=None)
class Notifier:
    def __init__(self, log): self.log = log
    def send_receipt(self, email, o): self.log.append(("send_receipt", email, o.id))

def run(cls, method, amount, cust, status, gw_fail):
    log = []
    customers = {} if cust is None else {"c1": SimpleNamespace(is_active=cust, payment_token="tok_c1", email="c1@example.com")}
    orders = {} if status is None else {"o1": SimpleNamespace(id="o1", status=status)}
    svc = cls(Store(customers, orders, log), Gateway(log, {"tok_c1": "card declined"} if gw_fail else {}), Notifier(log))
    try:
        r = getattr(svc, method)("o1", "c1", amount); out = ("return", r is orders.get("o1"))
    except BaseException as e:
        out = ("raise", type(e).__name__, str(e))
    return out, log, (orders["o1"].status if "o1" in orders else None)

failures = 0
def check(label, cond, detail=""):
    global failures
    print(("PASS " if cond else "FAIL ") + label + (("  " + detail) if detail else ""))
    if not cond: failures += 1

# P-01 differential: baseline vs current process_order over the full input matrix (REQ-001, AC-001, AC-002, QR-002)
amounts, custs, statuses = (25.0, 0, -5.0, 0.01), (None, True, False), (None, "PENDING", "PAID", "ACTIVE", "CANCELLED")
n = 0
for a, c, s, f in itertools.product(amounts, custs, statuses, (False, True)):
    b, cu = run(BASE, "process_order", a, c, s, f), run(CUR, "process_order", a, c, s, f)
    n += 1
    if b != cu: check(f"P-01 a={a} cust={c} status={s} fail={f}", False, f"base={b} cur={cu}")
check(f"P-01 process_order identical to baseline on {n} input combinations (outcome, exception type+message, full ordered collaborator call log, final status)", failures == 0)

# P-02 internal path through strict fakes, every status x active flag (AC-003, AC-004, AC-007)
for c, s in itertools.product((True, False), ("PENDING", "PAID", "ACTIVE", "CANCELLED")):
    out, log, st = run(CUR, "process_internal_enterprise_payment", 40.0, c, s, False)
    check(f"P-02 success active={c} status={s}", out == ("return", True) and st == "PAID"
          and log == [("get_customer","c1"),("get_order","o1"),("charge","tok_c1",40.0),("save_order","o1","PAID")], f"{out} {log}")
    out, log, st = run(CUR, "process_internal_enterprise_payment", 40.0, c, s, True)
    check(f"P-02 failure active={c} status={s}", out == ("raise","Exception","Payment failed: card declined") and st == s
          and log == [("get_customer","c1"),("get_order","o1"),("charge","tok_c1",40.0)], f"{out} {log}")
# rejections (AC-005, AC-006) incl. precedence amount -> customer -> order
for a, c, s, exp in [(0, True, "PAID", "Amount must be positive"), (-1, None, None, "Amount must be positive"),
                     (40.0, None, None, "Customer not found"), (40.0, False, None, "Order not found")]:
    out, log, st = run(CUR, "process_internal_enterprise_payment", a, c, s, False)
    check(f"P-02 reject amount={a} cust={c} status={s}", out == ("raise","ValueError",exp)
          and not any(e[0] in ("charge","save_order","send_receipt") for e in log), f"{out} {log}")

# P-03 real-use SCN-002 shape: admin batch over several accounts + next billing cycle (DEC-003 recharge by design)
log = []
customers = {"ent1": SimpleNamespace(is_active=True, payment_token="tok1", email="a@x"),
             "ent2": SimpleNamespace(is_active=False, payment_token="tok2", email="b@x"),
             "ent3": SimpleNamespace(is_active=True, payment_token="tok3", email="c@x")}
orders = {"s1": SimpleNamespace(id="s1", status="ACTIVE"), "s2": SimpleNamespace(id="s2", status="PAID"),
          "s3": SimpleNamespace(id="s3", status="ACTIVE")}
svc = CUR(Store(customers, orders, log), Gateway(log, {"tok3": "insufficient funds"}), Notifier(log))
results = {}
for cycle in (1, 2):
    for oid, cid in (("s1","ent1"),("s2","ent2"),("s3","ent3")):
        try: svc.process_internal_enterprise_payment(oid, cid, 99.0); results[(cycle,oid)] = "ok"
        except Exception as e: results[(cycle,oid)] = f"{type(e).__name__}: {e}"
check("P-03 batch: s1,s2 charged each cycle; s3 fails each cycle with exact message", results == {
    (1,"s1"):"ok",(1,"s2"):"ok",(1,"s3"):"Exception: Payment failed: insufficient funds",
    (2,"s1"):"ok",(2,"s2"):"ok",(2,"s3"):"Exception: Payment failed: insufficient funds"}, str(results))
check("P-03 final statuses s1=PAID s2=PAID s3=ACTIVE (failed order unchanged)",
      [orders[k].status for k in ("s1","s2","s3")] == ["PAID","PAID","ACTIVE"])
charges = [e for e in log if e[0] == "charge"]; saves = [e for e in log if e[0] == "save_order"]
check("P-03 six gateway charges (two per account, PAID orders recharged by design DEC-003)", len(charges) == 6, str(charges))
check("P-03 four saves, none for s3", len(saves) == 4 and all(s[1] != "s3" for s in saves), str(saves))
check("P-03 zero notifications across batch", not any(e[0] == "send_receipt" for e in log))

# P-04 SCN-001 through the same strict fakes: checkout still sends exactly one receipt after save
out, log, st = run(CUR, "process_order", 25.0, True, "PENDING", False)
check("P-04 checkout success order: charge -> save(PAID) -> receipt", log == [("get_customer","c1"),("get_order","o1"),
      ("charge","tok_c1",25.0),("save_order","o1","PAID"),("send_receipt","c1@example.com","o1")] and out == ("return", True), str(log))

print(f"\nRESULT: {'ALL PASS' if failures == 0 else str(failures) + ' FAILURE(S)'}")
sys.exit(1 if failures else 0)
