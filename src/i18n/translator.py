import json
from pathlib import Path
from typing import Any

_TRANSLATIONS: dict[str, dict[str, str]] = {}
_I18N_DIR = Path(__file__).parent
SUPPORTED_LANGUAGES = ("id", "en")
DEFAULT_LANGUAGE = "id"
_current_language: str = DEFAULT_LANGUAGE


def _flatten_dict(d: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, str]:
    items: list[tuple[str, str]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, str(v)))
    return dict(items)


def _load_translations() -> None:
    global _TRANSLATIONS
    if _TRANSLATIONS:
        return
    for lang in SUPPORTED_LANGUAGES:
        filepath = _I18N_DIR / f"{lang}.json"
        with open(filepath, encoding="utf-8") as f:
            _TRANSLATIONS[lang] = _flatten_dict(json.load(f))


def get_language() -> str:
    return _current_language


def set_language(lang: str) -> None:
    global _current_language
    if lang not in SUPPORTED_LANGUAGES:
        msg = f"Unsupported language: {lang!r}. Use one of {SUPPORTED_LANGUAGES}"
        raise ValueError(msg)
    _current_language = lang


def t(key: str) -> str:
    _load_translations()
    lang = _current_language
    translations = _TRANSLATIONS.get(lang, {})
    if key not in translations:
        msg = f"Missing translation key {key!r} for language {lang!r}"
        raise KeyError(msg)
    return translations[key]


def get_all_keys(lang: str) -> set[str]:
    _load_translations()
    return set(_TRANSLATIONS.get(lang, {}).keys())
