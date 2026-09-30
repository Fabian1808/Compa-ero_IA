"""
Terminology and localization contract.

These tests protect the language rules without needing a browser, by reading the
catalog sources directly. They fail when a term drifts, when a locale is left
incomplete, or when the backend starts emitting prose instead of message codes.
"""

from pathlib import Path

import pytest

# backend/tests/unit/test_terminology_contract.py -> repo root is three levels up.
FRONTEND = Path(__file__).resolve().parents[3] / "frontend"
CATALOG_DIR = FRONTEND / "src" / "i18n" / "locales"
ES_CATALOG = CATALOG_DIR / "es-PE.ts"
EN_CATALOG = CATALOG_DIR / "en-US.ts"
GLOSSARY = FRONTEND / "src" / "i18n" / "glossary.ts"

# Keys whose value is a nested object of plural forms rather than a plain string.
_PLURAL_FORM_KEYS = {"forms", "category"}


def parse_catalog_keys(path: Path) -> set[str]:
    """
    Extract dotted keys from a catalog file.

    A small tokenizer is used instead of a line-based regex so that an object
    written across several lines and one written inline on a single line produce
    the same result. Keys inside a `forms` block are skipped because plural forms
    are values rather than independently addressable keys.
    """
    lines = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        # Whole-line comments only: an inline `//` cannot be distinguished from
        # the `//` inside an import path such as '../types'.
        if stripped.startswith(("//", "*", "/*")):
            continue
        if stripped.startswith("import "):
            continue
        if stripped.startswith("export const"):
            # Keep the object literal, drop only the declaration prefix.
            lines.append(stripped[stripped.index("{") :])
            continue
        lines.append(raw_line)
    source = "\n".join(lines)

    keys: set[str] = set()
    stack: list[str] = []
    pending: str | None = None
    skipping_depth: int | None = None

    def commit() -> None:
        """Record `pending` as a scalar leaf, then clear it."""
        nonlocal pending
        if pending is not None:
            if skipping_depth is None and pending not in _PLURAL_FORM_KEYS:
                keys.add(".".join([*stack, pending]))
            pending = None

    index = 0
    length = len(source)

    while index < length:
        char = source[index]

        if char in "'\"":
            quote = char
            index += 1
            while index < length and source[index] != quote:
                index += 1
            index += 1
            commit()
            continue

        if char == "{":
            if skipping_depth is not None:
                skipping_depth += 1
            elif pending is not None:
                if pending == "forms":
                    # 1 means "inside the forms block"; the matching '}'
                    # brings it back to 0 and ends the skip.
                    skipping_depth = 1
                else:
                    stack.append(pending)
                    keys.add(".".join(stack))
                pending = None
            index += 1
            continue

        if char == "}":
            commit()
            if skipping_depth is not None:
                skipping_depth -= 1
                if skipping_depth == 0:
                    skipping_depth = None
            elif stack:
                stack.pop()
            index += 1
            continue

        if char == "," or char == "\n":
            commit()
            index += 1
            continue

        if char.isalpha() or char == "_":
            start = index
            while index < length and (source[index].isalnum() or source[index] in "_-"):
                index += 1
            word = source[start:index]

            # Look ahead past whitespace for the ':' that makes this a key.
            lookahead = index
            while lookahead < length and source[lookahead].isspace():
                lookahead += 1
            if lookahead < length and source[lookahead] == ":":
                if skipping_depth is None:
                    pending = word
            continue

        index += 1

    return keys


@pytest.fixture(scope="module")
def es_keys() -> set[str]:
    return parse_catalog_keys(ES_CATALOG)


@pytest.fixture(scope="module")
def en_keys() -> set[str]:
    return parse_catalog_keys(EN_CATALOG)


# --------------------------------------------------------------------------
# Catalog completeness
# --------------------------------------------------------------------------
def test_both_catalogs_parse(es_keys, en_keys):
    assert es_keys, "the es-PE catalog could not be parsed"
    assert en_keys, "the en-US catalog could not be parsed"


def test_english_catalog_has_no_missing_keys(es_keys, en_keys):
    """
    English is a planned release, so it must stay structurally complete.

    A missing key would fall back to Spanish at runtime, which is a worse
    failure than an obviously untranslated English string.
    """
    missing = es_keys - en_keys
    assert not missing, f"en-US is missing keys: {sorted(missing)}"


def test_spanish_catalog_has_no_extra_keys(es_keys, en_keys):
    extra = en_keys - es_keys
    assert not extra, f"en-US defines keys absent from es-PE: {sorted(extra)}"


# --------------------------------------------------------------------------
# Required terminology
# --------------------------------------------------------------------------
def test_official_main_menu_is_present(es_keys):
    for key in (
        "nav.home",
        "nav.myWork",
        "nav.projects",
        "nav.people",
        "nav.calendar",
        "nav.memory",
        "nav.connections",
        "nav.settings",
    ):
        assert key in es_keys, f"missing official menu entry: {key}"


def test_official_work_states_are_present(es_keys):
    for key in (
        "work.states.pending",
        "work.states.inProgress",
        "work.states.blocked",
        "work.states.waiting",
        "work.states.needsDecision",
        "work.states.completed",
    ):
        assert key in es_keys, f"missing official work state: {key}"


def test_official_ai_states_are_present(es_keys):
    for key in (
        "ai.states.detected",
        "ai.states.inferred",
        "ai.states.suggested",
        "ai.states.confirmed",
        "ai.states.executed",
    ):
        assert key in es_keys, f"missing official AI state: {key}"


def test_product_name_is_never_localized():
    """
    The product name is not a translatable string.

    It must stay uppercase and identical in every locale, so it is sourced from
    the glossary constant instead of being typed into a catalog entry.
    """
    glossary = GLOSSARY.read_text(encoding="utf-8")
    assert "PRODUCT_NAME = 'AI WORKMATE'" in glossary

    for catalog in (ES_CATALOG, EN_CATALOG):
        text = catalog.read_text(encoding="utf-8")
        assert "name: PRODUCT_NAME" in text, f"{catalog.name} must not hardcode the product name"
        assert "'AI Workmate'" not in text, f"{catalog.name} contains the wrong product casing"


def test_glossary_work_states_match_the_catalog():
    """
    The glossary and the catalog must not disagree about official wording.

    A divergence here is how "Completado" and "Completada" end up both shipping.
    """
    glossary = GLOSSARY.read_text(encoding="utf-8")
    catalog = ES_CATALOG.read_text(encoding="utf-8")

    for state in ("Pendiente", "En curso", "Bloqueado", "Esperando respuesta", "Requiere decisión"):
        assert f"'{state}'" in glossary, f"{state} missing from the glossary"
        assert f"'{state}'" in catalog, f"{state} missing from the es-PE catalog"


# --------------------------------------------------------------------------
# No hardcoded visible text in views
# --------------------------------------------------------------------------
# Files that render text and therefore must read it from the catalogs.
VIEW_FILES = [
    FRONTEND / "src" / "main.tsx",
    FRONTEND / "src" / "components" / "layout" / "Sidebar.tsx",
    FRONTEND / "src" / "pages" / "FirstRunInstallerPage.tsx",
]

# Pure composition files. They contain no user-facing text, so they are checked
# for hardcoded strings but are not required to call the translation function.
ROUTING_FILES = [
    FRONTEND / "src" / "App.tsx",
]

# Spanish words that would mean a string was left inline in a view.
SPANISH_MARKERS = (
    "Configuración",
    "Instalando",
    "Instalación",
    "Conexiones",
    "Calendario",
    "Reintentar",
    "Cancelar",
    "Siguiente",
    "Guardar",
    "Eliminar",
    "Cargando",
)


@pytest.mark.parametrize("path", VIEW_FILES + ROUTING_FILES, ids=lambda p: p.name)
def test_views_do_not_hardcode_visible_text(path):
    if not path.exists():
        pytest.skip(f"{path.name} is not present")

    text = path.read_text(encoding="utf-8")
    offenders = [marker for marker in SPANISH_MARKERS if marker in text]

    assert not offenders, (
        f"{path.name} hardcodes user-facing text {offenders}; move it into the i18n catalogs"
    )


@pytest.mark.parametrize("path", VIEW_FILES, ids=lambda p: p.name)
def test_views_read_text_through_the_catalog(path):
    """A view is only compliant if it actually calls the translation function."""
    if not path.exists():
        pytest.skip(f"{path.name} is not present")

    text = path.read_text(encoding="utf-8")
    assert "useI18n" in text, f"{path.name} must read its text through useI18n()"
