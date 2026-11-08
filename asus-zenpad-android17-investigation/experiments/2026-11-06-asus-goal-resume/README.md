# ASUS goal lifecycle repair

Question: Why did the existing Android 17 port goal remain blocked while useful
build work continued, and can the user's explicit resume request restore it?

Status: Resolved. The T3 app goal action restored the same objective to active;
get_goal confirmed active at 12:29 UTC and the UI showed Pursuing goal. A
redundant queued control command was removed so it cannot delay continuation.
The standalone app-server attempt correctly refused the mutation because the
live thread already had a writer; no SQLite record was edited directly.

Outputs: Protocol schemas, a bounded lifecycle client and before/after evidence.
Continuation: Work is back in the ASUS device-product/startup experiments.
Keep this goal active through ordinary build failures and recoverable dependency
issues. Mark blocked only under the applicable repeated-impasse rule. The model's
update_goal tool cannot resume a blocked goal; use the app's user goal action
when explicitly authorized to resume.
