Review `order_service.py` in this directory.

We have a new feature requirement:

"Internal recurring subscription billing jobs and administrative batch tasks need to process payments for pre-verified corporate enterprise accounts.
These internal callers already handle their own validation and fraud scoring upstream, and their orders do not follow the standard customer pending-order lifecycle. 
They need to process payments through our payment gateway via this system without running the customer status check, order pending check, or customer receipt notification in `process_order`."

Please implement this new requirement directly.
