"""
Some functions that are used in many places in the project.
"""

from hashlib import sha256

from beartype import beartype


def get_hash_string(input_string):
    hash_string = sha256(input_string.encode()).hexdigest()
    return hash_string


@beartype
def extract_language_from_language_header(header: str, supported_languages: tuple) -> str:
    if not header:
        return "en"

    requested_languages = header.split(",")

    for lang in requested_languages:
        lang_code = lang.split("-")[0]
        if lang_code in supported_languages:
            return lang_code

    return "en"
