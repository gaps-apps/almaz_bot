def replace_english_with_russian(text: str) -> str:
    replacements = {
        "A": "А",
        "a": "а",
        "B": "В",
        "E": "Е",
        "e": "е",
        "K": "К",
        "k": "к",
        "M": "М",
        "H": "Н",
        "O": "О",
        "o": "о",
        "P": "Р",
        "C": "С",
        "c": "с",
        "T": "Т",
        "X": "Х",
    }

    return "".join(replacements.get(char, char) for char in text)
