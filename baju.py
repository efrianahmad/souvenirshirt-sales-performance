import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =====================================================
# 1. KONFIGURASI HALAMAN & ENHANCED THEME ENGINE
# =====================================================
st.set_page_config(
    page_title="Executive Sales Performance & Predictive Analytics",
    layout="wide"
)

# Injeksi CSS Khusus untuk Duplikasi Tampilan Canvas Power BI
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #F8FAFC;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 15px;
        font-weight: 600;
        color: #64748B;
        padding: 14px 28px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #0052CC;
    }
    .stTabs [aria-selected="true"] {
        color: #0052CC !important;
        border-bottom: 3px solid #0052CC !important;
    }
    
    .kpi-container {
        background-color: #FFFFFF;
        padding: 22px 18px;
        border-radius: 6px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    .kpi-title {
        font-size: 12px;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    .kpi-num {
        font-size: 26px;
        font-weight: 700;
        color: #0F172A;
    }
    
    .chart-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 6px;
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

HEX_NAVY = "#0A2540"
HEX_BLUE = "#0052CC"
HEX_LIGHT_BLUE = "#2085EC"
HEX_SLATE = "#475569"
HEX_SILVER = "#94A3B8"
PALETTE_COMPREHENSIVE = ["#0A2540", "#0052CC", "#2085EC", "#38BDF8", "#64748B", "#CBD5E1"]

# =====================================================
# 2. DATA PIPELINE (CLEANING & IN-MEMORY CACHING)
# =====================================================
@st.cache_data
def load_data():
    df = pd.read_excel("Penjualan Baju.xlsx", sheet_name="Transaksi")
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])

    numeric_cols = ["Jml", "Harga_Jual", "Pemasukan", "Modal", "Laba"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    try:
        df_stok = pd.read_excel("Penjualan Baju.xlsx", sheet_name="Stok_Baju")
    except:
        df_stok = None
        
    try:
        df_belanja = pd.read_excel("Penjualan Baju.xlsx", sheet_name="belanja")
    except:
        df_belanja = None

    return df, df_stok, df_belanja

df, df_stok, df_belanja = load_data()

df["Size"] = df["Size"].astype(str).str.strip().str.upper()
df["Size"] = df["Size"].replace(["NAN", "NONE", ""], pd.NA)

# =====================================================
# 3. INTERACTIVE CONTROL PANEL (SIDEBAR)
# =====================================================
st.sidebar.markdown("### Control Panel Filters")

min_date = df["Tanggal"].min()
max_date = df["Tanggal"].max()

date_range = st.sidebar.date_input("Rentang Operasional", [min_date, max_date])
barang_list = ["Semua Kategori"] + sorted(df["Barang"].dropna().unique())
selected_barang = st.sidebar.selectbox("Kluster Komoditas Produk", barang_list)

filtered_df = df.copy()

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["Tanggal"] >= pd.to_datetime(start_date)) &
        (filtered_df["Tanggal"] <= pd.to_datetime(end_date))
    ]

if selected_barang != "Semua Kategori":
    filtered_df = filtered_df[filtered_df["Barang"] == selected_barang]

excluded_size_products = ["daster", "xseven"]
filtered_df["Barang_Clean"] = filtered_df["Barang"].astype(str).str.strip().str.lower()
size_filtered_df = filtered_df[~filtered_df["Barang_Clean"].isin(excluded_size_products)]

# =====================================================
# 4. KUMPULAN AGREGASI DATA UTAMA (GLOBAL SCOPE)
# =====================================================
total_omzet = filtered_df["Pemasukan"].sum()
total_laba = filtered_df["Laba"].sum()
total_qty = filtered_df["Jml"].sum()
total_transaksi = len(filtered_df)
margin = (total_laba / total_omzet) * 100 if total_omzet > 0 else 0

top_profit = filtered_df.groupby("Barang", as_index=False)["Laba"].sum().sort_values(by="Laba", ascending=False).head(5)
slow_moving = filtered_df.groupby("Barang", as_index=False)["Jml"].sum().sort_values(by="Jml", ascending=True).head(5)

top_product_name = top_profit.iloc[0]["Barang"] if not top_profit.empty else "N/A"
top_product_laba = top_profit.iloc[0]["Laba"] if not top_profit.empty else 0

slow_product_name = slow_moving.iloc[0]["Barang"] if not slow_moving.empty else "N/A"
slow_product_qty = slow_moving.iloc[0]["Jml"] if not slow_moving.empty else 0

# =====================================================
# 5. DASHBOARD FRAMEWORK INTERFACE LAYOUT
# =====================================================
st.title("Commercial Performance & Predictive Analytics")
st.markdown("Aplikasi visualisasi data terintegrasi untuk pemantauan arus kas ritel, margin profitabilitas, dan peramalan tren analitik masa depan.")
st.markdown("---")

# Mengubah Tab Navigasi Menjadi 4 Pilihan (Menambahkan Tab Predictive)
tab1, tab2, tab3, tab4 = st.tabs([
    "Financial Trends & Performance", 
    "Product & Attribute Analysis", 
    "Logistics & Capital Expenditure",
    "Predictive Analytics & Forecasting"
])

# -----------------------------------------------------
# TAB 1: FINANCIAL TRENDS & PERFORMANCE
# -----------------------------------------------------
with tab1:
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.markdown(f'<div class="kpi-container"><div class="kpi-title">Gross Revenue</div><div class="kpi-num">Rp {total_omzet:,.0f}</div></div>', unsafe_allow_html=True)
    with kpi_cols[1]:
        st.markdown(f'<div class="kpi-container"><div class="kpi-title">Net Profit</div><div class="kpi-num">Rp {total_laba:,.0f}</div></div>', unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown(f'<div class="kpi-container"><div class="kpi-title">Volume Terjual</div><div class="kpi-num">{total_qty:,.0f} Pcs</div></div>', unsafe_allow_html=True)
    with kpi_cols[3]:
        st.markdown(f'<div class="kpi-container"><div class="kpi-title">Total Transaksi</div><div class="kpi-num">{total_transaksi:,}</div></div>', unsafe_allow_html=True)
    with kpi_cols[4]:
        st.markdown(f'<div class="kpi-container"><div class="kpi-title">Profit Margin</div><div class="kpi-num">{margin:.2f}%</div></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background-color: #F8FAFC; padding: 22px; border-radius: 6px; border-left: 5px solid #0052CC; margin-bottom: 25px; border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;">
        <h5 style="color: #0052CC; margin-top:0; margin-bottom:6px; font-size:15px; font-weight:700;">Financial Performance Executive Summary</h5>
        <p style="margin:0; font-size:14px; line-height:1.6; color:#334155;">
            Evaluasi performa komersial menunjukkan rasio margin keuntungan bersih berada pada level stabil <b>{margin:.2f}%</b>. 
            Aktivitas transaksi pasar mengalami eskalasi volume yang sangat masif pada siklus akhir pekan (Sabtu dan Minggu). 
            Disarankan untuk menyelaraskan kesiapan operasional kasir dan ketersediaan display toko guna mengantisipasi puncak volatilitas pasar mingguan tersebut.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Tren Distribusi Penjualan Harian (Revenue Trend)")
    daily_sales = filtered_df.groupby("Tanggal", as_index=False)["Pemasukan"].sum()
    
    fig_sales = go.Figure()
    fig_sales.add_trace(go.Scatter(
        x=daily_sales["Tanggal"], y=daily_sales["Pemasukan"],
        mode='lines+markers',
        line=dict(color=HEX_BLUE, width=3, shape='spline'),
        marker=dict(size=6, color=HEX_NAVY)
    ))
    fig_sales.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=20, t=10, b=40), height=320,
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Pemasukan (Rp)")
    )
    st.plotly_chart(fig_sales, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Tren Akumulasi Perolehan Laba Bersih")
    daily_profit = filtered_df.groupby("Tanggal", as_index=False)["Laba"].sum()
    
    fig_profit = go.Figure()
    fig_profit.add_trace(go.Scatter(
        x=daily_profit["Tanggal"], y=daily_profit["Laba"],
        mode='lines',
        line=dict(color=HEX_LIGHT_BLUE, width=2.5, shape='spline'),
        fill='tozeroy',
        fillcolor='rgba(32, 133, 236, 0.12)'
    ))
    fig_profit.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=20, t=10, b=40), height=300,
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Laba (Rp)")
    )
    st.plotly_chart(fig_profit, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Analisis Volume Penjualan Berdasarkan Hari")
    filtered_df["Hari"] = filtered_df["Tanggal"].dt.day_name()
    hari_sales = filtered_df.groupby("Hari", as_index=False)["Pemasukan"].sum()
    
    urutan_hari = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    hari_sales["Hari"] = hari_sales["Hari"].map(urutan_hari)
    hari_sales["Hari"] = pd.Categorical(
        hari_sales["Hari"], 
        categories=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"], 
        ordered=True
    )
    hari_sales = hari_sales.sort_values("Hari")

    fig_hari = px.bar(
        hari_sales, x="Hari", y="Pemasukan", text_auto=".2s",
        color_discrete_sequence=[HEX_NAVY]
    )
    fig_hari.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=20, t=10, b=40), height=300,
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Total Omzet (Rp)"), xaxis=dict(title=None)
    )
    st.plotly_chart(fig_hari, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------
# TAB 2: PRODUCT & ATTRIBUTE ANALYSIS
# -----------------------------------------------------
with tab2:
    st.markdown("###Automated Executive Insights & Recommendations")
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.markdown(f"""
        <div style="background-color: #F0FDF4; padding: 20px; border-radius: 6px; border-left: 5px solid #16A34A; height: 100%; border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;">
            <h4 style="color: #16A34A; margin-top:0; font-size:14.5px; font-weight:700;">Alokasi Modal & Optimalisasi Profit</h4>
            <p style="font-size:13.5px; line-height:1.5; color:#1F2937; margin-bottom:8px;">Kategori produk <b>{top_product_name}</b> terbukti menjadi jangkar utama keuntungan operasional dengan kontribusi laba bersih akumulatif senilai <b>Rp {top_product_laba:,.0f}</b>.</p>
            <ul style="font-size:13px; color:#374151; padding-left:18px; margin:0;">
                <li><b>Rekomendasi Analis:</b> Prioritaskan sisa anggaran belanja modal (CapEx) bulan ini untuk mengamankan stok kategori tersebut guna menghindari kondisi <i>out-of-stock</i>.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with insight_col2:
        st.markdown(f"""
        <div style="background-color: #FEF2F2; padding: 20px; border-radius: 6px; border-left: 5px solid #DC2626; height: 100%; border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;">
            <h4 style="color: #DC2626; margin-top:0; font-size:14.5px; font-weight:700;">Manajemen Risiko & Slow Moving Stock</h4>
            <p style="font-size:13.5px; line-height:1.5; color:#1F2937; margin-bottom:8px;">Kategori produk <b>{slow_product_name}</b> terdeteksi mengalami hambatan perputaran (Slow-Moving) dengan volume penyerapan yang minim, yaitu hanya terjual <b>{slow_product_qty} Pcs</b>.</p>
            <ul style="font-size:13px; color:#374151; padding-left:18px; margin:0;">
                <li><b>Rekomendasi Analis:</b> Lakukan pembatasan atau pembekuan pemesanan baru ke pihak supplier. Optimalkan pencairan modal mati lewat strategi pemasaran bundel hemat.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    col_graph_l, col_graph_r = st.columns(2)
    with col_graph_l:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("#### Top 5 Kombinasi Produk & Ukuran Terlaris")
        produk_size = size_filtered_df.groupby(["Barang", "Size"], as_index=False)["Jml"].sum()
        produk_size["Produk_Size"] = produk_size["Barang"] + " (" + produk_size["Size"].astype(str) + ")"
        top_produk_size = produk_size.sort_values(by="Jml", ascending=False).head(5)

        fig_top_produk_size = px.bar(
            top_produk_size, x="Jml", y="Produk_Size", orientation="h", text_auto=True,
            color_discrete_sequence=[HEX_LIGHT_BLUE]
        )
        fig_top_produk_size.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=20, t=10, b=40), height=320,
            xaxis=dict(title="Volume Terjual (Pcs)"), yaxis={'categoryorder':'total ascending', 'title':None}
        )
        st.plotly_chart(fig_top_produk_size, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_graph_r:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("#### Top 5 Kategori Kinerja Keuntungan Bersih Tertinggi")
        fig_profit_top = px.bar(
            top_profit, x="Barang", y="Laba", text_auto=".2s",
            color_discrete_sequence=[HEX_BLUE]
        )
        fig_profit_top.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=20, t=10, b=40), height=320,
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Total Laba (Rp)"), xaxis=dict(title=None)
        )
        st.plotly_chart(fig_profit_top, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Visualisasi Efisiensi Arus Perputaran Produk (Slow Moving Funnel Analysis)")
    fig_funnel = px.funnel(
        slow_moving, x="Jml", y="Barang",
        color_discrete_sequence=[HEX_NAVY]
    )
    fig_funnel.update_layout(plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=20, t=10, b=40), height=320, yaxis=dict(title=None))
    st.plotly_chart(fig_funnel, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Proporsi Distribusi Volume Atribut Ukuran Secara Global")
    size_global = size_filtered_df.groupby(["Barang", "Size"], as_index=False)["Jml"].sum()
    size_global["Produk_Size"] = size_global["Barang"] + " - " + size_global["Size"].astype(str)
    
    fig_size = px.pie(
        size_global, names="Produk_Size", values="Jml", hole=0.45,
        color_discrete_sequence=PALETTE_COMPREHENSIVE
    )
    fig_size.update_layout(margin=dict(t=30, b=30, l=10, r=10), height=380)
    st.plotly_chart(fig_size, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### Matriks Komposisi Ukuran Spesifik Tiap Jenis Produk")
    produk_list = sorted(size_filtered_df["Barang"].dropna().unique())

    for produk in produk_list:
        st.markdown(f"##### Atribut Ukuran: **{produk}**")
        produk_df = size_filtered_df[size_filtered_df["Barang"] == produk]
        size_analysis = produk_df.groupby("Size", as_index=False)["Jml"].sum().sort_values(by="Jml", ascending=False)

        fig_produk_size = px.bar(
            size_analysis, x="Size", y="Jml", text_auto=True,
            color_discrete_sequence=[HEX_NAVY]
        )
        fig_produk_size.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", height=260, margin=dict(l=40, r=20, t=10, b=40),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Volume (Pcs)"), xaxis=dict(title="Size Attribute")
        )
        st.plotly_chart(fig_produk_size, use_container_width=True)

# -----------------------------------------------------
# TAB 3: LOGISTICS & CAPITAL EXPENDITURE
# -----------------------------------------------------
with tab3:
    st.markdown("### Audit Inventori Sistem & Alokasi Belanja Modal Supplier")
    col_stok1, col_stok2 = st.columns(2)
    
    with col_stok1:
        if df_stok is not None:
            st.markdown("#### Posisi Ketersediaan Stok & Display Lemari (Stok_Baju)")
            cols_to_show = [c for c in ["Barang_Size", "Stok_Awal", "Lemari", "Pajangan", "Brg_Keluar", "Total_stok"] if c in df_stok.columns]
            if cols_to_show:
                st.dataframe(df_stok[cols_to_show].dropna().head(15), use_container_width=True, hide_index=True)
        else:
            st.info("Data referensi Stok_Baju tidak terdeteksi dalam database Excel.")

    with col_stok2:
        if df_belanja is not None:
            st.markdown("#### Struktur Pengeluaran Belanja Logistik Supplier (Uda)")
            cols_belanja = [c for c in ["Nama_Barang", "belanja_lusin", "jml_pcs_belanja", "Harga+komisi_uda", "total_belanja"] if c in df_belanja.columns]
            if cols_belanja:
                st.dataframe(df_belanja[cols_belanja].dropna().head(15), use_container_width=True, hide_index=True)
        else:
            st.info("Data pembelanjaan logistik tidak terdeteksi dalam database Excel.")

    st.markdown("---")
    st.markdown("#### Tabel Konsolidasi Performa Finansial Produk")
    ranking_produk = filtered_df.groupby("Barang", as_index=False).agg({"Jml": "sum", "Pemasukan": "sum", "Laba": "sum"})
    ranking_produk = ranking_produk.sort_values(by="Pemasukan", ascending=False)

    ranking_produk["Laba"] = ranking_produk["Laba"].fillna(0).astype(int)
    ranking_produk["Pemasukan"] = ranking_produk["Pemasukan"].fillna(0).astype(int)

    ranking_produk["Pemasukan_Formatted"] = ranking_produk["Pemasukan"].apply(lambda x: f"Rp {x:,}".replace(",", "."))
    ranking_produk["Laba_Formatted"] = ranking_produk["Laba"].apply(lambda x: f"Rp {x:,}".replace(",", "."))
    
    display_ranking = ranking_produk[["Barang", "Jml", "Pemasukan_Formatted", "Laba_Formatted"]].copy()
    display_ranking.columns = ["Nama Barang", "Total Unit Terjual", "Gross Pemasukan", "Net Laba Bersih"]
    st.dataframe(display_ranking, use_container_width=True, hide_index=True)

# -----------------------------------------------------
# TAB 4: PREDICTIVE ANALYTICS & FORECASTING (NEW SEKSI)
# -----------------------------------------------------
with tab4:
    st.markdown("### 🔮 Advanced Predictive Modeling & Revenue Forecasting")
    st.markdown("Seksi analitik tingkat tinggi menggunakan perhitungan statistik **Linear Regression** murni (via NumPy) untuk meramal tren komersial masa depan.")
    st.markdown("---")

    # PERSIAPAN MODEL REGRESI LINEAR MENGGUNAKAN NUMPY
    # Kita ubah deret tanggal harian menjadi angka indeks x (0, 1, 2...) agar bisa dihitung matriks regresi statistika
    daily_data = filtered_df.groupby("Tanggal", as_index=False).agg({"Pemasukan": "sum", "Laba": "sum"})
    
    if len(daily_data) > 2:
        daily_data = daily_data.sort_values("Tanggal").reset_index(drop=True)
        daily_data["X_Index"] = daily_data.index
        
        X = daily_data["X_Index"].values
        Y_Omzet = daily_data["Pemasukan"].values
        Y_Laba = daily_data["Laba"].values
        
        # Perhitungan Rumus Manual Regresi Linear Sederhana via NumPy (y = mx + c)
        slope_o, intercept_o = np.polyfit(X, Y_Omzet, 1)
        slope_l, intercept_l = np.polyfit(X, Y_Laba, 1)
        
        # Membuat titik garis regresi historis
        daily_data["Regresi_Omzet"] = slope_o * X + intercept_o
        
        # Proyeksi ke Depan (Forecasting 7 Hari Mendatang)
        future_days = 7
        last_index = X[-1]
        future_X = np.array([last_index + i for i in range(1, future_days + 1)])
        
        last_date = daily_data["Tanggal"].max()
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=future_days)
        
        future_omzet_pred = slope_o * future_X + intercept_o
        future_laba_pred = slope_l * future_X + intercept_l
        
        # Cegah nilai minus muncul pada hasil prediksi regresi statistik
        future_omzet_pred = np.clip(future_omzet_pred, a_min=0, a_max=None)
        future_laba_pred = np.clip(future_laba_pred, a_min=0, a_max=None)
        
        # VISUALISASI GARIS TREN REGRESI LINEAR HISTORIS
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("#### Analisis Kecenderungan Tren (Linear Regression Trendline)")
        
        fig_reg = go.Figure()
        # Data Riil Penjualan
        fig_reg.add_trace(go.Scatter(x=daily_data["Tanggal"], y=Y_Omzet, mode='markers', name='Actual Revenue', marker=dict(color=HEX_NAVY, size=6)))
        # Garis Tren Regresi
        fig_reg.add_trace(go.Scatter(x=daily_data["Tanggal"], y=daily_data["Regresi_Omzet"], mode='lines', name='Linear Regression Line', line=dict(color=HEX_BLUE, width=3, dash='dash')))
        
        fig_reg.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=20, t=10, b=40), height=320,
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9"), yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_reg, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # LAYOUT HASIL PROYEKSI PERAMALAN 7 HARI KE DEPAN
        pred_col1, pred_col2 = st.columns(2)
        
        with pred_col1:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("#### Peramalan Pendapatan Kotor (Revenue Forecast) - 7 Hari Kedepan")
            df_fore_o = pd.DataFrame({"Tanggal": future_dates, "Prediksi Omzet": future_omzet_pred})
            
            fig_fore_o = px.bar(df_fore_o, x="Tanggal", y="Prediksi Omzet", text_auto=".2s", color_discrete_sequence=[HEX_LIGHT_BLUE])
            fig_fore_o.update_layout(plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=20, t=10, b=40), height=280, yaxis=dict(showgrid=True, gridcolor="#F1F5F9"))
            st.plotly_chart(fig_fore_o, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with pred_col2:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("#### Peramalan Laba Bersih (Net Profit Forecast) - 7 Hari Kedepan")
            df_fore_l = pd.DataFrame({"Tanggal": future_dates, "Prediksi Laba": future_laba_pred})
            
            fig_fore_l = px.bar(df_fore_l, x="Tanggal", y="Prediksi Laba", text_auto=".2s", color_discrete_sequence=["#10B981"]) # Hijau emerald profit
            fig_fore_l.update_layout(plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=20, t=10, b=40), height=280, yaxis=dict(showgrid=True, gridcolor="#F1F5F9"))
            st.plotly_chart(fig_fore_l, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        st.warning("Data operasional harian terlalu sedikit untuk merumuskan matriks Regresi Linear Sederhana. Silakan perluas rentang filter waktu Anda.")

    # MODEL KEDUA: SIMULASI INTERAKTIF TARGET FORECASTING (WHAT-IF ANALYSIS)
    st.markdown("###What-If Analysis: Target Penjualan & Simulasi Volume")
    st.markdown("Gunakan kontrol slider di bawah untuk mensimulasikan kenaikan target omzet dan mengetahui kebutuhan kuantitas penjualan harian.")
    
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    avg_daily_revenue = daily_data["Pemasukan"].mean() if len(daily_data) > 0 else 0
    avg_unit_price = filtered_df["Harga_Jual"].mean() if len(filtered_df) > 0 else 0
    
    # Slider interaktif untuk memilih persentase kenaikan target bisnis
    growth_slider = st.slider("Tentukan Target Pertumbuhan Omzet (%)", min_value=0, max_value=100, value=25, step=5)
    
    # Rumus Hitung Simulasi Bisnis
    simulated_target_revenue = avg_daily_revenue * (1 + (growth_slider / 100))
    additional_revenue_needed = simulated_target_revenue - avg_daily_revenue
    required_units_per_day = simulated_target_revenue / avg_unit_price if avg_unit_price > 0 else 0
    
    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        st.metric(label="Target Omzet Harian Baru", value=f"Rp {simulated_target_revenue:,.0f}")
    with sim_col2:
        st.metric(label="Tambahan Omzet Per Hari", value=f"Rp {additional_revenue_needed:,.0f}", delta=f"+{growth_slider}% Target")
    with sim_col3:
        st.metric(label="Kuota Penjualan Minimal Harian", value=f"{required_units_per_day:.1f} Pcs / Hari")
        
    st.markdown(f"""
    <p style="font-size:13.5px; color:#475569; margin-top:15px; line-height:1.5;">
        💡 <b>Insight Hasil Simulasi:</b> Untuk mendongkrak pendapatan harian Anda sebesar <b>{growth_slider}%</b> dari rata-rata historis berjalan, 
        operasional retail Anda wajib menjual minimal <b>{required_units_per_day:.1f} unit (Pcs)</b> pakaian setiap harinya dengan asumsi nilai rata-rata harga jual produk stabil pada kisaran <b>Rp {avg_unit_price:,.0f}</b>.
    </p>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)