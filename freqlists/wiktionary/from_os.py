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
from typing import Literal, TypedDict
from pathlib import Path
import csv
import requests
from pprint import pp

from tqdm import tqdm
from googletrans import Translator
import typer
import wiktionaryparser as wp

translator = Translator()
parser = wp.WiktionaryParser()
definitions = {}

LANGUAGES = {
    'en': 'english',
    'es': 'spanish',
    'fr': 'french',
    'de': 'german',
    'it': 'italian',
    'pt': 'portuguese',
    'ja': 'japanese',
    'ko': 'korean',
    'zh': 'chinese',
    'nl': 'dutch',
    'sv': 'swedish',
    'fi': 'finnish',
    'no': 'norwegian',
    'da': 'danish',
    'is': 'icelandic',
    'pl': 'polish',
    'hu': 'hungarian',
    'cs': 'czech',
    'ro': 'romanian',
    'ru': 'russian',
    'tr': 'turkish',
    'hr': 'croatian',
    'el': 'greek',
    'he': 'hebrew',
    'ar': 'arabic',
    'hi': 'hindi',
    'th': 'thai',
    'uk': 'ukrainian',
    'id': 'indonesian',
    'fa': 'persian',
    'bn': 'bengali',
    'vi': 'vietnamese',
    'sr': 'serbian',
    'sk': 'slovak',
    'sl': 'slovenian',
    'eo': 'esperanto',
    'tl': 'tagalog',
    'ms': 'malay',
    'km': 'khmer',
    'lo': 'lao',
    'bo': 'tibetan',
    'my': 'myanmar',
    'ka': 'georgian',
    'ti': 'tigrinya',
    'gu': 'gujarati',
    'kn': 'kannada',
    'ml': 'malayalam',
    'or': 'oriya',
    'pa': 'punjabi',
    'as': 'assamese',
    'mr': 'marathi',
    'sa': 'sanskrit',
    'ne': 'nepali',
    'ta': 'tamil',
    'te': 'telugu',
    'si': 'sinhala',
    'am': 'amhara',
    'kmr': 'kurdish',
    'az': 'azerbaijani',
}

Word = str
Lang = Literal['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh']
RelationshipType = Literal['synonyms', "related terms"]
PartOfSpeech = Literal['noun', 'verb', 'adjective', 'adverb', 'pronoun', 'conjunction', 'preposition', 'article', 'determiner', 'numeral', 'interjection', 'interrogative', 'exclamation', 'question', 'particle']

class WiktionaryRelatedWord(TypedDict):
    relationshipType: RelationshipType
    words: list[Word]

class WiktionaryPronunciation(TypedDict):
    text: list[str]
    audio: list

class WiktionaryDefinition(TypedDict):
    partOfSpeech: PartOfSpeech
    text: list[str]
    relatedWords: list[WiktionaryRelatedWord]
    examples: list[str]

class WiktionaryFetchResult(TypedDict):    
    etymology: str
    definitions: list[WiktionaryDefinition]
    pronunciation: list[WiktionaryPronunciation]


class EnrichedWiktionaryDefinition(TypedDict):
    partOfSpeech: PartOfSpeech

    #: ['<word>', 'some derived form of <some-other-word>'+]
    text: list[str]
    relatedWords: list[WiktionaryRelatedWord]
    examples: list[str]
    lemmas: list[str]
    translations: list[str]
    pronunciations: list[str]


class EnrichedWiktionaryPronunciation(TypedDict):
    text: list[str]

class EnrichedWiktionaryFetchResult(TypedDict):
    etymology: str
    definitions: list[EnrichedWiktionaryDefinition]
    pronunciation: list[EnrichedWiktionaryPronunciation]


# Local files

project_dir = Path(os.path.dirname(__file__), "../..")


def load_wfs(lang: Lang) -> list[tuple[str, int]]:
    with open(project_dir / f'languages/{lang}/frequencies_raw.csv', 'r') as f:
        return list(csv.reader(f))


def load_all_defs(lang: Lang) -> dict[Word, WiktionaryFetchResult]:
    with open(project_dir / f'languages/{lang}/definitions.json', 'r') as f:
        return json.load(f)


# Open Subtitles


def get_words_path(lang: Lang) -> str:
    return f"https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/{lang}/{lang}_full.txt"


def read_wf_line(line: str) -> tuple[str, int]: 
    """E.g.: 'word 123' -> `['word', 123]`"""
    [word, count] = line.split(" ")
    return word, int(count)


def read_wfs(list: str) -> list[tuple[str, int]]:
    return [read_wf_line(line) for line in list.split("\n") if line]


def fetch_wfs(lang: Lang) -> list[tuple[str, int]]:
    return read_wfs(requests.get(get_words_path(lang)).text)


def save_wfs(lang: Lang, wfs) -> None:
    with open(project_dir / f'languages/{lang}/frequencies_raw.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(wfs)

# Wiktionary

def get_long_lang(lang: Lang) -> str:
    return LANGUAGES[lang]


def fetch_defs(word: Word, lang: Lang) -> list[WiktionaryFetchResult]:
    print(f"Fetching definitions for {word} from wiktionary...", file=sys.stderr)
    return parser.fetch(word, get_long_lang(lang))

# CLI


def get_words(lang: Lang) -> list[str]:
    """Try to load the words from the local file, otherwise fetch them from Open Subtitles."""
    if os.path.isfile(project_dir / f'languages/{lang}/frequencies_raw.csv'):
        wfs = load_wfs(lang)
    else:
        wfs = fetch_wfs(lang)
        save_wfs(lang, wfs)

    return [word[0] for word in wfs]


def enrich_def(def_: WiktionaryDefinition) -> EnrichedWiktionaryDefinition:
    return def_


def get_ipa(maybe_ipa: str) -> list[str] | None:
    """ Regex match against `"IPA: /abc/"` """
    if "IPA" in maybe_ipa:
        prefix, raw_ipa  = maybe_ipa.split("IPA: ")
        
        detail = re.search(r"\((.+)\)", prefix)
        detail = detail and detail.group(1) or ""

        ipas = re.findall(r"(?:\((.*?)\) )?\/(.*?)\/", raw_ipa)
        return [{"ipa": ipa, "kind": detail, "extra": extra} for (extra, ipa) in ipas if ipa]


    return None



def enrich_pronunciation(pronunciation: WiktionaryPronunciation) -> EnrichedWiktionaryPronunciation:
    ipa = []
    text = []

    for maybe_ipa in pronunciation['text']:
        matches = get_ipa(maybe_ipa)

        if matches:
            ipa.extend(matches)
        elif maybe_ipa.startswith('Hyphenation: '):
            pronunciation['hyphenation'] = maybe_ipa[len('Hyphenation: '):]
        elif maybe_ipa.startswith('Rhymes: '):
            pronunciation['rhymes'] = maybe_ipa[len('Rhymes: '):].split(' ')
        elif maybe_ipa.startswith('Homophone: '):
            pronunciation['homophones'] = maybe_ipa[len('Homophone: '):].split(', ')
        elif maybe_ipa.startswith('Homophones: '):
            pronunciation['homophones'] = maybe_ipa[len('Homophones: '):].split(', ')
        else:
            text.append(maybe_ipa)

    pronunciation["ipa"] = ipa
    pronunciation["text"] = text

    return pronunciation


def enrich(result: WiktionaryFetchResult) -> EnrichedWiktionaryFetchResult:
    result['definitions'] = [enrich_def(def_) for def_ in result['definitions']]
    result['pronunciations'] = enrich_pronunciation(result['pronunciations'])
    return result

def get_defs(word: Word, lang: Lang, rank: int) -> list[WiktionaryFetchResult]:

    # Initialize the definitions dict above from a save if it hasn't been initialized
    # and a save exists.
    if not definitions and os.path.isfile(f'../languages/{lang}/definitions.json'):
        with open(f'../languages/{lang}/definitions.json', 'r') as f:
            print("Loading definitions from save...", file=sys.stderr)
            definitions.update(json.load(f))

    # If the word is not in the definitions dict, fetch it from Wiktionary.
    # Then save it to the definitions dict.
    if word not in definitions:
        defs = fetch_defs(word, lang)
        definitions[word] = {
            "rank": rank,
            "defs": defs
        }

        with open(f'../languages/{lang}/definitions.json', 'w') as f:
            print("Dumping definitions to save...", file=sys.stderr)
            json.dump(definitions, f)
    
    # Otherwise load it from the definitions dict.
    else:
        defs = definitions[word]

    # Enrich after loading the definition with extra information
    return [enrich(result) for result in defs['defs']]


# typer doesn't accept literal values
def main(lang: str, num: int = typer.Option(default=3)):
    words = get_words(lang)[:num]
    
    defs = {}

    for i, word in enumerate(tqdm(words, desc="Getting definitions...")):
        _defs = get_defs(word, lang, rank=i)
        defs[word] = _defs


    print(json.dumps(defs, indent=2))

if __name__ == "__main__":
    typer.run(main)
