"""Given a word-frequency .csv, this converts the file into  """

from typing import Literal
from pathlib import Path
import csv

from tqdm import tqdm
from googletrans import Translator
import typer

translator = Translator()


def get_translation_query(
    lang: str,
    *,
    word: str,
    part_of_speech: Literal[
        "Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Conjunction", "Preposition"
    ],
    **kwargs
):
    # Prepend `the` so we see the gender of the word
    if part_of_speech == "Noun":
        return "the " + word

    return word


def main(src: Path, lang: str):
    header = []
    data = []
    translation_queries = []

    with open(src, "r") as f:
        reader = csv.reader(f)

        fields = next(reader)
        safe_fields = [f.strip().replace(" ", "_").lower() for f in fields]
        header = [lang, "en", *fields[1:]]

        for _row in reader:
            row = [item.strip() for item in _row]

            translation_query = get_translation_query(
                lang, **{k: v for k, v in zip(safe_fields, row)}
            )
            data.append(row)
            translation_queries.append(translation_query)

    translations = [t.text for t in translator.translate(translation_queries, src="en", dest=lang)]
    body = [[translation, *row] for translation, row in zip(translations, data)]

    with open(str(src).replace("en", lang), "w") as f:
        writer = csv.writer(f)
        writer.writerows(
            [
                header,
                *body,
            ]
        )


if __name__ == "__main__":
    typer.run(main)
