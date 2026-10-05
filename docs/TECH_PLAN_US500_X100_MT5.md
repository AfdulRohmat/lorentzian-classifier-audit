# US500 x100 native MT5 audit

This work verifies whether the frozen Python SP500 M30 causal Lorentzian ATR runner can be reproduced and executed in MT5 Strategy Tester. It does not authorize live or demo account orders, observation mode, Telegram, or forward testing. The original research and conditional x100 sizing study remain unchanged.

## Frozen scope

- Parent revision: c0d309a15b5058555ef4744fa7ae9f2a561daa82.
- Branch: research/us500-x100-mt5-audit.
- Reference: contract_v3_atr_runner_sizing.json and conditional contract_us500_x100_sizing.json.
- Source anchor: January 2022. Evaluation: January 2024 through August 2026, subject to actual broker availability. Short smoke tests are engineering tests, not performance replacements.
- Primary audit account: USD 3000, risk 1% of closed balance, floor to volume step, skip below minimum. This is not a selected forward-test account configuration.
- No optimization, altered features, entry filters, exit parameters, or post-result timeframe selection.

## Stages and acceptance

1. Read-only broker audit: exact symbol, contract, tick value and size, volume bounds, stops/freeze, margin, currencies, sessions, available bars and ticks. Record unavailable fields rather than infer them from the x100 suffix. Never persist credentials or account identity.
2. Tester-only EA: independently calculate the five features, kernel, filters, matured-label nearest neighbors and transition signals. Preserve full historical normalization, price quantization and closed-bar timing. One position, one ATR stop, no fixed TP, net-R close-based trail, opposite reversal and 24-hour deadline at the first available quote. Fail closed outside Strategy Tester.
3. Verification: compile, compare features/predictions/starts on identical bars, exercise synthetic boundaries, run broker-native smoke and historical tests where available. Native tick fills need not equal M1 approximations. A missing test or history is not a pass.
4. Reconciliation: classify discrepancies by history, model, rounding, quote/spread, sizing, margin, stop handling, commission/swap and tick path. Report counts and unresolved differences. A positive PnL cannot waive signal or execution defects.

## Engineering constraints

Use immutable run folders, hashes, redacted evidence, tests and explicit failure statuses. Do not overwrite a user EA, terminate a pre-existing terminal, or submit external orders. Compilation and tester artifacts are isolated and ignored. Existing terminal must be closed for configured tester launches. Native simulator runs are allowed; real-account execution is blocked in code.

Historical running normalization requires an anchored prehistory. Broker-native histories may differ from archived US500 data; compare identical-bar parity separately from feed transfer. Numpy argpartition does not define a stable neighbor tie policy: detect boundary ties and do not conceal changed predictions.

Native commission and swap are taken from tester deals where available. The legacy commission/slippage inputs remain modeling assumptions, not verified broker fees. Real-tick mode may generate ticks for gaps; record the model and available quality evidence rather than calling all fills real.

## Completion report

Deliver source, reproducible commands, tests, per-stage status, any compiled artifact hash, parity metrics, native tester evidence if actually obtained, and an explicit remaining gate before forward testing. If broker access blocks native verification, finish safe local engineering and label stages three/four incomplete.

## Official references

- [MT5 testing runtime](https://www.mql5.com/en/docs/runtime/testing).
- [Real and generated ticks](https://www.metatrader5.com/en/terminal/help/algotrading/tick_generation).
- [Strategy Tester settings](https://www.metatrader5.com/en/terminal/help/algotrading/testing).
