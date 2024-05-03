from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter
import fitz
from pprint import pprint
from utils import text_skipping


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


def parse_page(page, score_counter, skip_counter) -> Page:
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
                if text_skipping.should_skip(text):
                    skip_counter[text] += 1
                    continue

                lines.append(current_line)

            else:
                current_line.spans += spans

        block = Block(lines=lines)
        blocks.append(block)

    return Page(blocks=blocks, scores=list(sorted(scores, reverse=True)))


def render(page: Page, level_for_score: dict, skip_counter: Counter):
    results = []

    # most common font size == body (no #)
    for block in page.blocks:
        for line in block.lines:
            text = " ".join([span.text for span in line.spans]).strip()

            if text_skipping.should_skip(text):
                skip_counter[text] += 1
                continue

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


def to_markdown(input_file):
    doc = fitz.open(input_file)

    score_counter = Counter()

    pages = [parse_page(page, score_counter) for page in doc.pages()]

    level_for_score = calculate_heading_levels(score_counter)

    rendered_lines = []
    skip_counter = Counter()

    for page_index, page in enumerate(pages):
        # rendered_lines.append(f"PAGE {page_index +1}")
        rendered_lines += render(page, level_for_score, skip_counter=skip_counter)

    rendered = "\n".join(rendered_lines)

    pprint(skip_counter.most_common())

    return rendered


def _main():
    base_dir = Path(__file__).parents[2]
    data_dir = base_dir / "data"
    input_file = data_dir / "JPM Electravision 14th Annual Energy Paper 20240305.pdf"

    output = to_markdown(input_file=input_file)

    output_dir = base_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{input_file.name}.md"
    output_file.write_text(output)


if __name__ == "__main__":
    _main()
