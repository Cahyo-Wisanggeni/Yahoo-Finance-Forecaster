import os
import sys
import io
import contextlib
import re
import warnings

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.system('')
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        hStdOut = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode))
        kernel32.SetConsoleMode(hStdOut, mode.value | 0x0004)
    except Exception:
        pass

warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

__version__ = "1.0.0"

if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--version"):
    print(f"Yahoo Finance Forecaster CLI v{__version__}")
    sys.exit(0)

import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from skforecast.direct import ForecasterDirect
from skforecast.preprocessing import RollingFeatures


def parse_date_input(prompt_text):
    while True:
        prompt = f"{prompt_text} : " if not prompt_text.endswith(":") else f"{prompt_text} "
        raw_val = input(prompt).strip()
        if not raw_val:
            print("[!] Tanggal tidak boleh kosong.")
            continue

        match_long = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", raw_val)
        if match_long:
            yyyy, mm, dd = match_long.groups()
            return f"{yyyy}-{int(mm):02d}-{int(dd):02d}"

        match_short = re.match(r"^(\d{2})-(\d{1,2})-(\d{1,2})$", raw_val)
        if match_short:
            yy, mm, dd = match_short.groups()
            return f"20{yy}-{int(mm):02d}-{int(dd):02d}"

        print("[!] Format tanggal tidak valid! Harap gunakan format YYYY-MM-DD (contoh: 2025-01-01).")


def plot_combined_results_popup(train, test, val_predictions, data, final_predictions, ticker, steps):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8.5), facecolor='white')

    train.plot(ax=ax1, label='Data Latih', color='#1f77b4', linewidth=1.5)
    test.plot(ax=ax1, label='Data Uji', color='#2ca02c', linewidth=1.5)
    val_predictions.plot(ax=ax1, label='Prediksi', color='#ff7f0e', linewidth=1.5)
    ax1.set_title(f"Evaluasi Peramalan ({ticker})", fontsize=11, pad=8, fontweight='bold')
    ax1.set_xlabel("Tanggal", fontsize=9)
    ax1.set_ylabel("Harga", fontsize=9)
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.4)

    data.plot(ax=ax2, label='Data Historis', color='#1f77b4', linewidth=1.5)
    final_predictions.plot(ax=ax2, label='Prediksi', color='#ff7f0e', linewidth=1.5)
    ax2.set_title(f"Hasil Peramalan Akhir ({ticker})", fontsize=11, pad=8, fontweight='bold')
    ax2.set_xlabel("Tanggal", fontsize=9)
    ax2.set_ylabel("Harga", fontsize=9)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout(h_pad=3.5)

    try:
        mngr = fig.canvas.manager
        mngr.set_window_title(f"Yahoo Finance Forecaster - {ticker}")
        if hasattr(mngr, 'window'):
            mngr.window.deiconify()
            mngr.window.attributes('-topmost', True)
            mngr.window.lift()
    except Exception:
        pass

    plt.show()


def print_header_logo():
    purple = "\033[38;2;168;85;247m"
    cyan   = "\033[38;2;34;211;238m"
    dim    = "\033[38;2;148;163;184m"
    reset  = "\033[0m"

    lines = [
        f"{purple}  █ █ █▀█ █ █ █▀█ █▀█ █{reset}",
        f"{purple}   █  █▀█ █▀█ █ █ █ █ ▀{reset}",
        f"{purple}   ▀  ▀ ▀ ▀ ▀ ▀▀▀ ▀▀▀ ▀{reset}",
        f"{purple}  █▀▀ █ █▀▄ █▀█ █▀▄ █▀▀ █▀▀{reset}    {cyan}█▀▀ █▀█ █▀▄ █▀▀ █▀▀ █▀█ █▀▀ ▀█▀ █▀▀ █▀▄{reset}",
        f"{purple}  █▀  █ █ █ █▀█ █ █ █   █▀ {reset}    {cyan}█▀  █ █ █▀▄ █▀  █   █▀█ ▀▀█  █  █▀  █▀▄{reset}",
        f"{purple}  ▀   ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀▀▀ ▀▀▀{reset}    {cyan}▀   ▀▀▀ ▀ ▀ ▀▀▀ ▀▀▀ ▀ ▀ ▀▀▀  ▀  ▀▀▀ ▀ ▀{reset}",
        f"  {dim}Edisi CLI v{__version__} - Time Series Machine Learning Platform{reset}"
    ]
    print("\n" + "\n".join(lines))


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--version"):
        print(f"Yahoo Finance Forecaster CLI v{__version__}")
        sys.exit(0)

    print_header_logo()

    print("\n[1] KONFIGURASI")

    while True:
        raw_ticker = input("Kode ticker (contoh: BBCA.JK): ").strip()
        ticker = raw_ticker.replace('ticker', '').replace('=', '').replace('"', '').replace("'", '').strip().upper()
        if not ticker:
            print("[!] Kode ticker tidak boleh kosong.")
            continue

        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                ticker_obj = yf.Ticker(ticker)
                info_saham = ticker_obj.info or {}
                nama_perusahaan = info_saham.get('longName') or info_saham.get('shortName')
            if not nama_perusahaan:
                print("Kode Ticker Tidak Valid!")
                continue
        except Exception:
            print("Kode Ticker Tidak Valid!")
            continue

        break

    print()
    start_date = parse_date_input("Tanggal Mulai (YYYY-MM-DD)")
    end_date = parse_date_input("Tanggal Selesai (YYYY-MM-DD)")

    while True:
        freq_in = input("\nJenis Frekuensi Data [B (Business Days) / D (Days)]: ").strip().upper()
        if freq_in in ["B", "D"]:
            freq = freq_in
            break
        print("[!] Frekuensi wajib diisi 'B' atau 'D'.")

    while True:
        steps_in = input("\nJumlah Periode Prediksi (Steps): ").strip()
        if not steps_in:
            print("[!] Jumlah periode prediksi tidak boleh kosong.")
            continue
        try:
            steps = int(steps_in)
            if steps > 0:
                break
            print("[!] Jumlah periode prediksi harus lebih besar dari 0.")
        except ValueError:
            print("[!] Jumlah periode prediksi harus berupa angka bulat (integer).")

    print("\n[2] PROSES KOMPUTASI & INFORMASI PERUSAHAAN")

    try:
        ticker_obj = yf.Ticker(ticker)
        info_saham = ticker_obj.info or {}
    except Exception:
        info_saham = {}

    nama_perusahaan = info_saham.get('longName') or info_saham.get('shortName') or ticker
    sektor = info_saham.get('sector', 'N/A')
    industri = info_saham.get('industry', 'N/A')

    freq_desc = "B (Business Days)" if freq == "B" else "D (Days)"

    info_lines = [
        f"Kode Ticker    : {ticker}",
        f"Nama           : {nama_perusahaan}",
        f"Sektor         : {sektor}",
        f"Industri       : {industri}",
        f"Tanggal Mulai  : {start_date}",
        f"Tanggal Selesai: {end_date}",
        f"Frekuensi      : {freq_desc}",
        f"Periode (Steps): {steps}"
    ]
    w_info = max(52, max(len(l) for l in info_lines) + 6)
    try:
        box_top = f"┌{'─' * w_info}┐"
        box_rows = [f"│  {l:<{w_info - 4}}  │" for l in info_lines]
        box_bot = f"└{'─' * w_info}┘"
        print(f"\n{box_top}\n" + "\n".join(box_rows) + f"\n{box_bot}\n")
    except Exception:
        box_top = f"+{'-' * w_info}+"
        box_rows = [f"|  {l:<{w_info - 4}}  |" for l in info_lines]
        box_bot = f"+{'-' * w_info}+"
        print(f"\n{box_top}\n" + "\n".join(box_rows) + f"\n{box_bot}\n")

    df_raw = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if df_raw.empty:
        print(f"[!] Tidak ada data yang ditemukan untuk ticker '{ticker}' pada rentang waktu {start_date} s/d {end_date}.")
        sys.exit(1)

    if isinstance(df_raw.columns, pd.MultiIndex):
        try:
            close_data = df_raw['Close'][ticker]
        except KeyError:
            close_data = df_raw['Close'].iloc[:, 0]
    else:
        close_data = df_raw['Close']

    close_data = close_data.squeeze()
    data = close_data.asfreq(freq).ffill().bfill()

    if len(data) < 30:
        print("[!] Data terlalu sedikit untuk melatih model time series. Harap perlebar rentang tanggal.")
        sys.exit(1)

    val_steps = max(1, round(0.2 * len(data)))
    train = data[:-val_steps]
    test = data[-val_steps:]

    lags = 10
    n_estimators = 100
    rolling_features = RollingFeatures(
        stats=['mean'] * 10,
        window_sizes=list(range(1, 11))
    )


    print("\n[1/2] Melatih Model Peramalan...")
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

    mae_str = f"Mean Absolute Error            : {error_mae:,.2f}"
    mape_str = f"Mean Absolute Percentage Error : {error_mape * 100:.2f}%"
    title_str = "METRIK EVALUASI INTERNAL"
    w = 52
    try:
        box_top = f"┌{'─' * w}┐"
        box_title = f"│{title_str.center(w)}│"
        box_mae = f"│  {mae_str:<{w - 4}}  │"
        box_mape = f"│  {mape_str:<{w - 4}}  │"
        box_bot = f"└{'─' * w}┘"
        print(f"\n{box_top}\n{box_title}\n{box_mae}\n{box_mape}\n{box_bot}")
    except Exception:
        box_top = f"+{'-' * w}+"
        box_title = f"|{title_str.center(w)}|"
        box_mae = f"|  {mae_str:<{w - 4}}  |"
        box_mape = f"|  {mape_str:<{w - 4}}  |"
        box_bot = f"+{'-' * w}+"
        print(f"\n{box_top}\n{box_title}\n{box_mae}\n{box_mape}\n{box_bot}")

    print("\n[2/2] Melakukan Peramalan...")
    forecaster_final = ForecasterDirect(
        estimator=RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1),
        steps=steps,
        lags=lags,
        differentiation=1,
        window_features=rolling_features
    )
    forecaster_final.fit(y=data)
    final_predictions = forecaster_final.predict(steps=steps)

    print("\nRincian Nilai Hasil Peramalan :")
    print("-" * 45)
    print(f"{'No':<5} | {'Tanggal':<15} | {'Prediksi Harga':<15}")
    print("-" * 45)
    pred_items = list(final_predictions.items())
    total_preds = len(pred_items)
    if total_preds <= 10:
        for idx, (dt, val) in enumerate(pred_items, start=1):
            dt_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)
            print(f"{idx:<5} | {dt_str:<15} | {val:,.2f}")
    else:
        for idx, (dt, val) in enumerate(pred_items[:5], start=1):
            dt_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)
            print(f"{idx:<5} | {dt_str:<15} | {val:,.2f}")
        print(f"{'...':<5} | {'...':<15} | {'...':<15}")
        for idx, (dt, val) in enumerate(pred_items[-5:], start=total_preds - 4):
            dt_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)
            print(f"{idx:<5} | {dt_str:<15} | {val:,.2f}")
    print("-" * 45 + "\n")

    plot_combined_results_popup(train, test, val_predictions, data, final_predictions, ticker, steps)


if __name__ == '__main__':
    main()
