import os
import sys

__version__ = "1.0.0"

if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--version"):
    print(f"Yahoo Finance Forecaster GUI v{__version__}")
    sys.exit(0)

import json
import threading
import warnings
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

import yfinance as yf

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import TimeSeriesSplit, learning_curve
from skforecast.direct import ForecasterDirect
from skforecast.preprocessing import RollingFeatures

try:
    import shap
except ImportError:
    shap = None

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

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

        self.colors = {
            "primary": "#6B21A8",
            "primary_light": "#7C3AED",
            "primary_dark": "#4C1D95",
            "accent": "#06B6D4",
            "bg": "#F8FAFC",
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
        self.history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forecast_history.json")
        self.history_items = []

        self._configure_styles()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure(".", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 9))
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Card.TFrame", background=self.colors["card_bg"], relief="flat")

        self.style.configure("Header.TLabel", background=self.colors["primary"], foreground="#FFFFFF", font=("Segoe UI", 17, "bold"))
        self.style.configure("HeaderSub.TLabel", background=self.colors["primary"], foreground="#F8FAFC", font=("Segoe UI", 10))
        self.style.configure("CardTitle.TLabel", background=self.colors["card_bg"], foreground=self.colors["primary_dark"], font=("Segoe UI", 11, "bold"))
        self.style.configure("Bold.TLabel", background=self.colors["card_bg"], font=("Segoe UI", 9, "bold"))
        self.style.configure("Muted.TLabel", background=self.colors["card_bg"], foreground=self.colors["text_muted"], font=("Segoe UI", 8))
        self.style.configure("MetricVal.TLabel", background=self.colors["card_bg"], foreground=self.colors["primary"], font=("Segoe UI", 13, "bold"))

        self.style.configure("Primary.TButton", background=self.colors["primary"], foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=6, anchor="center", justify="center")
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

        self.style.configure("Settings.TCheckbutton", background="#F8FAFC", foreground=self.colors["text"], font=("Segoe UI", 9))
        self.style.map("Settings.TCheckbutton", background=[("active", "#F8FAFC")])

        self.style.configure("TNotebook", background=self.colors["bg"], tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab", background="#E2E8F0", foreground="#475569", padding=[15, 6], font=("Segoe UI", 9, "bold"))
        self.style.map("TNotebook.Tab",
            background=[("selected", self.colors["primary"]), ("active", "#CBD5E1")],
            foreground=[("selected", "#FFFFFF")]
        )

        self.style.configure("Horizontal.TProgressbar", troughcolor="#E2E8F0", background=self.colors["primary_light"], thickness=8)

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

        main_container = ttk.Frame(self)
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=14, pady=12)

        left_sidebar = ttk.Frame(main_container, width=360)
        left_sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        left_sidebar.pack_propagate(False)

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

        lbl_ticker = tk.Label(cfg_inner, text="Kode Ticker (Saham / Indeks):", bg=self.colors["card_bg"], font=("Segoe UI", 9, "bold"))
        lbl_ticker.pack(anchor="w", pady=(4, 2))

        self.var_ticker = tk.StringVar(self)
        self.var_ticker.trace_add("write", self._on_ticker_changed)

        self.ent_ticker = ttk.Entry(cfg_inner, textvariable=self.var_ticker, font=("Segoe UI", 10, "bold"))
        self.ent_ticker.pack(fill=tk.X, pady=(0, 10))

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

        params_grid = tk.Frame(cfg_inner, bg=self.colors["card_bg"])
        params_grid.pack(fill=tk.X, pady=(4, 6))

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

        action_row = tk.Frame(cfg_inner, bg=self.colors["card_bg"])
        action_row.pack(fill=tk.X, pady=(4, 4))
        action_row.columnconfigure(0, weight=1, uniform="action_cols")
        action_row.columnconfigure(1, weight=1, uniform="action_cols")
        action_row.rowconfigure(0, weight=1)

        settings_box = tk.Frame(action_row, bg="#F8FAFC", bd=1, relief="solid")
        settings_box.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        settings_inner = tk.Frame(settings_box, bg="#F8FAFC")
        settings_inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=(5, 6))

        lbl_settings = tk.Label(
            settings_inner,
            text="⚙️ Pengaturan",
            bg="#F8FAFC",
            fg=self.colors["primary_dark"],
            font=("Segoe UI", 9, "bold")
        )
        lbl_settings.pack(anchor="w", pady=(0, 3))

        self.var_use_shap = tk.BooleanVar(self, value=False)
        self.var_use_lc = tk.BooleanVar(self, value=False)

        self.chk_shap = ttk.Checkbutton(settings_inner, text="SHAP analysis", variable=self.var_use_shap, style="Settings.TCheckbutton")
        self.chk_shap.pack(anchor="w", pady=(0, 1))

        self.chk_lc = ttk.Checkbutton(settings_inner, text="Learning Curve", variable=self.var_use_lc, style="Settings.TCheckbutton")
        self.chk_lc.pack(anchor="w")

        self.btn_run = ttk.Button(action_row, text="🚀 MULAI\nPERAMALAN", style="Primary.TButton", command=self._action_start_forecast)
        self.btn_run.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        self.pbar = ttk.Progressbar(cfg_inner, style="Horizontal.TProgressbar", mode="determinate")
        self.pbar.pack(fill=tk.X, pady=(6, 2))

        self.lbl_status = tk.Label(cfg_inner, text="Siap menjalankan peramalan.", bg=self.colors["card_bg"], fg=self.colors["text_muted"], font=("Segoe UI", 8), anchor="w")
        self.lbl_status.pack(fill=tk.X)

        card_info = tk.Frame(left_sidebar, bg=self.colors["card_bg"], bd=1, relief="solid", highlightbackground=self.colors["border"])
        card_info.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        lbl_info_title = tk.Label(card_info, text="📌 INFORMASI PERUSAHAAN & INPUT", bg=self.colors["card_bg"], fg=self.colors["primary_dark"], font=("Segoe UI", 10, "bold"))
        lbl_info_title.pack(anchor="w", padx=14, pady=(8, 4))

        self.info_container = tk.Frame(card_info, bg=self.colors["card_bg"])
        self.info_container.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))

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

        self.lbl_hyperparams = tk.Label(self.info_container, text="Model: ForecasterDirect (10 Lags, 10 Roll Mean, 100 Trees)", bg=self.colors["card_bg"], font=("Segoe UI", 8), fg=self.colors["text_muted"], anchor="w", wraplength=310, justify="left")
        self.lbl_hyperparams.pack(fill=tk.X, pady=(3, 0))

        right_container = ttk.Frame(main_container)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(right_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_charts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_charts, text=" 📊 Grafik Prediksi ")

        self.tab_table = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_table, text=" 📋 Tabel Rincian Prediksi ")

        self.tab_var_analysis = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_var_analysis, text=" 🔬 Analisis Variabel ")

        self.tab_log = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_log, text=" 📝 Log Komputasi ")

        self.tab_history = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_history, text=" 🕒 Riwayat ")

        self.tab_tutorial = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tutorial, text=" 📖 Tutorial ")

        self._setup_chart_tab()
        self._setup_table_tab()
        self._setup_var_analysis_tab()
        self._setup_log_tab()
        self._setup_history_tab()
        self._setup_tutorial_tab()

    def _setup_chart_tab(self):
        chart_top_bar = tk.Frame(self.tab_charts, bg=self.colors["bg"])
        chart_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(6, 4), padx=6)

        lbl_chart_hint = tk.Label(chart_top_bar, text="📈 Visualisasi Evaluasi Model & Hasil Proyeksi Masa Depan", bg=self.colors["bg"], font=("Segoe UI", 9, "bold"), fg=self.colors["primary_dark"])
        lbl_chart_hint.pack(side=tk.LEFT, pady=2)

        btn_popup_chart = ttk.Button(chart_top_bar, text="🖥️ Tampilkan Jendela Pop-up HD", style="Accent.TButton", command=self._action_popup_chart)
        btn_popup_chart.pack(side=tk.RIGHT, padx=4)

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(9, 6.5), facecolor='white')
        self._init_empty_chart()

        self.canvas_frame = tk.Frame(self.tab_charts, bg="#FFFFFF", bd=1, relief="solid")
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.draw()

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
        tbl_top_bar = tk.Frame(self.tab_table, bg=self.colors["bg"])
        tbl_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(6, 6), padx=6)

        lbl_tbl_title = tk.Label(tbl_top_bar, text="Tabel Proyeksi Harga Saham", bg=self.colors["bg"], font=("Segoe UI", 10, "bold"), fg=self.colors["primary_dark"])
        lbl_tbl_title.pack(side=tk.LEFT, pady=2)

        btn_export = ttk.Button(tbl_top_bar, text="💾 Ekspor Hasil ke CSV", style="Primary.TButton", command=self._action_export_csv)
        btn_export.pack(side=tk.RIGHT, padx=4)

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

    def _setup_var_analysis_tab(self):
        var_top_bar = tk.Frame(self.tab_var_analysis, bg=self.colors["bg"])
        var_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(6, 4), padx=6)

        title_wrap = tk.Frame(var_top_bar, bg=self.colors["bg"])
        title_wrap.pack(side=tk.LEFT, pady=2)

        lbl_var_title = tk.Label(
            title_wrap,
            text="🔬 Analisis Variabel (SHAP & Learning Curve)",
            bg=self.colors["bg"],
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["primary_dark"]
        )
        lbl_var_title.pack(side=tk.LEFT)

        self.lbl_var_status = tk.Label(
            title_wrap,
            text="• Belum ada analisis aktif",
            bg=self.colors["bg"],
            font=("Segoe UI", 8),
            fg=self.colors["text_muted"]
        )
        self.lbl_var_status.pack(side=tk.LEFT, padx=(8, 0))

        btn_popup_var = ttk.Button(
            var_top_bar,
            text="🖥️ Tampilkan Jendela Pop-up HD",
            style="Accent.TButton",
            command=self._action_popup_var_chart
        )
        btn_popup_var.pack(side=tk.RIGHT, padx=4)

        self.var_fig = plt.figure(figsize=(9.5, 6.5), facecolor="white")
        self._init_empty_var_chart(self.var_fig)

        self.var_canvas_frame = tk.Frame(self.tab_var_analysis, bg="#FFFFFF", bd=1, relief="solid")
        self.var_canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        self.var_canvas = FigureCanvasTkAgg(self.var_fig, master=self.var_canvas_frame)
        self.var_canvas.draw()

        self.var_toolbar_frame = tk.Frame(self.tab_var_analysis, bg="#F1F5F9")
        self.var_toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(0, 4))
        self.var_toolbar = NavigationToolbar2Tk(self.var_canvas, self.var_toolbar_frame)
        self.var_toolbar.update()

        self.var_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _init_empty_var_chart(self, fig=None):
        target_fig = fig if fig is not None else self.var_fig
        target_fig.clear()
        ax = target_fig.add_subplot(1, 1, 1)
        ax.axis("off")
        ax.text(
            0.5,
            0.52,
            "Tidak ada analisis variabel yang ditampilkan.\n\n"
            "Centang 'SHAP analysis' dan/atau 'Learning Curve' pada kotak Pengaturan\n"
            "di sebelah kiri, lalu jalankan 'MULAI PERAMALAN'.",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            color="#94A3B8",
            fontsize=10.5,
            style="italic",
            linespacing=1.5
        )
        if hasattr(self, "lbl_var_status") and target_fig is self.var_fig:
            self.lbl_var_status.config(text="• Tidak ada analisis aktif")

    def _plot_shap_panels(self, ax_bar, ax_bee, shap_data, ticker, fig):
        from matplotlib.colors import Normalize
        from matplotlib.cm import ScalarMappable
        from matplotlib.patches import Patch

        feature_names = shap_data["feature_names"]
        shap_values = np.asarray(shap_data["shap_values"], dtype=float)
        feature_values = np.asarray(shap_data["feature_values"], dtype=float)

        mean_abs = np.abs(shap_values).mean(axis=0)
        top_k = min(15, len(feature_names))
        order = np.argsort(mean_abs)[-top_k:]

        top_names = [feature_names[i] for i in order]
        top_vals = mean_abs[order]
        bar_colors = [
            "#6B21A8" if name.startswith("lag_") else ("#06B6D4" if name.startswith("roll_mean_") else "#64748B")
            for name in top_names
        ]

        y_pos = np.arange(len(order))
        ax_bar.barh(y_pos, top_vals, color=bar_colors, height=0.68, alpha=0.9)
        ax_bar.set_yticks(y_pos)
        ax_bar.set_yticklabels(top_names, fontsize=8)
        ax_bar.set_xlabel("Mean |SHAP Value|", fontsize=8.5)
        ax_bar.set_title(f"SHAP Feature Importance (Top {top_k} - {ticker})", fontsize=9.5, fontweight="bold", pad=8, color="#1E293B")
        ax_bar.grid(True, axis="x", linestyle="--", alpha=0.35)

        max_bar = float(top_vals.max()) if len(top_vals) else 1.0
        ax_bar.set_xlim(0, max_bar * 1.18 if max_bar > 0 else 1.0)
        for y_i, val in enumerate(top_vals):
            ax_bar.text(val + max_bar * 0.015, y_i, f"{val:.3f}", va="center", fontsize=7.5, color="#334155")

        legend_handles = [
            Patch(facecolor="#6B21A8", label="Lag Features"),
            Patch(facecolor="#06B6D4", label="Rolling Mean"),
        ]
        ax_bar.legend(handles=legend_handles, loc="lower right", fontsize=7.5, framealpha=0.9)

        cmap = plt.get_cmap("coolwarm")
        for y_i, feat_idx in enumerate(order):
            s_vals = shap_values[:, feat_idx]
            f_vals = feature_values[:, feat_idx]
            f_min, f_max = float(np.min(f_vals)), float(np.max(f_vals))
            if f_max > f_min:
                norm_f = (f_vals - f_min) / (f_max - f_min)
            else:
                norm_f = np.full_like(f_vals, 0.5)
            rng = np.random.default_rng(42 + y_i)
            jitter = rng.uniform(-0.22, 0.22, size=len(s_vals))
            ax_bee.scatter(
                s_vals,
                np.full_like(s_vals, y_i, dtype=float) + jitter,
                c=norm_f,
                cmap=cmap,
                vmin=0.0,
                vmax=1.0,
                s=14,
                alpha=0.75,
                edgecolors="none"
            )

        ax_bee.axvline(0.0, color="#475569", linestyle="--", linewidth=1.0)
        ax_bee.set_yticks(y_pos)
        ax_bee.set_yticklabels(top_names, fontsize=8)
        ax_bee.set_xlabel("SHAP Value (Dampak Prediksi)", fontsize=8.5)
        ax_bee.set_title(f"SHAP Summary Impact ({ticker})", fontsize=9.5, fontweight="bold", pad=8, color="#1E293B")
        ax_bee.grid(True, axis="x", linestyle="--", alpha=0.35)

        sm = ScalarMappable(norm=Normalize(vmin=0.0, vmax=1.0), cmap=cmap)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax_bee, pad=0.02, fraction=0.045)
        cbar.set_ticks([0.0, 1.0])
        cbar.set_ticklabels(["Rendah", "Tinggi"])
        cbar.ax.tick_params(labelsize=7.5)
        cbar.set_label("Nilai Fitur", fontsize=8)

    def _plot_learning_curve_panel(self, ax_lc, lc_data, ticker):
        train_sizes = np.asarray(lc_data["train_sizes"], dtype=float)
        tr_mean = np.asarray(lc_data["train_mae_mean"], dtype=float)
        tr_std = np.asarray(lc_data["train_mae_std"], dtype=float)
        va_mean = np.asarray(lc_data["val_mae_mean"], dtype=float)
        va_std = np.asarray(lc_data["val_mae_std"], dtype=float)
        n_splits = lc_data.get("n_splits", 5)

        ax_lc.plot(train_sizes, tr_mean, "o-", color="#6B21A8", linewidth=2, markersize=5, label=f"Training MAE (Akhir: {tr_mean[-1]:,.3f})")
        ax_lc.fill_between(train_sizes, np.maximum(0.0, tr_mean - tr_std), tr_mean + tr_std, color="#6B21A8", alpha=0.12)

        ax_lc.plot(train_sizes, va_mean, "s-", color="#0891B2", linewidth=2, markersize=5, label=f"Validation MAE (Akhir: {va_mean[-1]:,.3f})")
        ax_lc.fill_between(train_sizes, np.maximum(0.0, va_mean - va_std), va_mean + va_std, color="#06B6D4", alpha=0.14)

        ax_lc.set_title(f"Learning Curve - Random Forest ({ticker}, {n_splits}-Fold TimeSeriesSplit)", fontsize=9.5, fontweight="bold", pad=8, color="#1E293B")
        ax_lc.set_xlabel("Jumlah Sampel Data Latih", fontsize=8.5)
        ax_lc.set_ylabel("Mean Absolute Error (MAE)", fontsize=8.5)
        ax_lc.legend(loc="upper right", fontsize=8, framealpha=0.9)
        ax_lc.grid(True, linestyle="--", alpha=0.35)

    def _render_var_analysis_figure(self, fig, var_analysis, ticker):
        has_shap = bool(var_analysis and var_analysis.get("shap"))
        has_lc = bool(var_analysis and var_analysis.get("learning_curve"))

        fig.clear()
        if not has_shap and not has_lc:
            self._init_empty_var_chart(fig)
            return

        if has_shap and has_lc:
            gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0], hspace=0.42, wspace=0.32)
            ax_bar = fig.add_subplot(gs[0, 0])
            ax_bee = fig.add_subplot(gs[0, 1])
            ax_lc = fig.add_subplot(gs[1, :])
            self._plot_shap_panels(ax_bar, ax_bee, var_analysis["shap"], ticker, fig)
            self._plot_learning_curve_panel(ax_lc, var_analysis["learning_curve"], ticker)
            fig.subplots_adjust(left=0.12, right=0.94, top=0.93, bottom=0.09)
        elif has_shap:
            gs = fig.add_gridspec(1, 2, wspace=0.34)
            ax_bar = fig.add_subplot(gs[0, 0])
            ax_bee = fig.add_subplot(gs[0, 1])
            self._plot_shap_panels(ax_bar, ax_bee, var_analysis["shap"], ticker, fig)
            fig.subplots_adjust(left=0.13, right=0.93, top=0.90, bottom=0.12)
        else:
            ax_lc = fig.add_subplot(1, 1, 1)
            self._plot_learning_curve_panel(ax_lc, var_analysis["learning_curve"], ticker)
            fig.tight_layout(pad=2.0)

    def _render_var_analysis_tab(self, var_analysis, ticker):
        self._render_var_analysis_figure(self.var_fig, var_analysis, ticker)
        self.var_canvas.draw()

        active_parts = []
        if var_analysis and var_analysis.get("shap"):
            active_parts.append("SHAP analysis")
        if var_analysis and var_analysis.get("learning_curve"):
            active_parts.append("Learning Curve")

        if active_parts:
            self.lbl_var_status.config(text=f"• Aktif: {', '.join(active_parts)}")
        else:
            self.lbl_var_status.config(text="• Tidak ada analisis aktif")

    def _action_popup_var_chart(self):
        var_analysis = self.last_results.get("var_analysis") if self.last_results else None
        if not var_analysis or (not var_analysis.get("shap") and not var_analysis.get("learning_curve")):
            messagebox.showinfo("Informasi", "Belum ada hasil analisis variabel. Aktifkan centang pada Pengaturan lalu jalankan peramalan.")
            return

        ticker = self.last_results["ticker"]
        pop_fig = plt.figure(figsize=(13, 8.5), facecolor="white")
        self._render_var_analysis_figure(pop_fig, var_analysis, ticker)

        try:
            mngr = pop_fig.canvas.manager
            mngr.set_window_title(f"Yahoo Finance Forecaster - Analisis Variabel {ticker} (HD)")
            if hasattr(mngr, "window"):
                mngr.window.deiconify()
                mngr.window.attributes("-topmost", True)
                mngr.window.lift()
        except Exception:
            pass

        plt.show()

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

    def _setup_history_tab(self):
        hist_top_bar = tk.Frame(self.tab_history, bg=self.colors["bg"])
        hist_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(6, 4), padx=6)

        title_wrap = tk.Frame(hist_top_bar, bg=self.colors["bg"])
        title_wrap.pack(side=tk.LEFT, pady=2)

        lbl_hist_title = tk.Label(
            title_wrap,
            text="🕒 Riwayat Peramalan",
            bg=self.colors["bg"],
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["primary_dark"]
        )
        lbl_hist_title.pack(side=tk.LEFT)

        self.lbl_hist_count = tk.Label(
            title_wrap,
            text="(0 entri)",
            bg=self.colors["bg"],
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"]
        )
        self.lbl_hist_count.pack(side=tk.LEFT, padx=(6, 0))

        btn_frame = tk.Frame(hist_top_bar, bg=self.colors["bg"])
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(btn_frame, text="📂 Muat Hasil", style="Primary.TButton", command=self._action_load_history).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="⚙️ Pakai Parameter", style="Accent.TButton", command=self._action_apply_history_params).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="🗑️ Hapus", style="Quick.TButton", command=self._action_delete_history).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="🧹 Bersihkan", style="Quick.TButton", command=self._action_clear_history).pack(side=tk.LEFT)

        hist_filter_bar = tk.Frame(self.tab_history, bg=self.colors["bg"])
        hist_filter_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 6), padx=6)

        lbl_filter = tk.Label(hist_filter_bar, text="Cari Ticker / Perusahaan:", bg=self.colors["bg"], font=("Segoe UI", 8, "bold"), fg=self.colors["text_muted"])
        lbl_filter.pack(side=tk.LEFT, padx=(0, 6))

        self.var_hist_filter = tk.StringVar(self)
        self.var_hist_filter.trace_add("write", lambda *_: self._refresh_history_tree())
        ent_filter = ttk.Entry(hist_filter_bar, textvariable=self.var_hist_filter, width=26, font=("Segoe UI", 9))
        ent_filter.pack(side=tk.LEFT)

        ttk.Button(hist_filter_bar, text="✕", style="Quick.TButton", width=3, command=lambda: self.var_hist_filter.set("")).pack(side=tk.LEFT, padx=(4, 0))

        lbl_hint = tk.Label(
            hist_filter_bar,
            text="💡 Klik dua kali baris untuk memuat grafik & tabel hasil",
            bg=self.colors["bg"],
            font=("Segoe UI", 8, "italic"),
            fg=self.colors["text_muted"]
        )
        lbl_hint.pack(side=tk.RIGHT)

        hist_container = tk.Frame(self.tab_history, bg="#FFFFFF", bd=1, relief="solid")
        hist_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        columns = ("no", "timestamp", "ticker", "name", "date_range", "freq_steps", "mape", "mae", "last_price", "pred_price")
        self.hist_tree = ttk.Treeview(hist_container, columns=columns, show="headings", selectmode="browse")

        self.hist_tree.heading("no", text="No")
        self.hist_tree.heading("timestamp", text="Waktu Eksekusi")
        self.hist_tree.heading("ticker", text="Ticker")
        self.hist_tree.heading("name", text="Nama Perusahaan")
        self.hist_tree.heading("date_range", text="Rentang Data")
        self.hist_tree.heading("freq_steps", text="Frek / Steps")
        self.hist_tree.heading("mape", text="MAPE")
        self.hist_tree.heading("mae", text="MAE")
        self.hist_tree.heading("last_price", text="Harga Terakhir")
        self.hist_tree.heading("pred_price", text="Proyeksi Akhir")

        self.hist_tree.column("no", width=45, anchor="center", stretch=False)
        self.hist_tree.column("timestamp", width=135, anchor="center")
        self.hist_tree.column("ticker", width=85, anchor="center")
        self.hist_tree.column("name", width=175, anchor="w")
        self.hist_tree.column("date_range", width=165, anchor="center")
        self.hist_tree.column("freq_steps", width=90, anchor="center")
        self.hist_tree.column("mape", width=75, anchor="e")
        self.hist_tree.column("mae", width=90, anchor="e")
        self.hist_tree.column("last_price", width=105, anchor="e")
        self.hist_tree.column("pred_price", width=155, anchor="e")

        vsb = ttk.Scrollbar(hist_container, orient="vertical", command=self.hist_tree.yview)
        hsb = ttk.Scrollbar(hist_container, orient="horizontal", command=self.hist_tree.xview)
        self.hist_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.hist_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        hist_container.rowconfigure(0, weight=1)
        hist_container.columnconfigure(0, weight=1)

        self.hist_tree.bind("<Double-1>", self._on_history_double_click)
        self.hist_tree.bind("<Delete>", lambda _e: self._action_delete_history())

        self._load_history_from_disk()
        self._refresh_history_tree()

    @staticmethod
    def _serialize_series(series):
        return [
            [dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt), float(val)]
            for dt, val in series.items()
        ]

    @staticmethod
    def _deserialize_series(pairs):
        if not pairs:
            return pd.Series(dtype=float)
        dates = pd.to_datetime([p[0] for p in pairs])
        values = [float(p[1]) for p in pairs]
        return pd.Series(values, index=dates)

    def _load_history_from_disk(self):
        if not os.path.exists(self.history_file):
            self.history_items = []
            return
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.history_items = [item for item in data if isinstance(item, dict) and "id" in item]
            else:
                self.history_items = []
        except Exception as e:
            self.history_items = []
            self._log(f"Peringatan: Gagal memuat file riwayat ({str(e)}).")

    def _save_history_to_disk(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history_items[:100], f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"Peringatan: Gagal menyimpan file riwayat ({str(e)}).")

    def _add_history_entry(self, b):
        last_price = float(b["data"].iloc[-1])
        pred_end_price = float(b["final_predictions"].iloc[-1])
        pred_change_pct = ((pred_end_price - last_price) / last_price) * 100 if last_price != 0 else 0.0

        var_analysis = b.get("var_analysis") or {}
        serialized_var_analysis = {}
        if var_analysis.get("shap"):
            shap_d = var_analysis["shap"]
            serialized_var_analysis["shap"] = {
                "feature_names": list(shap_d["feature_names"]),
                "shap_values": np.asarray(shap_d["shap_values"], dtype=float).tolist(),
                "feature_values": np.asarray(shap_d["feature_values"], dtype=float).tolist(),
            }
        if var_analysis.get("learning_curve"):
            serialized_var_analysis["learning_curve"] = var_analysis["learning_curve"]

        now = datetime.now()
        entry = {
            "id": now.strftime("%Y%m%d_%H%M%S_%f"),
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": b["ticker"],
            "name": b["name"],
            "sector": b["sector"],
            "industry": b["industry"],
            "start_date": b["start_date"],
            "end_date": b["end_date"],
            "freq": b["freq"],
            "freq_desc": b["freq_desc"],
            "steps": int(b["steps"]),
            "mae": float(b["mae"]),
            "mape": float(b["mape"]),
            "last_price": last_price,
            "pred_end_price": pred_end_price,
            "pred_change_pct": pred_change_pct,
            "lags": int(b["lags"]),
            "n_estimators": int(b["n_estimators"]),
            "var_analysis": serialized_var_analysis,
            "series": {
                "train": self._serialize_series(b["train"]),
                "test": self._serialize_series(b["test"]),
                "val_predictions": self._serialize_series(b["val_predictions"]),
                "data": self._serialize_series(b["data"]),
                "final_predictions": self._serialize_series(b["final_predictions"]),
            },
        }
        self.history_items.insert(0, entry)
        self.history_items = self.history_items[:100]
        self._save_history_to_disk()
        self._refresh_history_tree()

    def _refresh_history_tree(self):
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        query = self.var_hist_filter.get().strip().lower() if hasattr(self, "var_hist_filter") else ""
        filtered = [
            entry for entry in self.history_items
            if not query or query in entry.get("ticker", "").lower() or query in entry.get("name", "").lower()
        ]

        for idx, entry in enumerate(filtered, start=1):
            pct = float(entry.get("pred_change_pct", 0.0))
            pct_sign = "+" if pct >= 0 else ""
            pred_end_str = f"{float(entry.get('pred_end_price', 0.0)):,.2f} ({pct_sign}{pct:.2f}%)"
            self.hist_tree.insert(
                "",
                tk.END,
                iid=entry["id"],
                values=(
                    idx,
                    entry.get("timestamp", "-"),
                    entry.get("ticker", "-"),
                    entry.get("name", "-"),
                    f"{entry.get('start_date', '-')} s/d {entry.get('end_date', '-')}",
                    f"{entry.get('freq', '-')} / {entry.get('steps', '-')}",
                    f"{float(entry.get('mape', 0.0)):.2f}%",
                    f"{float(entry.get('mae', 0.0)):,.2f}",
                    f"{float(entry.get('last_price', 0.0)):,.2f}",
                    pred_end_str,
                ),
            )

        total_count = len(self.history_items)
        if query:
            self.lbl_hist_count.config(text=f"({len(filtered)} dari {total_count} entri)")
        else:
            self.lbl_hist_count.config(text=f"({total_count} entri)")

    def _get_selected_history_entry(self):
        sel = self.hist_tree.selection()
        if not sel:
            messagebox.showinfo("Informasi", "Silakan pilih salah satu baris riwayat terlebih dahulu.")
            return None
        entry_id = sel[0]
        for entry in self.history_items:
            if entry["id"] == entry_id:
                return entry
        return None

    def _on_history_double_click(self, event):
        if self.hist_tree.identify_region(event.x, event.y) in ("cell", "tree"):
            self._action_load_history()

    def _apply_form_params(self, entry):
        self._set_ticker(entry.get("ticker", ""))
        self.ent_start.delete(0, tk.END)
        self.ent_start.insert(0, entry.get("start_date", ""))
        self.ent_end.delete(0, tk.END)
        self.ent_end.insert(0, entry.get("end_date", ""))
        freq = entry.get("freq", "B")
        self.cmb_freq.current(0 if freq == "B" else 1)
        self.spn_steps.delete(0, tk.END)
        self.spn_steps.insert(0, str(entry.get("steps", "")))
        va = entry.get("var_analysis") or {}
        self.var_use_shap.set(bool(va.get("shap")))
        self.var_use_lc.set(bool(va.get("learning_curve")))

    def _action_apply_history_params(self):
        if self.is_running:
            messagebox.showwarning("Peringatan", "Proses peramalan sedang berjalan. Harap tunggu hingga selesai.")
            return
        entry = self._get_selected_history_entry()
        if not entry:
            return
        self._apply_form_params(entry)
        self.lbl_status.config(text=f"Parameter dari riwayat {entry['ticker']} diisikan ke form.")
        self._log(f"Parameter riwayat dimuat ke form: {entry['ticker']} ({entry['start_date']} s/d {entry['end_date']}, {entry['freq']}, {entry['steps']} steps).")

    def _action_load_history(self):
        if self.is_running:
            messagebox.showwarning("Peringatan", "Proses peramalan sedang berjalan. Harap tunggu hingga selesai.")
            return
        entry = self._get_selected_history_entry()
        if not entry:
            return

        series_data = entry.get("series")
        if not series_data:
            messagebox.showwarning("Data Tidak Tersedia", "Data grafik/tabel tidak tersedia pada entri riwayat ini. Gunakan 'Pakai Parameter' untuk menjalankan ulang.")
            return

        try:
            bundle = {
                "ticker": entry["ticker"],
                "name": entry.get("name", entry["ticker"]),
                "sector": entry.get("sector", "N/A"),
                "industry": entry.get("industry", "N/A"),
                "start_date": entry.get("start_date", "-"),
                "end_date": entry.get("end_date", "-"),
                "freq": entry.get("freq", "B"),
                "freq_desc": entry.get("freq_desc", "B (Business Days)"),
                "train": self._deserialize_series(series_data["train"]),
                "test": self._deserialize_series(series_data["test"]),
                "val_predictions": self._deserialize_series(series_data["val_predictions"]),
                "data": self._deserialize_series(series_data["data"]),
                "final_predictions": self._deserialize_series(series_data["final_predictions"]),
                "steps": int(entry["steps"]),
                "mae": float(entry["mae"]),
                "mape": float(entry["mape"]),
                "lags": int(entry.get("lags", 10)),
                "n_estimators": int(entry.get("n_estimators", 100)),
                "var_analysis": entry.get("var_analysis", {}),
            }
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data riwayat:\n{str(e)}")
            return

        self._apply_form_params(entry)
        self._update_company_info(
            bundle["name"],
            bundle["sector"],
            bundle["industry"],
            bundle["ticker"],
            bundle["start_date"],
            bundle["end_date"],
            bundle["freq_desc"],
            bundle["steps"],
        )
        self.lbl_status.config(text=f"Menampilkan hasil riwayat {bundle['ticker']} ({entry['timestamp']}).")
        self._log(f"Riwayat dimuat: {bundle['ticker']} ({entry['timestamp']}).")
        self._display_results(bundle, save_history=False)

    def _action_delete_history(self):
        if self.is_running:
            messagebox.showwarning("Peringatan", "Proses peramalan sedang berjalan. Harap tunggu hingga selesai.")
            return
        entry = self._get_selected_history_entry()
        if not entry:
            return
        self.history_items = [item for item in self.history_items if item["id"] != entry["id"]]
        self._save_history_to_disk()
        self._refresh_history_tree()
        self._log(f"Entri riwayat dihapus: {entry.get('ticker', '-')} ({entry.get('timestamp', '-')}).")

    def _action_clear_history(self):
        if self.is_running:
            messagebox.showwarning("Peringatan", "Proses peramalan sedang berjalan. Harap tunggu hingga selesai.")
            return
        if not self.history_items:
            messagebox.showinfo("Informasi", "Riwayat peramalan sudah kosong.")
            return
        if not messagebox.askyesno("Konfirmasi", "Hapus seluruh riwayat peramalan secara permanen?"):
            return
        self.history_items = []
        self._save_history_to_disk()
        self._refresh_history_tree()
        self._log("Seluruh riwayat peramalan berhasil dibersihkan.")

    def _setup_tutorial_tab(self):
        tut_top_bar = tk.Frame(self.tab_tutorial, bg=self.colors["bg"])
        tut_top_bar.pack(side=tk.TOP, fill=tk.X, pady=(6, 6), padx=6)

        lbl_tut_title = tk.Label(tut_top_bar, text="📖 Panduan Singkat & Tutorial Penggunaan", bg=self.colors["bg"], font=("Segoe UI", 10, "bold"), fg=self.colors["primary_dark"])
        lbl_tut_title.pack(side=tk.LEFT, pady=2)

        tut_container = tk.Frame(self.tab_tutorial, bg="#FFFFFF", bd=1, relief="solid")
        tut_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        txt_tut = ScrolledText(tut_container, bg="#FFFFFF", fg="#1E293B", font=("Segoe UI", 10), relief="flat", wrap="word", padx=18, pady=16)
        txt_tut.pack(fill=tk.BOTH, expand=True)

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
            ("• Forecast Steps: Masukkan berapa langkah / hari ke depan yang ingin diproyeksikan (contoh: 10, 30, atau 60).\n", "bullet"),
            ("• Pengaturan (Opsional): Centang 'SHAP analysis' dan/atau 'Learning Curve' jika ingin menampilkan analisis variabel dan kurva pembelajaran pada tab '🔬 Analisis Variabel'.\n\n", "bullet"),

            ("4. Memulai Peramalan (Mulai Peramalan)\n", "h2"),
            ("• Klik tombol '🚀 MULAI PERAMALAN'. Seluruh proses dijalankan di background thread sehingga GUI tetap responsif.\n", "bullet"),
            ("• Tahap [1/2] Melatih Model Peramalan: Model dilatih pada data latih (80%) dan diuji ke data uji (20%) untuk menghitung metrik evaluasi (MAPE & MAE).\n", "bullet"),
            ("• Tahap [2/2] Melakukan Peramalan: Model final dilatih pada 100% data historis untuk memproyeksikan harga masa depan sejumlah Forecast Steps.\n\n", "bullet"),

            ("5. Membaca & Mengekspor Hasil Prediksi\n", "h2"),
            ("• Tab '📊 Grafik Prediksi': Menampilkan 2 grafik bersusun (Evaluasi Model dan Hasil Proyeksi Masa Depan). Tersedia tombol 'Tampilkan Jendela Pop-up HD' untuk fitur Zoom dan Pan interaktif.\n", "bullet"),
            ("• Tab '📋 Tabel Rincian Prediksi': Menampilkan daftar tanggal prediksi, estimasi harga, selisih nominal, dan % perubahan. Klik '💾 Ekspor Hasil ke CSV' untuk menyimpan hasil ke file spreadsheet/Excel.\n", "bullet"),
            ("• Tab '🔬 Analisis Variabel': Menampilkan grafik SHAP analysis dan/atau Learning Curve sesuai kotak centang yang diaktifkan pada Pengaturan.\n", "bullet"),
            ("• Tab '📝 Log Komputasi': Memantau catatan teknis proses download data, evaluasi error, dan eksekusi model secara langsung.\n", "bullet"),
            ("• Tab '🕒 Riwayat': Menyimpan riwayat peramalan yang pernah dijalankan secara otomatis. Anda dapat mencari, memuat ulang grafik & tabel hasil (klik dua kali / 'Muat Hasil'), memakai ulang parameter, atau menghapus riwayat.\n\n", "bullet"),

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

        use_shap = bool(self.var_use_shap.get())
        use_lc = bool(self.var_use_lc.get())

        self.is_running = True
        self.btn_run.config(state="disabled")
        self.btn_reset.config(state="disabled")
        self.chk_shap.config(state="disabled")
        self.chk_lc.config(state="disabled")
        self.pbar["value"] = 0
        self.lbl_status.config(text="Memulai proses peramalan...")
        self._log(f"=== Memulai Peramalan untuk {ticker} ===")
        self._log(f"Rentang: {start_date} s/d {end_date} | Frekuensi: {freq_desc} | Steps: {steps}")
        self._log("Model: ForecasterDirect (10 Lags, 10 Rolling Means, 100 Trees - Fixed)")
        if use_shap or use_lc:
            opts = [name for flag, name in ((use_shap, "SHAP analysis"), (use_lc, "Learning Curve")) if flag]
            self._log(f"Analisis Variabel aktif: {', '.join(opts)}")

        threading.Thread(
            target=self._forecast_worker,
            args=(ticker, start_date, end_date, freq, steps, use_shap, use_lc),
            daemon=True
        ).start()

    def _forecast_worker(self, ticker, start_date, end_date, freq, steps, use_shap=False, use_lc=False):
        try:
            freq_desc = "B (Business Days)" if freq == "B" else "D (Days)"

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

            val_steps = max(1, round(0.2 * total_points))
            train = data[:-val_steps]
            test = data[-val_steps:]
            self.after(0, lambda: self._log(f"Data Split: Train={len(train)} titik, Test={len(test)} titik."))

            rolling_features = RollingFeatures(
                stats=['mean'] * 10,
                window_sizes=list(range(1, 11))
            )
            lags = 10
            n_estimators = 100

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

            var_analysis = {}
            if use_shap or use_lc:
                self.after(0, lambda: self.pbar.config(value=82))
                X_train, y_train_dict = forecaster_final.create_train_X_y(y=data)
                first_step = list(forecaster_final.estimators_.keys())[0]

                if use_shap:
                    self.after(0, lambda: self.lbl_status.config(text="Menghitung SHAP analysis..."))
                    self.after(0, lambda: self._log("Menghitung SHAP analysis (TreeExplainer)..."))
                    if shap is None:
                        self.after(0, lambda: self._log("Peringatan: Pustaka 'shap' belum terpasang. SHAP analysis dilewati."))
                    else:
                        X_sample = X_train.tail(200)
                        explainer = shap.TreeExplainer(forecaster_final.estimators_[first_step])
                        shap_vals = np.asarray(explainer.shap_values(X_sample), dtype=float)
                        if shap_vals.ndim == 3:
                            shap_vals = shap_vals[0]
                        var_analysis["shap"] = {
                            "feature_names": list(X_sample.columns),
                            "shap_values": shap_vals,
                            "feature_values": X_sample.to_numpy(dtype=float),
                        }
                        self.after(0, lambda n=len(X_sample): self._log(f"SHAP analysis selesai ({n} sampel)."))

                if use_lc:
                    self.after(0, lambda: self.lbl_status.config(text="Menghitung Learning Curve..."))
                    self.after(0, lambda: self._log("Menghitung Learning Curve (TimeSeriesSplit CV)..."))
                    y_target = y_train_dict[first_step]
                    n_splits = min(5, max(2, len(X_train) // 5))
                    cv = TimeSeriesSplit(n_splits=n_splits)
                    train_sizes, train_scores, val_scores = learning_curve(
                        RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1),
                        X_train,
                        y_target,
                        cv=cv,
                        scoring="neg_mean_absolute_error",
                        train_sizes=np.linspace(0.3, 1.0, 5),
                        n_jobs=-1,
                    )
                    train_mae = -train_scores
                    val_mae = -val_scores
                    var_analysis["learning_curve"] = {
                        "train_sizes": train_sizes.tolist(),
                        "train_mae_mean": train_mae.mean(axis=1).tolist(),
                        "train_mae_std": train_mae.std(axis=1).tolist(),
                        "val_mae_mean": val_mae.mean(axis=1).tolist(),
                        "val_mae_std": val_mae.std(axis=1).tolist(),
                        "n_splits": int(n_splits),
                    }
                    self.after(0, lambda s=n_splits: self._log(f"Learning Curve selesai ({s}-Fold TimeSeriesSplit)."))

            self.after(0, lambda: self.pbar.config(value=100))
            self.after(0, lambda: self.lbl_status.config(text="Peramalan selesai dengan sukses!"))
            self.after(0, lambda: self._log("Peramalan Berhasil Diselesaikan!"))

            bundle = {
                "ticker": ticker,
                "name": name,
                "sector": sector,
                "industry": industry,
                "start_date": start_date,
                "end_date": end_date,
                "freq": freq,
                "freq_desc": freq_desc,
                "train": train,
                "test": test,
                "val_predictions": val_predictions,
                "data": data,
                "final_predictions": final_predictions,
                "steps": steps,
                "mae": error_mae,
                "mape": mape_pct,
                "lags": lags,
                "n_estimators": n_estimators,
                "var_analysis": var_analysis,
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
        self.chk_shap.config(state="normal")
        self.chk_lc.config(state="normal")

    def _action_reset_form(self):
        if self.is_running:
            messagebox.showwarning("Peringatan", "Proses peramalan sedang berjalan. Harap tunggu hingga selesai.")
            return

        self.ent_ticker.delete(0, tk.END)
        self.ent_start.delete(0, tk.END)
        self.ent_end.delete(0, tk.END)
        self.spn_steps.delete(0, tk.END)
        self.cmb_freq.current(0)
        self.var_use_shap.set(False)
        self.var_use_lc.set(False)

        self.lbl_comp_ticker.config(text="Kode Ticker: -")
        self.lbl_comp_name.config(text="Nama: -")
        self.lbl_comp_sector.config(text="Sektor: -")
        self.lbl_comp_ind.config(text="Industri: -")
        self.lbl_comp_dates.config(text="Rentang Tanggal: -")
        self.lbl_comp_freq.config(text="Frekuensi: -")
        self.lbl_comp_steps.config(text="Periode Prediksi (Steps): -")

        self.lbl_mape.config(text="- %")
        self.lbl_mae.config(text="-")
        self.lbl_hyperparams.config(text="Model: ForecasterDirect (10 Lags, 10 Roll Mean, 100 Trees)")

        self.pbar["value"] = 0
        self.lbl_status.config(text="Seluruh kotak isian berhasil direset.")

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.ax1.clear()
        self.ax2.clear()
        self.ax1.set_title("Evaluasi Peramalan", fontsize=10, pad=8, fontweight='bold', color='#1E293B')
        self.ax1.grid(True, linestyle='--', alpha=0.35)
        self.ax2.set_title("Hasil Peramalan Akhir", fontsize=10, pad=8, fontweight='bold', color='#1E293B')
        self.ax2.grid(True, linestyle='--', alpha=0.35)
        self.fig.tight_layout(h_pad=3.0)
        self.canvas.draw()

        self._render_var_analysis_tab({}, "")

        self.last_results = None
        self._log("Semua kotak input dan data peramalan berhasil direset.")

    def _display_results(self, b, save_history=True):
        self.last_results = b

        self.lbl_mape.config(text=f"{b['mape']:.2f}%")
        self.lbl_mae.config(text=f"{b['mae']:,.2f}")
        self.lbl_hyperparams.config(
            text=f"Direct ({b['steps']} stp) | Trees={b['n_estimators']} | Lags={b['lags']} | 10 Rolling Means (1..10) | Diff=1"
        )

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

        self._render_charts(b["train"], b["test"], b["val_predictions"], b["data"], b["final_predictions"], b["ticker"])
        self._render_var_analysis_tab(b.get("var_analysis", {}), b["ticker"])

        if save_history:
            self._add_history_entry(b)

        self.notebook.select(self.tab_charts)

    def _render_charts(self, train, test, val_predictions, data, final_predictions, ticker):
        self.ax1.clear()
        self.ax2.clear()

        train.plot(ax=self.ax1, label='Data Latih', color='#1f77b4', linewidth=1.5)
        test.plot(ax=self.ax1, label='Data Uji', color='#2ca02c', linewidth=1.5)
        val_predictions.plot(ax=self.ax1, label='Prediksi Validasi', color='#ff7f0e', linewidth=1.5)
        self.ax1.set_title(f"Evaluasi Peramalan ({ticker})", fontsize=10, pad=8, fontweight='bold', color='#1E293B')
        self.ax1.set_xlabel("Tanggal", fontsize=8)
        self.ax1.set_ylabel("Harga", fontsize=8)
        self.ax1.legend(loc='upper left', fontsize=8, framealpha=0.85)
        self.ax1.grid(True, linestyle='--', alpha=0.35)

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
