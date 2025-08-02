import ollama
import json
import logging
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io

# Set up logging
logger = logging.getLogger(__name__)

# Copied directly from your old project. No changes needed.
def generate_pdf_from_dataframe(df: pd.DataFrame, title: str) -> bytes:
    """Generates a PDF file from a pandas DataFrame."""
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, title, 0, 1, 'C')
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font('Arial', 'B', 8)
    page_width = pdf.w - 2 * pdf.l_margin
    num_columns = len(df.columns)
    col_width = page_width / num_columns if num_columns > 0 else page_width
    
    for col in df.columns:
        pdf.cell(col_width, 10, col, 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font('Arial', '', 8)
    for index, row in df.iterrows():
        for item in row:
            cell_text = str(item).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(col_width, 10, cell_text, 1, 0)
        pdf.ln()
        
    return bytes(pdf.output())

# Copied directly from your old project. No changes needed.
def generate_excel_from_dataframe(df: pd.DataFrame) -> bytes:
    """Generates an Excel file from a pandas DataFrame."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Submissions')
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            # Accessing sheet_properties is deprecated, use column_dimensions directly
            sheet = writer.sheets['Submissions']
            sheet.column_dimensions[column[0].upper() if isinstance(column, str) else column].width = column_width + 2
            
    return output.getvalue()

# Copied directly from your old project.
# This function is still perfect for generating the JSON structure.
def generate_fields_with_llama(description: str) -> tuple[bool, str]:
    """
    Uses an LLM to generate a form's field structure from a natural language description.
    Returns a tuple: (success: bool, content: str), where content is either
    a JSON string of the fields or an error message.
    """
    valid_types = [
        "VARCHAR(255)", "INTEGER", "FLOAT", "DATE", "BOOLEAN", "TEXT", "PHONE",
        "TEXTAREA", "PASSWORD", "CHECKBOX", "RADIO", "SELECT", "DATETIME", "TIME",
        "MULTISELECT", "EMAIL", "URL", "COLOR", "RANGE"
    ]

    prompt = f"""
You are an expert JSON generator for a form-building application.
Based on the user's request, generate a JSON array of field objects.

**RULES:**
1.  **ONLY output the raw JSON array.** Do NOT include any explanations, markdown like ```json, or introductory text. Your entire response must be only the JSON.
2.  Each object in the array represents a form field and must have a "name" and a "type".
3.  The "name" should be a human-readable string (e.g., "Full Name").
4.  The "type" MUST be one of the following values: {', '.join(valid_types)}.
5.  For types 'SELECT', 'RADIO', or 'MULTISELECT', you MUST include an "options" key with an array of strings.
6.  Infer the most appropriate type. 'TEXTAREA' is for long text. 'VARCHAR(255)' is for short text. 'EMAIL' for emails, 'DATE' for dates, etc.

**USER'S REQUEST:**
"{description}"

**YOUR JSON OUTPUT:**
"""
    try:
        response = ollama.generate(
            model='llama2',
            prompt=prompt,
            options={'temperature': 0.1}
        )
        
        json_response = response['response']
        
        try:
            json.loads(json_response)
            return (True, json_response)
        except json.JSONDecodeError as e:
            error_msg = f"AI returned malformed JSON. Error: {e}\nRaw Response: {json_response}"
            logger.error(error_msg)
            return (False, error_msg)

    except Exception as e:
        logger.error(f"Error calling LLM for field generation: {e}")
        return (False, f"An error occurred while contacting the AI: {e}")