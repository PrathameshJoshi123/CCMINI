import logging
from typing import List
from dotenv import load_dotenv 
load_dotenv()  # Load environment variables from .env file
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

from backend.models.document import TextChunk, TextSourceEnum


logger = logging.getLogger(__name__)


def _pixmap_to_pil(pix) -> Image.Image:
    mode = "RGB" if pix.n < 4 else "RGBA"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    return img


def extract_text_from_pdf(file_path: str) -> List[TextChunk]:
    """Extract text from PDF using a hybrid strategy: direct text extraction first, then OCR fallback for image pages.

    Returns a list of TextChunk objects (one per page with extracted text and source).
    """
    chunks: List[TextChunk] = []
    try:
        with fitz.open(file_path) as doc:
            for i, page in enumerate(doc, start=1):
                try:
                    # Detect tables on the page
                    tables = page.find_tables()
                    table_bboxes = []
                    for table in tables:
                        bbox = table.bbox  # (x0, y0, x1, y1)
                        table_bboxes.append(bbox)
                        # extract table data
                        try:
                            table_data = table.extract()
                        except Exception:
                            # Older PyMuPDF may not have table.extract(); try table.get_text('blocks') fallback
                            table_data = []

                        # Convert table_data (list of rows) to markdown
                        md_lines = []
                        if table_data:
                            # assume table_data is list of lists; sanitize None values
                            def _cell_to_str(c):
                                if c is None:
                                    return ""
                                return str(c)

                            header = table_data[0]
                            header_cells = [_cell_to_str(h).strip() for h in header]
                            # fallback: if header is empty, skip table
                            if any(header_cells):
                                md_lines.append("| " + " | ".join(header_cells) + " |")
                                md_lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")
                                for row in table_data[1:]:
                                    row_cells = [_cell_to_str(c).strip() for c in row]
                                    md_lines.append("| " + " | ".join(row_cells) + " |")
                            else:
                                md_lines = []

                        if md_lines:
                            md_table = "\n".join(md_lines)
                            chunks.append(TextChunk(text=md_table, page_number=i, source=TextSourceEnum.TABLE.value))

                    # Now extract text blocks, excluding those inside table bounding boxes
                    blocks = page.get_text("blocks")  # list of tuples (x0, y0, x1, y1, text, block_no) or variant lengths
                    page_text_parts = []
                    for b in blocks:
                        # blocks can vary by PyMuPDF version; unpack defensively
                        try:
                            x0, y0, x1, y1, btext, *rest = b
                        except Exception:
                            # fallback: coerce to list and pick what we can
                            b_list = list(b)
                            if len(b_list) >= 5:
                                x0, y0, x1, y1 = b_list[0:4]
                                btext = b_list[4]
                            else:
                                # unexpected format; skip
                                continue
                        # Ensure text is a string
                        if btext is None:
                            btext = ""
                        in_table = False
                        for tb in table_bboxes:
                            tx0, ty0, tx1, ty1 = tb
                            # simple bbox containment check (block inside table bbox)
                            if x0 >= tx0 and x1 <= tx1 and y0 >= ty0 and y1 <= ty1:
                                in_table = True
                                break
                        if not in_table and isinstance(btext, str) and btext.strip():
                            page_text_parts.append(btext)

                    page_text = "\n".join(page_text_parts).strip()
                    if page_text and len(page_text) >= 20:
                        chunks.append(TextChunk(text=page_text, page_number=i, source=TextSourceEnum.TEXT.value))
                    elif page_text:
                        # small text — try OCR on the whole page image
                        pix = page.get_pixmap()
                        pil_img = _pixmap_to_pil(pix)
                        ocr_text = pytesseract.image_to_string(pil_img)
                        if ocr_text and ocr_text.strip():
                            chunks.append(TextChunk(text=ocr_text, page_number=i, source=TextSourceEnum.OCR.value))
                        else:
                            chunks.append(TextChunk(text="", page_number=i, source=TextSourceEnum.OCR.value))

                except Exception as page_err:
                    logger.exception("Error extracting page %s from %s: %s", i, file_path, page_err)
                    chunks.append(TextChunk(text="", page_number=i, source=TextSourceEnum.OCR.value))
        return chunks

    except FileNotFoundError as fnf:
        logger.exception("PDF file not found: %s", file_path)
        return []
    except Exception as e:
        # fitz.errors.FitzError might be raised for corrupted PDFs
        logger.exception("Error opening or processing PDF %s: %s", file_path, e)
        return []
