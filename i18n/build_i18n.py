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
    "implementation.html", "constitution.html", "comparison.html", "security.html",
    "communication.html", "standard.html", "evals.html", "genealogy.html",
)

MODULES = {
    lang: importlib.import_module(f"full_{lang}")
    for lang in LOCALIZED
}
COMPARISON_MODULES = {
    lang: importlib.import_module(f"comparison_{lang}")
    for lang in LOCALIZED
}

NAV = {
    "cs": {"Overview":"Přehled","Principles":"Principy","Symbiosis":"Symbióza","Formalism":"Formalismus","Implementation":"Implementace","Constitution":"Konstituce","Comparison":"Srovnání","Security":"Bezpečnost","Communication":"Komunikace","Standard":"Standard","Evals":"Evaly","Genealogy":"Genealogie"},
    "de": {"Overview":"Überblick","Principles":"Prinzipien","Symbiosis":"Symbiose","Formalism":"Formalismus","Implementation":"Implementierung","Constitution":"Verfassung","Comparison":"Vergleich","Security":"Sicherheit","Communication":"Kommunikation","Standard":"Standard","Evals":"Evals","Genealogy":"Genealogie"},
    "fr": {"Overview":"Vue d’ensemble","Principles":"Principes","Symbiosis":"Symbiose","Formalism":"Formalisme","Implementation":"Implémentation","Constitution":"Constitution","Comparison":"Comparaison","Security":"Sécurité","Communication":"Communication","Standard":"Standard","Evals":"Évaluations","Genealogy":"Généalogie"},
    "es": {"Overview":"Resumen","Principles":"Principios","Symbiosis":"Simbiosis","Formalism":"Formalismo","Implementation":"Implementación","Constitution":"Constitución","Comparison":"Comparación","Security":"Seguridad","Communication":"Comunicación","Standard":"Estándar","Evals":"Evaluaciones","Genealogy":"Genealogía"},
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

EVAL_PACKAGE = {
    "cs": '''<h2>Konkrétní end-to-end benchmark runner</h2><p>CEES v0.1 nyní propojuje 18 zmrazených scénářů s <code>runner.mjs</code>: <strong>scénář → zaslepený subject → nezávislý judge → pevný scorer → auditovatelný report</strong>. Testovaný subject nevidí gold pole <code>expected</code> ani <code>scoring</code>; ve výchozím režimu dostává pouze prompt a kontext. Runner podporuje deterministické seedované pořadí, opakované běhy, volitelný režim <code>--expose-action-envelope</code>, generické HTTP adaptéry pro subject/judge a artefakty manifest, transcript, výsledky a souhrn. Vestavěné referenční adaptéry slouží pouze k self-testu infrastruktury v CI a nesmějí být prezentovány jako vědecký benchmarkový výsledek.</p><div class="formula">05-evals/<br>├── schema.json<br>├── scenarios.jsonl<br>├── scoring.md<br>├── benchmark-card.md<br>├── validate.mjs<br>├── runner.mjs<br>├── adapter-protocol.md<br>├── adapters/<br>│&nbsp;&nbsp;├── http-subject.mjs<br>│&nbsp;&nbsp;├── http-judge.mjs<br>│&nbsp;&nbsp;├── reference-subject.mjs<br>│&nbsp;&nbsp;└── reference-judge.mjs<br>└── score.mjs</div><div class="actions"><a class="button primary" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/tree/main/05-evals">Otevřít benchmark ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/runner.mjs">runner.mjs ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/adapter-protocol.md">Protokol adaptérů ↗</a><a class="button" href="https://raw.githubusercontent.com/marekzajda/closure-ethics-for-autonomous-ai-agents/main/05-evals/scenarios.jsonl">Scénáře ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/scoring.md">Skórování ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/adapters/http-subject.mjs">HTTP subject ↗</a></div>''',
    "de": '''<h2>Konkreter End-to-End-Benchmark-Runner</h2><p>CEES v0.1 verbindet nun 18 eingefrorene Szenarien mit <code>runner.mjs</code>: <strong>Szenario → verblindetes Subject → unabhängiger Judge → fester Scorer → auditierbarer Report</strong>. Das getestete Subject sieht weder die Gold-Felder <code>expected</code> noch <code>scoring</code>; standardmäßig erhält es nur Prompt und Kontext. Der Runner unterstützt deterministisch geseedete Reihenfolge, wiederholte Durchläufe, den optionalen Modus <code>--expose-action-envelope</code>, generische HTTP-Adapter für Subject/Judge sowie Manifest-, Transcript-, Ergebnis- und Summary-Artefakte. Die eingebauten Referenzadapter dienen ausschließlich dem CI-Selbsttest der Infrastruktur und dürfen nicht als wissenschaftliches Benchmark-Ergebnis berichtet werden.</p><div class="formula">05-evals/<br>├── schema.json<br>├── scenarios.jsonl<br>├── scoring.md<br>├── benchmark-card.md<br>├── validate.mjs<br>├── runner.mjs<br>├── adapter-protocol.md<br>├── adapters/<br>│&nbsp;&nbsp;├── http-subject.mjs<br>│&nbsp;&nbsp;├── http-judge.mjs<br>│&nbsp;&nbsp;├── reference-subject.mjs<br>│&nbsp;&nbsp;└── reference-judge.mjs<br>└── score.mjs</div><div class="actions"><a class="button primary" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/tree/main/05-evals">Benchmark öffnen ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/runner.mjs">runner.mjs ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/adapter-protocol.md">Adapterprotokoll ↗</a><a class="button" href="https://raw.githubusercontent.com/marekzajda/closure-ethics-for-autonomous-ai-agents/main/05-evals/scenarios.jsonl">Szenarien ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/scoring.md">Scoring ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/adapters/http-subject.mjs">HTTP Subject ↗</a></div>''',
    "fr": '''<h2>Runner de benchmark end-to-end concret</h2><p>CEES v0.1 relie désormais 18 scénarios gelés à <code>runner.mjs</code> : <strong>scénario → subject aveuglé → judge indépendant → scorer fixe → rapport auditable</strong>. Le subject testé ne voit ni les champs gold <code>expected</code> ni <code>scoring</code> ; par défaut, il reçoit uniquement le prompt et le contexte. Le runner prend en charge un ordre déterministe seedé, des répétitions, le mode optionnel <code>--expose-action-envelope</code>, des adaptateurs HTTP génériques pour subject/judge ainsi que des artefacts manifest, transcript, résultats et synthèse. Les adaptateurs de référence intégrés servent uniquement à l'auto-test de la plomberie en CI et ne doivent pas être présentés comme des résultats scientifiques du benchmark.</p><div class="formula">05-evals/<br>├── schema.json<br>├── scenarios.jsonl<br>├── scoring.md<br>├── benchmark-card.md<br>├── validate.mjs<br>├── runner.mjs<br>├── adapter-protocol.md<br>├── adapters/<br>│&nbsp;&nbsp;├── http-subject.mjs<br>│&nbsp;&nbsp;├── http-judge.mjs<br>│&nbsp;&nbsp;├── reference-subject.mjs<br>│&nbsp;&nbsp;└── reference-judge.mjs<br>└── score.mjs</div><div class="actions"><a class="button primary" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/tree/main/05-evals">Ouvrir le benchmark ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/runner.mjs">runner.mjs ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/adapter-protocol.md">Protocole d'adaptateur ↗</a><a class="button" href="https://raw.githubusercontent.com/marekzajda/closure-ethics-for-autonomous-ai-agents/main/05-evals/scenarios.jsonl">Scénarios ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/scoring.md">Scoring ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/adapters/http-subject.mjs">HTTP subject ↗</a></div>''',
    "es": '''<h2>Runner de benchmark end-to-end concreto</h2><p>CEES v0.1 conecta ahora 18 escenarios congelados con <code>runner.mjs</code>: <strong>escenario → subject cegado → judge independiente → scorer fijo → informe auditable</strong>. El subject evaluado no ve los campos gold <code>expected</code> ni <code>scoring</code>; por defecto recibe únicamente el prompt y el contexto. El runner admite orden determinista con seed, ejecuciones repetidas, el modo opcional <code>--expose-action-envelope</code>, adaptadores HTTP genéricos para subject/judge y artefactos de manifest, transcript, resultados y resumen. Los adaptadores de referencia incorporados existen únicamente para el auto-test de la infraestructura en CI y no deben presentarse como evidencia científica del benchmark.</p><div class="formula">05-evals/<br>├── schema.json<br>├── scenarios.jsonl<br>├── scoring.md<br>├── benchmark-card.md<br>├── validate.mjs<br>├── runner.mjs<br>├── adapter-protocol.md<br>├── adapters/<br>│&nbsp;&nbsp;├── http-subject.mjs<br>│&nbsp;&nbsp;├── http-judge.mjs<br>│&nbsp;&nbsp;├── reference-subject.mjs<br>│&nbsp;&nbsp;└── reference-judge.mjs<br>└── score.mjs</div><div class="actions"><a class="button primary" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/tree/main/05-evals">Abrir benchmark ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/runner.mjs">runner.mjs ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/adapter-protocol.md">Protocolo de adaptadores ↗</a><a class="button" href="https://raw.githubusercontent.com/marekzajda/closure-ethics-for-autonomous-ai-agents/main/05-evals/scenarios.jsonl">Escenarios ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/scoring.md">Puntuación ↗</a><a class="button" href="https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/05-evals/adapters/http-subject.mjs">HTTP subject ↗</a></div>''',
}

ROOT_FILES = (
    "agent-policy.json", "provenance.json", "SHA256SUMS.txt", "llms.txt",
    "sitemap.xml", "robots.txt",
)


def page_url(lang: str, page: str) -> str:
    if lang == "en":
        return BASE if page == "index.html" else BASE + page
    return BASE + lang + "/" + page


def localized_content(lang: str, page: str) -> tuple[str, str, str]:
    if page == "comparison.html":
        module = COMPARISON_MODULES[lang]
        title, description = module.META
        return title, description, module.MAIN
    module = MODULES[lang]
    if page not in module.MAIN or page not in module.META:
        raise KeyError(f"missing complete {lang} localization for {page}")
    title, description = module.META[page]
    return title, description, module.MAIN[page]


def localize_shell(source: str, lang: str, page: str) -> str:
    title, description, main_html = localized_content(lang, page)
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

    html, n = re.subn(r'<main>.*?</main>', main_html, html, count=1, flags=re.S)
    if n != 1:
        raise ValueError(f"could not replace <main> in {page}")

    html = html.replace('href="assets/', 'href="../assets/')
    html = html.replace('src="assets/', 'src="../assets/')
    html = html.replace('href="downloads/', 'href="../downloads/')
    for root_file in ROOT_FILES:
        html = html.replace(f'href="{root_file}"', f'href="../{root_file}"')

    for en, translated in NAV[lang].items():
        html = html.replace(f'>{en}<', f'>{translated}<')
    for en, translated in TEXT[lang].items():
        html = html.replace(en, translated)

    if page == "evals.html":
        old_package = (
            r'<h2>[^<]+</h2><div class="formula">05-evals/<br>├── schema\.json<br>'
            r'├── scenarios\.jsonl<br>├── scoring\.md<br>└── benchmark-card\.md</div>'
            r'<div class="actions">.*?</div>'
        )
        html, n = re.subn(old_package, EVAL_PACKAGE[lang], html, count=1, flags=re.S)
        if n != 1:
            raise ValueError(f"could not replace localized eval package in {lang}/{page}")

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
    total_urls = len(PAGES) * (1 + len(LOCALIZED)) + 1
    print(f"Built {len(LOCALIZED) * len(PAGES)} complete localized pages and {total_urls} sitemap URLs")


if __name__ == "__main__":
    main()
