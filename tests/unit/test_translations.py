import json
from pathlib import Path

import pytest

from src.i18n.translator import get_all_keys, set_language, t

I18N_DIR = Path(__file__).parent.parent.parent / "src" / "i18n"


def _load_raw_keys(lang: str) -> set[str]:
    filepath = I18N_DIR / f"{lang}.json"
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    return set(_flatten(data))


def _flatten(d: dict, parent: str = "") -> list[str]:
    keys: list[str] = []
    for k, v in d.items():
        full = f"{parent}.{k}" if parent else k
        if isinstance(v, dict):
            keys.extend(_flatten(v, full))
        else:
            keys.append(full)
    return keys


class TestTranslationKeyParity:
    def test_id_and_en_have_identical_keys(self) -> None:
        id_keys = _load_raw_keys("id")
        en_keys = _load_raw_keys("en")
        missing_in_en = id_keys - en_keys
        missing_in_id = en_keys - id_keys
        assert not missing_in_en, f"Keys in id.json missing from en.json: {missing_in_en}"
        assert not missing_in_id, f"Keys in en.json missing from id.json: {missing_in_id}"

    def test_get_all_keys_matches_raw(self) -> None:
        for lang in ("id", "en"):
            raw = _load_raw_keys(lang)
            loaded = get_all_keys(lang)
            assert raw == loaded, f"Key mismatch for {lang}"


class TestTranslationValues:
    @pytest.mark.parametrize("lang", ["id", "en"])
    def test_no_empty_values(self, lang: str) -> None:
        filepath = I18N_DIR / f"{lang}.json"
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        self._check_no_empty(data, lang)

    def _check_no_empty(self, d: dict, lang: str, parent: str = "") -> None:
        for k, v in d.items():
            full = f"{parent}.{k}" if parent else k
            if isinstance(v, dict):
                self._check_no_empty(v, lang, full)
            else:
                assert str(v).strip(), f"Empty value for key '{full}' in {lang}.json"


class TestTranslatorFunction:
    def test_indonesian_product_title(self) -> None:
        set_language("id")
        assert t("app.title") == "tetani"

    def test_english_product_title(self) -> None:
        set_language("en")
        assert t("app.title") == "tetani (Farmers' Dream)"

    def test_language_switch_changes_output(self) -> None:
        set_language("id")
        id_label = t("nav.radar")
        set_language("en")
        en_label = t("nav.radar")
        assert id_label != en_label
        assert id_label == "Radar Surplus"
        assert en_label == "Surplus Radar"

    def test_missing_key_raises_key_error(self) -> None:
        set_language("id")
        with pytest.raises(KeyError, match="nonexistent.key"):
            t("nonexistent.key")

    def test_unsupported_language_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unsupported language"):
            set_language("fr")

    def test_nested_keys_accessible(self) -> None:
        set_language("id")
        assert t("risk.level.high") == "Tinggi"
        set_language("en")
        assert t("risk.level.high") == "High"
