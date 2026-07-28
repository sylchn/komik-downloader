# 🌐 Multi-Site Manga Scraper & PDF Generator

A powerful, high-performance Python manga downloader and PDF generator supporting multiple Indonesian manga sites with Cloudflare bypass, multithreading, and Google Colab integration.

---

## ✨ Features

- 🌐 **Multi-Site Support**: Easily download from multiple manga websites in one tool.
- ⚡ **Fast Concurrent Downloads**: Multi-threaded image downloader for high-speed downloads.
- 📄 **Automatic PDF Generation**: Merges downloaded chapter images into clean PDF documents automatically.
- 🔓 **Cloudflare Bypass**: Built-in TLS fingerprinting bypass (`curl_cffi`) for protected sites like Shinigami.
- 🖥️ **Interactive Menu & CLI**: User-friendly terminal interface or CLI arguments for automation.
- 📓 **Google Colab Ready**: Includes a Google Colab notebook (`multi_downloader_colab.ipynb`) for cloud downloading directly to Google Drive.
- 📝 **Activity Logging**: Saves all user inputs, download progress, and results to `scraper.log`.

---

## 📚 Supported Websites

| Website | URL | Support Status |
| :--- | :--- | :---: |
| **Komikcast** | `https://v3.komikcast.fit` | ✅ Active |
| **Shinigami Scans** | `https://g.shinigami.asia` | ✅ Active |

---

## 🛠️ Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/<your-username>/multi-manga-scraper.git
   cd multi-manga-scraper
   ```

2. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Usage

### 1. Interactive Menu Mode (Recommended)
Run without arguments to launch the interactive prompt:
```bash
python main.py
```

Follow the terminal menu to:
1. Select target website (Komikcast, Shinigami, or Auto-Detect).
2. Input Manga URL or Slug/UUID.
3. Select download mode (*Latest Chapter*, *All Chapters*, or *Custom Range*).
4. Select output format (*PDF + Images*, *PDF Only*, or *Images Only*).

### 2. Command Line Arguments Mode
```bash
# Auto-detect website and download latest chapter (Test mode)
python main.py https://v3.komikcast.fit/series/tensei-shitara-slime-datta-ken --latest-only

# Download ALL chapters from Shinigami
python main.py https://g.shinigami.asia/series/fb9be087-b8b4-4a26-b088-58fbc7cfce49 --all

# Download PDF only and clean up raw image files
python main.py https://v3.komikcast.fit/series/solo-leveling --latest-only --pdf-only
```

---

## 📓 Google Colab

Use the included Notebook `multi_downloader_colab.ipynb` to download manga directly on Google Colab and save PDFs straight into your **Google Drive**:
1. Open [Google Colab](https://colab.research.google.com/).
2. Upload `multi_downloader_colab.ipynb`.
3. Run Step 1 to mount Google Drive, Step 2 to load engines, and Step 3 to use the interactive form.

---

## 📄 License & Disclaimer

This project is intended for personal and educational use only. Respect comic creators, translators, and site owners.
