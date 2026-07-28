import os
import re
import sys
import shutil
import logging
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Ensure UTF-8 output encoding for Windows terminal compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Logging configuration
LOG_FILE = "scraper.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MultiMangaScraper")

def sanitize_folder_name(name):
    """Sanitize string for folder/filename in Windows/Linux."""
    if not name:
        return "Unknown"
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).strip()

def convert_folder_to_pdf(chapter_dir, pdf_save_path):
    """Convert all image files in chapter_dir to a single PDF file."""
    valid_exts = ('.jpg', '.png', '.jpeg', '.webp', '.bmp')
    image_files = [
        os.path.join(chapter_dir, f) for f in os.listdir(chapter_dir)
        if f.lower().endswith(valid_exts)
    ]
    image_files.sort()
    
    if not image_files:
        logger.warning(f"No images found in {chapter_dir} to convert to PDF.")
        return False
    
    pil_images = []
    for filepath in image_files:
        try:
            img = Image.open(filepath)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            pil_images.append(img)
        except Exception as err:
            logger.warning(f"Skipping corrupted image {filepath}: {err}")
            
    if pil_images:
        os.makedirs(os.path.dirname(pdf_save_path), exist_ok=True)
        pil_images[0].save(pdf_save_path, save_all=True, append_images=pil_images[1:])
        logger.info(f"📄 Created PDF: {pdf_save_path}")
        return True
    return False

class BaseScraper:
    """Base class for all site scrapers."""
    
    def __init__(self, output_dir="download", max_workers=5):
        self.output_dir = output_dir
        self.max_workers = max_workers

    def get_series_info(self, url_or_identifier):
        raise NotImplementedError

    def get_chapter_list(self, identifier):
        raise NotImplementedError

    def get_chapter_details(self, chapter_item):
        raise NotImplementedError

    def download_image(self, img_url, save_path, retries=3):
        raise NotImplementedError
