# Official model cold-restart diagnostic

The same untouched indicator and tester wrapper run continuously from January, then separately cold-start in February. We compare only actually observed closed-bar predictions, directions and starts at common timestamps through August. Market bars, VWAP, sigma and compiled builds must remain identical.

| Symbol | Overlap bars | Prediction changes | Direction changes | Start changes | Verdict |
|---|---:|---:|---:|---:|---|
| US500 | 6903 | 0 | 0 | 0 | MATCH_ON_THIS_REPLAY |
| US500_x100 | 6903 | 0 | 0 | 0 | MATCH_ON_THIS_REPLAY |

A mismatch is state/history-start dependence, not proof that previously observed online signals used future data. Endpoint-prefix and next-bar stability test other properties. A matching restart is also not proof of live every-tick calculation parity.
The comparison JSON records the native history origin and initial bar count for both starts, so a preload-origin change is not misreported as pure ANN state dependence.

These two runs are diagnostic only, not additional optimization candidates. Their portfolios start later and are not compared as investment performance. The generic runner's eight-month frequency/monthly summaries on these February-start artifacts are not used as seven-month performance statistics.

Evidence: [comparison JSON](../evidence/native_vwap_restart/comparison.json), [every mismatching timestamp](../evidence/native_vwap_restart/signal_differences.csv), [engineering notes](NATIVE_VWAP_ENGINEERING_NOTES.md).
