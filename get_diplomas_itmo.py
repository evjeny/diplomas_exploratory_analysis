from argparse import ArgumentParser
from dataclasses import dataclass
import json
import os
import re

import tqdm

from base import Diploma
from cache import DiplomaListCache


@dataclass
class Diploma:
    title: str
    educational_programme: str
    year: int
    abstract: str
    level: str = ""
    faculty: str = ""


year_line_regexp = re.compile("год рождения")
programme_line_regexp = re.compile("(специальность|направление.*):", flags=re.IGNORECASE)
email_line_regexp = re.compile("e-mail:")
udk_line_regexp = re.compile("удк")
s_director_line_regexp = re.compile("научный руководитель")
literature_line_regexp = re.compile("литература")

year_regexp = re.compile("[0-9]{4}")
multiple_ws_regexp = re.compile(r"\s{2,}")
group_regexp = re.compile(r"(,\s+)?группа.*\d+", flags=re.IGNORECASE)


def get_diplomas_level(text: str) -> str:
    low_text = text.lower()
    most_frequent_level = ""
    max_count = 0
    for level in ["бакалавр", "магистр", "специалист"]:
        current_count = low_text.count(level)
        if current_count > max_count:
            max_count = current_count
            most_frequent_level = level
    if max_count == 0:
        raise Exception("No level information!")
    
    return most_frequent_level


def locate_lines(low_lines: list[str], regexp: re.Pattern) -> list[int]:
    return [
        i for i, line in enumerate(low_lines)
        if regexp.search(line)
    ]


def get_closest_indices(target_index: int, indices: list[int], max_distance: int) -> list[int]:
    # may be optimized with BinSearch
    closest_indices = [i for i in indices if abs(target_index - i) <= max_distance]
    return sorted(closest_indices, key=lambda i: abs(i - target_index)) # sort by distance from target_index


def group_closest_indices(*indices_group: list[list[int]], max_distance: int) -> list[tuple[int]]:
    primary_indices = indices_group[0]
    secondary_group = indices_group[1:]
    
    group_matches = [
        [first_index] +\
        [
            get_closest_indices(first_index, secondary_indices, max_distance)
            for secondary_indices in secondary_group
        ]
        for first_index in primary_indices
    ]

    # filter groups without matches
    result = []
    used_indices: list[set[int]] = [set() for _ in range(len(indices_group) - 1)]
    for first_index, *macthes_group in group_matches:
        filtered_matches = [
            [index for index in matched_indices if index not in used_indices[i_group]]
            for i_group, matched_indices in enumerate(macthes_group)
        ]
        if not all(len(matched_indices) > 0 for matched_indices in filtered_matches):
            continue
        
        rest_indices = [matched_indices[0] for matched_indices in filtered_matches]
        result.append(tuple([first_index] + rest_indices))

        # add rest_indices to used
        for i_group, index in enumerate(rest_indices):
            used_indices[i_group].add(index)
    
    return result


def find_literature_index(lines: list[str], begin_index: int):
    global literature_line_regexp

    current_index = begin_index
    while not literature_line_regexp.search(lines[current_index]) and current_index < len(lines):
        current_index += 1
    return current_index


def extract_year(line: str) -> int:
    global year_regexp
    begin, end = year_regexp.search(line).span()
    return int(line[begin: end])


def remove_empty_lines(lines: list[str], empty_thresh: int = 1) -> list[str]:
    stripped_lines = map(lambda line: line.strip(), lines)
    return list(filter(lambda line: len(line) > empty_thresh, stripped_lines))


def remove_useless_whitespaces(line: str) -> str:
    global multiple_ws_regexp
    return multiple_ws_regexp.sub(" ", line).strip()


def extract_title(lines: list[str]) -> str:
    not_empty = remove_empty_lines(lines)
    return remove_useless_whitespaces(" ".join(not_empty))


def extract_programme(lines: list[str]) -> str:
    global programme_line_regexp
    
    not_empty = remove_empty_lines(lines)
    without_programme = list(map(
        lambda line: programme_line_regexp.sub("", line),
        not_empty
    ))
    return remove_useless_whitespaces(" ".join(without_programme))


def extract_faculty(lines: list[str]) -> str:
    global group_regexp

    not_empty = remove_empty_lines(lines)
    without_group = list(map(
        lambda line: group_regexp.sub("", line),
        not_empty
    ))
    return remove_useless_whitespaces(" ".join(without_group))


def extract_abstract(lines: list[str]) -> str:
    not_empty = remove_empty_lines(lines, empty_thresh=7)
    return remove_useless_whitespaces(" ".join(not_empty))


def parse_file(path: str) -> list[Diploma]:
    global year_line_regexp, programme_line_regexp, email_line_regexp
    global udk_line_regexp, s_director_line_regexp, year_regexp

    with open(path) as f:
        content = f.read()

    try:
        year = extract_year(os.path.basename(path)) # year encoded in filename
        assert year >= 2000 and year <= 2022, "year is in reasonable range"
        diplomas_level = get_diplomas_level(content)
    except Exception:
        return []

    lines = content.split("\n")
    low_lines = [line.lower() for line in lines]

    year_indices = locate_lines(low_lines, year_line_regexp)
    programme_indices = locate_lines(low_lines, programme_line_regexp)
    email_indices = locate_lines(low_lines, email_line_regexp)
    udk_indices = locate_lines(low_lines, udk_line_regexp)
    s_director_indices = locate_lines(low_lines, s_director_line_regexp)
    
    indices_groups = group_closest_indices(
        email_indices, year_indices, programme_indices,
        udk_indices, s_director_indices,

        max_distance=20
    )

    result = []
    for group_i, (email_i, year_i, programme_i, udk_i, s_director_i) in enumerate(indices_groups):
        try:
            title = extract_title(lines[udk_i+1: s_director_i-1])
            programme = extract_programme(lines[programme_i: email_i])
            faculty = extract_faculty(lines[year_i+1: programme_i])

            literature_i = find_literature_index(low_lines, s_director_i)
            if group_i < len(indices_groups) - 1 and literature_i >= indices_groups[group_i + 1][0]:
                # if literature index is greater then begin of the next group
                continue

            abstract = extract_abstract(lines[s_director_i+1: literature_i])
        except Exception:
            continue

        result.append(Diploma(
            title=title, educational_programme=programme,
            year=year, abstract=abstract, level=diplomas_level, faculty=faculty
        ))
    return result
        


def main(cache_folder: str, txts_folder: str, output_path: str):
    os.makedirs(cache_folder, exist_ok=True)
    cache = DiplomaListCache(cache_folder)

    txt_files = [fn for fn in os.listdir(txts_folder) if fn.endswith(".txt")]
    cached_mask = cache.contains_multiple(txt_files)

    not_cached_txts = []
    for txt, is_cached in zip(txt_files, cached_mask):
        if is_cached:
            continue
        not_cached_txts.append(txt)
    print(f"Loaded uncached txts: {len(not_cached_txts)}")

    for filename in tqdm.tqdm(not_cached_txts):
        file_diplomas = parse_file(os.path.join(txts_folder, filename))
        cache.save_state(filename, file_diplomas)
    
    with open(output_path, "w+") as f:
        json.dump(cache.load(), f)


if __name__ == "__main__":
    parser = ArgumentParser("ITMO diplomas scraper")
    parser.add_argument("--cache_folder", type=str, default="_itmo_cache", help="folder to store intermediate cache files")
    parser.add_argument("--txts_folder", type=str, required=True, help="path to .txt files extracted from pdfs")
    parser.add_argument("--output_path", type=str, required=True, help="path to save output json")
    args = parser.parse_args()

    main(args.cache_folder, args.txts_folder, args.output_path)
