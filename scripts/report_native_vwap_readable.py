"""Readable account comparisons from independently validated native results."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def f(value, digits=2):
    return "n/a" if value is None or pd.isna(value) else f"{value:,.{digits}f}"


def main():
    root = Path(__file__).resolve().parents[1]
    evidence = root / "evidence/native_vwap_2026_v3"
    records = json.loads((evidence / "validated_results.json").read_text())
    primary = [r for r in records if not r["smoke"]]
    summary = json.loads((evidence / "validated_summary.json").read_text())
    restart = json.loads((root / "evidence/native_vwap_restart/comparison.json").read_text())
    selected = [r for r in primary if r["balance"] == 3000 and r["sizing"] == 2]
    lookup = {r["tag"]: r for r in primary}
    lines = [
        "# Diskusi hasil Lorentzian + VWAP di MT5",
        "",
        "Seluruh angka di bawah berasal dari Strategy Tester MT5 dan ledger native, "
        "bukan simulasi fill Python. Python dipakai untuk audit independen dan laporan.",
        "",
        "## Kesimpulan utama",
        "",
        "Ada perbaikan historis pada beberapa pasangan, terutama swing dan model "
        "modifikasi. Tetapi VWAP memperburuk intraday model resmi pada banyak "
        "konfigurasi, dan jumlah trade turun tajam. Delapan interval bootstrap "
        "pasangan lot tetap semuanya masih melintasi nol; peningkatan yang robust "
        "belum terbukti. Verdict: **VWAP_UPGRADE_NOT_CONFIRMED**.",
        "",
        "Hipotesis dekat pusat VWAP mendapatkan lebih banyak observasi daripada "
        "hipotesis reversal dari band. Yang terakhir hanya memiliki satu kejadian "
        "unik dalam acuan lot tetap. Kita belum mengganti baseline atau "
        "mengaktifkan EA forward. Ini bukan kesimpulan bahwa semua penggunaan "
        "VWAP atau seluruh model Lorentzian pasti gagal.",
        "",
        "## Ruang lingkup dan cara membaca",
        "",
        "Januari-Agustus 2026, M30, Exness US500 dan US500_x100. Modal $500, $1.000, "
        "$3.000; lot minimum tetap atau risiko ketat 1-5% dari saldo berjalan. "
        "288 kombinasi, ditambah empat smoke test dan dua diagnostik restart. "
        "Semua laporan utama menyatakan 100% real ticks; ini tidak menjamin bahwa "
        "semua spesifikasi broker historis atau eksekusi live sudah direplikasi.",
        "",
        f"Matriks: **{summary['positive']} positif, {summary['negative']} negatif, "
        f"{summary['no_trade']} tanpa trade**. Baris modal/risiko berbagi sejarah "
        "dan sinyal; jumlah baris positif bukan jumlah bukti independen.",
        "",
        "Model M adalah causal exact-KNN modifikasi sebelumnya. Model A adalah "
        "source resmi MQL5 v1.00 yang dikompilasi tanpa mengubah algoritmenya; "
        "bukan klaim parity binary Market atau chart TradingView. Kedua model "
        "mendapat wrapper exit dan sizing yang sama.",
        "",
        "SL awal 3 ATR14 M30. Trailing aktif setelah +1R, berjarak 1R, hanya "
        "mengencang memakai quote pada penutupan bar. Tidak ada TP tetap. "
        "Sinyal lawan mentah tetap menutup posisi meskipun entry balik ditolak VWAP. "
        "Swing boleh menginap; intraday hanya mengambil bar sesi New York dan "
        "menutup posisi 15.45 New York.",
        "",
        "VWAP memakai HLC3 dan tick volume broker, reset 00.00 UTC. Di dalam "
        "1 sigma kedua arah boleh; di bawah -1 sampai -3 sigma hanya buy; di atas "
        "+1 sampai +3 sigma hanya sell. Lewat 3 sigma atau benchmark belum valid: "
        "skip. VWAP tidak menciptakan atau menunda sinyal model. Ini satu definisi "
        "mekanikal ide screenshot, bukan pengujian semua cara memakai VWAP.",
        "",
        "## Contoh perbandingan seragam: $3.000, risiko ketat 2%",
        "",
        "Angka ini untuk membaca perbedaan pada modal/risiko yang sama, bukan "
        "rekomendasi setting terbaik. Panah berarti tanpa VWAP menjadi dengan VWAP. "
        "PF dihitung dari PnL posisi setelah biaya. n/a berarti PF tidak bisa "
        "diukur dari loss yang tersedia, bukan bukti sistem tanpa risiko.",
        "",
        "| Instrumen | Model | Gaya | Trade off → on | Return off → on | "
        "PF on | DD equity on | Trade/minggu on |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in selected:
        if not r["use_vwap"]:
            continue
        off = lookup[r["tag"].replace("_v1_", "_v0_")]
        lines.append(
            f"| {r['symbol']} | {'A' if r['model_kind'] else 'M'} | "
            f"{'Intraday' if r['intraday'] else 'Swing'} | "
            f"{int(off['trades'])} → {int(r['trades'])} | "
            f"{f(off['return_percent'])}% → {f(r['return_percent'])}% | "
            f"{f(r['net_profit_factor'], 3)} | {f(r['equity_dd_percent'])}% | "
            f"{f(r['trades_per_week'])} |"
        )
    lines += [
        "",
        "## PnL bulanan contoh yang sama, VWAP aktif",
        "",
        "Cash PnL yang dibukukan pada bulan tersebut, bukan perubahan equity "
        "marked-to-market. Posisi swing yang melewati akhir bulan dapat memindahkan "
        "pengakuan hasil ke bulan berikutnya. Rata-rata tidak berarti gaji bulanan.",
        "",
        "| Instrumen | Model/gaya | Jan | Feb | Mar | Apr | Mei | Jun | Jul | "
        "Agu | Rata-rata USD/bulan | Geometrik %/bulan |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in selected:
        if r["use_vwap"]:
            months = " | ".join(f(m["net_profit"]) for m in r["monthly"])
            lines.append(
                f"| {r['symbol']} | {'A' if r['model_kind'] else 'M'}/"
                f"{'I' if r['intraday'] else 'S'} | {months} | "
                f"{f(r['mean_monthly_profit_usd'])} | "
                f"{f(r['geometric_monthly_return_percent'])}% |"
            )
    lines += [
        "",
        "## Risiko dan frekuensi bukan sekadar angka return",
        "",
        "Minimum volume native saat audit: US500 0,14 lot atau sekitar $0,14 per "
        "poin indeks, x100 0,01 lot atau $1 per poin. Broker menetapkan minimum "
        "volume, bukan persentase risiko aman. Baris minimum tetap tidak memiliki "
        "batas risiko persentase. Sebaliknya, baris 1-5% melakukan skip jika "
        "minimum lot terlalu besar; tidak ada fallback tersembunyi.",
        "",
        "| Instrumen | Modal | Risiko rencana tertinggi, lot minimum | "
        "Kasus berhenti karena insolvensi |",
        "|---|---:|---:|---:|",
    ]
    df = pd.DataFrame(primary)
    for (symbol, capital), group in df.loc[df.sizing.eq(0)].groupby(["symbol", "balance"]):
        lines.append(
            f"| {symbol} | ${capital:,} | "
            f"{f(group.planned_actual_risk_percent_max.max())}% | "
            f"{int(group.coverage.eq('STOPPED_EARLY_INSOLVENT').sum())} |"
        )
    lines += [
        "",
        "Persentase risiko rencana membesar ketika saldo menyusut. Stop juga "
        "bukan jaminan batas rugi saat terjadi gap atau biaya tambahan. Return "
        "di bawah -100% pada artefak insolvensi adalah hasil tester, bukan "
        "klaim kewajiban nasabah atau aturan perlindungan saldo broker.",
        "",
        "## Reproduksibilitas model resmi",
        "",
        "| Instrumen | Bar overlap restart Februari | Prediksi berubah | "
        "Start berubah | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for r in restart:
        lines.append(
            f"| {r['symbol']} | {r['overlap_bars']} | {r['prediction_mismatches']} | "
            f"{r['start_mismatches']} | {r['status']} |"
        )
    lines += [
        "",
        "Uji prefix Januari vs run sampai Agustus dan stabilitas bar berikutnya "
        "adalah pengujian berbeda dari cold restart. Perubahan setelah restart "
        "tidak dengan sendirinya membuktikan sinyal online memakai masa depan. "
        "Parity perhitungan live setiap tick juga belum disertifikasi. Lihat "
        "[audit restart](RESULT_NATIVE_VWAP_RESTART.md).",
        "",
        "## Batas kesimpulan dan langkah setelah diskusi",
        "",
        f"Pada acuan $3.000/lot minimum, hanya ada **"
        f"{summary['band_reversion_unique_entry_events']} kejadian entry band unik** "
        "berdasarkan waktu dan arah. Kejadian yang sama pada US500 dan x100 tidak "
        "menjadi dua bukti independen. Angka ini penting untuk memisahkan "
        "hipotesis lokasi entry dekat VWAP dari hipotesis reversal band.",
        "",
        "1. VWAP merupakan filter lokasi pada model ini, bukan bukti bahwa harga "
        "pasti kembali ke garis rata-rata. Pisahkan trade area tengah dan trade "
        "band menuju VWAP pada laporan diagnostik; jumlah trade kecil tidak "
        "cukup untuk menyimpulkan kedua mekanisme bekerja.",
        "2. Bandingkan dulu pasangan lot tetap untuk mengurangi pengaruh "
        "compounding/skip. Lalu evaluasi akun yang benar-benar bisa dieksekusi. "
        "Jangan memilih baris return tertinggi dari 288 baris sebagai edge baru.",
        "3. Anchor UTC dan timeframe M30 berbeda dari screenshot M15 Pepperstone. "
        "Riwayat pemanasan US500 dan x100 juga berbeda. Kinerja antarsimbol "
        "bukan eksperimen pengali kontrak murni.",
        "4. Drawdown lebih rendah juga bisa berasal dari berkurangnya jumlah trade "
        "dan waktu berada di pasar. Kontrol gate acak dengan frekuensi sebanding "
        "belum dijalankan; penurunan DD sendiri belum membuktikan informasi VWAP "
        "lebih baik daripada sekadar mengurangi exposure.",
        "5. Seluruh periode sudah pernah diperiksa; belum ada holdout baru. "
        "Jika ada kandidat yang tetap ingin dipertahankan, bekukan satu kontrak "
        "dan selesaikan audit state/cadence sebelum observasi demo. Tidak ada "
        "order akun, Telegram atau forward EA yang diaktifkan pada pekerjaan ini.",
        "",
        "## Semua detail",
        "",
        "- [Laporan penuh dan 288 baris](RESULT_NATIVE_VWAP.md).",
        "- [Matriks CSV](../evidence/native_vwap_2026_v3/matrix_summary.csv).",
        "- [2.304 catatan bulanan](../evidence/native_vwap_2026_v3/monthly_results.csv).",
        "- [Kontrak teknis](TECH_PLAN_NATIVE_VWAP.md).",
        "- [Catatan engineering](NATIVE_VWAP_ENGINEERING_NOTES.md).",
        "",
    ]
    (root / "docs/DISCUSSION_NATIVE_VWAP.md").write_text("\n".join(lines), encoding="utf-8")
    print("Readable discussion regenerated from validated native evidence")


if __name__ == "__main__":
    main()
