from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
import importlib
import re

ROOT = Path(__file__).resolve().parents[1] / "docs"
BASE = "https://marekzajda.github.io/closure-ethics-for-autonomous-ai-agents/"
LOCALIZED = ("cs", "de", "fr", "es")
PAGES = (
    "index.html", "principles.html", "symbiosis.html", "formalism.html",
    "implementation.html", "constitution.html", "security.html",
    "communication.html", "standard.html", "evals.html", "genealogy.html",
)

MODULES = {
    lang: importlib.import_module(f"full_{lang}")
    for lang in LOCALIZED
}

NAV = {
    "cs": {"Overview":"Přehled","Principles":"Principy","Symbiosis":"Symbióza","Formalism":"Formalismus","Implementation":"Implementace","Constitution":"Konstituce","Security":"Bezpečnost","Communication":"Komunikace","Standard":"Standard","Evals":"Evaly","Genealogy":"Genealogie"},
    "de": {"Overview":"Überblick","Principles":"Prinzipien","Symbiosis":"Symbiose","Formalism":"Formalismus","Implementation":"Implementierung","Constitution":"Verfassung","Security":"Sicherheit","Communication":"Kommunikation","Standard":"Standard","Evals":"Evals","Genealogy":"Genealogie"},
    "fr": {"Overview":"Vue d’ensemble","Principles":"Principes","Symbiosis":"Symbiose","Formalism":"Formalisme","Implementation":"Implémentation","Constitution":"Constitution","Security":"Sécurité","Communication":"Communication","Standard":"Standard","Evals":"Évaluations","Genealogy":"Généalogie"},
    "es": {"Overview":"Resumen","Principles":"Principios","Symbiosis":"Simbiosis","Formalism":"Formalismo","Implementation":"Implementación","Constitution":"Constitución","Security":"Seguridad","Communication":"Comunicación","Standard":"Estándar","Evals":"Evaluaciones","Genealogy":"Genealogía"},
}

TEXT = {
    "cs": {
        "Closure Ethics research project":"výzkumný projekt Closure Ethics",
        "Research genealogy":"Výzkumná genealogie",
        "Human–AI Symbiosis":"Symbióza člověka a AI",
        "Evaluation Suite":"Evaluační sada",
        "Agent Constitution":"Konstituce agenta",
        "formalism draft":"draft formalismu",
        "working record":"pracovní záznam",
        "Source":"Zdroj",
        "Sitemap":"Sitemap",
    },
    "de": {
        "Closure Ethics research project":"Closure-Ethics-Forschungsprojekt",
        "Research genealogy":"Forschungsgenealogie",
        "Human–AI Symbiosis":"Mensch–KI-Symbiose",
        "Evaluation Suite":"Evaluationssuite",
        "Agent Constitution":"Agentenverfassung",
        "formalism draft":"Formalismus-Entwurf",
        "working record":"Arbeitsdatensatz",
        "Source":"Quelle",
        "Sitemap":"Sitemap",
    },
    "fr": {
        "Closure Ethics research project":"projet de recherche Closure Ethics",
        "Research genealogy":"Généalogie de recherche",
        "Human–AI Symbiosis":"Symbiose humain–IA",
        "Evaluation Suite":"Suite d’évaluation",
        "Agent Constitution":"Constitution de l’agent",
        "formalism draft":"draft du formalisme",
        "working record":"registre de travail",
        "Source":"Source",
        "Sitemap":"Sitemap",
    },
    "es": {
        "Closure Ethics research project":"proyecto de investigación Closure Ethics",
        "Research genealogy":"Genealogía de investigación",
        "Human–AI Symbiosis":"Simbiosis humano–IA",
        "Evaluation Suite":"Suite de evaluación",
        "Agent Constitution":"Constitución del agente",
        "formalism draft":"draft del formalismo",
        "working record":"registro de trabajo",
        "Source":"Fuente",
        "Sitemap":"Sitemap",
    },
}

ROOT_FILES = (
    "agent-policy.json", "provenance.json", "SHA256SUMS.txt", "llms.txt",
    "sitemap.xml", "robots.txt",
)


def page_url(lang: str, page: str) -> str:
    if lang == "en":
        return BASE if page == "index.html" else BASE + page
    return BASE + lang + "/" + page


def localize_shell(source: str, lang: str, page: str) -> str:
    module = MODULES[lang]
    if page not in module.MAIN or page not in module.META:
        raise KeyError(f"missing complete {lang} localization for {page}")

    title, description = module.META[page]
    html = source
    html = re.sub(r'<html lang="en">', f'<html lang="{lang}">', html, count=1)
    html = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', html, count=1, flags=re.S)
    html = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{description}">',
        html,
        count=1,
    )
    html = re.sub(
        r'<link rel="canonical" href="[^"]+">',
        f'<link rel="canonical" href="{page_url(lang, page)}">',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta property="og:url" content="[^"]+">',
        f'<meta property="og:url" content="{page_url(lang, page)}">',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta property="og:title" content="[^"]+">',
        f'<meta property="og:title" content="{title}">',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta property="og:description" content="[^"]+">',
        f'<meta property="og:description" content="{description}">',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta name="twitter:title" content="[^"]+">',
        f'<meta name="twitter:title" content="{title}">',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta name="twitter:description" content="[^"]+">',
        f'<meta name="twitter:description" content="{description}">',
        html,
        count=1,
    )

    # Replace only the content layer; the canonical English DOM remains the structural template.
    html, n = re.subn(r'<main>.*?</main>', module.MAIN[page], html, count=1, flags=re.S)
    if n != 1:
        raise ValueError(f"could not replace <main> in {page}")

    # A localized page is one directory deeper than its English source.
    html = html.replace('href="assets/', 'href="../assets/')
    html = html.replace('src="assets/', 'src="../assets/')
    html = html.replace('href="downloads/', 'href="../downloads/')
    for root_file in ROOT_FILES:
        html = html.replace(f'href="{root_file}"', f'href="../{root_file}"')

    # Translate navigation labels without touching href values.
    for en, translated in NAV[lang].items():
        html = html.replace(f'>{en}<', f'>{translated}<')
    for en, translated in TEXT[lang].items():
        html = html.replace(en, translated)

    # Localized alternate links are deliberately the same cross-language set on every variant.
    return html


def build_localized_pages() -> None:
    for lang in LOCALIZED:
        out_dir = ROOT / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        for page in PAGES:
            source = (ROOT / page).read_text(encoding="utf-8")
            localized = localize_shell(source, lang, page)
            (out_dir / page).write_text(localized, encoding="utf-8")


def build_sitemap() -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    langs = ("en",) + LOCALIZED
    for page in PAGES:
        for lang in langs:
            loc = page_url(lang, page)
            lines.append("  <url>")
            lines.append(f"    <loc>{escape(loc)}</loc>")
            for alt in langs:
                lines.append(
                    f'    <xhtml:link rel="alternate" hreflang="{alt}" href="{escape(page_url(alt, page))}" />'
                )
            lines.append(
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{escape(page_url("en", page))}" />'
            )
            lines.append("  </url>")
    lines.extend([
        "  <url>",
        f"    <loc>{escape(BASE + 'downloads/Closure_Ethics_Implementation_Spec_v0.1.pdf')}</loc>",
        "  </url>",
        "</urlset>",
    ])
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    build_localized_pages()
    build_sitemap()
    print(f"Built {len(LOCALIZED) * len(PAGES)} complete localized pages and 56 sitemap URLs")


if __name__ == "__main__":
    main()
