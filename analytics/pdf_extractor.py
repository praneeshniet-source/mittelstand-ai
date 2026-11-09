import pytesseract
from PIL import Image
from datetime import datetime
import pymupdf
import re

def extract_text_from_pdf(pdf_path):

    document = pymupdf.open(pdf_path)

    extracted_text = ""

    for page in document:

        page_text = page.get_text().strip()

        if page_text:
            extracted_text += page_text + "\n"

        else:
            pix = page.get_pixmap(dpi=200)

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            ocr_text = pytesseract.image_to_string(
                image,
                lang="eng"
            )

            extracted_text += ocr_text + "\n"

    document.close()

    return extracted_text

def extract_invoice_details(text):

    details = {}

    patterns = {
       "invoice_number": [
    r"Invoice Number\s*[:#]?\s*(.+)",
    r"Invoice No\.?\s*[:#]?\s*(.+)",
    r"Invoice Na\s*[:#]?\s*(.+)",
    r"Rechnungsnummer\s*[:#]?\s*(.+)"
   ],

        "supplier": [
            r"Supplier\s*[:#]?\s*(.+)",
            r"Vendor\s*[:#]?\s*(.+)",
            r"Lieferant\s*[:#]?\s*(.+)"
        ],

        "invoice_date": [
            r"Invoice Date\s*[:#]?\s*(\d{4}-\d{2}-\d{2})",
            r"Rechnungsdatum\s*[:#]?\s*(\d{4}-\d{2}-\d{2})"
        ],

        "due_date": [
            r"Due Date\s*[:#]?\s*(\d{4}-\d{2}-\d{2})",
            r"Payment Due Date\s*[:#]?\s*(\d{4}-\d{2}-\d{2})",
            r"Fälligkeitsdatum\s*[:#]?\s*(\d{4}-\d{2}-\d{2})"
        ],

        "amount": [
            r"(?:Amount|Total|Gesamtbetrag)\s*[:#]?\s*(?:EUR|€)?\s*([\d.,]+)",
            r"(?:Amount|Total|Gesamtbetrag)\s*[:#]?\s*([\d.,]+)\s*(?:EUR|€)"
        ]
    }

    for field, field_patterns in patterns.items():

        details[field] = None

        for pattern in field_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE | re.MULTILINE
            )

            if match:
                value = match.group(1).strip()

                if field == "amount":
                    value = value.replace(" ", "")

                    if "," in value and "." in value:
                        if value.rfind(",") > value.rfind("."):
                            value = value.replace(".", "").replace(",", ".")
                        else:
                            value = value.replace(",", "")

                    elif "," in value:
                        value = value.replace(",", ".")

                    try:
                        value = float(value)
                    except ValueError:
                        continue

                details[field] = value
                break

    return details

def validate_invoice_details(details):
    errors = []

    required_fields = [
        "invoice_number",
        "supplier",
        "invoice_date",
        "due_date",
        "amount"
    ]

    for field in required_fields:
        if not details.get(field):
            errors.append(f"Missing field: {field}")

    if errors:
        return errors

    try:
        invoice_date = datetime.strptime(
            details["invoice_date"], "%Y-%m-%d"
        )
        due_date = datetime.strptime(
            details["due_date"], "%Y-%m-%d"
        )

        if due_date < invoice_date:
            errors.append("Due date is earlier than invoice date")

    except ValueError:
        errors.append("Invalid invoice date or due date")

    try:
        if float(details["amount"]) <= 0:
            errors.append("Invoice amount must be greater than zero")
    except (ValueError, TypeError):
        errors.append("Invalid invoice amount")

    return errors
