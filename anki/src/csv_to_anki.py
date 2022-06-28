import csv
from pathlib import Path
from pprint import pp
import ssl

from bs4 import BeautifulSoup
import typer
import plotext as plt

from ddgi import get_ddgi_results

FIELDS = ["word", "english", "part_of_speech", "notes", "related"]

def plot_images(word, results):
    safe_word = word.strip().lower().replace(" ", "_").replace("'", "")

    # Required to make `download` behave
    ssl._create_default_https_context = ssl._create_unverified_context

    for i, result in enumerate(results):
        path = "/tmp/{}-{}.jpg".format(safe_word, i)
        plt.download(result["thumbnail"][:-8], path)
        plt.image_plot(path)
        plt.show()
        plt.delete_file(path)
        # plt.delete_file(path)

def main(src: Path, lang: str):
    with open(src, "r") as f:
        reader = csv.reader(f)

        fields = next(reader)
        safe_fields = [f.strip().replace(" ", "_").lower() for f in fields][:-1]

        assert safe_fields == FIELDS, f"Fields do not match {safe_fields} {FIELDS}"

        for _row in reader:
            row = [item.strip() for item in _row]
            row_dict = {k: v for k, v in zip(safe_fields, row)}
            images =get_ddgi_results(row_dict["word"], 5, lang=lang)
            pp(row_dict)
            pp(images)
            plot_images(row_dict["word"], images)

if __name__ == "__main__":
    typer.run(main)