import random

def get_random_unicode_character():
    # Unicode character range from 0x0000 to 0x10FFFF
    random_code_point = random.randint(0, 0x10FFFF)
    
    # Exclude surrogate pairs (range 0xD800 to 0xDFFF)
    while 0xD800 <= random_code_point <= 0xDFFF:
        random_code_point = random.randint(0, 0x10FFFF)
    
    return chr(random_code_point)

# Example usage
random_unicode_char = get_random_unicode_character()
print(f"Random Unicode Character: {random_unicode_char}")