import os
import re
import sys
import argparse
from scrapers import KomikcastScraper, ShinigamiScraper
from scrapers.base import logger

AVAILABLE_SCRAPERS = {
    "komikcast": KomikcastScraper,
    "shinigami": ShinigamiScraper
}

def detect_site(url_or_input):
    """Auto-detect website scraper class based on input URL/string."""
    url_lower = url_or_input.lower()
    if 'shinigami' in url_lower or re_uuid(url_or_input):
        return "shinigami"
    elif 'komikcast' in url_lower:
        return "komikcast"
    return None

def re_uuid(input_str):
    return bool(re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', input_str, re.IGNORECASE))

def interactive_menu():
    """Display interactive CLI menu to select website, URL, and options."""
    print("=" * 65)
    print("     🌐 MULTI-SITE MANGA SCRAPER & PDF GENERATOR 🌐")
    print("=" * 65)
    
    print("\n[1] Pilih Website Target:")
    print("    1. Komikcast (v3.komikcast.fit)")
    print("    2. Shinigami Scans (g.shinigami.asia)")
    print("    3. Otomatis Deteksi dari URL")
    
    site_choice = input("    Pilihan (1/2/3) [Default: 3]: ").strip() or "3"
    
    if site_choice == "1":
        site_key = "komikcast"
        default_url = "https://v3.komikcast.fit/series/tensei-shitara-slime-datta-ken"
    elif site_choice == "2":
        site_key = "shinigami"
        default_url = "https://g.shinigami.asia/series/fb9be087-b8b4-4a26-b088-58fbc7cfce49"
    else:
        site_key = None
        default_url = "https://v3.komikcast.fit/series/tensei-shitara-slime-datta-ken"
        
    url_input = input(f"\n[2] Masukkan URL / Identifier Komik (Default: {default_url}): ").strip()
    if not url_input:
        url_input = default_url
        
    if not site_key:
        site_key = detect_site(url_input) or "komikcast"
        print(f"    ℹ️ Target terdeteksi sebagai: [{AVAILABLE_SCRAPERS[site_key].SITE_NAME}]")
        
    print("\n[3] Pilih Mode Download:")
    print("    1. Chapter Terbaru Saja (Test Mode)")
    print("    2. SEMUA Chapter")
    print("    3. Range Chapter Tertentu (contoh: Chapter 1 sampai 10)")
    mode_choice = input("    Pilihan Mode (1/2/3) [Default: 1]: ").strip() or "1"
    
    print("\n[4] Pilih Format Output:")
    print("    1. PDF + Folder Gambar (Default)")
    print("    2. PDF Saja (Hapus gambar mentah setelah selesai)")
    print("    3. Folder Gambar Saja (Tanpa PDF)")
    format_choice = input("    Pilihan Format (1/2/3) [Default: 1]: ").strip() or "1"
    
    make_pdf = format_choice in ["1", "2"]
    keep_images = format_choice in ["1", "3"]
    
    return site_key, url_input, mode_choice, make_pdf, keep_images

def main():
    parser = argparse.ArgumentParser(description="Multi-site Manga Scraper & PDF Generator")
    parser.add_argument("url_or_identifier", nargs="?", default=None,
                        help="Series URL or slug/UUID")
    parser.add_argument("--site", choices=["komikcast", "shinigami"], default=None,
                        help="Specify site scraper (komikcast or shinigami)")
    parser.add_argument("--latest-only", action="store_true", help="Download only the latest chapter (Test mode)")
    parser.add_argument("--all", action="store_true", help="Download all chapters")
    parser.add_argument("--no-pdf", action="store_true", help="Disable PDF generation (keep images only)")
    parser.add_argument("--pdf-only", action="store_true", help="Generate PDF and delete raw image folder after")
    parser.add_argument("--output", default="download", help="Base download directory (default: download)")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent image download threads")

    args = parser.parse_args()
    
    if args.url_or_identifier is None and not (args.latest_only or args.all):
        site_key, url_input, mode_choice, make_pdf, keep_images = interactive_menu()
    else:
        url_input = args.url_or_identifier or "https://v3.komikcast.fit/series/tensei-shitara-slime-datta-ken"
        site_key = args.site or detect_site(url_input) or "komikcast"
        make_pdf = not args.no_pdf
        keep_images = not args.pdf_only
        if args.all:
            mode_choice = "2"
        else:
            mode_choice = "1"
            
    scraper_cls = AVAILABLE_SCRAPERS.get(site_key)
    if not scraper_cls:
        logger.error(f"Unknown scraper site key: {site_key}")
        sys.exit(1)
        
    scraper = scraper_cls(output_dir=args.output, max_workers=args.workers)
    logger.info(f"Initialized [{scraper.SITE_NAME}] scraper session for input: {url_input}")
    
    try:
        series_info = scraper.get_series_info(url_input)
        logger.info(f"Series Info Retrieved - Title: '{series_info['title']}', Author: '{series_info.get('author')}'")
        
        identifier = series_info.get("slug") or series_info.get("manga_id") or url_input
        chapters = scraper.get_chapter_list(identifier)
        if not chapters:
            logger.error("No chapters found for this series.")
            return
        
        logger.info(f"Total chapters available: {len(chapters)}")
        
        if mode_choice == "2":
            logger.info("Mode: Downloading ALL chapters...")
            for ch in chapters:
                scraper.download_chapter(identifier, series_info['title'], ch, make_pdf=make_pdf, keep_images=keep_images)
        elif mode_choice == "3":
            ch_nums = []
            for c in chapters:
                num = c.get("data", {}).get("index") or c.get("index") or c.get("chapter_number") or 0
                ch_nums.append(float(num))
            ch_nums.sort()
            
            print(f"\n[INFO] Indeks chapter tersedia: {ch_nums[0]} s/d {ch_nums[-1]}")
            try:
                start_idx = float(input("    Masukkan Chapter Awal (misal: 1): ").strip())
                end_idx = float(input("    Masukkan Chapter Akhir (misal: 10): ").strip())
                logger.info(f"Mode Custom Range: Chapter {start_idx} to {end_idx}")
                
                filtered_chapters = []
                for ch in chapters:
                    num = float(ch.get("data", {}).get("index") or ch.get("index") or ch.get("chapter_number") or 0)
                    if start_idx <= num <= end_idx:
                        filtered_chapters.append(ch)
                        
                logger.info(f"Found {len(filtered_chapters)} chapters within specified range.")
                for ch in filtered_chapters:
                    scraper.download_chapter(identifier, series_info['title'], ch, make_pdf=make_pdf, keep_images=keep_images)
            except ValueError:
                logger.error("Invalid range input. Please enter valid numbers.")
                return
        else:
            # Mode 1: Latest chapter
            latest_chapter = chapters[-1]
            logger.info("Mode: Downloading Latest Chapter Only...")
            scraper.download_chapter(identifier, series_info['title'], latest_chapter, make_pdf=make_pdf, keep_images=keep_images)
            
        logger.info(f"Session finished cleanly. Files stored in: '{os.path.abspath(args.output)}'")
        print(f"\n[DONE] Log aktivitas telah dicatat di file 'scraper.log'.")
        
    except Exception as e:
        logger.error(f"Error during scraping session: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
