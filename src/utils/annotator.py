from pathlib import Path

import fitz
from pdf2image import convert_from_bytes
from PIL import ImageDraw
from tqdm import tqdm


def rect_intersection(a, b):
    x1 = max(min(a[0], a[2]), min(b[0], b[2]))
    y1 = max(min(a[1], a[3]), min(b[1], b[3]))
    x2 = min(max(a[0], a[2]), max(b[0], b[2]))
    y2 = min(max(a[1], a[3]), max(b[1], b[3]))

    return x1 < x2 and y1 < y2


# def annotate_from_df(blocks_df, pdf_path, pdf_bytes, output_path):
#     pdf = fitz.open(str(pdf_path))
#     images = convert_from_bytes(pdf_bytes)

#     output_path.mkdir(exist_ok=True, parents=True)

#     for page_index, (page, image) in enumerate(zip(pdf.pages(), images)):
#         # if page_index != 3:
#         #     continue

#         draw = ImageDraw.Draw(image, "RGBA")

#         page_w = page.rect[2]
#         page_h = page.rect[3]

#         pdf_drawings = page.get_drawings()
#         scaled_drawings = [
#             scale_rect(
#                 from_size=(page_w, page_h),
#                 from_rect=drawing["rect"],
#                 to_size=image.size,
#             )
#             for drawing in pdf_drawings
#         ]
#         scaled_bboxes = [
#             scale_rect(
#                 from_size=(page_w, page_h),
#                 from_rect=row["bbox"],
#                 to_size=image.size,
#             )
#             for i, row in blocks_df[blocks_df.page == page_index].iterrows()
#         ]
#         for scaled_drawing in scaled_drawings:
#             draw.rectangle(
#                 scaled_drawing, outline="blue", fill=(0, 0, 255, 80), width=1
#             )
#         for scaled_bbox in scaled_bboxes:
#             draw.rectangle(scaled_bbox, outline="red", width=2)

#         # for bbox in scaled_bboxes:
#         #     if any(
#         #         [
#         #             rect_intersection(bbox, drawing_rect)
#         #             for drawing_rect in scaled_drawings
#         #         ]
#         #     ):
#         #         draw.rectangle(bbox, outline="green", fill=(0, 255, 0, 80), width=1)
#         #     else:
#         #         draw.rectangle(bbox, outline="red", width=2)

#         image.save(output_path / f"{page_index}.png", "PNG")

#     return output_path


def annotate_from_bytes(pdf_bytes, output_path):
    pdf = fitz.open(stream=pdf_bytes)
    images = convert_from_bytes(pdf_bytes)

    output_path.mkdir(exist_ok=True, parents=True)

    pages = list(zip(pdf.pages(), images))

    for page_num, (page, image) in enumerate(tqdm(pages)):
        page_w = page.rect[2]
        page_h = page.rect[3]

        blocks = page.get_text("dict", sort=False)["blocks"]

        draw = ImageDraw.Draw(image)

        for b in blocks:
            bbox = scale_rect(
                from_size=image.size, from_rect=b["bbox"], to_size=(page_w, page_h)
            )

            draw.rectangle(bbox, outline="red", width=1)

        scaled_mediabox = scale_rect(
            from_size=image.size,
            from_rect=page.mediabox,
            to_size=(page_w, page_h),
        )
        draw.rectangle(scaled_mediabox, outline="yellow", width=10)

        for cluster_drawing in page.cluster_drawings():
            scaled_cluster_drawings = scale_rect(
                from_size=image.size,
                from_rect=cluster_drawing,
                to_size=(page_w, page_h),
            )
            draw.rectangle(scaled_cluster_drawings, outline="purple", width=10)

        # for table in page.find_tables():
        #     scaled_table = scale_rect(
        #         from_size=image.size,
        #         from_rect=table.bbox,
        #         to_size=(page_w, page_h),
        #     )
        #     draw.rectangle(scaled_table, outline="red", width=10)

        # for drawing in page.get_drawings():
        #     scaled_drawing = scale_rect(
        #         from_size=image.size,
        #         from_rect=drawing["rect"],
        #         to_size=(page_w, page_h),
        #     )
        #     draw.rectangle(scaled_drawing, outline="blue", width=1)

        # for pixmap in page.get_images():
        #     image_rect = (
        #         pixmap[0],
        #         pixmap[1],
        #         pixmap[0] + pixmap[2],
        #         pixmap[1] + pixmap[3],
        #     )
        #     scaled_image = scale_rect(
        #         from_size=image.size,
        #         from_rect=image_rect,
        #         to_size=(page_w, page_h),
        #     )
        #     draw.rectangle(scaled_image, outline="cyan", width=10)

        # for item_text, item_rect, item_type in drawing["items"]:
        #     scaled_item = scale_rect(
        #         from_size=image.size,
        #         from_rect=item_rect,
        #         to_size=(page_w, page_h),
        #     )
        #     draw.rectangle(scaled_item, outline="green", width=1)

        image.save(output_path / f"{page_num}.png", "PNG")

    return output_path


def scale_rect(from_rect, from_size, to_size):
    from_w, from_h = from_size
    to_w, to_h = to_size

    bbox = (
        from_rect[0] * from_w / to_w,
        from_rect[1] * from_h / to_h,
        from_rect[2] * from_w / to_w,
        from_rect[3] * from_h / to_h,
    )

    return bbox


def annotate_from_file(file_path, output_path):
    pdf_bytes = file_path.read_bytes()
    annotate_from_bytes(pdf_bytes=pdf_bytes, output_path=output_path)


def main():
    base_dir = Path(__file__).parents[2]

    pdf_path = (
        base_dir / "data" / "JPM Electravision 14th Annual Energy Paper 20240305.pdf"
    )
    output_path = Path(__file__).parents[2] / "output" / Path(pdf_path).name

    annotate_from_file(file_path=pdf_path, output_path=output_path)


if __name__ == "__main__":
    main()
