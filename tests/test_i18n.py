import inspect
import pathlib
import sys
import unittest
from datetime import datetime


SERVER_DIR = pathlib.Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))

import i18n  # noqa: E402

try:
    import babel  # noqa: F401
    HAS_BABEL = True
except ImportError:
    HAS_BABEL = False

# A fixed date so assertions never depend on "today". 2026-07-10 is a Friday.
D = datetime(2026, 7, 10, 15, 48, 5)


class TranslateTests(unittest.TestCase):
    def test_english_is_passthrough(self):
        # No language, English, and any en-* region all return the text unchanged.
        for lang in (None, "", "en", "en-US", "en-GB"):
            self.assertEqual(i18n.translate("SUNSET", lang, "sun"), "SUNSET")

    def test_known_translation(self):
        self.assertEqual(i18n.translate("SUNSET", "fr", "sun"), "COUCHER")
        self.assertEqual(i18n.translate("FULL MOON", "de", "moon"), "VOLLMOND")
        self.assertEqual(i18n.translate("GOLD", "nl", "metals"), "GOUD")

    def test_unknown_key_falls_back_to_english(self):
        self.assertEqual(i18n.translate("TOTALLY UNKNOWN", "fr", "sun"), "TOTALLY UNKNOWN")

    def test_unknown_language_falls_back_to_english_key(self):
        # A language we don't have a translation for keeps the English text.
        self.assertEqual(i18n.translate("SUNSET", "sw", "sun"), "SUNSET")

    def test_wrong_context_does_not_leak(self):
        # SUNSET lives in the 'sun' domain, so asking a different domain must not
        # find it (it's not a 'common' word) -> English text.
        self.assertEqual(i18n.translate("SUNSET", "fr", "weather"), "SUNSET")


class ContextKeyTests(unittest.TestCase):
    """The same English word carries different translations per context/domain
    (gettext msgctxt), and a shared 'common' domain backs every context."""

    def test_homograph_splits_by_context(self):
        # HIGH: a weather level vs a tide height -> different French words.
        self.assertEqual(i18n.translate("HIGH", "fr", "weather"), "ELEVE")
        self.assertEqual(i18n.translate("HIGH", "fr", "tides"), "HAUTE")
        self.assertNotEqual(i18n.translate("HIGH", "fr", "weather"),
                            i18n.translate("HIGH", "fr", "tides"))
        self.assertEqual(i18n.translate("LOW", "fr", "tides"), "BASSE")

    def test_shared_time_vocabulary_is_one_domain(self):
        # DAYS/IN are one meaning shared by many apps -> a single 'time' domain,
        # not duplicated per app. countdown/holidays/f1/rocket all use ctx='time'.
        self.assertEqual(i18n.translate("DAYS", "fr", "time"), "JOURS")
        self.assertEqual(i18n.translate("IN", "fr", "time"), "DANS")
        self.assertEqual(i18n.translate("NOW", "de", "time"), "JETZT")

    def test_common_domain_fallback(self):
        # 'OFFLINE' lives only in 'common'; any domain resolves it via fallback.
        for ctx in ("aurora", "sentiment", "weather"):
            self.assertEqual(i18n.translate("OFFLINE", "fr", ctx), "HORS LIGNE")

    def test_default_context_is_common(self):
        self.assertEqual(i18n.translate("OFFLINE", "fr"), "HORS LIGNE")
        # A domain-specific word is NOT found under the default (common) context.
        self.assertEqual(i18n.translate("SUNSET", "fr"), "SUNSET")


class DurationAndClockTests(unittest.TestCase):
    def test_duration_unit_localizes_day(self):
        self.assertEqual(i18n.duration_unit("D", "fr"), "J")   # jour
        self.assertEqual(i18n.duration_unit("D", "de"), "T")   # Tag
        self.assertEqual(i18n.duration_unit("D", "it"), "G")   # giorno

    def test_duration_unit_passthrough(self):
        self.assertEqual(i18n.duration_unit("D", "en-US"), "D")
        self.assertEqual(i18n.duration_unit("H", None), "H")
        self.assertEqual(i18n.duration_unit("Z", "fr"), "Z")   # unknown key

    def test_duration_lives_in_time_domain(self):
        # Abbreviations and full-word forms are one duration vocabulary in 'time'.
        self.assertEqual(i18n.duration_unit("D", "fr"), i18n.translate("D", "fr", "time"))
        self.assertEqual(i18n.translate("WEEKS", "fr", "time"), "SEMAINES")
        self.assertEqual(i18n.translate("YEARS", "de", "time"), "JAHRE")
        self.assertEqual(i18n.translate("SECONDS", "es", "time"), "SEGUNDOS")

    def test_uses_24h(self):
        self.assertFalse(i18n.uses_24h("en-US"))
        self.assertFalse(i18n.uses_24h("en-GB"))
        self.assertFalse(i18n.uses_24h(None))
        self.assertTrue(i18n.uses_24h("fr"))
        self.assertTrue(i18n.uses_24h("de"))

    def test_clock_format_follows_language(self):
        self.assertEqual(i18n.clock(D, "fr"), "15:48")
        self.assertEqual(i18n.clock(D, "en-US"), "3:48 PM")


class CurrencyCountryHolidayTests(unittest.TestCase):
    def test_base_currency(self):
        self.assertEqual(i18n.base_currency("en-US"), "USD")
        self.assertEqual(i18n.base_currency("en-GB"), "GBP")
        self.assertEqual(i18n.base_currency("en-AU"), "AUD")
        self.assertEqual(i18n.base_currency("fr"), "EUR")
        self.assertEqual(i18n.base_currency("zz"), "USD")   # unknown default

    def test_country(self):
        self.assertEqual(i18n.country("nl"), "NL")
        self.assertEqual(i18n.country("en-AU"), "AU")
        self.assertEqual(i18n.country("zz"), "US")          # unknown default

    def test_holiday_localization(self):
        self.assertEqual(i18n.holiday("Christmas Day", "fr"), "Noël")
        self.assertIsNone(i18n.holiday("Some Local Fete", "fr"))  # no translation
        self.assertIsNone(i18n.holiday("Christmas Day", None))    # no language


class LocalizerTests(unittest.TestCase):
    def test_translate_and_flags(self):
        fr = i18n.Localizer("fr")
        self.assertEqual(fr.t("SUNSET", "sun"), "COUCHER")
        self.assertTrue(fr.is_24h)
        self.assertEqual(fr.unit("D"), "J")

    def test_english_localizer_is_noop(self):
        en = i18n.Localizer("en-US")
        self.assertEqual(en.t("SUNSET", "sun"), "SUNSET")
        self.assertFalse(en.is_24h)

    def test_lang_base_strips_region(self):
        self.assertEqual(i18n.Localizer("en-GB").lang_base, "en")
        self.assertEqual(i18n.Localizer("fr").lang_base, "fr")

    def test_country_and_base_currency(self):
        self.assertEqual(i18n.Localizer("en-GB").base_currency(), "GBP")
        self.assertEqual(i18n.Localizer("nl").country(), "NL")


class BabelBackedTests(unittest.TestCase):
    """Date/month/number use babel for CLDR output; every helper degrades to an
    English-ish fallback without it, so we assert shape always and exact values
    only when babel is installed (the production dependency)."""

    def test_weekday_month_are_uppercase_nonempty(self):
        for lang in ("en-US", "fr", "de"):
            self.assertTrue(i18n.weekday(D, lang).isupper())
            self.assertTrue(i18n.month(D, lang))

    def test_date_order_is_locale_specific(self):
        en = i18n.date(D, "en-US")
        self.assertIn("JULY", en)
        self.assertIn("10", en)
        if HAS_BABEL:
            # Romance/Germanic order: day precedes month.
            self.assertEqual(i18n.date(D, "fr"), "10 JUILLET")
            self.assertEqual(i18n.date(D, "en-US"), "JULY 10")

    def test_number_separators(self):
        if HAS_BABEL:
            self.assertEqual(i18n.number(1234.5, "en-US"), "1,234.50")
            self.assertEqual(i18n.number(1234.5, "de"), "1.234,50")
            self.assertEqual(i18n.number(1234.5, "fr"), "1 234,50")
        else:
            # Fallback still produces a parseable, non-empty string.
            self.assertTrue(i18n.number(1234.5, "de"))


class LocalizationDataFileTests(unittest.TestCase):
    """All localization data lives in i18n_data.json (loaded at import), not in code.
    Lock that contract: the file is valid and populated, the loader fills the module
    tables, and a missing file degrades to defaults instead of crashing."""

    def test_data_file_is_valid_and_populated(self):
        import json
        path = pathlib.Path(i18n.__file__).with_name("i18n_data.json")
        self.assertTrue(path.is_file(), "i18n_data.json must ship next to i18n.py")
        data = json.loads(path.read_text(encoding="utf-8"))
        for section in ("languages", "strings", "holidays",
                        "base_currency", "country"):
            self.assertIn(section, data)
            self.assertTrue(data[section], f"{section} should not be empty")
        # 'strings' is grouped by context/domain; each entry uses the
        # {context, translations} schema, with a translator context note.
        for domain, entries in data["strings"].items():
            for key, entry in entries.items():
                self.assertIn("context", entry, f"{domain}.{key} missing context note")
                self.assertIn("translations", entry)
        self.assertEqual(data["strings"]["sun"]["SUNSET"]["translations"]["fr"], "COUCHER")
        # The same word differs by domain (weather level vs tide height).
        self.assertEqual(data["strings"]["weather"]["HIGH"]["translations"]["fr"], "ELEVE")
        self.assertEqual(data["strings"]["tides"]["HIGH"]["translations"]["fr"], "HAUTE")
        self.assertEqual(data["holidays"]["christmas day"]["translations"]["fr"], "Noël")
        self.assertEqual(data["base_currency"]["en-gb"], "GBP")
        self.assertEqual(data["country"]["nl"], "NL")

    def test_loader_populates_module_tables(self):
        self.assertTrue(all([i18n._STRINGS, i18n._DURATION_UNITS, i18n._HOLIDAYS,
                             i18n._BASE_CURRENCY, i18n._COUNTRY, i18n.LANGUAGE_OPTIONS]))
        # The loader flattens into {domain: {NAME: {lang: value}}}.
        self.assertEqual(i18n._STRINGS["sun"]["SUNSET"]["fr"], "COUCHER")

    def test_missing_file_degrades_gracefully(self):
        original = i18n._DATA_PATH
        try:
            i18n._DATA_PATH = original + ".does-not-exist"
            strings, holidays, cur, country, langs = i18n._load_i18n_data()
            self.assertEqual((strings, holidays, cur, country), ({}, {}, {}, {}))
            # ...but the Language list still has at least English so the UI works.
            self.assertTrue(langs and langs[0]["value"].startswith("en"))
        finally:
            i18n._DATA_PATH = original


class LanguageOptionsTests(unittest.TestCase):
    def test_language_options_shape(self):
        self.assertTrue(i18n.LANGUAGE_OPTIONS)
        for opt in i18n.LANGUAGE_OPTIONS:
            self.assertIn("value", opt)
            self.assertIn("label", opt)
        values = {o["value"] for o in i18n.LANGUAGE_OPTIONS}
        self.assertIn("en-US", values)
        self.assertIn("pt-BR", values)   # a non-European regional variant


class RegionalVariantTests(unittest.TestCase):
    """A region-tagged language inherits its base language's translations but keeps
    its own currency/country (pt-BR reuses pt words but resolves to Brazil / BRL)."""

    def test_variant_inherits_base_translations(self):
        self.assertEqual(i18n.translate("SUNSET", "pt-BR", "sun"),
                         i18n.translate("SUNSET", "pt", "sun"))
        self.assertEqual(i18n.duration_unit("D", "pt-BR"), i18n.duration_unit("D", "pt"))

    def test_variant_currency_and_country_override_base(self):
        self.assertEqual(i18n.base_currency("pt-BR"), "BRL")
        self.assertEqual(i18n.country("pt-BR"), "BR")
        self.assertEqual(i18n.base_currency("pt"), "EUR")     # base unchanged
        self.assertEqual(i18n.base_currency("es-MX"), "MXN")
        self.assertEqual(i18n.country("fr-CA"), "CA")
        self.assertEqual(i18n.base_currency("de-CH"), "CHF")

    def test_expanded_base_languages(self):
        self.assertEqual(i18n.base_currency("da"), "DKK")
        self.assertEqual(i18n.country("sv"), "SE")
        self.assertEqual(i18n.base_currency("af"), "ZAR")

    def test_scandinavian_strings_present(self):
        self.assertEqual(i18n.translate("SUNSET", "sv", "sun"), "SOLNEDGÅNG")
        self.assertEqual(i18n.translate("SNOW", "da", "weather"), "SNE")


def _accepts(fn, name):
    """The exact predicate app.py._fetch_accepts uses to decide whether to inject a
    helper: the parameter is named, or the function takes **kwargs. Kept in lockstep
    here so a Python signature-inspection change would surface in tests."""
    params = inspect.signature(fn).parameters
    return name in params or any(p.kind == p.VAR_KEYWORD for p in params.values())


class InjectionContractTests(unittest.TestCase):
    def test_classic_four_arg_app_opts_into_nothing(self):
        def fetch(settings, format_lines, get_rows, get_cols):
            return []
        for helper in ("i18n", "get_weather", "get_location"):
            self.assertFalse(_accepts(fetch, helper))

    def test_declared_parameter_opts_in(self):
        def fetch(settings, format_lines, get_rows, get_cols, i18n=None):
            return []
        self.assertTrue(_accepts(fetch, "i18n"))
        self.assertFalse(_accepts(fetch, "get_weather"))

    def test_var_keyword_opts_into_everything(self):
        def fetch(settings, format_lines, get_rows, get_cols, **kw):
            return []
        for helper in ("i18n", "get_weather", "get_location"):
            self.assertTrue(_accepts(fetch, helper))


if __name__ == "__main__":
    unittest.main()
