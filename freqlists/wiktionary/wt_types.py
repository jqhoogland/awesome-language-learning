
from typing import Literal, TypedDict

Word = str
Lang = Literal[
    'en',
    'es',
    'fr',
    'de',
    'it',
    'pt',
    'ja',
    'ko',
    'zh',
    'nl',
    'sv',
    'fi',
    'no',
    'da',
    'is',
    'pl',
    'hu',
    'cs',
    'ro',
    'ru',
    'tr',
    'hr',
    'el',
    'he',
    'ar',
    'hi',
    'th',
    'uk',
    'id',
    'fa',
    'bn',
    'vi',
    'sr',
    'sk',
    'sl',
    'eo',
    'tl',
    'ms',
    'km',
    'lo',
    'bo',
    'my',
    'ka',
    'ti',
    'gu',
    'kn',
    'ml',
    'or',
    'pa',
    'as',
    'mr',
    'sa',
    'ne',
    'ta',
    'te',
    'si',
    'am',
    'kmr',
    'az',
]

PartOfSpeech = Literal[
    "noun", "verb", "adjective", "adverb", "determiner",
    "article", "preposition", "conjunction", "proper noun",
    "letter", "character", "phrase", "proverb", "idiom",
    "symbol", "syllable", "numeral", "initialism", "interjection", 
    "definitions", "pronoun",
]

RelationshipType = Literal[
    "synonyms", "antonyms", "hypernyms", "hyponyms",
    "meronyms", "holonyms", "troponyms", "related terms",
    "coordinate terms",
]

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
