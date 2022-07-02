"""
### Frequency Lists
Raw frequency lists aren't very useful.
They're full of redundancies (e.g., "run", "runs", "ran" are all the same underlying word).
They also hide synonyms (e.g., "run" as verb vs. "run" as noun).

### What this file does:
Load a frequency list derived from [open subtitles](https://github.com/hermitdave/FrequencyWords),
lemmatize the words, split by definitions, and reorder.
"""
import json
import os
import re
import sys
from pathlib import Path
import csv
import requests
from pprint import pp

from tqdm import tqdm
from googletrans import Translator
import typer
import wiktionaryparser as wp

from wiktionary.constants import LANGUAGES
from wiktionary.wt_types import (
    Word,
    WiktionaryDefinition,
    WiktionaryPronunciation,
    WiktionaryFetchResult,
    EnrichedWiktionaryDefinition,
    EnrichedWiktionaryPronunciation,
    EnrichedWiktionaryFetchResult,
    Lang,
)

translator = Translator()
parser = wp.WiktionaryParser()

# _updated tracks whether we have fetched new entries from wiktionary
# (and therefore need to re-dump to json)
definitions = {"_updated": False}


# Local files

project_dir = Path(os.path.dirname(__file__), "../..")


def load_wfs(lang: Lang) -> list[tuple[str, int]]:
    with open(project_dir / f"languages/{lang}/frequencies_raw.csv", "r") as f:
        return list(csv.reader(f))


def load_all_defs(lang: Lang) -> dict[Word, WiktionaryFetchResult]:
    with open(project_dir / f"languages/{lang}/definitions.json", "r") as f:
        return json.load(f)


# Open Subtitles


def get_words_path(lang: Lang) -> str:
    return f"https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/{lang}/{lang}_full.txt"


def read_wf_line(line: str) -> tuple[str, int]:
    """E.g.: 'word 123' -> `['word', 123]`"""

    [word, count] = line.rsplit(" ", maxsplit=1)
    return word, int(count)


def read_wfs(list: str) -> list[tuple[str, int]]:
    return [read_wf_line(line) for line in list.split("\n") if line]


def fetch_wfs(lang: Lang) -> list[tuple[str, int]]:
    return read_wfs(requests.get(get_words_path(lang)).text)


def save_wfs(lang: Lang, wfs) -> None:
    with open(project_dir / f"languages/{lang}/frequencies_raw.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(wfs)


# Wiktionary


def get_long_lang(lang: Lang) -> str:
    return LANGUAGES[lang]


def fetch_defs(word: Word, lang: Lang) -> list[WiktionaryFetchResult]:
    try:
        return parser.fetch(word, get_long_lang(lang))
    except (KeyError, AttributeError) as e:
        # pt entries are missing "class" somewhere in pronunciation
        # ko entries are missing a "name" attribute somewhere
        print(f"Error fetching/parsing {word} from {lang}", e, file=sys.stderr)
        return []


# CLI

def get_or_create_language_dir(lang: str) -> Path:
    dirpath = project_dir / f"languages/{lang}"

    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)

    return dirpath


def get_wfs(lang: Lang) -> list[tuple[str, int]]:
    """Try to load the words from the local file, otherwise fetch them from Open Subtitles."""

    if os.path.isfile(get_or_create_language_dir(lang) / "frequencies_raw.csv"):
        wfs = load_wfs(lang)
    else:
        wfs = fetch_wfs(lang)
        save_wfs(lang, wfs)

    return wfs


def get_words(lang: Lang) -> list[str]:
    return [word[0] for word in get_wfs(lang)]


def enrich_def(def_: WiktionaryDefinition) -> EnrichedWiktionaryDefinition:
    return def_


def get_ipa(maybe_ipa: str) -> list[str] | None:
    """Regex match against `"IPA: /abc/"`"""
    if "IPA: " in maybe_ipa:
        prefix, raw_ipa = maybe_ipa.split("IPA: ", maxsplit=1)

        detail = re.search(r"\((.+)\)", prefix)
        detail = detail and detail.group(1) or ""

        ipas = re.findall(r"(?:\((.*?)\) )?(?:IPA: )?([\/\[]].*?[\/\]])", raw_ipa)

        return [
            {"ipa": ipa, "kind": detail, "extra": extra} for (extra, ipa) in ipas if ipa
        ]

    return None


def enrich_pronunciation(
    pronunciation: WiktionaryPronunciation,
) -> EnrichedWiktionaryPronunciation:
    """We enrich *after* loading from the save & not before because this
    enricher isn't perfect, and it's changing regularly."""

    ipa = []
    text = []

    for maybe_ipa in pronunciation["text"]:
        matches = get_ipa(maybe_ipa)

        # TODO: Move this extra processing into a fork of wiktionaryparser
        if matches:
            ipa.extend(matches)
        elif maybe_ipa.startswith("Hyphenation: "):
            pronunciation["hyphenation"] = maybe_ipa[len("Hyphenation: ") :].split(", ")
        elif maybe_ipa.startswith("Rhymes: "):
            pronunciation["rhymes"] = maybe_ipa[len("Rhymes: ") :].split(" ")
        elif maybe_ipa.startswith("Homophone: "):
            pronunciation["homophones"] = maybe_ipa[len("Homophone: ") :].split(", ")
        elif maybe_ipa.startswith("Homophones: "):
            pronunciation["homophones"] = maybe_ipa[len("Homophones: ") :].split(", ")

        else:
            text.append(maybe_ipa)

    pronunciation["ipa"] = ipa
    pronunciation["text"] = text

    return pronunciation


def enrich(result: WiktionaryFetchResult) -> EnrichedWiktionaryFetchResult:
    result["definitions"] = [enrich_def(def_) for def_ in result["definitions"]]
    result["pronunciations"] = enrich_pronunciation(result["pronunciations"])
    return result


def load_defs(word: Word, lang: Lang, **kwargs) -> None:
    # If the word is not in the definitions dict, fetch it from Wiktionary.
    # Then store it in the definitions dict.
    if word not in definitions:
        definitions["_updated"] = True
        definitions[word] = {"defs": fetch_defs(word, lang), **kwargs}


def save_defs(lang: Lang) -> None:
    if not definitions["_updated"]:
        return

    with open(f"../languages/{lang}/definitions.json", "w") as f:
        definitions["_updated"] = False
        json.dump(definitions, f)


def wfs_to_defs(lang: str, num: int, save_every: int = 100):
    wfs = get_wfs(lang)[:num]
    enriched_defs = {}

    # Initialize the definitions dict above from a save if a save exists.
    language_dir = get_or_create_language_dir(lang)
    if os.path.isfile(language_dir / f"definitions.json"):
        with open(language_dir / "definitions.json", "r") as f:
            print(f"    {lang}: Loading from save...", file=sys.stderr)
            definitions.update(json.load(f))

    pbar = tqdm(wfs, desc=f"    {lang}: Defining...")
    for i, (word, count) in enumerate(pbar):
        load_defs(word, lang, rank=i, count=count)
        enriched_defs[word] = [enrich(result) for result in definitions[word]["defs"]]
        pbar.set_description(f"    {lang}: Defining '{word}'...")

        # Save the definitions to a file every 10 words.
        # (Fetching from wiktionary is slow, >1s per word.)
        if i > 0 and i % save_every == 0:
            pbar.set_description(f"    {lang}: Dumping...")
            save_defs(lang)

    save_defs(lang)

    # Use in combination with, e.g., jq as in `python from_os en | jq`
    return enriched_defs


# typer doesn't accept literal values
def main(lang: str, num: int = typer.Option(default=3)):

    if lang == "all":
        print("{")

        pbar = tqdm(LANGUAGES, desc="Iterating over languages...")
        for lang in pbar:
            pbar.set_description(f"Defining {lang}...")
            print(f'"{lang}": {json.dumps(wfs_to_defs(lang, num))},')
            definitions.clear()
            definitions.update({"_updated": False})

        print("}")
    else:
        enriched_defs = wfs_to_defs(lang, num)

        # Use in combination with, e.g., jq as in `python from_os en | jq`
        print(json.dumps(enriched_defs, indent=2))


if __name__ == "__main__":
    typer.run(main)
