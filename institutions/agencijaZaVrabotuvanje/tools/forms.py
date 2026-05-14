import difflib

FORMS = {
    "Овластување на овластено лице со список на лица кои ги одјавува од работен однос поради деловни причини (технолошки вишок)": {
        "url": "https://shorturl.at/wKOl6",
        "file_type": "docx",
    },
    "Овластување на овластено лице со список на лица кои ги одјавува од работен однос": {
        "url": "https://shorturl.at/q0WeQ",
        "file_type": "docx",
    },
    "Овластување на овластено лице со список на лица кои ги пријавува од работен однос": {
        "url": "https://shorturl.at/o18Te",
        "file_type": "docx",
    },
    "ППП - образец pdf": {
        "url": "https://shorturl.at/pJr7I",
        "file_type": "pdf",
    },
    "ППП - образец word": {
        "url": "https://tinyurl.com/459ffk6c",
        "file_type": "docx",
    },
    "Оглас за практикантска работа": {
        "url": "https://tinyurl.com/5h5u6dy3",
        "file_type": "doc",
    },
    "Овластување за пријавување на практикант/и": {
        "url": "https://tinyurl.com/bdy8f2dw",
        "file_type": "docx",
    },
    "Овластување за одјавување на практикант/и": {
        "url": "https://tinyurl.com/bpamc3h5",
        "file_type": "docx",
    },
    "Апликационен формулар и програма за учество во програмата Општини корисна работа 2025": {
        "url": "https://tinyurl.com/ywj9zr4c",
        "file_type": "docx",
    },
}

_FORM_NAMES = list(FORMS.keys())

_MIN_STEM = 5  # minimum shared-prefix length to treat two words as related


def _stem_match(query_word: str, form_word: str) -> bool:
    """
    Return True if query_word and form_word share a common root.

    Matches exact substrings AND words that share >= _MIN_STEM leading
    characters, which handles Macedonian inflections like
    пријава / пријавување, практикант / практикантска.
    """
    if query_word in form_word or form_word in query_word:
        return True
    shared = sum(1 for a, b in zip(query_word, form_word) if a == b)
    # Stop counting at first mismatch (prefix check)
    prefix = 0
    for a, b in zip(query_word, form_word):
        if a == b:
            prefix += 1
        else:
            break
    return prefix >= _MIN_STEM


def _score_form(query_words: list[str], form_name: str) -> int:
    """Count how many query words stem-match at least one word in form_name."""
    form_words = [
        w.strip("/(),.-") for w in form_name.lower().split() if len(w.strip("/(),.-")) > 2
    ]
    return sum(
        1 for qw in query_words if any(_stem_match(qw, fw) for fw in form_words)
    )


def get_form(query: str) -> dict:
    """
    Return the download link for an official Employment Agency (av.gov.mk) form.

    Call this tool when the user asks for a downloadable form, document, or
    образец related to employment registration/deregistration, internships
    (практиканти), job ads, or the ППП form. The query can be a partial name,
    a keyword (e.g. "технолошки вишок", "практикант пријава", "ППП"), or the
    exact Macedonian form title.

    Uses fuzzy matching so typos and partial queries work. When no form matches,
    returns a list of all 9 available forms so the user can choose.

    Args:
        query: Natural-language description or partial name of the desired form.

    Returns:
        On match:
            {
                "name": <full official form name>,
                "url": <direct download URL>,
                "file_type": <"pdf", "docx", or "doc">,
                "message": "Here is the download link for the requested form."
            }
        On no match:
            {
                "message": "No matching form found. Here are all available forms:",
                "available_forms": [<list of all 9 form names>]
            }
    """
    query_lower = query.lower()

    # 1. Substring match (handles "практикант пријава", "технолошки вишок", etc.)
    for name in _FORM_NAMES:
        if query_lower in name.lower():
            return {
                "name": name,
                "url": FORMS[name]["url"],
                "file_type": FORMS[name]["file_type"],
                "message": "Here is the download link for the requested form.",
            }

    # 2. Rank by how many query words stem-match words in the form name
    words = [w for w in query_lower.split() if len(w) > 2]
    if words:
        scored = [(_score_form(words, name), name) for name in _FORM_NAMES]
        best_score, best_name = max(scored, key=lambda x: x[0])
        if best_score > 0:
            return {
                "name": best_name,
                "url": FORMS[best_name]["url"],
                "file_type": FORMS[best_name]["file_type"],
                "message": "Here is the download link for the requested form.",
            }

    # 3. Fuzzy match via difflib
    matches = difflib.get_close_matches(query, _FORM_NAMES, n=1, cutoff=0.3)
    if matches:
        name = matches[0]
        return {
            "name": name,
            "url": FORMS[name]["url"],
            "file_type": FORMS[name]["file_type"],
            "message": "Here is the download link for the requested form.",
        }

    return {
        "message": "No matching form found. Here are all available forms:",
        "available_forms": _FORM_NAMES,
    }
