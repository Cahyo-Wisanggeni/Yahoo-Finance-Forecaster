"""
Yahoo Finance Forecaster GUI
Aplikasi Antarmuka Grafis (GUI) untuk Prediksi Harga Saham menggunakan skforecast,
RandomForestRegressor, dan ForecasterDirect (10 Lags, 10 Rolling Means, 100 Trees).
"""

import os
import sys

__version__ = "1.0.0"

if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--version"):
    print(f"Yahoo Finance Forecaster GUI v{__version__}")
    sys.exit(0)

import threading
import warnings
from datetime import datetime, timedelta
import pandas as pd

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

import yfinance as yf

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from skforecast.direct import ForecasterDirect
from skforecast.preprocessing import RollingFeatures

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

# Matplotlib integration with Tkinter
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class YahooForecasterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Yahoo Finance Forecaster - GUI Edition v{__version__}")
        self.geometry("1280x820")
        self.minsize(1050, 700)
        
        # Color Theme
        self.colors = {
            "primary": "#6B21A8",        # Yahoo Purple Deep
            "primary_light": "#7C3AED",  # Purple Bright
            "primary_dark": "#4C1D95",
            "accent": "#06B6D4",         # Cyan Bright
            "bg": "#F8FAFC",             # Clean light slate
            "card_bg": "#FFFFFF",
            "text": "#0F172A",
            "text_muted": "#64748B",
            "border": "#E2E8F0",
            "success": "#10B981",
            "warning": "#F59E0B",
            "danger": "#EF4444"
        }

        self.configure(bg=self.colors["bg"])
        self.is_running = False
        self.last_results = None

        self._configure_styles()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Configure base styles
        self.style.configure(".", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 9))
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Card.TFrame", background=self.colors["card_bg"], relief="flat")
        
        # Labels
        self.style.configure("Header.TLabel", background=self.colors["primary"], foreground="#FFFFFF", font=("Segoe UI", 17, "bold"))
        self.style.configure("HeaderSub.TLabel", background=self.colors["primary"], foreground="#F8FAFC", font=("Segoe UI", 10))
        self.style.configure("CardTitle.TLabel", background=self.colors["card_bg"], foreground=self.colors["primary_dark"], font=("Segoe UI", 11, "bold"))
        self.style.configure("Bold.TLabel", background=self.colors["card_bg"], font=("Segoe UI", 9, "bold"))
        self.style.configure("Muted.TLabel", background=self.colors["card_bg"], foreground=self.colors["text_muted"], font=("Segoe UI", 8))
        self.style.configure("MetricVal.TLabel", background=self.colors["card_bg"], foreground=self.colors["primary"], font=("Segoe UI", 13, "bold"))

        # Buttons
        self.style.configure("Primary.TButton", background=self.colors["primary"], foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.map("Primary.TButton",
            background=[("active", self.colors["primary_light"]), ("disabled", "#CBD5E1")],
            foreground=[("disabled", "#94A3B8")]
        )

        self.style.configure("Accent.TButton", background=self.colors["accent"], foreground="#FFFFFF", font=("Segoe UI", 9, "bold"), padding=4)
        self.style.map("Accent.TButton", background=[("active", "#0891B2")])

        self.style.configure("Quick.TButton", background="#F1F5F9", foreground="#334155", font=("Segoe UI", 8), padding=3)
        self.style.map("Quick.TButton", background=[("active", "#E2E8F0")])

        self.style.configure("Reset.TButton", background="#F1F5F9", foreground="#475569", font=("Segoe UI", 9, "bold"), padding=5)
        self.style.map("Reset.TButton",
            background=[("active", "#E2E8F0"), ("disabled", "#F8FAFC")],
            foreground=[("disabled", "#94A3B8")]
        )

        # Notebook tabs
        self.style.configure("TNotebook", background=self.colors["bg"], tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab", background="#E2E8F0", foreground="#475569", padding=[15, 6], font=("Segoe UI", 9, "bold"))
        self.style.map("TNotebook.Tab",
            background=[("selected", self.colors["primary"]), ("active", "#CBD5E1")],
            foreground=[("selected", "#FFFFFF")]
        )

        # Progressbar
        self.style.configure("Horizontal.TProgressbar", troughcolor="#E2E8F0", background=self.colors["primary_light"], thickness=8)

        # Treeview
        self.style.configure("Treeview", 
            background="#FFFFFF", 
            foreground=self.colors["text"], 
            fieldbackground="#FFFFFF", 
            rowheight=26, 
            font=("Segoe UI", 9)
        )
        self.style.configure("Treeview.Heading", 
            background="#F1F5F9", 
            foreground=self.colors["primary_dark"], 
            font=("Segoe UI", 9, "bold"), 
            padding=5
        )
        self.style.map("Treeview", background=[("selected", "#EDE9FE")], foreground=[("selected", self.colors["primary_dark"])])

    def _build_ui(self):
        # ----------------------------------------------------
        # TOP HEADER
        # ----------------------------------------------------
        header_frame = tk.Frame(self, bg=self.colors["primary"], height=80)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        header_frame.pack_propagate(False)

        header_content = tk.Frame(header_frame, bg=self.colors["primary"])
        header_content.pack(side=tk.LEFT, fill=tk.Y, padx=22, pady=(12, 10))

        lbl_title = ttk.Label(header_content, text="Yahoo! Finance Forecaster", style="Header.TLabel")
        lbl_title.pack(anchor="w")

        lbl_subtitle = ttk.Label(header_content, text="Peramalan Deret Waktu Pasar Keuangan Berbasis Machine Learning", style="HeaderSub.TLabel")
        lbl_subtitle.pack(anchor="w", pady=(3, 0))

        badge_frame = tk.Frame(header_frame, bg=self.colors["primary"])
        badge_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=22, pady=22)
        lbl_version = tk.Label(badge_frame, text=f"EDISI GUI v{__version__}", bg=self.colors["primary_dark"], fg="#A7F3D0", font=("Segoe UI", 8, "bold"), padx=10, pady=4)
        lbl_version.pack()

        # ----------------------------------------------------
        # MAIN LAYOUT: LEFT CONTROLS & RIGHT CONTENT
        # ----------------------------------------------------
        main_container = ttk.Frame(self)
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=14, pady=12)

        # LEFT SIDEBAR (Scrollable Frame for Controls)
        left_sidebar = ttk.Frame(main_container, width=360)
        left_sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        left_sidebar.pack_propagate(False)

        # Card 1: Configuration Form
        card_config = tk.Frame(left_sidebar, bg=self.colors["card_bg"], bd=1, relief="solid", highlightbackground=self.colors["border"])
        card_config.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        cfg_header = tk.Frame(card_config, bg=self.colors["card_bg"])
        cfg_header.pack(fill=tk.X, padx=14, pady=(10, 4))

        lbl_cfg_title = tk.Label(cfg_header, text="⚙️ PARAMETER PERAMALAN", bg=self.colors["card_bg"], fg=self.colors["primary_dark"], font=("Segoe UI", 10, "bold"))
        lbl_cfg_title.pack(side=tk.LEFT)

        self.btn_reset = ttk.Button(cfg_header, text="🔄 Reset", style="Quick.TButton", command=self._action_reset_form)
        self.btn_reset.pack(side=tk.RIGHT)

        cfg_inner = tk.Frame(card_config, bg=self.colors["card_bg"])
        cfg_inner.pack(fill=tk.X, padx=14, pady=(0, 14))

        # 1. Ticker Symbol
        lbl_ticker = tk.Label(cfg_inner, text="Kode Ticker (Saham / Indeks):", bg=self.colors["card_bg"], font=("Segoe UI", 9, "bold"))
        lbl_ticker.pack(anchor="w", pady=(4, 2))

        self.var_ticker = tk.StringVar(self)
        self.var_ticker.trace_add("write", self._on_ticker_changed)

        self.ent_ticker = ttk.Entry(cfg_inner, textvariable=self.var_ticker, font=("Segoe UI", 10, "bold"))
        self.ent_ticker.pack(fill=tk.X, pady=(0, 10))

        # 2. Date Presets & Date Inputs
        lbl_dates = tk.Label(cfg_inner, text="Rentang Tanggal Historis:", bg=self.colors["card_bg"], font=("Segoe UI", 9, "bold"))
        lbl_dates.pack(anchor="w", pady=(4, 2))

        preset_row = tk.Frame(cfg_inner, bg=self.colors["card_bg"])
        preset_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(preset_row, text="1 Tahun", style="Quick.TButton", command=lambda: self._set_date_preset(365)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(preset_row, text="2 Tahun", style="Quick.TButton", command=lambda: self._set_date_preset(730)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(preset_row, text="3 Tahun", style="Quick.TButton", command=lambda: self._set_date_preset(1095)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(preset_row, text="5 Tahun", style="Quick.TButton", command=lambda: self._set_date_preset(1825)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        dates_grid = tk.Frame(cfg_inner, bg=self.colors["card_bg"])
        dates_grid.pack(fill=tk.X, pady=(0, 8))

        lbl_start = tk.Label(dates_grid, text="Tanggal Mulai (YYYY-MM-DD):", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"])
        lbl_start.grid(row=0, column=0, sticky="w", padx=(0, 4))
        lbl_end = tk.Label(dates_grid, text="Tanggal Selesai (YYYY-MM-DD):", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"])
        lbl_end.grid(row=0, column=1, sticky="w", padx=(4, 0))

        self.ent_start = ttk.Entry(dates_grid, font=("Segoe UI", 9))
        self.ent_start.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(2, 0))

        self.ent_end = ttk.Entry(dates_grid, font=("Segoe UI", 9))
        self.ent_end.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(2, 0))
        dates_grid.columnconfigure(0, weight=1)
        dates_grid.columnconfigure(1, weight=1)

        # 3. Frequency & Forecast Steps
        params_grid = tk.Frame(cfg_inner, bg=self.colors["card_bg"])
        params_grid.pack(fill=tk.X, pady=(4, 8))

        lbl_freq = tk.Label(params_grid, text="Jenis Frekuensi Data:", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"])
        lbl_freq.grid(row=0, column=0, sticky="w", padx=(0, 4))
        lbl_steps = tk.Label(params_grid, text="Periode Prediksi (Steps):", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"])
        lbl_steps.grid(row=0, column=1, sticky="w", padx=(4, 0))

        self.cmb_freq = ttk.Combobox(params_grid, values=["B (Business Days)", "D (Days)"], state="readonly", font=("Segoe UI", 9))
        self.cmb_freq.current(0)
        self.cmb_freq.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(2, 0))

        self.spn_steps = ttk.Spinbox(params_grid, from_=1, to=365, font=("Segoe UI", 9))
        self.spn_steps.delete(0, tk.END)
        self.spn_steps.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(2, 0))
        params_grid.columnconfigure(0, weight=1)
        params_grid.columnconfigure(1, weight=1)

        # ACTION BUTTON
        self.btn_run = ttk.Button(cfg_inner, text="🚀 MULAI PERAMALAN", style="Primary.TButton", command=self._action_start_forecast)
        self.btn_run.pack(fill=tk.X, pady=(10, 4))

        # Progress bar & status
        self.pbar = ttk.Progressbar(cfg_inner, style="Horizontal.TProgressbar", mode="determinate")
        self.pbar.pack(fill=tk.X, pady=(6, 2))
        
        self.lbl_status = tk.Label(cfg_inner, text="Siap menjalankan peramalan.", bg=self.colors["card_bg"], fg=self.colors["text_muted"], font=("Segoe UI", 8), anchor="w")
        self.lbl_status.pack(fill=tk.X)

        # Card 2: Company Info & Evaluation Metrics
        card_info = tk.Frame(left_sidebar, bg=self.colors["card_bg"], bd=1, relief="solid", highlightbackground=self.colors["border"])
        card_info.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        lbl_info_title = tk.Label(card_info, text="📌 INFORMASI PERUSAHAAN & INPUT", bg=self.colors["card_bg"], fg=self.colors["primary_dark"], font=("Segoe UI", 10, "bold"))
        lbl_info_title.pack(anchor="w", padx=14, pady=(8, 4))

        self.info_container = tk.Frame(card_info, bg=self.colors["card_bg"])
        self.info_container.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))

        # Info labels
        self.lbl_comp_ticker = tk.Label(self.info_container, text="Kode Ticker: -", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"], anchor="w")
        self.lbl_comp_ticker.pack(fill=tk.X, pady=1)

        self.lbl_comp_name = tk.Label(self.info_container, text="Nama: -", bg=self.colors["card_bg"], font=("Segoe UI", 9, "bold"), anchor="w", wraplength=310, justify="left")
        self.lbl_comp_name.pack(fill=tk.X, pady=1)

        self.lbl_comp_sector = tk.Label(self.info_container, text="Sektor: -", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"], anchor="w")
        self.lbl_comp_sector.pack(fill=tk.X, pady=1)

        self.lbl_comp_ind = tk.Label(self.info_container, text="Industri: -", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"], anchor="w")
        self.lbl_comp_ind.pack(fill=tk.X, pady=1)

        self.lbl_comp_dates = tk.Label(self.info_container, text="Rentang Tanggal: -", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"], anchor="w")
        self.lbl_comp_dates.pack(fill=tk.X, pady=1)

        self.lbl_comp_freq = tk.Label(self.info_container, text="Frekuensi: -", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"], anchor="w")
        self.lbl_comp_freq.pack(fill=tk.X, pady=1)

        self.lbl_comp_steps = tk.Label(self.info_container, text="Periode Prediksi (Steps): -", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"], anchor="w")
        self.lbl_comp_steps.pack(fill=tk.X, pady=1)

        sep = ttk.Separator(self.info_container, orient="horizontal")
        sep.pack(fill=tk.X, pady=4)

        # Metric Tiles
        metrics_box = tk.Frame(self.info_container, bg="#F8FAFC", bd=1, relief="solid")
        metrics_box.pack(fill=tk.X, pady=(2, 4))

        m_inner = tk.Frame(metrics_box, bg="#F8FAFC")
        m_inner.pack(fill=tk.X, padx=8, pady=4)

        lbl_m1 = tk.Label(m_inner, text="Mean Absolute Percentage Error (MAPE)", bg="#F8FAFC", font=("Segoe UI", 8), fg=self.colors["text_muted"])
        lbl_m1.pack(anchor="w")
        self.lbl_mape = tk.Label(m_inner, text="- %", bg="#F8FAFC", font=("Segoe UI", 12, "bold"), fg=self.colors["primary"])
        self.lbl_mape.pack(anchor="w", pady=(0, 2))

        lbl_m2 = tk.Label(m_inner, text="Mean Absolute Error (MAE)", bg="#F8FAFC", font=("Segoe UI", 8), fg=self.colors["text_muted"])
        lbl_m2.pack(anchor="w")
        self.lbl_mae = tk.Label(m_inner, text="-", bg="#F8FAFC", font=("Segoe UI", 11, "bold"), fg="#0D9488")
        self.lbl_mae.pack(anchor="w")

        # Hyperparameters summary
        self.lbl_hyperparams = tk.Label(self.info_container, text="Model: ForecasterDirect (10 Lags, 10 Roll Mean, 100 Trees)", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"], anchor="w", wraplength=310, justify="left")
        self.lbl_hyperparams.pack(fill=tk.X, pady=(3, 0))

        # ----------------------------------------------------
        # RIGHT AREA: NOTEBOOK (TABS)
        # ----------------------------------------------------
        right_container = ttk.Frame(main_container)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(right_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # TAB 1: Visualisasi Grafik
        self.tab_charts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_charts, text=" 📊 Grafik Prediksi ")

        # TAB 2: Tabel Hasil
        self.tab_table = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_table, text=" 📋 Tabel Rincian Prediksi ")

        # TAB 3: Log Proses
        self.tab_log = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_log, text=" 📝 Log Komputasi ")

        # TAB 4: Tutorial
        self.tab_tutorial = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tutorial, text=" 📖 Tutorial ")

        self._setup_chart_tab()
        self._setup_table_tab()
        self._setup_log_tab()
        self._setup_tutorial_tab()

    def _setup_chart_tab(self):
        # Top toolbar row inside chart tab
        chart_top_bar = tk.Frame(self.tab_charts, bg=self.colors["bg"])
        chart_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(6, 4), padx=6)

        lbl_chart_hint = tk.Label(chart_top_bar, text="📈 Visualisasi Evaluasi Model & Hasil Proyeksi Masa Depan", bg=self.colors["bg"], font=("Segoe UI", 9, "bold"), fg=self.colors["primary_dark"])
        lbl_chart_hint.pack(side=tk.LEFT, pady=2)

        btn_popup_chart = ttk.Button(chart_top_bar, text="🖥️ Tampilkan Jendela Pop-up HD", style="Accent.TButton", command=self._action_popup_chart)
        btn_popup_chart.pack(side=tk.RIGHT, padx=4)

        # Matplotlib Canvas embedded
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(9, 6.5), facecolor='white')
        self._init_empty_chart()

        self.canvas_frame = tk.Frame(self.tab_charts, bg="#FFFFFF", bd=1, relief="solid")
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.draw()
        
        # Toolbar
        self.toolbar_frame = tk.Frame(self.tab_charts, bg="#F1F5F9")
        self.toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(0, 4))
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _init_empty_chart(self):
        self.ax1.clear()
        self.ax2.clear()
        self.ax1.text(0.5, 0.5, "Klik 'MULAI PERAMALAN' untuk menghasilkan grafik evaluasi model.",
                      horizontalalignment='center', verticalalignment='center', transform=self.ax1.transAxes,
                      color='#94A3B8', fontsize=11, style='italic')
        self.ax1.set_title("1. Evaluasi Model (Data Latih vs Data Uji vs Prediksi)", fontsize=10, fontweight='bold', pad=8)
        self.ax1.grid(True, linestyle='--', alpha=0.3)

        self.ax2.text(0.5, 0.5, "Grafik peramalan akhir akan ditampilkan di sini.",
                      horizontalalignment='center', verticalalignment='center', transform=self.ax2.transAxes,
                      color='#94A3B8', fontsize=11, style='italic')
        self.ax2.set_title("2. Hasil Peramalan Akhir (Data Historis vs Prediksi)", fontsize=10, fontweight='bold', pad=8)
        self.ax2.grid(True, linestyle='--', alpha=0.3)
        self.fig.tight_layout(h_pad=2.5)

    def _setup_table_tab(self):
        # Table Top Action Bar
        tbl_top_bar = tk.Frame(self.tab_table, bg=self.colors["bg"])
        tbl_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(6, 6), padx=6)

        lbl_tbl_title = tk.Label(tbl_top_bar, text="Tabel Proyeksi Harga Saham", bg=self.colors["bg"], font=("Segoe UI", 10, "bold"), fg=self.colors["primary_dark"])
        lbl_tbl_title.pack(side=tk.LEFT, pady=2)

        btn_export = ttk.Button(tbl_top_bar, text="💾 Ekspor Hasil ke CSV", style="Primary.TButton", command=self._action_export_csv)
        btn_export.pack(side=tk.RIGHT, padx=4)

        # Treeview Table
        table_container = tk.Frame(self.tab_table, bg="#FFFFFF", bd=1, relief="solid")
        table_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        columns = ("no", "date", "pred_price", "diff_val", "diff_pct")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("no", text="No")
        self.tree.heading("date", text="Tanggal Prediksi")
        self.tree.heading("pred_price", text="Prediksi Harga")
        self.tree.heading("diff_val", text="Perubahan (vs Harga Terakhir)")
        self.tree.heading("diff_pct", text="% Perubahan")

        self.tree.column("no", width=60, anchor="center")
        self.tree.column("date", width=160, anchor="center")
        self.tree.column("pred_price", width=180, anchor="e")
        self.tree.column("diff_val", width=220, anchor="e")
        self.tree.column("diff_pct", width=140, anchor="e")

        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

    def _setup_log_tab(self):
        log_top_bar = tk.Frame(self.tab_log, bg=self.colors["bg"])
        log_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(6, 6), padx=6)

        lbl_log_title = tk.Label(log_top_bar, text="Terminal Log Proses Real-time", bg=self.colors["bg"], font=("Segoe UI", 10, "bold"), fg=self.colors["primary_dark"])
        lbl_log_title.pack(side=tk.LEFT, pady=2)

        btn_clear_log = ttk.Button(log_top_bar, text="Bersihkan Log", style="Quick.TButton", command=self._action_clear_log)
        btn_clear_log.pack(side=tk.RIGHT, padx=4)

        log_container = tk.Frame(self.tab_log, bg="#FFFFFF", bd=1, relief="solid")
        log_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        self.txt_log = ScrolledText(log_container, bg="#0F172A", fg="#F8FAFC", insertbackground="#FFFFFF", font=("Consolas", 9), relief="flat")
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self._log("Yahoo Finance Forecaster GUI diinisialisasi dan siap digunakan.")

    def _log(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert(tk.END, f"[{timestamp}] {text}\n")
        self.txt_log.see(tk.END)

    def _action_clear_log(self):
        self.txt_log.delete("1.0", tk.END)

    def _setup_tutorial_tab(self):
        tut_top_bar = tk.Frame(self.tab_tutorial, bg=self.colors["bg"])
        tut_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(6, 6), padx=6)

        lbl_tut_title = tk.Label(tut_top_bar, text="📖 Panduan Singkat & Tutorial Penggunaan", bg=self.colors["bg"], font=("Segoe UI", 10, "bold"), fg=self.colors["primary_dark"])
        lbl_tut_title.pack(side=tk.LEFT, pady=2)

        tut_container = tk.Frame(self.tab_tutorial, bg="#FFFFFF", bd=1, relief="solid")
        tut_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        txt_tut = ScrolledText(tut_container, bg="#FFFFFF", fg="#1E293B", font=("Segoe UI", 10), relief="flat", wrap="word", padx=18, pady=16)
        txt_tut.pack(fill=tk.BOTH, expand=True)

        # Style tags for tutorial content
        txt_tut.tag_configure("h1", font=("Segoe UI", 13, "bold"), foreground=self.colors["primary_dark"], spacing1=4, spacing3=6)
        txt_tut.tag_configure("h2", font=("Segoe UI", 11, "bold"), foreground=self.colors["primary"], spacing1=12, spacing3=4)
        txt_tut.tag_configure("body", font=("Segoe UI", 10), foreground="#334155", spacing3=3)
        txt_tut.tag_configure("bullet", font=("Segoe UI", 10), foreground="#334155", lmargin1=18, lmargin2=34, spacing3=3)

        tutorial_content = [
            ("Panduan Lengkap Penggunaan Yahoo! Finance Forecaster\n", "h1"),
            ("Aplikasi ini menggunakan algoritma Machine Learning Random Forest Regressor & skforecast (ForecasterDirect) untuk memproyeksikan pergerakan harga penutupan saham masa depan secara akurat.\n\n", "body"),

            ("1. Memasukkan Kode Ticker Saham\n", "h2"),
            ("• Ketik kode ticker saham Yahoo Finance pada kolom Kode Ticker (contoh: BBCA.JK, BBRI.JK, TLKM.JK, AAPL, NVDA).\n", "bullet"),
            ("• Untuk saham bursa Indonesia (BEI/IDX), pastikan selalu menggunakan akhiran .JK (contoh: BBCA.JK).\n\n", "bullet"),

            ("2. Menentukan Rentang Tanggal Historis\n", "h2"),
            ("• Start Date (YYYY-MM-DD): Tanggal awal riwayat data saham (contoh: 2024-01-01).\n", "bullet"),
            ("• End Date (YYYY-MM-DD): Tanggal akhir riwayat data saham (contoh: 2026-11-16).\n", "bullet"),
            ("• Gunakan tombol preset cepat (1 Tahun, 2 Tahun, 3 Tahun, 5 Tahun) untuk mengisi rentang tanggal secara instan.\n", "bullet"),
            ("• Tips: Rentang 2 Tahun umumnya memberikan performa optimal antara akurasi dan kecepatan komputasi.\n\n", "bullet"),

            ("3. Memilih Frekuensi Data & Langkah Peramalan\n", "h2"),
            ("• Jenis Frekuensi Data:\n", "bullet"),
            ("  - B (Business Days): Hanya hari bursa aktif (Senin–Jumat). Sangat direkomendasikan untuk analisis saham.\n", "bullet"),
            ("  - D (Days): Setiap hari kalender termasuk akhir pekan (mengisi hari libur dengan harga terakhir).\n", "bullet"),
            ("• Forecast Steps: Masukkan berapa langkah / hari ke depan yang ingin diproyeksikan (contoh: 10, 30, atau 60).\n\n", "bullet"),

            ("4. Memulai Peramalan (Mulai Peramalan)\n", "h2"),
            ("• Klik tombol '🚀 MULAI PERAMALAN'. Seluruh proses dijalankan di background thread sehingga GUI tetap responsif.\n", "bullet"),
            ("• Tahap [1/2] Melatih Model Peramalan: Model dilatih pada data latih (80%) dan diuji ke data uji (20%) untuk menghitung metrik evaluasi (MAPE & MAE).\n", "bullet"),
            ("• Tahap [2/2] Melakukan Peramalan: Model final dilatih pada 100% data historis untuk memproyeksikan harga masa depan sejumlah Forecast Steps.\n\n", "bullet"),

            ("5. Membaca & Mengekspor Hasil Prediksi\n", "h2"),
            ("• Tab '📊 Grafik Prediksi': Menampilkan 2 grafik bersusun (Evaluasi Model dan Hasil Proyeksi Masa Depan). Tersedia tombol 'Tampilkan Jendela Pop-up HD' untuk fitur Zoom dan Pan interaktif.\n", "bullet"),
            ("• Tab '📋 Tabel Rincian Prediksi': Menampilkan daftar tanggal prediksi, estimasi harga, selisih nominal, dan % perubahan. Klik '💾 Ekspor Hasil ke CSV' untuk menyimpan hasil ke file spreadsheet/Excel.\n", "bullet"),
            ("• Tab '📝 Log Komputasi': Memantau catatan teknis proses download data, evaluasi error, dan eksekusi model secara langsung.\n\n", "bullet"),

            ("6. Fitur Tombol Reset Form\n", "h2"),
            ("• Jika ingin meramal saham lain atau membersihkan seluruh data, klik tombol '🔄 Reset' di kanan atas panel Parameter Peramalan.\n", "bullet"),
            ("• Tombol ini akan mengosongkan seluruh kotak input dan mengembalikan tabel serta grafik ke kondisi awal.", "bullet"),
        ]

        for text, tag in tutorial_content:
            txt_tut.insert(tk.END, text, tag)

        txt_tut.config(state="disabled")

    def _on_ticker_changed(self, *args):
        val = self.var_ticker.get()
        if val != val.upper():
            def to_upper():
                try:
                    pos = self.ent_ticker.index(tk.INSERT)
                except Exception:
                    pos = None
                self.var_ticker.set(self.var_ticker.get().upper())
                if pos is not None:
                    try:
                        self.ent_ticker.icursor(pos)
                    except Exception:
                        pass
            self.after_idle(to_upper)

    def _set_ticker(self, ticker):
        self.ent_ticker.delete(0, tk.END)
        self.ent_ticker.insert(0, ticker)

    def _set_date_preset(self, days_back):
        today = datetime.now()
        past_date = today - timedelta(days=days_back)
        self.ent_start.delete(0, tk.END)
        self.ent_start.insert(0, past_date.strftime("%Y-%m-%d"))
        self.ent_end.delete(0, tk.END)
        self.ent_end.insert(0, today.strftime("%Y-%m-%d"))

    def _action_check_ticker(self):
        ticker = self.ent_ticker.get().strip().upper()
        if not ticker:
            messagebox.showwarning("Peringatan", "Silakan masukkan kode ticker terlebih dahulu.")
            return

        start_date = self.ent_start.get().strip()
        end_date = self.ent_end.get().strip()
        freq_str = self.cmb_freq.get()
        steps = self.spn_steps.get().strip()

        self._log(f"Memeriksa informasi ticker: {ticker}...")
        self.lbl_status.config(text=f"Mengecek ticker {ticker}...")

        def worker():
            try:
                t = yf.Ticker(ticker)
                info = t.info or {}
                name = info.get('longName') or info.get('shortName')
                sector = info.get('sector', 'N/A')
                industry = info.get('industry', 'N/A')
                
                if not name:
                    self.after(0, lambda: messagebox.showerror("Error", f"Ticker '{ticker}' tidak ditemukan atau data tidak tersedia di Yahoo Finance!"))
                    self.after(0, lambda: self._log(f"Gagal: Ticker '{ticker}' tidak valid."))
                    self.after(0, lambda: self.lbl_status.config(text="Ticker tidak valid."))
                    return

                self.after(0, lambda: self._update_company_info(name, sector, industry, ticker, start_date, end_date, freq_str, steps))
                self.after(0, lambda: self._log(f"Ticker valid: {name} | Sektor: {sector}"))
                self.after(0, lambda: self.lbl_status.config(text=f"Ticker '{ticker}' valid."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Gagal mengambil info ticker: {str(e)}"))
                self.after(0, lambda: self.lbl_status.config(text="Gagal mengecek ticker."))

        threading.Thread(target=worker, daemon=True).start()

    def _update_company_info(self, name, sector, industry, ticker, start_date=None, end_date=None, freq_desc=None, steps=None):
        self.lbl_comp_ticker.config(text=f"Kode Ticker: {ticker}")
        self.lbl_comp_name.config(text=f"Nama: {name}")
        self.lbl_comp_sector.config(text=f"Sektor: {sector}")
        self.lbl_comp_ind.config(text=f"Industri: {industry}")
        if start_date and end_date:
            self.lbl_comp_dates.config(text=f"Rentang Tanggal: {start_date} s/d {end_date}")
        if freq_desc:
            self.lbl_comp_freq.config(text=f"Frekuensi: {freq_desc}")
        if steps:
            self.lbl_comp_steps.config(text=f"Periode Prediksi: {steps} steps")

    def _action_start_forecast(self):
        if self.is_running:
            return

        ticker = self.ent_ticker.get().strip().upper()
        start_date = self.ent_start.get().strip()
        end_date = self.ent_end.get().strip()
        freq_str = self.cmb_freq.get()
        freq = "B" if freq_str.startswith("B") else "D"
        freq_desc = "B (Business Days)" if freq == "B" else "D (Days)"

        # Validasi Input
        if not ticker:
            messagebox.showerror("Error Input", "Kode ticker tidak boleh kosong.")
            return

        if not start_date:
            messagebox.showerror("Error Input", "Tanggal Mulai tidak boleh kosong.\nFormat: YYYY-MM-DD (contoh: 2024-01-01) atau gunakan tombol preset tanggal di atas.")
            return

        if not end_date:
            messagebox.showerror("Error Input", "Tanggal Selesai tidak boleh kosong.\nFormat: YYYY-MM-DD (contoh: 2025-01-01) atau gunakan tombol preset tanggal di atas.")
            return

        if start_date >= end_date:
            messagebox.showerror("Error Input", "Tanggal Mulai harus lebih awal daripada Tanggal Selesai.")
            return

        steps_raw = self.spn_steps.get().strip()
        if not steps_raw:
            messagebox.showerror("Error Input", "Periode Prediksi (Steps) tidak boleh kosong.\nSilakan masukkan jumlah langkah peramalan (contoh: 30).")
            return

        try:
            steps = int(steps_raw)
            if steps <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error Input", "Periode Prediksi (Steps) harus berupa angka bulat positif lebih besar dari 0.")
            return

        # Start execution in background thread
        self.is_running = True
        self.btn_run.config(state="disabled")
        self.btn_reset.config(state="disabled")
        self.pbar["value"] = 0
        self.lbl_status.config(text="Memulai proses peramalan...")
        self._log(f"=== Memulai Peramalan untuk {ticker} ===")
        self._log(f"Rentang: {start_date} s/d {end_date} | Frekuensi: {freq_desc} | Steps: {steps}")
        self._log("Model: ForecasterDirect (10 Lags, 10 Rolling Means, 100 Trees - Fixed)")

        threading.Thread(
            target=self._forecast_worker,
            args=(ticker, start_date, end_date, freq, steps),
            daemon=True
        ).start()

    def _forecast_worker(self, ticker, start_date, end_date, freq, steps):
        try:
            freq_desc = "B (Business Days)" if freq == "B" else "D (Days)"

            # 1. Fetch Company Info
            self.after(0, lambda: self.lbl_status.config(text="Mengunduh informasi perusahaan..."))
            try:
                t_obj = yf.Ticker(ticker)
                info = t_obj.info or {}
            except Exception:
                info = {}

            name = info.get('longName') or info.get('shortName') or ticker
            sector = info.get('sector', 'N/A')
            industry = info.get('industry', 'N/A')
            self.after(0, lambda: self._update_company_info(name, sector, industry, ticker, start_date, end_date, freq_desc, steps))

            # 2. Download Historical Price Data
            self.after(0, lambda: self.lbl_status.config(text="Mengunduh data historis harga saham..."))
            self.after(0, lambda: self._log(f"Mengunduh data {ticker} dari Yahoo Finance..."))
            
            df_raw = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if df_raw.empty:
                raise ValueError(f"Tidak ada data ditemukan untuk ticker '{ticker}' pada rentang {start_date} s/d {end_date}.")

            if isinstance(df_raw.columns, pd.MultiIndex):
                try:
                    close_data = df_raw['Close'][ticker]
                except KeyError:
                    close_data = df_raw['Close'].iloc[:, 0]
            else:
                close_data = df_raw['Close']

            close_data = close_data.squeeze()
            data = close_data.asfreq(freq).ffill().bfill()

            total_points = len(data)
            self.after(0, lambda: self._log(f"Data berhasil diambil: {total_points} titik data ({freq})."))

            if total_points < 30:
                raise ValueError(f"Data terlalu sedikit ({total_points} titik). Diperlukan minimal 30 titik data time series.")

            self.after(0, lambda: self.pbar.config(value=15))

            # 3. Train-Test Split (20% for testing)
            val_steps = max(1, round(0.2 * total_points))
            train = data[:-val_steps]
            test = data[-val_steps:]
            self.after(0, lambda: self._log(f"Data Split: Train={len(train)} titik, Test={len(test)} titik."))

            # Inisialisasi 10 Fitur Rolling Mean & Konfigurasi Fixed
            rolling_features = RollingFeatures(
                stats=['mean'] * 10,
                window_sizes=list(range(1, 11))
            )
            lags = 10
            n_estimators = 100

            # 4. Model Validation & Evaluation
            self.after(0, lambda: self.lbl_status.config(text="[1/2] Melatih Model Peramalan..."))
            self.after(0, lambda: self._log("Tahap 1/2: Melatih Model Peramalan..."))
            self.after(0, lambda: self.pbar.config(value=30))

            forecaster_val = ForecasterDirect(
                estimator=RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1),
                steps=val_steps,
                lags=lags,
                differentiation=1,
                window_features=rolling_features
            )
            forecaster_val.fit(y=train)
            val_predictions = forecaster_val.predict(steps=val_steps)

            error_mae = mean_absolute_error(y_true=test, y_pred=val_predictions)
            error_mape = mean_absolute_percentage_error(y_true=test, y_pred=val_predictions)
            mape_pct = error_mape * 100

            self.after(0, lambda: self._log(f"Hasil Evaluasi: MAE = {error_mae:,.2f} | MAPE = {mape_pct:.2f}%"))
            self.after(0, lambda: self._log("Ringkasan Fitur: 10 Lags + 10 Rolling Means (20 Fitur Prediktor)"))
            self.after(0, lambda: self.pbar.config(value=65))

            # 5. Final Prediction on Entire Dataset
            self.after(0, lambda: self.lbl_status.config(text="[2/2] Melakukan Peramalan..."))
            self.after(0, lambda: self._log(f"Tahap 2/2: Melakukan Peramalan ({steps} steps)..."))

            forecaster_final = ForecasterDirect(
                estimator=RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1),
                steps=steps,
                lags=lags,
                differentiation=1,
                window_features=rolling_features
            )
            forecaster_final.fit(y=data)
            final_predictions = forecaster_final.predict(steps=steps)

            self.after(0, lambda: self.pbar.config(value=100))
            self.after(0, lambda: self.lbl_status.config(text="Peramalan selesai dengan sukses!"))
            self.after(0, lambda: self._log("Peramalan Berhasil Diselesaikan!"))

            # Store result bundle
            bundle = {
                "ticker": ticker,
                "name": name,
                "sector": sector,
                "industry": industry,
                "train": train,
                "test": test,
                "val_predictions": val_predictions,
                "data": data,
                "final_predictions": final_predictions,
                "steps": steps,
                "mae": error_mae,
                "mape": mape_pct,
                "lags": lags,
                "n_estimators": n_estimators
            }

            self.after(0, lambda: self._display_results(bundle))

        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: messagebox.showerror("Kesalahan", f"Terjadi kesalahan saat memproses:\n{err_msg}"))
            self.after(0, lambda: self._log(f"ERROR: {err_msg}"))
            self.after(0, lambda: self.lbl_status.config(text="Proses gagal."))
        finally:
            self.after(0, self._finish_process)

    def _finish_process(self):
        self.is_running = False
        self.btn_run.config(state="normal")
        self.btn_reset.config(state="normal")

    def _action_reset_form(self):
        if self.is_running:
            messagebox.showwarning("Peringatan", "Proses peramalan sedang berjalan. Harap tunggu hingga selesai.")
            return

        # 1. Kosongkan semua kotak isian
        self.ent_ticker.delete(0, tk.END)
        self.ent_start.delete(0, tk.END)
        self.ent_end.delete(0, tk.END)
        self.spn_steps.delete(0, tk.END)
        self.cmb_freq.current(0)

        # 2. Reset informasi perusahaan & input
        self.lbl_comp_ticker.config(text="Kode Ticker: -")
        self.lbl_comp_name.config(text="Nama: -")
        self.lbl_comp_sector.config(text="Sektor: -")
        self.lbl_comp_ind.config(text="Industri: -")
        self.lbl_comp_dates.config(text="Rentang Tanggal: -")
        self.lbl_comp_freq.config(text="Frekuensi: -")
        self.lbl_comp_steps.config(text="Periode Prediksi (Steps): -")

        # 3. Reset metrik evaluasi
        self.lbl_mape.config(text="- %")
        self.lbl_mae.config(text="-")
        self.lbl_hyperparams.config(text="Model: ForecasterDirect (10 Lags, 10 Roll Mean, 100 Trees)")

        # 4. Reset progress bar & status
        self.pbar["value"] = 0
        self.lbl_status.config(text="Seluruh kotak isian berhasil direset.")

        # 5. Bersihkan tabel hasil
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 6. Bersihkan grafik tampilan
        self.ax1.clear()
        self.ax2.clear()
        self.ax1.set_title("Evaluasi Peramalan", fontsize=10, pad=8, fontweight='bold', color='#1E293B')
        self.ax1.grid(True, linestyle='--', alpha=0.35)
        self.ax2.set_title("Hasil Peramalan Akhir", fontsize=10, pad=8, fontweight='bold', color='#1E293B')
        self.ax2.grid(True, linestyle='--', alpha=0.35)
        self.fig.tight_layout(h_pad=3.0)
        self.canvas.draw()

        self.last_results = None
        self._log("Semua kotak input dan data peramalan berhasil direset.")

    def _display_results(self, b):
        self.last_results = b

        # 1. Update Metrics in UI
        self.lbl_mape.config(text=f"{b['mape']:.2f}%")
        self.lbl_mae.config(text=f"{b['mae']:,.2f}")
        self.lbl_hyperparams.config(
            text=f"Direct ({b['steps']} stp) | Trees={b['n_estimators']} | Lags={b['lags']} | 10 Rolling Means (1..10) | Diff=1"
        )

        # 2. Populate Treeview Table
        for item in self.tree.get_children():
            self.tree.delete(item)

        last_known_price = float(b["data"].iloc[-1])
        pred_items = list(b["final_predictions"].items())

        for idx, (dt, val) in enumerate(pred_items, start=1):
            dt_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)
            pred_val = float(val)
            diff_val = pred_val - last_known_price
            diff_pct = (diff_val / last_known_price) * 100 if last_known_price != 0 else 0

            diff_val_str = f"{'+' if diff_val >= 0 else ''}{diff_val:,.2f}"
            diff_pct_str = f"{'+' if diff_pct >= 0 else ''}{diff_pct:.2f}%"

            self.tree.insert("", tk.END, values=(
                idx,
                dt_str,
                f"{pred_val:,.2f}",
                diff_val_str,
                diff_pct_str
            ))

        # 3. Render Matplotlib Charts
        self._render_charts(b["train"], b["test"], b["val_predictions"], b["data"], b["final_predictions"], b["ticker"])

        # Auto switch to Chart tab
        self.notebook.select(self.tab_charts)

    def _render_charts(self, train, test, val_predictions, data, final_predictions, ticker):
        self.ax1.clear()
        self.ax2.clear()

        # 1. Subplot Atas: Evaluasi Train vs Test vs Predictions
        train.plot(ax=self.ax1, label='Data Latih', color='#1f77b4', linewidth=1.5)
        test.plot(ax=self.ax1, label='Data Uji', color='#2ca02c', linewidth=1.5)
        val_predictions.plot(ax=self.ax1, label='Prediksi Validasi', color='#ff7f0e', linewidth=1.5)
        self.ax1.set_title(f"Evaluasi Peramalan ({ticker})", fontsize=10, pad=8, fontweight='bold', color='#1E293B')
        self.ax1.set_xlabel("Tanggal", fontsize=8)
        self.ax1.set_ylabel("Harga", fontsize=8)
        self.ax1.legend(loc='upper left', fontsize=8, framealpha=0.85)
        self.ax1.grid(True, linestyle='--', alpha=0.35)

        # 2. Subplot Bawah: Data Historis vs Hasil Prediksi Akhir
        data.plot(ax=self.ax2, label='Data Historis', color='#1f77b4', linewidth=1.5)
        final_predictions.plot(ax=self.ax2, label='Prediksi Masa Depan', color='#ff7f0e', linewidth=1.5)
        self.ax2.set_title(f"Hasil Peramalan Akhir ({ticker})", fontsize=10, pad=8, fontweight='bold', color='#1E293B')
        self.ax2.set_xlabel("Tanggal", fontsize=8)
        self.ax2.set_ylabel("Harga", fontsize=8)
        self.ax2.legend(loc='upper left', fontsize=8, framealpha=0.85)
        self.ax2.grid(True, linestyle='--', alpha=0.35)

        self.fig.tight_layout(h_pad=3.0)
        self.canvas.draw()

    def _action_popup_chart(self):
        if self.last_results is None:
            messagebox.showinfo("Informasi", "Belum ada hasil peramalan untuk ditampilkan.")
            return

        b = self.last_results
        
        # Create detached high-res matplotlib window
        pop_fig, (pax1, pax2) = plt.subplots(2, 1, figsize=(12, 8.5), facecolor='white')

        b["train"].plot(ax=pax1, label='Data Latih', color='#1f77b4', linewidth=1.5)
        b["test"].plot(ax=pax1, label='Data Uji', color='#2ca02c', linewidth=1.5)
        b["val_predictions"].plot(ax=pax1, label='Prediksi Validasi', color='#ff7f0e', linewidth=1.5)
        pax1.set_title(f"Evaluasi Peramalan ({b['ticker']})", fontsize=11, pad=8, fontweight='bold')
        pax1.set_xlabel("Tanggal", fontsize=9)
        pax1.set_ylabel("Harga", fontsize=9)
        pax1.legend(loc='upper left', fontsize=9)
        pax1.grid(True, linestyle='--', alpha=0.4)

        b["data"].plot(ax=pax2, label='Data Historis', color='#1f77b4', linewidth=1.5)
        b["final_predictions"].plot(ax=pax2, label='Prediksi Masa Depan', color='#ff7f0e', linewidth=1.5)
        pax2.set_title(f"Hasil Peramalan Akhir ({b['ticker']})", fontsize=11, pad=8, fontweight='bold')
        pax2.set_xlabel("Tanggal", fontsize=9)
        pax2.set_ylabel("Harga", fontsize=9)
        pax2.legend(loc='upper left', fontsize=9)
        pax2.grid(True, linestyle='--', alpha=0.3)

        pop_fig.tight_layout(h_pad=3.5)

        try:
            mngr = pop_fig.canvas.manager
            mngr.set_window_title(f"Yahoo Finance Forecaster - {b['ticker']} (Tampilan HD)")
            if hasattr(mngr, 'window'):
                mngr.window.deiconify()
                mngr.window.attributes('-topmost', True)
                mngr.window.lift()
        except Exception:
            pass

        plt.show()

    def _action_export_csv(self):
        if self.last_results is None:
            messagebox.showinfo("Informasi", "Belum ada hasil peramalan untuk diekspor.")
            return

        b = self.last_results
        ticker = b["ticker"]
        default_filename = f"prediksi_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")],
            initialfile=default_filename,
            title="Simpan Hasil Peramalan ke CSV"
        )

        if not filepath:
            return

        try:
            rows = []
            last_known_price = float(b["data"].iloc[-1])
            for idx, (dt, val) in enumerate(b["final_predictions"].items(), start=1):
                dt_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)
                pred_val = float(val)
                diff_val = pred_val - last_known_price
                diff_pct = (diff_val / last_known_price) * 100 if last_known_price != 0 else 0
                rows.append({
                    "No": idx,
                    "Tanggal": dt_str,
                    "Prediksi_Harga": pred_val,
                    "Perubahan_Harga": diff_val,
                    "Perubahan_Persen": diff_pct,
                    "Harga_Terakhir": last_known_price,
                    "Ticker": ticker
                })

            df_export = pd.DataFrame(rows)
            df_export.to_csv(filepath, index=False)
            messagebox.showinfo("Berhasil", f"Data peramalan berhasil disimpan ke:\n{filepath}")
            self._log(f"Hasil peramalan diekspor ke: {filepath}")
        except Exception as e:
            messagebox.showerror("Error Ekspor", f"Gagal menyimpan file CSV:\n{str(e)}")

    def _on_close(self):
        plt.close('all')
        self.destroy()
        sys.exit(0)


def main():
    app = YahooForecasterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
