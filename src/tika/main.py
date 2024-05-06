from pathlib import Path

import re
from tqdm import tqdm

from tika import parser
from markdownify import markdownify
from bs4 import BeautifulSoup

from utils import text_skipping


def to_html(input_file):
    parsed = parser.from_file(str(input_file), xmlContent=True)
    result = parsed["content"]

    return result


def clean_html(html):
    soup = BeautifulSoup(html, features="lxml", preserve_whitespace_tags=["p"])

    for x in soup.find_all():
        # if x.name in ["html", "body", "head", "meta", "div"]:
        #     continue

        text = x.text.strip()

        if text_skipping.should_skip(text):
            # if (
            #     x.text.startswith("0")
            # or x.name == "div"
            # and "page" in x.attrs["class"]
            # or text_skipping.should_skip(text)
            # ):
            # delete this tag
            x.decompose()
        # else:
        # text = text.replace("\n", " ")
        # x.string = text

    # for x in soup.find_all():
    #     text = x.text.strip()
    #     x.string = text

    soup.smooth()
    clean = soup.prettify()  # "utf-8", formatter="minimal")

    # clean = str(clean)

    return clean


def to_markdown(html):
    markdown = markdownify(html, strip=["meta"])

    return markdown


def _main():
    base_dir = Path(__file__).parents[2]
    data_dir = base_dir / "data"

    for input_file in tqdm(
        [
            data_dir / "JPM Electravision 14th Annual Energy Paper 20240305.pdf",
            data_dir / "sample.docx",
            data_dir / "sample.pptx",
        ]
    ):
        html = to_html(input_file)
        cleaned_html = clean_html(html)
        markdown = to_markdown(cleaned_html)

        output_dir = base_dir / "output" / "tika"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{input_file.name}.md").write_text(markdown)
        (output_dir / f"{input_file.name}.html").write_text(cleaned_html)
        (output_dir / f"{input_file.name}.raw.html").write_text(html)


if __name__ == "__main__":
    _main()
