# Reject duplicate producer records

Question: can identical raw Ninja edges hide conflicting producer scopes?

Status: parent one-line graph-selection correction. The real tiny graph/index regression fails before and passes after. It covers a unique producer, identical duplicates in one file or conflicting scopes, and different duplicate text. No native engine, real graph/index, product, device or network is used.

Outputs: source/graph.py, duplicate-producer.patch, source-pins.json and evidence/{before,after}.json.

Continuation: incorporate this exact correction into a separate capture-reader revision with the effective-binding and dyndep fixes. The other two review findings remain open. No actual capture or product admission is authorized.
