from pathlib import Path

import re
from tqdm import tqdm

from tika import parser
from markdownify import markdownify
from bs4 import BeautifulSoup

from utils import text_skipping


def to_html(input_file):
    parsed = parser.from_file(str(input_file), xmlContent=True)
    # metadata = parsed["metadata"]
    result = parsed["content"]

    return result


def to_markdown(html):
    markdown = markdownify(html, strip=["meta"])

    return markdown


def trim_tag(tag):
    if tag is None:
        return False
    return not tag.contents and not tag.name == "br"


def clean_html(html):
    soup = BeautifulSoup(html, features="lxml")
    # soup.smooth()

    p = soup.find_all("p")

    for x in soup.find_all():
        text = x.text.strip()

        if text_skipping.should_skip(text):
            # delete this tag
            x.decompose()
        else:
            text = text.replace("\n", " ")
            x.string = text

    clean = soup.prettify("utf-8")

    return clean


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
        (output_dir / f"{input_file.name}.html").write_text(html)


if __name__ == "__main__":
    _main()
