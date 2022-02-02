from argparse import ArgumentParser
from dataclasses import dataclass
import json
from multiprocessing.pool import ThreadPool
import os

import requests
from bs4 import BeautifulSoup
import tqdm

from cache import BaseCache


@dataclass
class Diploma:
    title: str
    educational_programme: str
    year: int
    abstract: str
    level: str = ""
    faculty: str = ""


class HSECache(BaseCache):
    def _diploma_to_json(self, diploma: Diploma) -> dict:
        return {
            "title": diploma.title,
            "educational_programme": diploma.educational_programme,
            "year": diploma.year,
            "abstract": diploma.abstract,
            "level": diploma.level,
            "faculty": diploma.faculty
        }
    
    def _json_to_diploma(self, diploma_json: dict) -> Diploma:
        return Diploma(
            title=diploma_json["title"],
            educational_programme=diploma_json["educational_programme"],
            year=diploma_json["year"],
            abstract=diploma_json["abstract"],
            level=diploma_json["level"],
            faculty=diploma_json["faculty"]
        )
    
    def save_state(self, state_name: str, state: list[Diploma]):
        json_data = [self._diploma_to_json(diploma) for diploma in state]
        with open(os.path.join(self.folder, state_name), "w+") as f:
            json.dump(json_data, f)
    
    def load_state(self, state_name: str) -> list[Diploma]:
        with open(os.path.join(self.folder, state_name)) as f:
            json_data = json.load(f)
        
        return [self._json_to_diploma(diploma_json) for diploma_json in json_data]
    
    def aggregate_states(self, states: list[list[Diploma]]) -> list[dict]:
        result = []
        for diploma_list in states:
            for diploma in diploma_list:
                result.append(self._diploma_to_json(diploma))
        return result


base_url = "https://www.hse.ru"
diplomas_list_url = base_url + "/edu/vkr/?language=ru&page={page}"


def page_contains_diplomas(page: int) -> bool:
    response = requests.get(base_url.format(page=page))
    page_text = response.text
    
    return "ВКР не найдены" not in page_text


def find_max_page() -> int:
    page = 1
    while page_contains_diplomas(page):
        page += 1
    return page - 1


def get_single_diploma(diploma_url: str) -> Diploma:
    response = requests.get(diploma_url)
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("h1", class_="vkr__title vkr__title-page").text
    abstract = soup.find("div", class_="vkr-content__text").text

    for diploma_item in soup.find_all("p", class_="vkr-card__item"):
        item_text = diploma_item.text
        if "Кампус/факультет" in item_text:
            faculty = diploma_item.find("a").text.strip()
        elif "Программа" in item_text:
            programme, level = [span.text.strip() for span in diploma_item.find_all("span")]
        elif "Год защиты" in item_text:
            year = int(diploma_item.find("span").text.strip())
    
    return Diploma(
        title=title,
        educational_programme=programme,
        year=year,
        abstract=abstract,
        level=level,
        faculty=faculty
    )


def get_diplomas(page: int) -> list[Diploma]:
    response = requests.get(diplomas_list_url.format(page=page))
    soup = BeautifulSoup(response.text, "html.parser")
    
    result = []
    for diploma_li in soup.find_all("li", class_="vkr-list__item vkr-card"):
        try:
            card_title = diploma_li.find("h3", class_="vkr-card__title")
            diploma_url = card_title.find("a", class_="link")["href"]
            result.append(get_single_diploma(base_url + diploma_url))
        except Exception:
            continue
    
    return result


def main(cache_folder: str, max_page: int, n_threads: int, output_path: str):
    os.makedirs(cache_folder, exist_ok=True)
    cache = HSECache(cache_folder)

    max_page = find_max_page() if max_page == 0 else max_page
    print(f"Max page: {max_page}")

    all_pages = list(range(1, max_page + 1))
    cached_mask = cache.contains_multiple(map(str, all_pages))

    not_cached_pages = []
    for page, is_cached in zip(all_pages, cached_mask):
        if is_cached:
            continue
        not_cached_pages.append(page)
    print(f"Loaded uncached pages: {len(not_cached_pages)}")

    def load_save_diplomas(page: int):
        page_diplomas = get_diplomas(page)
        cache.save_state(str(page), page_diplomas)

    if not n_threads:
        for page in tqdm.tqdm(not_cached_pages):
            load_save_diplomas(page)
    else:
        with ThreadPool(n_threads) as pool, tqdm.tqdm(total=len(not_cached_pages)) as pbar:
            for _ in pool.imap_unordered(load_save_diplomas, not_cached_pages):
                pbar.update()
    
    with open(output_path, "w+") as f:
        json.dump(cache.load(), f)


if __name__ == "__main__":
    parser = ArgumentParser("HSE diplomas scraper")
    parser.add_argument("--cache_folder", type=str, default="_hse_cache", help="folder to store intermediate cache files")
    parser.add_argument("--max_page", type=int, default=0, help="maximum amount of pages to parse")
    parser.add_argument("--n_threads", type=int, default=0, help="number of threads to parse pages")
    parser.add_argument("--output_path", type=str, required=True, help="path to save output json")
    args = parser.parse_args()

    main(args.cache_folder, args.max_page, args.n_threads, args.output_path)
