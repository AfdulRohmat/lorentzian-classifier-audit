"""Generate deterministic README figures from committed research evidence.

The script intentionally uses only pandas and Python's standard library.  The
resulting SVG files therefore remain reproducible on a clean Windows or macOS
checkout without adding a plotting dependency to the research environment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets"
WIDTH = 1600
HEIGHT = 900

INK = "#172033"
MUTED = "#657087"
GRID = "#dfe5ef"
BLUE = "#1769aa"
BLUE_LIGHT = "#a9cce8"
TEAL = "#158f84"
RED = "#c7463b"
GOLD = "#d69816"
PANEL = "#f7f9fc"


def _line(points: list[tuple[float, float]], color: str, width: float = 4.0) -> str:
    path = " ".join(
        ("M" if index == 0 else "L") + f" {x:.2f} {y:.2f}"
        for index, (x, y) in enumerate(points)
    )
    return (
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width}" '
        'stroke-linejoin="round" stroke-linecap="round"/>'
    )


def _text(
    x: float,
    y: float,
    value: str,
    *,
    size: int = 24,
    color: str = INK,
    weight: int = 400,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" font-family="Inter,Segoe UI,Arial,sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}" '
        f'text-anchor="{anchor}">{escape(value)}</text>'
    )


def _svg_document(body: list[str], title: str, description: str) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title>',
            f'<desc id="desc">{escape(description)}</desc>',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            *body,
            "</svg>",
            "",
        ]
    )


@dataclass(frozen=True)
class Scale:
    source_min: float
    source_max: float
    target_min: float
    target_max: float

    def __call__(self, value: float) -> float:
        if self.source_max == self.source_min:
            return (self.target_min + self.target_max) / 2
        fraction = (value - self.source_min) / (self.source_max - self.source_min)
        return self.target_min + fraction * (self.target_max - self.target_min)


def generate_equity_curve() -> Path:
    source = ROOT / "evidence" / "v3_atr_runner_sizing" / "accounts.csv.gz"
    frame = pd.read_csv(source, parse_dates=["entry_time", "exit_time"])
    frame = frame[
        (frame["asset"] == "sp500")
        & (frame["timeframe"] == "30min")
        & (frame["initial_balance_usd"] == 500)
        & (frame["risk_percent"] == 1)
    ].sort_values(["exit_time", "trade_id"])
    if len(frame) != 688:
        raise RuntimeError(f"Expected 688 SP500 M30 rows, found {len(frame)}")

    start = pd.Timestamp("2024-01-01T00:00:00Z")
    dates = pd.concat([pd.Series([start]), frame["exit_time"].reset_index(drop=True)])
    equity = pd.concat([pd.Series([500.0]), frame["equity_after"].reset_index(drop=True)])
    running_peak = equity.cummax()
    drawdown = (equity / running_peak - 1.0) * 100.0

    left, right = 135.0, 1535.0
    equity_top, equity_bottom = 185.0, 590.0
    dd_top, dd_bottom = 680.0, 805.0
    time_values = dates.map(pd.Timestamp.timestamp).astype(float)
    x_scale = Scale(time_values.min(), time_values.max(), left, right)
    equity_min = float(equity.min())
    equity_max = float(equity.max())
    padding = (equity_max - equity_min) * 0.08
    y_scale = Scale(equity_min - padding, equity_max + padding, equity_bottom, equity_top)
    dd_floor = min(-25.0, float(drawdown.min()) * 1.08)
    dd_scale = Scale(dd_floor, 0.0, dd_bottom, dd_top)

    body = [
        _text(
            80, 68, "SP500 M30 Lorentzian ATR runner — simulated equity", size=38, weight=700
        ),
        _text(
            80,
            108,
            "USD 500 start · 1% current-equity risk · Exness cost model · Jan 2024-Aug 2026",
            size=23,
            color=MUTED,
        ),
        f'<rect x="{left}" y="{equity_top}" width="{right - left}" '
        f'height="{equity_bottom - equity_top}" rx="10" fill="{PANEL}"/>',
        f'<rect x="{left}" y="{dd_top}" width="{right - left}" '
        f'height="{dd_bottom - dd_top}" rx="10" fill="{PANEL}"/>',
    ]

    # Equity grid and labels.
    first_tick = int((equity_min - padding) // 100 * 100)
    last_tick = int((equity_max + padding + 99) // 100 * 100)
    for value in range(first_tick, last_tick + 1, 100):
        y = y_scale(float(value))
        if equity_top <= y <= equity_bottom:
            body.append(
                f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" '
                f'stroke="{GRID}" stroke-width="1"/>'
            )
            body.append(
                _text(left - 18, y + 8, f"${value:,}", size=20, color=MUTED, anchor="end")
            )

    tick_dates = [
        pd.Timestamp("2024-01-01T00:00:00Z"),
        pd.Timestamp("2024-07-01T00:00:00Z"),
        pd.Timestamp("2025-01-01T00:00:00Z"),
        pd.Timestamp("2025-07-01T00:00:00Z"),
        pd.Timestamp("2026-01-01T00:00:00Z"),
        pd.Timestamp("2026-07-01T00:00:00Z"),
    ]
    for tick in tick_dates:
        x = x_scale(tick.timestamp())
        body.extend(
            [
                f'<line x1="{x:.2f}" y1="{equity_top}" x2="{x:.2f}" y2="{dd_bottom}" '
                f'stroke="{GRID}" stroke-width="1" stroke-dasharray="5 7"/>',
                _text(x, 846, tick.strftime("%b %Y"), size=19, color=MUTED, anchor="middle"),
            ]
        )

    body.append(
        _line(
            list(
                zip(
                    time_values.map(x_scale),
                    equity.map(lambda value: y_scale(float(value))),
                    strict=True,
                )
            ),
            BLUE,
            4.5,
        )
    )
    body.append(
        f'<line x1="{left}" y1="{y_scale(500):.2f}" x2="{right}" y2="{y_scale(500):.2f}" '
        f'stroke="{MUTED}" stroke-width="2" stroke-dasharray="9 9"/>'
    )

    # Drawdown panel.
    zero_y = dd_scale(0.0)
    dd_points = list(
        zip(
            time_values.map(x_scale),
            drawdown.map(lambda value: dd_scale(float(value))),
            strict=True,
        )
    )
    polygon = " ".join(f"{x:.2f},{y:.2f}" for x, y in dd_points)
    polygon = f"{left:.2f},{zero_y:.2f} {polygon} {right:.2f},{zero_y:.2f}"
    body.extend(
        [
            f'<polygon points="{polygon}" fill="#f1b4ae" opacity="0.72"/>',
            _line(dd_points, RED, 2.5),
            _text(left - 18, dd_top + 7, "0%", size=19, color=MUTED, anchor="end"),
            _text(left - 18, dd_bottom, f"{dd_floor:.0f}%", size=19, color=MUTED, anchor="end"),
            _text(80, 656, "Drawdown", size=21, weight=600),
        ]
    )

    final_equity = float(equity.iloc[-1])
    executed = int((frame["status"] == "EXECUTED").sum())
    skipped = int((frame["status"] != "EXECUTED").sum())
    body.extend(
        [
            f'<circle cx="{right:.2f}" cy="{y_scale(final_equity):.2f}" r="7" fill="{BLUE}"/>',
            _text(
                right - 14,
                y_scale(final_equity) - 18,
                f"Final ${final_equity:,.2f}",
                size=24,
                weight=700,
                anchor="end",
            ),
            _text(
                80,
                884,
                f"Executed {executed} · skipped {skipped} · "
                f"max drawdown {abs(drawdown.min()):.2f}%",
                size=21,
                color=MUTED,
            ),
            _text(
                1520,
                884,
                "Research simulation; margin and swap not modeled",
                size=19,
                color=MUTED,
                anchor="end",
            ),
        ]
    )

    target = ASSET_DIR / "sp500_m30_equity_curve.svg"
    target.write_text(
        _svg_document(
            body,
            "SP500 M30 simulated equity curve",
            "USD 500 account at one percent risk grows to USD 922.85 "
            "with a 23.64 percent maximum drawdown.",
        ),
        encoding="utf-8",
    )
    return target


def generate_monte_carlo() -> Path:
    source = ROOT / "evidence" / "v4_tail_robustness" / "summary.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload["historical"]["monte_carlo"]
    if len(rows) != 4:
        raise RuntimeError(f"Expected four Monte Carlo scenarios, found {len(rows)}")

    probabilities = [float(row["tail_miss_probability"]) * 100.0 for row in rows]
    lows = [float(row["total_r_ci95_median"][0]) for row in rows]
    medians = [float(row["total_r_ci95_median"][1]) for row in rows]
    highs = [float(row["total_r_ci95_median"][2]) for row in rows]
    positive = [float(row["probability_total_r_positive"]) * 100.0 for row in rows]
    drawdowns = [
        float(row["one_percent_max_drawdown_fraction_ci95_median"][1]) * 100.0 for row in rows
    ]

    left, right = 150.0, 1515.0
    top, bottom = 190.0, 595.0
    lower_top, lower_bottom = 690.0, 820.0
    x_positions = [left + (right - left) * index / 3 for index in range(4)]
    y_scale = Scale(-50.0, 80.0, bottom, top)
    probability_scale = Scale(0.0, 100.0, lower_bottom, lower_top)
    drawdown_scale = Scale(20.0, 45.0, lower_bottom, lower_top)

    body = [
        _text(80, 68, "SP500 M30 tail-miss Monte Carlo", size=38, weight=700),
        _text(
            80,
            108,
            "20,000 simulations per scenario · only >3R winners may be missed · "
            "every losing trade retained",
            size=23,
            color=MUTED,
        ),
        f'<rect x="{left}" y="{top}" width="{right - left}" height="{bottom - top}" '
        f'rx="10" fill="{PANEL}"/>',
        f'<rect x="{left}" y="{lower_top}" width="{right - left}" '
        f'height="{lower_bottom - lower_top}" '
        f'rx="10" fill="{PANEL}"/>',
    ]

    for value in [-40, -20, 0, 20, 40, 60, 80]:
        y = y_scale(float(value))
        body.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" '
                f'stroke="{GRID}" stroke-width="{2 if value == 0 else 1}"/>',
                _text(left - 20, y + 8, f"{value:+d}R", size=20, color=MUTED, anchor="end"),
            ]
        )

    # Confidence interval, median points and labels.
    polygon_points = [
        *(f"{x:.2f},{y_scale(high):.2f}" for x, high in zip(x_positions, highs, strict=True)),
        *(
            f"{x:.2f},{y_scale(low):.2f}"
            for x, low in reversed(list(zip(x_positions, lows, strict=True)))
        ),
    ]
    body.append(
        f'<polygon points="{" ".join(polygon_points)}" fill="{BLUE_LIGHT}" opacity="0.62"/>'
    )
    median_points = list(zip(x_positions, (y_scale(value) for value in medians), strict=True))
    body.append(_line(median_points, BLUE, 5.0))
    for x, low, median, high, probability in zip(
        x_positions, lows, medians, highs, probabilities, strict=True
    ):
        body.extend(
            [
                f'<line x1="{x:.2f}" y1="{y_scale(low):.2f}" x2="{x:.2f}" '
                f'y2="{y_scale(high):.2f}" stroke="{BLUE}" stroke-width="3"/>',
                f'<circle cx="{x:.2f}" cy="{y_scale(median):.2f}" r="8" fill="{BLUE}"/>',
                _text(
                    x,
                    y_scale(median) - 20,
                    f"{median:+.1f}R",
                    size=22,
                    weight=700,
                    anchor="middle",
                ),
                _text(
                    x,
                    858,
                    f"{probability:.0f}% tails missed",
                    size=21,
                    color=MUTED,
                    anchor="middle",
                ),
            ]
        )

    body.extend(
        [
            _text(80, 164, "Final total R: median and 95% interval", size=22, weight=600),
            _text(80, 662, "Chance total R stays positive", size=22, weight=600),
        ]
    )

    bar_width = 130.0
    dd_points: list[tuple[float, float]] = []
    for x, chance, dd in zip(x_positions, positive, drawdowns, strict=True):
        y = probability_scale(chance)
        body.extend(
            [
                f'<rect x="{x - bar_width / 2:.2f}" y="{y:.2f}" width="{bar_width:.2f}" '
                f'height="{lower_bottom - y:.2f}" rx="8" fill="{TEAL}" opacity="0.82"/>',
                _text(
                    x,
                    y - 10,
                    f"{chance:.1f}%",
                    size=20,
                    color=TEAL,
                    weight=700,
                    anchor="middle",
                ),
            ]
        )
        dd_points.append((x, drawdown_scale(dd)))
    body.append(_line(dd_points, GOLD, 4.0))
    for index, ((x, y), dd) in enumerate(zip(dd_points, drawdowns, strict=True)):
        label_x = x - 13 if index == len(dd_points) - 1 else x + 13
        anchor = "end" if index == len(dd_points) - 1 else "start"
        body.extend(
            [
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="{GOLD}"/>',
                _text(
                    label_x,
                    y + 7,
                    f"DD {dd:.1f}%",
                    size=18,
                    color="#966800",
                    weight=600,
                    anchor=anchor,
                ),
            ]
        )

    body.extend(
        [
            _text(
                80,
                888,
                "Blue: final R distribution · green: P(total R > 0) · "
                "gold: median 1% sizing drawdown",
                size=20,
                color=MUTED,
            ),
            _text(
                1520,
                888,
                "Tail-risk stress test, not a return forecast",
                size=19,
                color=MUTED,
                anchor="end",
            ),
        ]
    )

    target = ASSET_DIR / "sp500_m30_tail_monte_carlo.svg"
    target.write_text(
        _svg_document(
            body,
            "SP500 M30 tail-miss Monte Carlo",
            "Strategy resilience deteriorates sharply when twenty to thirty percent "
            "of greater-than-three-R winners are missed.",
        ),
        encoding="utf-8",
    )
    return target


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [generate_equity_curve(), generate_monte_carlo()]
    now = datetime.now(UTC).isoformat(timespec="seconds")
    for output in outputs:
        print(f"generated {output.relative_to(ROOT)} at {now}")


if __name__ == "__main__":
    main()
