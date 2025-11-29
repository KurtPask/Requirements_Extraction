from pathlib import Path
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Return full text of the PDF with simple [PAGE X] markers."""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text")
        pages.append(f"[PAGE {i}]\n{text}")
    return "\n\n".join(pages)


def batch_extract(input_dir: Path, output_dir: Path) -> None:
    """Convert all PDFs in input_dir to .txt in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for pdf in input_dir.glob("*.pdf"):
        txt = extract_text_from_pdf(pdf)
        out_path = output_dir / (pdf.stem + ".txt")
        out_path.write_text(txt, encoding="utf-8")
        print(f"Parsed {pdf.name} -> {out_path.name}")


if __name__ == "__main__":
    input_dir = Path("In")      # folder where the PDFs live
    output_dir = Path("parsed_text")    # new folder for .txt output
    batch_extract(input_dir, output_dir)
