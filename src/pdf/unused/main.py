import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from pprint import pformat

import utils.annotator as annotator
import fitz
import pandas as pd
from structural_chunking.markdown import custom_markdown, orig_markdown


@dataclass
class Line:
    score: float
    text: str


@dataclass
class Chunk:
    score: float
    features: dict
    text: str = ""
    # lines: list[Line] = field(default_factory=list)


@dataclass
class Page:
    text: str
    chunks: list[Chunk] = field(default_factory=list)


def flags_decomposer(flags):
    l = []
    if flags & 2**0:
        l.append("superscript")
    if flags & 2**1:
        l.append("italic")
    if flags & 2**2:
        l.append("serifed")
    else:
        l.append("sans")
    if flags & 2**3:
        l.append("monospaced")
    else:
        l.append("proportional")

    if flags & 2**4:
        l.append("bold")

    return ", ".join(l)


def is_bold(span):
    return int((span["flags"] & 2**4) == 16)


def is_superscript(span):
    return int(span["flags"] & 1) == 1


def calculate_line_score(bbox, l):
    s = l["spans"][0]

    first_span_style = {
        "name": s["font"],
        "style": flags_decomposer(s["flags"]),
        "size": s["size"],
        "colour": s["color"],
    }

    x = bbox[0]
    y = bbox[1]
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]

    score_weights = {"size": 1.0, "bold": 1.0, "x": 1.0}
    score = (
        score_weights["size"] * first_span_style["size"]
        + score_weights["bold"] * is_bold(s)
        + score_weights["x"] * x  # / page_width
    )
    features = {
        "size": first_span_style["size"],
        "bold": is_bold(s),
        "x": x,  # / page_width,
        "y": y,  # / page_height,
        "width": width,
        "height": height,
        "bbox": bbox,
    }

    return score, features


def format_outline(outline, level):
    result = ""
    while outline:
        indent = "\t" * level
        result += f"{indent}{outline.title}\n"
        if outline.down:
            result += format_outline(outline.down, level=level + 1)
        outline = outline.next

    return result


def block_filter(block):
    return block["type"] != 0


def block_text_filter(text):
    text = text.strip()

    if len(text) <= 1:
        return True

    if len(re.findall(r"^\d+%?$", text)) == 1:
        # e.g. 12%
        return True

    return False


def line_filter(line):
    if line["wmode"] == 1 or line["dir"] != (1.0, 0.0):
        return True

    text = "".join([span["text"] for span in line["spans"]]).strip()

    if len(text) <= 1:
        return True

    # for span in line["spans"]:
    #     if len(text) <= 1:
    #         return True

    return False


def collect_source_references(line, block, references):
    for span_index, span in enumerate(line["spans"]):
        if span_index == 0:
            if span["text"].isdigit() and span["text"] in references:
                reference = references[span["text"]]
                # if 'number' in reference:

                if (
                    reference["font"] == span["font"]
                    and reference["size"] == span["size"]
                ):
                    references[span["text"]] = block
            if is_superscript(span):
                reference_id = span["text"].strip()
                assert reference_id not in references
                references[reference_id] = line["spans"]
        else:
            if is_superscript(span) and span["text"].isdigit():
                references[span["text"].strip()] = span

    return None


def load_text(pdf) -> list[Page]:
    results_pages = []

    for page_index, pdf_page in enumerate(pdf.pages()):
        page_dict = pdf_page.get_text("dict")
        page = Page(text=pdf.get_page_text(page_index))

        page_width = page_dict["width"]

        for b in page_dict["blocks"]:
            if block_filter(b):
                continue

            block_text_list = []
            for l in b["lines"]:
                if line_filter(l):
                    continue

                # collect_source_references(l, b, references)

                score, features = calculate_line_score(bbox=b["bbox"], l=l)

                block_text_list.append("".join([s["text"] for s in l["spans"]]))

            block_text = "\n".join(block_text_list).strip()
            if block_text_filter(block_text):
                continue

            chunk = Chunk(score=score, features=features, text=block_text)

            page.chunks.append(chunk)

        results_pages.append(page)

    return results_pages


def collapse_lines(pages):
    result_pages = []

    for page in pages:
        result_blocks = []

        for block in page:
            result_lines = []
            reference_line = None

            for line in block:
                if reference_line and line["style"] == reference_line["style"]:
                    reference_line["text"] = f"{reference_line['text']} {line['text']}"
                else:
                    reference_line = line
                    result_lines.append(reference_line)

            result_blocks.append(result_lines)

        result_pages.append(result_blocks)

    return result_pages


def collapse_blocks(pages):
    result_pages = []

    for page in pages:
        result_blocks = []
        reference_block = None

        for block in page:
            if reference_block:
                if reference_block[-1]["style"] == block[0]["style"]:
                    ...
            else:
                reference_block == block

            result_lines = []

            result_blocks.append(result_lines)

        result_pages.append(result_blocks)

    return result_pages


def export_blocks(output_base, document):
    data = {
        "page": [],
        "chunk": [],
        "score": [],
        "size": [],
        "bold": [],
        "x": [],
        "y": [],
        "width": [],
        "height": [],
        "text": [],
        "bbox": [],
    }

    for page_index, page in enumerate(document):
        for chunk_pos, chunk in enumerate(page.chunks):
            data["page"].append(page_index)
            data["chunk"].append(chunk_pos)
            data["score"].append(chunk.score)
            data["size"].append(chunk.features["size"])
            data["bold"].append(chunk.features["bold"])
            data["x"].append(chunk.features["x"])
            data["y"].append(chunk.features["y"])
            data["width"].append(chunk.features["width"])
            data["height"].append(chunk.features["height"])
            data["text"].append(chunk.text)
            data["bbox"].append(chunk.features["bbox"])

    output_path = output_base / "blocks.csv"
    output_df = pd.DataFrame(data=data)
    output_df.to_csv(output_path, index=None, quoting=csv.QUOTE_ALL)

    return output_df


def export_page_text(output_base, document):
    page_text_path = output_base / "page_text.csv"
    page_text_data = [page.text for page in document]
    page_text_df = pd.DataFrame(data=page_text_data)
    page_text_df.to_csv(page_text_path, index=None, quoting=csv.QUOTE_ALL)


def export_misc(output_base, misc_df):
    misc_path = output_base / "misc.csv"
    misc_df.to_csv(misc_path, index=None, quoting=csv.QUOTE_ALL)


def export_orig_markdown(output_base, pdf):
    md_text = custom_markdown.to_markdown(pdf)

    (output_base / "export.md").write_text(md_text)


def export_orig_markdown(output_base, pdf):
    # from pdf4llm import to_markdown
    from structural_chunking.markdown.orig_markdown import to_markdown

    md_text = orig_markdown.to_markdown(pdf)

    (output_base / "orig_export.md").write_text(md_text)


def load_misc(pdf):
    misc_data = {
        "id_pdf": pdf.is_pdf,
        "metadata": pformat(pdf.metadata, indent=2),
        "toc": pformat(
            [
                {
                    "level": level,
                    "title": title,
                    "page": page,
                    "destination": destination,
                }
                for level, title, page, destination in pdf.get_toc(False)
            ],
            indent=2,
        ),
        "has_annotations": pdf.has_annots(),
        # "outline": format_outline(pdf.outline, level=0),
        "chapter_count": pdf.chapter_count,
        "page_labels": pdf.get_page_labels(),
        "page_layout": pdf.pagelayout,
        "page_mode": pdf.pagemode,
    }

    misc_df = pd.Series(data=misc_data).to_frame().transpose()

    return misc_df


def process_file(input_path):
    pdf = fitz.open(str(input_path))

    misc_df = load_misc(pdf)

    output_base = Path(__file__).parents[2] / "output" / input_path
    output_base.mkdir(parents=True, exist_ok=True)

    should_export_orig_markdown = True

    if should_export_orig_markdown:
        export_orig_markdown(output_base, pdf)

    # should_export_markdown = True

    # if should_export_markdown:
    #     export_markdown(output_base, pdf)

    should_export_blocks = True

    if should_export_blocks:
        document = load_text(pdf)
        blocks_df = export_blocks(output_base=output_base, document=document)
        export_page_text(output_base=output_base, document=document)
        export_misc(output_base=output_base, misc_df=misc_df)

    create_page_annotations = False

    if create_page_annotations:
        pdf_bytes = input_path.read_bytes()

        annotator.annotate_from_df(
            blocks_df=blocks_df,
            pdf_path=input_path,
            pdf_bytes=pdf_bytes,
            output_path=output_base / "annotations",
        )


def _main():
    data_path = Path(__file__).parents[2] / "data"
    for input_path in data_path.glob("**/JPM*.pdf"):
        process_file(input_path=input_path)


if __name__ == "__main__":
    _main()
