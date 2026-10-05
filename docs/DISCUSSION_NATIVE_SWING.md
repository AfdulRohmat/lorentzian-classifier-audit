# Diskusi hasil swing US500 x100

Eksperimen menghasilkan beberapa kombinasi positif, tetapi tidak mendukung
kesimpulan bahwa semakin lebar SL pasti semakin baik. Statusnya **layak dibahas
sebagai temuan eksplorasi, belum promosi ke trading otomatis**. Semua angka di
bawah berasal dari Strategy Tester MT5, Januari sampai Agustus 2026, setelah
warm-up Juni sampai Desember 2025. Periode evaluasi sudah pernah diperiksa.

## Apa yang diuji

Entry Lorentzian M30 tidak diganti. Yang berubah adalah holding dan exit:
batas 24 jam dihapus; sinyal searah tidak menutup atau menambah posisi; sinyal
berlawanan menutup dan boleh membalik posisi bila sizing memungkinkan. Tidak
ada fixed TP. SL awal 1 sampai 10 kali ATR14 saat entry; jarak itu dibekukan,
ditambah reserve biaya lama untuk mendefinisikan R. Aktivasi trailing di +1R,
jarak trailing 1R, diperbarui menggunakan quote candle M30 yang telah selesai.

Ada 150 variasi: 10 jarak stop, tiga modal ($500/$1000/$3000), lima target
risiko (1 sampai 5 persen). Baris 1 persen mengizinkan minimum-lot fallback
sesuai permintaan sebelumnya, jadi bukan batas risiko ketat. Baris 2 sampai 5
persen tetap skip bila lot minimum melanggar anggaran. Hasil keseluruhan:
22 positif, 82 negatif, dan 46 tanpa trade. Empat dari hasil negatif berhenti
lebih awal karena stop-out dan saldo simulasi nonpositif. Tidak ada run negatif
yang dihapus atau disamarkan sebagai error pengujian.

## Tiga kombinasi untuk diskusi

Tabel ini dipilih setelah seluruh grid dilihat, bukan hipotesis yang sudah
dikonfirmasi pada data baru. Ketiganya memakai sizing ketat, tanpa fallback.

| Modal | SL dan trailing | Target risk | Trade | Return 8 bulan | PF native | Equity DD maksimum | Trade per minggu |
|---|---|---:|---:|---:|---:|---:|---:|
| $1000 | 3 ATR | 4% | 87 | +36,77% | 1,223 | 22,56% | 2,51 |
| $3000 | 8 ATR | 3% | 61 | +15,45% | 1,420 | 8,76% | 1,76 |
| $3000 | 10 ATR | 4% | 64 | +24,85% | 1,618 | 9,90% | 1,84 |

Return tertinggi bukan otomatis pilihan terbaik. Baris 3 ATR mempunyai drawdown
lebih besar. Baris 8 dan 10 ATR mempunyai holding lebih lama dan sampel lebih
kecil. Skenario saling tumpang tindih pada sejarah yang sama; bukan 150 bukti
independen. Angka 10 ATR berada di batas grid yang diuji, bukan bukti optimum.

## Membaca kombinasi 10 ATR dengan modal 3000 USD

Saldo akhir $3745,61, profit bersih $745,61. Win rate 42,19 persen, dengan
64 trade atau 8 trade per bulan. Rata-rata profit dolar per bulan $93,20.
Rata-rata return cash bulanan aritmetis 2,92 persen; tingkat bulanan geometris
yang menghasilkan pertumbuhan total sama adalah 2,81 persen. Ini bukan janji
profit yang teratur setiap bulan.

| Bulan 2026 | Return cash terealisasi |
|---|---:|
| Januari | -6,94% |
| Februari | +5,45% |
| Maret | +9,41% |
| April | +5,20% |
| Mei | +5,39% |
| Juni | -0,08% |
| Juli | +2,67% |
| Agustus | +2,24% |

Tabel bulanan memakai cash yang terealisasi, bukan equity mark-to-market pada
akhir bulan. Holding lintas bulan dapat menggeser pengakuan PnL. Drawdown native
9,90 persen sudah menggunakan equity, termasuk floating loss.

Rata-rata holding 59,17 jam; maksimum 163 jam, hampir tujuh hari. Sebanyak
55 posisi keluar karena setup berlawanan, satu karena initial SL, tujuh karena
SL yang sudah ditrailing, dan satu dilikuidasi pada akhir pengujian. Jadi
hasilnya lebih tepat dibaca sebagai **menahan posisi sampai sinyal berbalik**
dengan stop pengaman, bukan keberhasilan trailing stop semata.

PnL harga sebelum komisi dan swap +$914,58; komisi -$9,04 dan swap -$159,93.
Kontribusi net long +$391,60 dan short +$354,01. Rata-rata risiko awal yang
direncanakan 3,02 persen, rentang 2,09 sampai 3,93 persen. Tidak ada fallback dan
tidak ada kerugian trade melebihi budget nominal 4 persen pada sejarah ini;
itu bukan jaminan loss cap pada eksekusi mendatang. Sebanyak 48 kesempatan entry
di-skip karena ukuran lot di bawah minimum broker.

## Tetangga parameter dan pengaruh sizing

Pada modal $3000 dan risk ketat 4 persen:

| ATR | Trade | Return | PF native | Equity DD maksimum |
|---|---:|---:|---:|---:|
| 7 | 92 | -7,90% | 0,916 | 24,44% |
| 8 | 78 | +7,97% | 1,121 | 12,50% |
| 9 | 71 | +12,22% | 1,238 | 11,11% |
| 10 | 64 | +24,85% | 1,618 | 9,90% |

Ada area positif pada 8 sampai 10 ATR untuk baris ini, bukan hanya satu titik.
Namun jumlah dan komposisi trade berubah. Pelebaran stop mengurangi lot hasil
perhitungan; aturan minimum-lot kemudian memilih setup mana yang bisa masuk.
Karena itu, tabel tidak membuktikan bahwa jarak stop sendiri menghasilkan edge.

Contoh lain: 3 ATR/risk 4 persen menghasilkan +36,77 persen dengan modal $1000
(87 trade), tetapi -24,97 persen dengan modal $3000 (124 trade). Ini bukan
sekadar return yang diskalakan sesuai modal. Entry yang lolos, ukuran lot,
compounding, dan keberadaan posisi terbuka ikut berubah secara kausal.

Menghapus deadline saja juga tidak otomatis membantu. Pada $1000, 1 ATR,
minimum-lot fallback, 167 entry dan lot sama dengan kontrol lama. Hanya lima
outcome berubah, total -$79,31. Hasil ini mengisolasi deadline lebih bersih
daripada membandingkan seluruh grid sizing yang mempunyai trade berbeda.

## Batas kesimpulan

Implementasi dua aturan yang disepakati selesai dan ada hasil positif untuk
diteliti, tetapi belum ada validasi unseen. Jangan langsung menjadikan 10 ATR
sebagai default, memperlebar grid lagi sampai menemukan angka lebih tinggi,
atau mengaktifkan EA pada akun. Baseline lama tetap tersimpan dan default EA
tetap aturan lama untuk regresi. Build ini hanya dapat berjalan di tester.

Jika riset dilanjutkan, pembahasan perlu membekukan kandidat beserta kebijakan
sizing dan skip sebagai satu kesatuan, kemudian menguji data baru, sensitivitas
biaya serta ketergantungan pada sedikit winner besar. Langkah lanjutan tersebut
belum dijalankan dalam eksperimen ini. Swap historis dan delay live belum
divalidasi independen; trailing juga tidak menjamin profit setelah semua swap.

Tiga kontrol native mereproduksi deal lama persis. Audit memeriksa ledger,
signal stream/prefix sebelum kebangkrutan, stop, sizing, dan jalur exit. Kompilasi
EA nol error/warning dan 87 tes Python lulus. Terminal demo dikembalikan dalam
keadaan terhubung, Algo Trading mati, tanpa posisi atau pending order.

Lihat [seluruh grid dan laporan bulanan](RESULT_NATIVE_SWING.md),
[kontrak sebelum pengujian](TECH_PLAN_NATIVE_SWING.md), dan
[evidence tervalidasi](../evidence/native_x100_swing_2026/validated_summary.json).
