def ensure_loan_number_format(text: str) -> str:
    replacements = {
        "A": "А",
        "a": "а",
    }

    return "".join(replacements.get(char, char) for char in text).upper()
