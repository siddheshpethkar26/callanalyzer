import os
import csv
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import argparse


@dataclass
class Project:
    name: str
    price: Optional[str] = None
    carpet_area: Optional[str] = None
    configuration: Optional[str] = None
    builder: Optional[str] = None
    status: Optional[str] = None
    rera_number: Optional[str] = None
    amenities: List[str] = None
    image_urls: List[str] = None
    video_urls: List[str] = None
    brochure_links: List[str] = None
    address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    nearby_landmarks: Optional[str] = None
    possession_date: Optional[str] = None
    rating: Optional[str] = None
    tags: Optional[str] = None
    highlights: Optional[str] = None


class SquareYardsScraper:
    def __init__(self, headless: bool = True, proxy: Optional[str] = None):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        if proxy:
            chrome_options.add_argument(f"--proxy-server={proxy}")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

    def close(self):
        self.driver.quit()

    def get_project_links(self, city_url: str) -> List[str]:
        links = []
        self.driver.get(city_url)
        while True:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.projectCard')))
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            for a in soup.select('.projectCard a[href*="/project/"]'):
                href = a.get('href')
                if href and href not in links:
                    links.append('https://www.squareyards.com' + href)
            next_btn = soup.select_one('a[rel="next"]')
            if next_btn and 'disabled' not in next_btn.get('class', []):
                self.driver.get('https://www.squareyards.com' + next_btn['href'])
                time.sleep(2)
            else:
                break
        return links

    def parse_project(self, url: str) -> Project:
        self.driver.get(url)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        name = soup.select_one('h1')
        project = Project(name=name.text.strip() if name else 'N/A')
        price = soup.find(text=lambda t: t and 'Price' in t)
        if price:
            project.price = price.find_next().get_text(strip=True)
        area = soup.find(text=lambda t: t and 'Carpet Area' in t)
        if area:
            project.carpet_area = area.find_next().get_text(strip=True)
        config = soup.find(text=lambda t: t and 'BHK' in t)
        if config:
            project.configuration = config.strip()
        builder = soup.find(text=lambda t: t and 'Builder' in t)
        if builder:
            project.builder = builder.find_next().get_text(strip=True)
        status = soup.find(text=lambda t: t and 'Status' in t)
        if status:
            project.status = status.find_next().get_text(strip=True)
        rera = soup.find(text=lambda t: t and 'RERA' in t)
        if rera:
            project.rera_number = rera.find_next().get_text(strip=True)
        amenities = [li.get_text(strip=True) for li in soup.select('.amenities li')]
        project.amenities = amenities
        images = [img['src'] for img in soup.select('img') if 'http' in img.get('src', '')]
        project.image_urls = images
        videos = [v['src'] for v in soup.select('iframe[src*="youtube"], video source[src]')]
        project.video_urls = videos
        brochures = [a['href'] for a in soup.select('a[href*="brochure"]')]
        project.brochure_links = brochures
        address = soup.find('address')
        if address:
            project.address = address.get_text(strip=True)
        map_iframe = soup.select_one('iframe[src*="google.com/maps"]')
        if map_iframe:
            src = map_iframe['src']
            if 'latitude' in src and 'longitude' in src:
                # hypothetical params
                project.latitude = src.split('latitude=')[1].split('&')[0]
                project.longitude = src.split('longitude=')[1].split('&')[0]
        possession = soup.find(text=lambda t: t and 'Possession' in t)
        if possession:
            project.possession_date = possession.find_next().get_text(strip=True)
        return project

    def save_media(self, project: Project, folder: str):
        os.makedirs(folder, exist_ok=True)
        for i, img_url in enumerate(project.image_urls or []):
            # Here we simply save the URL references. Downloading is skipped due to environment limits.
            with open(os.path.join(folder, f"image_{i}.txt"), 'w') as f:
                f.write(img_url)
        for i, video_url in enumerate(project.video_urls or []):
            with open(os.path.join(folder, f"video_{i}.txt"), 'w') as f:
                f.write(video_url)

    def scrape(self, city_url: str, limit: int = 10) -> List[Project]:
        projects = []
        links = self.get_project_links(city_url)
        for link in links[:limit]:
            try:
                project = self.parse_project(link)
                folder_name = project.name.replace(' ', '_')
                self.save_media(project, folder_name)
                projects.append(project)
            except Exception as e:
                print(f"Failed to scrape {link}: {e}")
        return projects

    @staticmethod
    def save_to_csv(projects: List[Project], filename: str):
        if not projects:
            return
        fieldnames = list(asdict(projects[0]).keys())
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for project in projects:
                writer.writerow(asdict(project))

    @staticmethod
    def save_to_json(projects: List[Project], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([asdict(p) for p in projects], f, ensure_ascii=False, indent=2)




def build_city_url(city: str) -> str:
    """Return a SquareYards URL for the given city."""
    city = city.lower().replace(" ", "-")
    return f"https://www.squareyards.com/new-projects-in-{city}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape SquareYards projects")
    parser.add_argument(
        "--city",
        help="City name to scrape (e.g. Mumbai). Overrides --url if provided.",
    )
    parser.add_argument(
        "--url",
        help="Full SquareYards listing URL to scrape.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of projects to scrape",
    )
    parser.add_argument(
        "--output",
        default="sample_output.csv",
        help="CSV file to save results",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.city:
        city_url = build_city_url(args.city)
    else:
        city_url = args.url or "https://www.squareyards.com/new-projects-in-india"

    scraper = SquareYardsScraper()
    try:
        projects = scraper.scrape(city_url, limit=args.limit)
        scraper.save_to_csv(projects, args.output)
        json_output = os.path.splitext(args.output)[0] + ".json"
        scraper.save_to_json(projects, json_output)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
