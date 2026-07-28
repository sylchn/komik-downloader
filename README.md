# 🌐 Multi-Site Manga Scraper & PDF Generator

A powerful, high-performance Python manga downloader and PDF generator supporting multiple Indonesian manga sites with Cloudflare bypass, multithreading, and Google Colab integration.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sylchn/komik-downloader/blob/main/multi_downloader_colab.ipynb)

---

## ✨ Features

- 🌐 **Multi-Site Support**: Easily download from multiple manga websites in one tool.
- ⚡ **Fast Concurrent Downloads**: Multi-threaded image downloader for high-speed downloads.
- 📄 **Automatic PDF Generation**: Merges downloaded chapter images into clean PDF documents automatically.
- 🔓 **Cloudflare Bypass**: Built-in TLS fingerprinting bypass (`curl_cffi`) for protected sites like Shinigami.
- 🖥️ **Interactive Menu & CLI**: User-friendly terminal interface or CLI arguments for automation.
- 📓 **Google Colab Direct Badge**: Click the "Open In Colab" badge to launch `multi_downloader_colab.ipynb` directly in Colab and save PDFs to Google Drive.
- 📝 **Activity Logging**: Saves all user inputs, download progress, and results to `scraper.log`.

---

## 📚 Supported Websites

| Website | URL | Support Status |
| :--- | :--- | :---: |
| **Komikcast** | `https://v3.komikcast.fit` | ✅ Active |
| **Shinigami Scans** | `https://g.shinigami.asia` | ✅ Active |

---

## 📓 Run Directly in Google Colab

Click the badge below to open the notebook directly in Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sylchn/komik-downloader/blob/main/multi_downloader_colab.ipynb)

---

## 🛠️ Local Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/sylchn/komik-downloader.git
   cd komik-downloader
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

## 📄 License & Disclaimer

This project is intended for personal and educational use only. Respect comic creators, translators, and site owners.
