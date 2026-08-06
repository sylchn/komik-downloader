import os
import re
import shutil
from curl_cffi import requests as curl_requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from .base import BaseScraper, sanitize_folder_name, convert_folder_to_pdf, logger

BASE_API_URL = "https://be.komikcast.cc"
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Origin': 'https://v3.komikcast.fit',
    'Referer': 'https://v3.komikcast.fit/'
}

class KomikcastScraper(BaseScraper):
    """Scraper implementation for Komikcast v3 (v3.komikcast.fit)."""
    
    SITE_NAME = "Komikcast"
    
    def __init__(self, output_dir="download", max_workers=5):
        super().__init__(output_dir=output_dir, max_workers=max_workers)
        self.session = curl_requests.Session(impersonate="chrome120")
    
    @staticmethod
    def extract_slug(input_str):
        """Extract series slug from URL (supporting series/ or komik/) or raw slug string."""
        input_str = input_str.strip()
        match = re.search(r'(?:series|komik)/([^/]+)', input_str)
        if match:
            return match.group(1)
        return input_str.rstrip('/').split('/')[-1]

    def get_series_info(self, url_or_slug):
        slug = self.extract_slug(url_or_slug)
        url = f"{BASE_API_URL}/series/{slug}"
        res = self.session.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if res.status_code != 200:
            raise Exception(f"Failed to fetch series info for '{slug}'. HTTP {res.status_code}")
        
        data = res.json().get("data", {})
        inner_data = data.get("data", {})
        title = inner_data.get("title", slug)
        return {
            "id": data.get("id"),
            "title": title,
            "slug": inner_data.get("slug", slug),
            "total_chapters": inner_data.get("totalChapters", 0),
            "author": inner_data.get("author", "Unknown")
        }

    def get_chapter_list(self, slug):
        url = f"{BASE_API_URL}/series/{slug}/chapters"
        res = self.session.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if res.status_code != 200:
            raise Exception(f"Failed to fetch chapter list. HTTP {res.status_code}")
        
        chapters_data = res.json().get("data", [])
        # Sort chapters ascending by index
        sorted_chapters = sorted(
            chapters_data,
            key=lambda x: float(x.get("data", {}).get("index") or x.get("index") or 0)
        )
        return sorted_chapters

    def get_chapter_details(self, slug, chapter_item):
        ch_index = chapter_item.get("data", {}).get("index") or chapter_item.get("index")
        url = f"{BASE_API_URL}/series/{slug}/chapters/{ch_index}"
        res = self.session.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if res.status_code != 200:
            raise Exception(f"Failed to fetch details for chapter {ch_index}. HTTP {res.status_code}")
        
        data = res.json().get("data", {})
        inner_data = data.get("data", {})
        images = inner_data.get("images", [])
        title = inner_data.get("title")
        return {
            "id": data.get("id"),
            "number": ch_index,
            "title": title,
            "images": images
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

    def download_chapter(self, slug, series_title, chapter_item, make_pdf=True, keep_images=True):
        details = self.get_chapter_details(slug, chapter_item)
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
                    ext = "jpg"
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
