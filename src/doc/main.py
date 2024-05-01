import os
from pptx import Presentation
from pptx.util import Pt
from pathlib import Path
from docx.text.run import Run

# import docx2txt
from docx import Document
from docx.shared import StoryChild
from docx.styles.style import ParagraphStyle
from docx.text.hyperlink import Hyperlink
from docx.text.pagebreak import RenderedPageBreak
from docx.text.parfmt import ParagraphFormat

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
        for content in paragraph.iter_inner_content():
            font_sizes = []
            if isinstance(content, Run):
                font_size = content.style.font.size
                font_sizes.append(font_size)

            elif isinstance(content, Hyperlink):
                font_size = content.style.font.size
                lines.append(f"{font_size}: {content.text}")
            else:
                assert False

            if len(content.text.strip()) == 0:
                continue

            # lines.append(f"{max(font_sizes)}: {content.text}")

        if len(paragraph.text.strip()) == 0:
            continue

        font_size = paragraph.style.font.size
        lines.append(f"{font_size}: {paragraph.text}")

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
