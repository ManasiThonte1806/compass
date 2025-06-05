# security/compliance_tagger.py

import re
import logging

def flag_compliance_terms(text: str, terms: list = ["restatement", "earnings risk", "insider trading", "price fixing"]) -> list:
    """
    Flags potentially sensitive terms in a text related to compliance.

    Args:
        text (str): The text to check.
        terms (list, optional): A list of terms to flag.
                               Defaults to ["restatement", "earnings risk", "insider trading", "price fixing"].

    Returns:
        list: A list of the flagged terms found in the text.
               Returns an empty list if no terms are found.
    """
    flagged_terms = []
    for term in terms:
        if re.search(r"\b" + re.escape(term) + r"\b", text, re.IGNORECASE):
            flagged_terms.append(term)
    return flagged_terms

if __name__ == "__main__":
    text = "The company is facing an earnings risk due to the recent restatement of financial results. Insider trading is strictly prohibited."
    print("Original Text:", text)
    flagged = flag_compliance_terms(text)
    if flagged:
        print("Flagged Terms:", flagged)
    else:
        print("No compliance terms flagged.")