import string
from pathlib import Path
import fitz


class IdentifyHeaders:

    def __init__(self, doc, body_limit: float = None):
        SPACES = set(string.whitespace)

        pages = doc.pages

        fontsizes = {}

        for pno in pages:
            page = doc[pno]
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
            for span in [  # look at all non-empty horizontal spans
                s
                for b in blocks
                for l in b["lines"]
                for s in l["spans"]
                if not SPACES.issuperset(s["text"])
            ]:
                fontsz = round(span["size"])
                count = fontsizes.get(fontsz, 0) + len(span["text"].strip())
                fontsizes[fontsz] = count

        self.header_id = {}

        if body_limit is None:
            body_limit = sorted(
                [(k, v) for k, v in fontsizes.items()],
                key=lambda i: i[1],
                reverse=True,
            )[0][0]

        sizes = sorted([f for f in fontsizes.keys() if f > body_limit], reverse=True)

        for i, size in enumerate(sizes):
            self.header_id[size] = "#" * (i + 1) + " "

    def get_header_id(self, span):
        """Return appropriate markdown header prefix.

        Given a text span from a "dict"/"radict" extraction, determine the
        markdown header prefix string of 0 to many concatenated '#' characters.
        """
        fontsize = round(span["size"])  # compute fontsize
        hdr_id = self.header_id.get(fontsize, "")
        return hdr_id


def resolve_links(links, span):
    """Accept a span bbox and return a markdown link string."""
    bbox = fitz.Rect(span["bbox"])

    # a link should overlap at least 70% of the span
    bbox_area = 0.7 * abs(bbox)

    for link in links:
        hot = link["from"]
        if not abs(hot & bbox) >= bbox_area:
            continue  # does not touch the bbox
        text = f'[{span["text"].strip()}]({link["uri"]})'
        return text


def write_text(page, clip):
    out_string = ""

    links = [l for l in page.get_links() if l["kind"] == 2]

    blocks = page.get_text(
        "dict",
        clip=clip,
        flags=fitz.TEXTFLAGS_TEXT,
        # sort=True,
    )["blocks"]

    for block in blocks:

        for line in block["lines"]:
            if line["dir"][1] != 0:
                # rotated
                continue

            spans = line["spans"]

            this_y = line["bbox"][3]  # current bottom coord

            text = "".join([s["text"] for s in spans])

            if not out_string.endswith("\n"):
                out_string += "\n"

            for i, s in enumerate(spans):
                mono = s["flags"] & 8
                bold = s["flags"] & 16
                italic = s["flags"] & 2

                if mono:
                    out_string += f"`{s['text'].strip()}` "
                else:
                    if i == 0:
                        hdr_string = "#"
                        # hdr_string = hdr_prefix.get_header_id(s)
                    else:
                        hdr_string = ""

                    prefix = ""
                    suffix = ""

                    if hdr_string == "":
                        if bold:
                            prefix = "**"
                            suffix += "**"
                        if italic:
                            prefix += "_"
                            suffix = "_" + suffix

                    ltext = resolve_links(links, s)
                    if ltext:
                        text = f"{hdr_string}{prefix}{ltext}{suffix} "
                    else:
                        text = f"{hdr_string}{prefix}{s['text'].strip()}{suffix} "
                    text = (
                        text.replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace(chr(0xF0B7), "-")
                        .replace(chr(0xB7), "-")
                        .replace(chr(8226), "-")
                        .replace(chr(9679), "-")
                    )
                    out_string += text

            previous_y = this_y
            out_string += "\n"

        out_string += "\n"

    return out_string.replace(" \n", "\n")


def find_clip_rects(page):
    tabs = page.find_tables()

    # 2. make a list of table boundary boxes, sort by top-left corner.
    # Must include the header bbox, which may be external.
    tab_rects = sorted(
        [
            (fitz.Rect(t.bbox) | fitz.Rect(t.header.bbox), i)
            for i, t in enumerate(tabs.tables)
        ],
        key=lambda r: (r[0].y0, r[0].x0),
    )

    # 3. final list of all text and table rectangles
    text_rects = []
    # compute rectangles outside tables and fill final rect list
    for i, (r, idx) in enumerate(tab_rects):
        if i == 0:  # compute rect above all tables
            tr = page.rect
            tr.y1 = r.y0
            if not tr.is_empty:
                text_rects.append(("text", tr, 0))
            text_rects.append(("table", r, idx))
            continue
        # read previous rectangle in final list: always a table!
        _, r0, idx0 = text_rects[-1]

        # check if a non-empty text rect is fitting in between tables
        tr = page.rect
        tr.y0 = r0.y1
        tr.y1 = r.y0
        if not tr.is_empty:  # empty if two tables overlap vertically!
            text_rects.append(("text", tr, 0))

        text_rects.append(("table", r, idx))

        # there may also be text below all tables
        if i == len(tab_rects) - 1:
            tr = page.rect
            tr.y0 = r.y1
            if not tr.is_empty:
                text_rects.append(("text", tr, 0))

    if not text_rects:  # this will happen for table-free pages
        text_rects.append(("text", page.rect, 0))
    else:
        rtype, r, idx = text_rects[-1]
        if rtype == "table":
            tr = page.rect
            tr.y0 = r.y1
            if not tr.is_empty:
                text_rects.append(("text", tr, 0))

    return tabs


def generated_output(page):
    write_text(page=page, clip=page.trimbox)


def to_markdown(doc) -> str:
    pages = doc.pages()

    result = [generated_output(page) for page in [next(pages)]]

    return result


def _main(input_filename):
    doc = fitz.open(input_filename)

    to_markdown(doc)


if __name__ == "__main__":
    data_path = Path(__file__).parents[3] / "data"

    _main(data_path / "JPM Electravision 14th Annual Energy Paper 20240305.pdf")
