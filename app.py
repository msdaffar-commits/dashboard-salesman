import pandas as pd
import streamlit as st

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard Monitoring Transaksi Toko",
    page_icon="📊",
    layout="wide",
)


# Fungsi untuk memuat dan membersihkan data
@st.cache_data
def load_data():
  df = pd.read_excel("LBP LDC KRW 09 SEP 2026.xlsx", sheet_name="Data")
  # Membersihkan spasi berlebih pada nama salesman
  if "Nama Salesman" in df.columns:
    df["Nama Salesman"] = df["Nama Salesman"].astype(str).str.strip()
  return df


try:
  df_raw = load_data()
except Exception as e:
  st.error(
      f"Gagal memuat file Excel. Pastikan file 'LBP LDC KRW 09 SEP 2026.xlsx'"
      f" berada di folder yang sama. Error: {e}"
  )
  st.stop()

# Judul Utama Dashboard
st.title("📊 Dashboard Monitoring Transaksi & Detail SKU Toko")
st.markdown(
    "Aplikasi khusus Salesman untuk memantau performa toko dan rincian produk"
    " (SKU) yang sudah ditransaksikan."
)

# Sidebar untuk Filter Akses Salesman & Toko
st.sidebar.header("🔍 Filter Wilayah & Toko")

# 1. Filter Pilih Salesman
list_salesman = sorted(
    df_raw["Nama Salesman"].dropna().unique().tolist()
)  # type: ignore
selected_salesman = st.sidebar.selectbox(
    "Pilih Nama Salesman:", ["-- Pilih Semua --"] + list_salesman
)

# Filter dataframe berdasarkan Salesman
if selected_salesman != "-- Pilih Semua --":
  df_filtered = df_raw[df_raw["Nama Salesman"] == selected_salesman]
else:
  df_filtered = df_raw

# 2. Filter Pilih Toko (Outlet)
# Membuat list gabungan "Kode - Nama Outlet" agar unik
df_filtered["Outlet_Display"] = (
    df_filtered["Outlet"].astype(str) + " - " + df_filtered["Nama Outlet"]
)
list_toko = sorted(df_filtered["Outlet_Display"].dropna().unique().tolist())

selected_toko = st.sidebar.selectbox(
    "Pilih Toko / Outlet:", ["-- Pilih Toko --"] + list_toko
)

# Main Content Area
if selected_toko == "-- Pilih Toko --":
  st.info(
      "👈 Silakan pilih **Nama Salesman** dan **Toko** pada panel di sebelah"
      " kiri untuk melihat detail transaksi SKU."
  )

  # Menampilkan Ringkasan Umum jika belum pilih toko
  st.subheader("📋 Ringkasan Performa Keseluruhan")
  col1, col2, col3 = st.columns(3)
  col1.metric("Total Transaksi (Baris)", len(df_filtered))
  col2.metric("Total Toko Unik", df_filtered["Outlet"].nunique())
  total_omset = (
      df_filtered["Total"].sum() if "Total" in df_filtered.columns else 0
  )
  col3.metric("Total Omset (Rp)", f"Rp {total_omset:,.0f}")

  st.dataframe(
      df_filtered[
          [
              "Outlet",
              "Nama Outlet",
              "Nama Salesman",
              "Tgl Faktur",
              "No Faktur",
              "Nama Barang",
              "Qty Total Pcs",
              "Total",
          ]
      ].head(50),
      use_container_width=True,
  )

else:
  # Filter data berdasarkan toko yang dipilih
  toko_ terpilih_df = df_filtered[
      df_filtered["Outlet_Display"] == selected_toko
  ]

  # Header Informasi Toko
  nama_toko_str = toko_terpilih_df["Nama Outlet"].iloc[0]
  id_toko_str = str(toko_terpilih_df["Outlet"].iloc[0])
  sales_toko_str = str(toko_terpilih_df["Nama Salesman"].iloc[0])

  st.success(f"### Toko: {nama_toko_str} (ID: {id_toko_str})")
  st.markdown(f"**Salesman Penanggung Jawab:** {sales_toko_str}")

  # Ringkasan Metrik Toko
  col1, col2, col3, col4 = st.columns(4)
  total_qty_toko = (
      toko_terpilih_df["Qty Total Pcs"].sum()
      if "Qty Total Pcs" in toko_terpilih_df.columns
      else 0
  )
  total_nilai_toko = (
      toko_terpilih_df["Total"].sum()
      if "Total" in toko_terpilih_df.columns
      else 0
  )
  jumlah_sku = (
      toko_terpilih_df["PCode"].nunique()
      if "PCode" in toko_terpilih_df.columns
      else 0
  )
  jumlah_faktur = (
      toko_terpilih_df["No Faktur"].nunique()
      if "No Faktur" in toko_terpilih_df.columns
      else 0
  )

  col1.metric("Total Jenis SKU Dibeli", f"{jumlah_sku} SKU")
  col2.metric("Total Qty Terjual (Pcs)", f"{total_qty_toko:,.0f}")
  col3.metric("Total Nilai Transaksi", f"Rp {total_nilai_toko:,.0f}")
  col4.metric("Jumlah Faktur/Nota", jumlah_faktur)

  st.markdown("---")

  # Tabel Detail SKU yang sudah dibeli toko tersebut
  st.subheader("📦 Rincian SKU / Produk yang Sudah Ditransaksikan")

  if "PCode" in toko_terpilih_df.columns and "Nama Barang" in toko_terpilih_df.columns:
    # Agregasi per SKU untuk toko tersebut
    sku_summary = (
        toko_terpilih_df.groupby(
            ["PCode", "Nama Barang", "UoM"]
        )  # type: ignore
        .agg(
            Total_Qty=("Qty", "sum"),
            Total_Pcs=("Qty Total Pcs", "sum"),
            Total_Brutto=("Brutto", "sum"),
            Total_Nilai=("Total", "sum"),
            Faktur_Terakhir=("Tgl Faktur", "max"),
        )
        .reset_index()
    )

    st.dataframe(sku_summary, use_container_width=True)

  # Tabel Riwayat Faktur Lengkap
  st.subheader("📑 Riwayat Faktur & Detail Transaksi")
  st.dataframe(
      toko_terpilih_df[
          [
              "Tgl Faktur",
              "No Faktur",
              "Billing Type Text",
              "PCode",
              "Nama Barang",
              "Qty",
              "UoM",
              "Qty Total Pcs",
              "Total",
          ]
      ],
      use_container_width=True,
  )
