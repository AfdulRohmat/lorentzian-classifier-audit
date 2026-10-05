# Diskusi hasil Lorentzian + VWAP di MT5

Seluruh angka di bawah berasal dari Strategy Tester MT5 dan ledger native, bukan simulasi fill Python. Python dipakai untuk audit independen dan laporan.

## Kesimpulan utama

Ada perbaikan historis pada beberapa pasangan, terutama swing dan model modifikasi. Tetapi VWAP memperburuk intraday model resmi pada banyak konfigurasi, dan jumlah trade turun tajam. Delapan interval bootstrap pasangan lot tetap semuanya masih melintasi nol; peningkatan yang robust belum terbukti. Verdict: **VWAP_UPGRADE_NOT_CONFIRMED**.

Hipotesis dekat pusat VWAP mendapatkan lebih banyak observasi daripada hipotesis reversal dari band. Yang terakhir hanya memiliki satu kejadian unik dalam acuan lot tetap. Kita belum mengganti baseline atau mengaktifkan EA forward. Ini bukan kesimpulan bahwa semua penggunaan VWAP atau seluruh model Lorentzian pasti gagal.

## Ruang lingkup dan cara membaca

Januari-Agustus 2026, M30, Exness US500 dan US500_x100. Modal $500, $1.000, $3.000; lot minimum tetap atau risiko ketat 1-5% dari saldo berjalan. 288 kombinasi, ditambah empat smoke test dan dua diagnostik restart. Semua laporan utama menyatakan 100% real ticks; ini tidak menjamin bahwa semua spesifikasi broker historis atau eksekusi live sudah direplikasi.

Matriks: **133 positif, 115 negatif, 40 tanpa trade**. Baris modal/risiko berbagi sejarah dan sinyal; jumlah baris positif bukan jumlah bukti independen.

Model M adalah causal exact-KNN modifikasi sebelumnya. Model A adalah source resmi MQL5 v1.00 yang dikompilasi tanpa mengubah algoritmenya; bukan klaim parity binary Market atau chart TradingView. Kedua model mendapat wrapper exit dan sizing yang sama.

SL awal 3 ATR14 M30. Trailing aktif setelah +1R, berjarak 1R, hanya mengencang memakai quote pada penutupan bar. Tidak ada TP tetap. Sinyal lawan mentah tetap menutup posisi meskipun entry balik ditolak VWAP. Swing boleh menginap; intraday hanya mengambil bar sesi New York dan menutup posisi 15.45 New York.

VWAP memakai HLC3 dan tick volume broker, reset 00.00 UTC. Di dalam 1 sigma kedua arah boleh; di bawah -1 sampai -3 sigma hanya buy; di atas +1 sampai +3 sigma hanya sell. Lewat 3 sigma atau benchmark belum valid: skip. VWAP tidak menciptakan atau menunda sinyal model. Ini satu definisi mekanikal ide screenshot, bukan pengujian semua cara memakai VWAP.

## Contoh perbandingan seragam: $3.000, risiko ketat 2%

Angka ini untuk membaca perbedaan pada modal/risiko yang sama, bukan rekomendasi setting terbaik. Panah berarti tanpa VWAP menjadi dengan VWAP. PF dihitung dari PnL posisi setelah biaya. n/a berarti PF tidak bisa diukur dari loss yang tersedia, bukan bukti sistem tanpa risiko.

| Instrumen | Model | Gaya | Trade off → on | Return off → on | PF on | DD equity on | Trade/minggu on |
|---|---|---|---:|---:|---:|---:|---:|
| US500 | M | Swing | 119 → 22 | 4.13% → 7.06% | 1.340 | 12.60% | 0.63 |
| US500 | M | Intraday | 61 → 10 | -2.33% → 3.02% | 1.561 | 4.57% | 0.29 |
| US500 | A | Swing | 237 → 46 | -20.49% → 4.31% | 1.083 | 17.55% | 1.33 |
| US500 | A | Intraday | 89 → 21 | 2.37% → -6.37% | 0.495 | 10.32% | 0.60 |
| US500_x100 | M | Swing | 116 → 24 | -4.89% → 3.30% | 1.181 | 7.65% | 0.69 |
| US500_x100 | M | Intraday | 63 → 15 | 4.19% → 4.59% | 2.126 | 3.83% | 0.43 |
| US500_x100 | A | Swing | 206 → 42 | -18.40% → 7.76% | 1.215 | 13.77% | 1.21 |
| US500_x100 | A | Intraday | 85 → 18 | -0.78% → -4.02% | 0.531 | 7.15% | 0.52 |

## PnL bulanan contoh yang sama, VWAP aktif

Cash PnL yang dibukukan pada bulan tersebut, bukan perubahan equity marked-to-market. Posisi swing yang melewati akhir bulan dapat memindahkan pengakuan hasil ke bulan berikutnya. Rata-rata tidak berarti gaji bulanan.

| Instrumen | Model/gaya | Jan | Feb | Mar | Apr | Mei | Jun | Jul | Agu | Rata-rata USD/bulan | Geometrik %/bulan |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| US500 | M/S | 209.68 | -72.15 | 146.95 | -33.93 | 23.49 | -168.45 | 77.14 | 29.18 | 26.49 | 0.86% |
| US500 | M/I | 4.07 | 0.00 | 114.56 | 61.93 | -13.00 | -63.20 | -13.80 | 0.00 | 11.32 | 0.37% |
| US500 | A/S | 75.29 | -34.38 | 208.95 | -41.22 | -16.34 | 160.27 | -116.00 | -107.14 | 16.18 | 0.53% |
| US500 | A/I | 24.79 | -17.63 | 50.20 | -34.27 | 26.26 | -110.70 | -56.80 | -72.82 | -23.87 | -0.82% |
| US500_x100 | M/S | 177.02 | -50.10 | 54.02 | -28.29 | 32.74 | -136.60 | 106.71 | -56.45 | 12.38 | 0.41% |
| US500_x100 | M/I | 10.09 | 0.00 | 99.36 | 51.09 | 10.73 | -24.29 | -7.52 | -1.81 | 17.21 | 0.56% |
| US500_x100 | A/S | 89.34 | -50.07 | 134.06 | -21.04 | 22.59 | 212.01 | -68.64 | -85.55 | 29.09 | 0.94% |
| US500_x100 | A/I | 22.45 | -11.03 | 26.86 | -24.12 | 17.62 | -46.86 | -39.67 | -65.86 | -15.08 | -0.51% |

## Risiko dan frekuensi bukan sekadar angka return

Minimum volume native saat audit: US500 0,14 lot atau sekitar $0,14 per poin indeks, x100 0,01 lot atau $1 per poin. Broker menetapkan minimum volume, bukan persentase risiko aman. Baris minimum tetap tidak memiliki batas risiko persentase. Sebaliknya, baris 1-5% melakukan skip jika minimum lot terlalu besar; tidak ada fallback tersembunyi.

| Instrumen | Modal | Risiko rencana tertinggi, lot minimum | Kasus berhenti karena insolvensi |
|---|---:|---:|---:|
| US500 | $500 | 3.25% | 0 |
| US500 | $1,000 | 1.46% | 0 |
| US500 | $3,000 | 0.49% | 0 |
| US500_x100 | $500 | 173.56% | 2 |
| US500_x100 | $1,000 | 124.41% | 0 |
| US500_x100 | $3,000 | 4.55% | 0 |

Persentase risiko rencana membesar ketika saldo menyusut. Stop juga bukan jaminan batas rugi saat terjadi gap atau biaya tambahan. Return di bawah -100% pada artefak insolvensi adalah hasil tester, bukan klaim kewajiban nasabah atau aturan perlindungan saldo broker.

## Reproduksibilitas model resmi

| Instrumen | Bar overlap restart Februari | Prediksi berubah | Start berubah | Status |
|---|---:|---:|---:|---|
| US500 | 6903 | 0 | 0 | MATCH_ON_THIS_REPLAY |
| US500_x100 | 6903 | 0 | 0 | MATCH_ON_THIS_REPLAY |

Uji prefix Januari vs run sampai Agustus dan stabilitas bar berikutnya adalah pengujian berbeda dari cold restart. Perubahan setelah restart tidak dengan sendirinya membuktikan sinyal online memakai masa depan. Parity perhitungan live setiap tick juga belum disertifikasi. Lihat [audit restart](RESULT_NATIVE_VWAP_RESTART.md).

## Batas kesimpulan dan langkah setelah diskusi

Pada acuan $3.000/lot minimum, hanya ada **1 kejadian entry band unik** berdasarkan waktu dan arah. Kejadian yang sama pada US500 dan x100 tidak menjadi dua bukti independen. Angka ini penting untuk memisahkan hipotesis lokasi entry dekat VWAP dari hipotesis reversal band.

1. VWAP merupakan filter lokasi pada model ini, bukan bukti bahwa harga pasti kembali ke garis rata-rata. Pisahkan trade area tengah dan trade band menuju VWAP pada laporan diagnostik; jumlah trade kecil tidak cukup untuk menyimpulkan kedua mekanisme bekerja.
2. Bandingkan dulu pasangan lot tetap untuk mengurangi pengaruh compounding/skip. Lalu evaluasi akun yang benar-benar bisa dieksekusi. Jangan memilih baris return tertinggi dari 288 baris sebagai edge baru.
3. Anchor UTC dan timeframe M30 berbeda dari screenshot M15 Pepperstone. Riwayat pemanasan US500 dan x100 juga berbeda. Kinerja antarsimbol bukan eksperimen pengali kontrak murni.
4. Drawdown lebih rendah juga bisa berasal dari berkurangnya jumlah trade dan waktu berada di pasar. Kontrol gate acak dengan frekuensi sebanding belum dijalankan; penurunan DD sendiri belum membuktikan informasi VWAP lebih baik daripada sekadar mengurangi exposure.
5. Seluruh periode sudah pernah diperiksa; belum ada holdout baru. Jika ada kandidat yang tetap ingin dipertahankan, bekukan satu kontrak dan selesaikan audit state/cadence sebelum observasi demo. Tidak ada order akun, Telegram atau forward EA yang diaktifkan pada pekerjaan ini.

## Semua detail

- [Laporan penuh dan 288 baris](RESULT_NATIVE_VWAP.md).
- [Matriks CSV](../evidence/native_vwap_2026_v3/matrix_summary.csv).
- [2.304 catatan bulanan](../evidence/native_vwap_2026_v3/monthly_results.csv).
- [Kontrak teknis](TECH_PLAN_NATIVE_VWAP.md).
- [Catatan engineering](NATIVE_VWAP_ENGINEERING_NOTES.md).
