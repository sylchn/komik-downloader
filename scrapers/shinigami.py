import os
import re
import shutil
from curl_cffi import requests as curl_requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from .base import BaseScraper, sanitize_folder_name, convert_folder_to_pdf, logger

BASE_API_URL = "https://api.shngm.io/v1"
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Origin': 'https://g.shinigami.asia',
    'Referer': 'https://g.shinigami.asia/'
}

class ShinigamiScraper(BaseScraper):
    """Scraper implementation for Shinigami Scans (g.shinigami.asia)."""
    
    SITE_NAME = "Shinigami Scans"
    
    def __init__(self, output_dir="download", max_workers=5):
        super().__init__(output_dir=output_dir, max_workers=max_workers)
        self.session = curl_requests.Session(impersonate="chrome120")

    @staticmethod
    def extract_manga_id(input_str):
        """Extract manga UUID from URL or raw string."""
        input_str = input_str.strip()
        match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', input_str, re.IGNORECASE)
        if match:
            return match.group(0)
        return input_str.rstrip('/')

    def get_series_info(self, url_or_id):
        manga_id = self.extract_manga_id(url_or_id)
        url = f"{BASE_API_URL}/manga/detail/{manga_id}"
        res = self.session.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if res.status_code != 200:
            raise Exception(f"Failed to fetch series info for ID '{manga_id}'. HTTP {res.status_code}")
        
        data = res.json().get("data", {})
        return {
            "manga_id": data.get("manga_id", manga_id),
            "title": data.get("title", manga_id),
            "author": data.get("author_name") or data.get("author") or "Unknown"
        }

    def get_chapter_list(self, manga_id):
        manga_id = self.extract_manga_id(manga_id)
        all_chapters = []
        page = 1
        page_size = 100
        
        while True:
            url = f"{BASE_API_URL}/chapter/{manga_id}/list?page={page}&pageSize={page_size}"
            res = self.session.get(url, headers=DEFAULT_HEADERS, timeout=10)
            if res.status_code != 200:
                raise Exception(f"Failed to fetch chapter list (page {page}). HTTP {res.status_code}")
            
            data = res.json()
            chapters = data.get("data", [])
            if not chapters:
                break
                
            all_chapters.extend(chapters)
            
            meta = data.get("meta", {})
            total_pages = meta.get("total_page") or meta.get("totalPages") or 1
            if page >= total_pages:
                break
            page += 1

        # Sort chapters ascending by chapter_number
        sorted_chapters = sorted(
            all_chapters,
            key=lambda x: float(x.get("chapter_number") or 0)
        )
        return sorted_chapters

    def get_chapter_details(self, chapter_item):
        ch_id = chapter_item.get("chapter_id")
        url = f"{BASE_API_URL}/chapter/detail/{ch_id}"
        res = self.session.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if res.status_code != 200:
            raise Exception(f"Failed to fetch details for chapter ID {ch_id}. HTTP {res.status_code}")
        
        data = res.json().get("data", {})
        base_url = data.get("base_url", "https://assets.shngm.id").rstrip('/')
        chapter_info = data.get("chapter", {})
        path = chapter_info.get("path", "").strip('/')
        image_filenames = chapter_info.get("data", [])
        
        full_urls = []
        for fname in image_filenames:
            full_url = f"{base_url}/{path}/{fname}" if path else f"{base_url}/{fname}"
            full_urls.append(full_url)
            
        return {
            "chapter_id": ch_id,
            "number": data.get("chapter_number"),
            "title": data.get("chapter_title", ""),
            "images": full_urls
        }

    def download_single_image(self, img_url, save_path, retries=3):
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            return True
        for attempt in range(retries):
            try:
                res = self.session.get(img_url, headers=DEFAULT_HEADERS, timeout=15)
                if res.status_code == 200 and len(res.content) > 0:
                    with open(save_path, "wb") as f:
                        f.write(res.content)
                    return True
            except Exception as e:
                if attempt == retries - 1:
                    logger.warning(f"Failed to download image {img_url}: {e}")
        return False

    def download_chapter(self, identifier, series_title, chapter_item, make_pdf=True, keep_images=True):
        details = self.get_chapter_details(chapter_item)
        images = details.get("images", [])
        ch_number = details.get("number")
        
        if not images:
            logger.warning(f"No images found for Chapter {ch_number}")
            return
        
        clean_series = sanitize_folder_name(series_title)
        chapter_folder_name = f"Chapter {ch_number}"
        if details.get("title"):
            chapter_folder_name += f" - {sanitize_folder_name(details['title'])}"
            
        chapter_dir = os.path.join(self.output_dir, clean_series, chapter_folder_name)
        os.makedirs(chapter_dir, exist_ok=True)
        
        logger.info(f"Downloading Chapter {ch_number} ({len(images)} images) -> {chapter_dir}")
        
        tasks = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for idx, img_url in enumerate(images, start=1):
                ext = img_url.split('.')[-1].split('?')[0]
                if len(ext) > 4 or not ext.isalnum():
                    ext = "webp"
                filename = f"{idx:03d}.{ext}"
                save_path = os.path.join(chapter_dir, filename)
                tasks.append(executor.submit(self.download_single_image, img_url, save_path))
            
            for _ in tqdm(as_completed(tasks), total=len(tasks), desc=f"Ch {ch_number}", unit="img", leave=False):
                pass

        logger.info(f"Downloaded Chapter {ch_number} images successfully.")

        if make_pdf:
            pdf_name = f"{chapter_folder_name}.pdf"
            pdf_path = os.path.join(self.output_dir, clean_series, pdf_name)
            convert_folder_to_pdf(chapter_dir, pdf_path)
            
            if not keep_images:
                shutil.rmtree(chapter_dir, ignore_errors=True)
                logger.info(f"Deleted raw image folder: {chapter_dir}")
