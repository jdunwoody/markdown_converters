from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter

import fitz
import pandas as pd


@dataclass
class Span:
    score: float
    text: str


@dataclass
class Line:
    score: float
    spans: list = field(default_factory=list)


@dataclass
class Block:
    lines: list[Line] = field(default_factory=list)


@dataclass
class Page:
    scores: list[float] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)


def parse_page(page, score_counter) -> Page:
    max_score = None
    min_score = None
    scores = set()

    blocks = []

    for b in page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]:
        lines = []

        current_line = None

        for l in b["lines"]:
            spans = []

            for s in l["spans"]:
                text = s["text"].strip()
                if len(text) == 0:
                    continue

                # font_size = f"{s['size']:0.2}"
                score = round(s["size"])

                if max_score is None or score > max_score:
                    max_score = score

                if min_score is None or score < min_score:
                    min_score = score

                span = Span(score=score, text=text)

                spans.append(span)

            if len(spans) == 0:
                continue

            max_span_score = max([s.score for s in spans])
            scores.add(max_span_score)
            score_counter.update([max_span_score])

            line_score = max_span_score

            if current_line is None or current_line.score != line_score:
                current_line = Line(score=line_score, spans=spans)
                lines.append(current_line)

            else:
                current_line.spans += spans

        block = Block(lines=lines)
        blocks.append(block)

    return Page(blocks=blocks, scores=list(sorted(scores, reverse=True)))


def render(page: Page, level_for_score: dict):
    results = []

    # most common font size == body (no #)
    for block in page.blocks:
        for line in block.lines:
            text = " ".join([span.text for span in line.spans])

            prefix = level_for_score[line.score]

            results.append(f"{prefix} {text}")

    return results


def calculate_heading_levels(score_counter):
    body_score = score_counter.most_common(1)[0][0]
    heading_score_levels = sorted(score_counter.keys(), reverse=True)
    level_for_score = {}
    max_heading_levels = 6

    for index, score in enumerate(heading_score_levels):
        if score <= body_score or index >= max_heading_levels:
            level_for_score[score] = ""
        else:
            level_for_score[score] = "#" * (index + 1)

    return level_for_score


def _main(input_filename, output_path):
    doc = fitz.open(input_filename)

    score_counter = Counter()

    pages = [parse_page(page, score_counter) for page in doc.pages()]

    level_for_score = calculate_heading_levels(score_counter)

    rendered_lines = []

    for page_index, page in enumerate(pages):
        rendered_lines.append(f"PAGE {page_index +1}")
        rendered_lines += render(page, level_for_score)

    rendered = "\n".join(rendered_lines)

    (output_path / f"{input_filename.name}.md").write_text(rendered)

    return pages


if __name__ == "__main__":
    data_path = Path(__file__).parents[3] / "data"
    output_path = Path(__file__).parents[3] / "output"

    _main(
        input_filename=data_path
        / "JPM Electravision 14th Annual Energy Paper 20240305.pdf",
        output_path=output_path,
    )
