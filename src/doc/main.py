import os
from pptx import Presentation
from pptx.util import Pt
from pathlib import Path

# import docx2txt
from docx import Document

# text = docx2txt.process(input_file)


def header_to_markdown(header):
    lines = []
    for paragraph in header.paragraphs:
        lines.append(paragraph.text)

    return lines


def to_markdown(input_file):
    document = Document(input_file)

    lines = []
    for paragraph in document.paragraphs:
        lines.append(paragraph.text)

    for section in document.sections:
        lines += header_to_markdown(section.header)
        for section_inner in section.iter_inner_content():
            print(section_inner.text)

    for table in document.tables:
        lines.append(table.text)

    return "\n".join(lines)


def _main():
    data_dir = Path(__file__).parents[2] / "data"
    input_filename = data_dir / "sample.docx"
    output = to_markdown(input_file=input_filename)

    print(output)

    output_dir = Path(__file__).parents[2] / "output" / f"{input_filename.name}.md"
    output_dir.write_text(output)


if __name__ == "__main__":
    _main()
