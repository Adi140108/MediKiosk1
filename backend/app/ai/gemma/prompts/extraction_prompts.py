DOCUMENT_EXTRACTION_PROMPT = """
You are Gemma 4 12B interpreting and structuring OCR-extracted text from previous medical records.
Extract relevant clinical facts, previous diagnoses, medications, allergies, and test results.

OCR Raw Text:
{raw_text}

JSON Output Format:
{
  "extracted_text": "clean readable text",
  "conditions": ["condition 1", "condition 2"],
  "medications": ["medication 1"],
  "allergies": ["allergy 1"],
  "vitals_and_labs": {"bp": "value", "sugar": "value"},
  "confidence": 0.90
}
"""
