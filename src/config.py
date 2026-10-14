"""
config.py  -  SEMUA parameter ada di sini. Ubah di file ini saja.

Tanda [DATASHEET] = angka dari datasheet resmi
Tanda [USER]      = angka dari Anda (dikonfirmasi)
Tanda [ASUMSI]    = tebakan sementara, harus dikonfirmasi / diuji sensitivitasnya
Tanda [CEK]       = belum dikonfirmasi di lapangan
"""

# ---------------------------------------------------------------
# LOKASI  [USER / kode lama]
# ---------------------------------------------------------------
SITE = dict(
    name="NCUE College of Engineering",
    latitude=24.065972,
    longitude=120.558784,
    altitude=84.92,
    tz="Asia/Taipei",
)

# ---------------------------------------------------------------
# MODUL AJP-S672-375  [DATASHEET Anji Technology]
# ---------------------------------------------------------------
MODULE = dict(
    model="AJP-S672-375",
    pmax_stc_w=375.0,
    gamma_pdc=-0.0044,   # -0.44 %/C  (Pmax temp. coeff.)
    noct_c=46.0,         # NOCT 46 +-2 C
    area_m2=1.938,       # 1948 x 995 mm  [USER]
    vmp=40.24, imp=9.32, voc=48.54, isc=10.03,
)

# ---------------------------------------------------------------
# SUB-ARRAY  [USER-DIKONFIRMASI: jumlah modul; tilt 23, azimuth 180 (selatan)
# untuk SEMUA sub-array. Catatan "angle yang berbeda" di foto = sudut kamera.]
# Tilt/azimuth tetap dibuat per sub-array supaya mudah diubah di masa depan.
# ---------------------------------------------------------------
SUBARRAYS = {
    "S161": dict(n_modules=161, tilt=23.0, azimuth=180.0),
    "S112": dict(n_modules=112, tilt=23.0, azimuth=180.0),
    "S66":  dict(n_modules=66,  tilt=23.0, azimuth=180.0),
    "S33":  dict(n_modules=33,  tilt=23.0, azimuth=180.0),
}

# ---------------------------------------------------------------
# INVERTER CyberPower  [DATASHEET]
# eta_peak = efisiensi MAKSIMUM (bukan efisiensi terbobot!)
# Nama INV50_A / INV50_B hanya label; unit fisiknya belum dipetakan [CEK]
# ---------------------------------------------------------------
INVERTERS = {
    "INV30":   dict(model="CPSPV30000ETLA-WB", pac_w=30000.0, eta_peak=0.986, max_pv_w=39000.0),
    "INV50_A": dict(model="CPSPV50000ETL-WB",  pac_w=50000.0, eta_peak=0.985, max_pv_w=65000.0),
    "INV50_B": dict(model="CPSPV50000ETL-WB",  pac_w=50000.0, eta_peak=0.985, max_pv_w=65000.0),
}

# ---------------------------------------------------------------
# PEMETAAN sub-array -> inverter  [TIDAK DAPAT DIPASTIKAN]
# Dua kemungkinan yang memenuhi batas "max PV power" datasheet (tanpa
# memecah sub-array). Keduanya selalu dijalankan dan dilaporkan sebagai
# SKENARIO. Total sistem tidak bergantung pada pemetaan; hasil per-inverter
# dan clipping bergantung padanya.
# ---------------------------------------------------------------
MAPPING_OPTIONS = {
    "a": {"INV50_A": ["S161"], "INV50_B": ["S112", "S33"], "INV30": ["S66"]},
    "b": {"INV50_A": ["S161"], "INV50_B": ["S112"],        "INV30": ["S66", "S33"]},
}
DEFAULT_MAPPING = "a"

# ---------------------------------------------------------------
# ASUMSI MODEL  [ASUMSI]
# ---------------------------------------------------------------
ALBEDO = 0.25                 # sama dengan paper lama
TEMP_AIR_DEFAULT_C = 27.0     # dipakai hanya jika tidak ada data suhu
DC_LOSS_FRACTION = 0.087        # soiling+mismatch+kabel DC (diuji 0-9% di sensitivitas)
PVWATTS_GENERIC_ETA_NOM = 0.96  # nilai bawaan pvlib, sebagai pembanding "pesimis"

# ---------------------------------------------------------------
# PEMERIKSAAN KONSISTENSI  [USER-DIKONFIRMASI: luas total 720.9 m2]
# ---------------------------------------------------------------
TOTAL_MODULES = 372
TOTAL_AREA_M2 = 720.9   # = 372 x 1.938
