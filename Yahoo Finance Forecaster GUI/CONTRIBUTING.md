# Contributing to Yahoo Finance Forecaster GUI

Thank you for contributing to **Yahoo Finance Forecaster GUI**!

## 🛠️ Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/USERNAME/yahoo-finance-forecaster-gui.git
   cd yahoo-finance-forecaster-gui
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

4. Launch the GUI:
   ```bash
   python app.py
   # or on Windows:
   run_gui.bat
   ```

---

## 🎨 GUI Guidelines

- The application uses native Tkinter / TTK without requiring heavy external UI dependencies (like Qt or wxWidgets). Keep UI components pure Tkinter + Matplotlib for maximum cross-platform compatibility and minimal install friction.
- Long-running tasks (fetching Yahoo Finance data, training model, predictions) **must run in a background daemon thread** so the GUI event loop never freezes.
- Follow the established color theme (`primary: #6D28D9`, `primary_dark: #4C1D95`, `accent: #0284C7`, `bg: #F1F5F9`).

---

## 🚀 Pull Request Workflow

1. Create a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes:
   ```bash
   git commit -m "feat: Add interactive chart export"
   ```
3. Push to your branch and open a Pull Request.
