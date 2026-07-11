"""Word of the Day — one characterful word, chosen by the date (no definition).

Localized: when the companion injects i18n, the word is drawn from a curated list in
the current Language (falling back to English), and the header is translated. The
word is picked by the calendar day, so it's stable for the day and cycles over time.
"""

# Accent-free (Windows-1252-safe) uppercase words, one evocative list per language.
WORDS_BY_LANG = {
    "en": [
        "EPHEMERAL", "UBIQUITOUS", "SERENDIPITY", "ELOQUENT", "RESILIENT",
        "PRAGMATIC", "CANDOR", "TENACIOUS", "MELLIFLUOUS", "LUMINOUS",
        "QUINTESSENTIAL", "EFFERVESCENT", "PERSPICACIOUS", "SUCCINCT", "GREGARIOUS",
        "INEFFABLE", "LABYRINTHINE", "MAGNANIMOUS", "NEBULOUS", "OBSTINATE",
        "PANACEA", "QUERULOUS", "RESPLENDENT", "SANGUINE", "TACITURN",
        "UMBRAGE", "VORACIOUS", "WISTFUL", "ZEALOUS", "AMBIVALENT",
        "BENEVOLENT", "CACOPHONY", "DILIGENT", "ENIGMATIC", "FASTIDIOUS",
        "GARRULOUS", "HALCYON", "IDIOSYNCRASY", "JUXTAPOSE", "LETHARGIC",
        "MERCURIAL", "NONCHALANT", "OSTENTATIOUS", "PENCHANT", "QUIXOTIC",
        "RECALCITRANT", "TRANQUIL", "VENERABLE", "WHIMSICAL", "ZENITH",
    ],
    "fr": [
        "FLANERIE", "DEPAYSEMENT", "RETROUVAILLES", "CREPUSCULE", "EBLOUISSANT",
        "CHATOYANT", "INSOUCIANT", "MELANCOLIE", "QUIETUDE", "SAGACITE",
        "PERSPICACE", "OPINIATRE", "LOQUACE", "VOLUBILE", "EPHEMERE",
        "LUMINEUX", "RESILIENT", "TENACE", "SERENITE", "VENERABLE",
        "NONCHALANT", "ENIGMATIQUE", "EXQUIS", "IMPROMPTU",
    ],
    "de": [
        "FERNWEH", "WALDEINSAMKEIT", "ZEITGEIST", "GEBORGENHEIT", "SEHNSUCHT",
        "VERGAENGLICH", "LEUCHTEND", "BEHARRLICH", "SCHARFSINNIG", "WORTKARG",
        "UEBERSCHWANG", "GEMUETLICH", "WEHMUT", "GELASSENHEIT", "EIGENSINNIG",
        "BESONNEN", "VERWEGEN", "ANMUTIG", "UNERGRUENDLICH", "AUGENBLICK",
        "DAEMMERUNG", "SCHWELGEN", "VERSCHMITZT", "EHRFURCHT",
    ],
    "es": [
        "EFIMERO", "INEFABLE", "SERENDIPIA", "ELOCUENTE", "RESILIENTE",
        "LUMINOSO", "TENAZ", "PERSPICAZ", "LOCUAZ", "OBSTINADO",
        "PANACEA", "RESPLANDECIENTE", "TRANQUILO", "VENERABLE", "SAGAZ",
        "NOSTALGIA", "CREPUSCULO", "DESLUMBRANTE", "MELANCOLIA", "QUIETUD",
        "SOSIEGO", "ENIGMATICO", "EXQUISITO", "IMPETU",
    ],
    "it": [
        "EFFIMERO", "INEFFABILE", "SERENDIPITA", "ELOQUENTE", "RESILIENTE",
        "LUMINOSO", "TENACE", "PERSPICACE", "LOQUACE", "OSTINATO",
        "PANACEA", "SPLENDENTE", "TRANQUILLO", "VENERABILE", "SAGACE",
        "NOSTALGIA", "CREPUSCOLO", "ABBAGLIANTE", "MALINCONIA", "QUIETE",
        "SERENITA", "ENIGMATICO", "SQUISITO", "IMPETO",
    ],
    "pt": [
        "EFEMERO", "INEFAVEL", "SERENDIPIA", "ELOQUENTE", "RESILIENTE",
        "LUMINOSO", "TENAZ", "PERSPICAZ", "LOQUAZ", "OBSTINADO",
        "PANACEIA", "RESPLANDECENTE", "TRANQUILO", "VENERAVEL", "SAGAZ",
        "SAUDADE", "CREPUSCULO", "DESLUMBRANTE", "MELANCOLIA", "QUIETUDE",
        "SOSSEGO", "ENIGMATICO", "REQUINTADO", "IMPETO",
    ],
    "nl": [
        "VLUCHTIG", "ONUITSPREKELIJK", "TIJDGEEST", "VEERKRACHTIG", "LICHTEND",
        "VASTBERADEN", "SCHERPZINNIG", "WOORDKARIG", "KOPPIG", "WONDERMIDDEL",
        "STRALEND", "SEREEN", "EERBIEDWAARDIG", "WIJSHEID", "WEEMOED",
        "SCHEMERING", "OOGVERBLINDEND", "MELANCHOLIE", "GEZELLIG", "RAADSELACHTIG",
        "VERRUKKELIJK", "ONSTUIMIG", "VOORBIJGAAND", "BEDACHTZAAM",
    ],
}


def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
    from datetime import date
    lang = i18n.lang_base if i18n is not None else "en"
    words = WORDS_BY_LANG.get(lang) or WORDS_BY_LANG["en"]
    word = words[date.today().toordinal() % len(words)]
    header = i18n.t("WORD OF THE DAY", "vocab") if i18n is not None else "WORD OF THE DAY"
    if get_rows() == 1:
        return [format_lines(word)]
    return [format_lines(header, word)]
