from pathlib import Path

import re
from tqdm import tqdm

from tika import parser
from html.parser import HTMLParser
from markdownify import markdownify
import xml.sax
from bs4 import BeautifulSoup


def to_html(input_file):
    parsed = parser.from_file(str(input_file), xmlContent=True)
    # metadata = parsed["metadata"]
    result = parsed["content"]

    return result


def to_markdown(html):
    markdown = markdownify(html, strip=["meta"])

    return markdown


def clean_html(html):
    soup = BeautifulSoup(html)
    # soup.smooth()

    # findtoure = clean.find_all(text=re.compile("Gnegneri Toure Yaya"))
    # fixed_comments = []
    # for comment in findtoure:
    #     fixed_text = comment.replace("Gnegneri Toure Yaya", "Yaya Toure")
    #     comment.replace_with(fixed_text)
    #     fixed_comments.append(fixed_text)

    a = soup.find_all("p", string=re.compile(r"\w{,3}"))
    # .replace_with(
    #     "***********************************"
    # )

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
