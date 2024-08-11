

def translate_text_to_english(text):
    # Define a translation table
    translation_table = str.maketrans({
        "ç": "c",
        "ğ": "g",
        "ş": "s",
        "ü": "u",
        "ö": "o",
        "ı": "i",
        "Ç": "C",
        "Ğ": "G",
        "Ş": "S",
        "Ü": "U",
        "Ö": "O",
        "İ": "I"
    })
    
    # Translate the text using the translation table
    translated_text = text.translate(translation_table)
    
    return translated_text