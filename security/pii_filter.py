# security/pii_filter.py

import re
import logging

def redact_pii(text: str) -> str:
    """
    Redacts Personally Identifiable Information (PII) from a text.

    Args:
        text (str): The text to redact.

    Returns:
        str: The text with PII redacted.
    """
    redacted_text = text

    # Email
    redacted_text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL_REDACTED]", redacted_text)

    # SSN (Social Security Number - US)
    redacted_text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]", redacted_text)

    # Phone Number (US)
    redacted_text = re.sub(r"\b(?:\d{3}[-\s]?){2}\d{4}\b", "[PHONE_REDACTED]", redacted_text)

    return redacted_text

def mask_pii(text: str) -> str:
    """
    Masks Personally Identifiable Information (PII) in a text, partially revealing some characters.

    Args:
        text (str): The text to mask.

    Returns:
        str: The text with PII masked.
    """
    masked_text = text

    # Email
    masked_text = re.sub(r"([a-zA-Z0-9._%+-]{1,3})[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+)", r"\1****@\2", masked_text)

    # SSN
    masked_text = re.sub(r"(\d{3}-\d{2})-\d{4}", r"\1-****", masked_text)

    # Phone Number (US)
    masked_text = re.sub(r"(\d{3})[-.\s]?\d{3}[-.\s]?(\d{4})", r"\1-***-\2", masked_text)

    return masked_text

def find_pii(text: str) -> list:
    """
    Finds Personally Identifiable Information (PII) in a text and returns a list of the PII found.

    Args:
        text (str): The text to search for PII.

    Returns:
        list: A list of strings, where each string is a PII found in the text.
               Returns an empty list if no PII is found.
    """
    pii_list = []

    # Email
    pii_list.extend(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))

    # SSN
    pii_list.extend(re.findall(r"\b\d{3}-\d{2}-\d{4}\b", text))

    # Phone Number (US)
    pii_list.extend(re.findall(r"\b(?:\d{3}[-\s]?){2}\d{4}\b", text))

    return pii_list

if __name__ == "__main__":
    text = "My email is test@example.com, my SSN is 123-45-6789, and my phone number is 555-123-4567.  Please contact me at another@test.co.uk."
    print("Original Text:", text)
    print("Redacted Text:", redact_pii(text))
    print("Masked Text:", mask_pii(text))
    print("Found PII:", find_pii(text))