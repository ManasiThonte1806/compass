# src/ingest/document_parser.py

import os
import fitz # PyMuPDF
import email # Python's built-in email package
import json

def parse_pdf(file_path):
    """
    Extracts text from a PDF file using PyMuPDF.
    Returns the extracted text.
    """
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
        return None

def parse_eml(file_path):
    """
    Extracts subject and body from an EML file using Python's email package.
    Returns a dictionary with 'subject' and 'body'.
    """
    subject = None
    body = None
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            msg = email.message_from_file(f)

        subject = msg['Subject']

        # Iterate over parts to find the plain text body
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))

                # Look for plain text parts, skip attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                    break
        else:
            # Not multipart, assume plain text body
            body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='ignore')

        return {"subject": subject, "body": body}
    except Exception as e:
        print(f"Error parsing EML {file_path}: {e}")
        return None

def main():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    unstructured_data_path = os.path.join(project_root, 'data', 'unstructured')
    output_jsonl_path = os.path.join(project_root, 'data', 'unstructured', 'parsed.jsonl')

    print(f"Looking for unstructured data in: {unstructured_data_path}")
    print(f"Output will be saved to: {output_jsonl_path}")

    parsed_documents = []

    for filename in os.listdir(unstructured_data_path):
        file_path = os.path.join(unstructured_data_path, filename)
        if os.path.isfile(file_path):
            doc_id = os.path.splitext(filename)[0] # Use filename without extension as ID

            if filename.lower().endswith('.pdf'):
                print(f"Parsing PDF: {filename}")
                content = parse_pdf(file_path)
                if content:
                    parsed_documents.append({
                        "id": doc_id,
                        "filename": filename,
                        "type": "pdf",
                        "content": content
                    })
            elif filename.lower().endswith('.eml'):
                print(f"Parsing EML: {filename}")
                email_data = parse_eml(file_path)
                if email_data:
                    parsed_documents.append({
                        "id": doc_id,
                        "filename": filename,
                        "type": "email",
                        "subject": email_data.get("subject"),
                        "body": email_data.get("body")
                    })
            else:
                print(f"Skipping unsupported file type: {filename}")

    # Write parsed documents to JSONL file
    if parsed_documents:
        with open(output_jsonl_path, 'w', encoding='utf-8') as f:
            for doc in parsed_documents:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        print(f"\nSuccessfully parsed {len(parsed_documents)} documents and saved to {output_jsonl_path}")
    else:
        print("\nNo documents were parsed. Please check the 'data/unstructured' folder and file types.")

if __name__ == "__main__":
    main()
