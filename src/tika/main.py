from pathlib import Path

from tqdm import tqdm

from tika import parser


def to_markdown(input_file):
    parsed = parser.from_file(str(input_file), xmlContent=True)
    metadata = parsed["metadata"]
    result = parsed["content"]

    return result


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
        output = to_markdown(input_file=input_file)

        output_dir = base_dir / "output" / "tika"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{input_file.name}.xml"
        output_file.write_text(output)


if __name__ == "__main__":
    _main()
