# Contributing to Yahoo Finance Forecaster CLI

Thank you for your interest in contributing to **Yahoo Finance Forecaster CLI**!

## 🛠️ Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/USERNAME/yahoo-finance-forecaster-cli.git
   cd yahoo-finance-forecaster-cli
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Test running the CLI:
   ```bash
   python main.py
   ```

---

## 📌 Coding Standards

- Follow **PEP 8** style guidelines.
- Keep comments concise and informative (explain *why*, not obvious *what*).
- Ensure error handling handles network failures or invalid ticker symbols gracefully.
- Test with both IDX tickers (e.g. `BBCA.JK`) and global tickers (e.g. `AAPL`).

---

## 🚀 Pull Request Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes:
   ```bash
   git commit -m "feat: Add new forecasting metric"
   ```
3. Push to your branch and open a Pull Request with a clear description of changes.
