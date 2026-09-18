import csv
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "design"
DATA = PLUGIN / "data"
SEARCH = PLUGIN / "scripts" / "search.py"

sys.path.insert(0, str(PLUGIN / "scripts"))
import catalog  # noqa: E402

REQUIRED_COLUMNS = {
    "styles.csv": {"id", "nombre", "resumen", "cuando_usar", "cuando_evitar", "efectos", "riesgos_a11y", "keywords"},
    "palettes.csv": {
        "id", "dominio", "mood", "primario", "secundario", "acento", "fondo_claro", "fondo_oscuro",
        "texto_claro", "texto_oscuro", "exito", "aviso", "error", "notas_contraste", "keywords",
    },
    "typography.csv": {"id", "titulos", "cuerpo", "mood", "base_px", "line_height", "cuando_usar", "notas", "keywords"},
    "ux-guidelines.csv": {"id", "categoria", "prioridad", "regla", "criterio", "wcag", "anti_patron", "keywords"},
    "motion.csv": {"id", "nombre", "duracion_ms", "easing", "uso", "reduced_motion", "compose", "web", "keywords"},
    "stacks/compose.csv": {"id", "tema", "regla", "implementacion", "anti_patron", "keywords"},
    "stacks/web.csv": {"id", "tema", "regla", "implementacion", "anti_patron", "keywords"},
}
PRIORITIES = {"critica", "alta", "media", "baja"}
HEX = "0123456789abcdefABCDEF"


def rows(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def run_search(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SEARCH), *args], text=True, capture_output=True, check=False, encoding="utf-8"
    )


class CatalogContractTests(unittest.TestCase):
    def test_every_catalog_has_required_columns_and_unique_nonempty_ids(self) -> None:
        for name, columns in REQUIRED_COLUMNS.items():
            with self.subTest(catalog=name):
                data = rows(name)
                self.assertGreaterEqual(len(data), 8, name)
                self.assertTrue(columns <= set(data[0]), columns - set(data[0]))
                ids = [r["id"] for r in data]
                self.assertEqual(len(ids), len(set(ids)))
                for row in data:
                    for column in columns:
                        self.assertTrue(row[column].strip(), f"{name}:{row['id']}:{column} vacio")

    def test_catalog_text_has_no_accents_and_no_third_party_attribution(self) -> None:
        banned = ("inspirado en", "basado en", "github.com")
        for name in REQUIRED_COLUMNS:
            text = (DATA / name).read_text(encoding="utf-8").lower()
            with self.subTest(catalog=name):
                for char in "áéíóúñ":
                    self.assertNotIn(char, text, f"{name} contiene '{char}'")
                for phrase in banned:
                    self.assertNotIn(phrase, text)

    def test_ux_guidelines_have_valid_priority_and_wcag_reference(self) -> None:
        for row in rows("ux-guidelines.csv"):
            with self.subTest(id=row["id"]):
                self.assertIn(row["prioridad"], PRIORITIES)
                self.assertRegex(row["wcag"], r"^(\d\.\d\.\d+( [A]{1,3})?(; )?)+$|^n/a$")

    def test_palettes_use_hex_colors_with_readable_contrast(self) -> None:
        for row in rows("palettes.csv"):
            with self.subTest(id=row["id"]):
                for column in ("primario", "secundario", "acento", "fondo_claro", "fondo_oscuro",
                               "texto_claro", "texto_oscuro", "exito", "aviso", "error"):
                    value = row[column]
                    self.assertEqual(7, len(value), f"{column}={value}")
                    self.assertEqual("#", value[0])
                    self.assertTrue(all(c in HEX for c in value[1:]), value)
                # Texto sobre fondo en cada modo cumple AA para texto normal (4.5:1).
                self.assertGreaterEqual(catalog.contrast_ratio(row["texto_claro"], row["fondo_claro"]), 4.5)
                self.assertGreaterEqual(catalog.contrast_ratio(row["texto_oscuro"], row["fondo_oscuro"]), 4.5)
                # Primario sobre fondo claro sirve al menos para botones y texto grande (3:1).
                self.assertGreaterEqual(catalog.contrast_ratio(row["primario"], row["fondo_claro"]), 3.0)

    def test_contrast_claims_in_notes_match_computed_ratios(self) -> None:
        # "X:1" en notas_contraste sobre el primario y blanco debe coincidir con el calculo (tolerancia 0.15).
        for row in rows("palettes.csv"):
            note = row["notas_contraste"]
            match = re.search(r"(?:primario|azul|verde|violeta|cian|indigo|rojo)[^;.]*?(\d+(?:\.\d)?):1 sobre blanco", note, re.I)
            if not match:
                continue
            with self.subTest(id=row["id"]):
                claimed = float(match.group(1))
                actual = catalog.contrast_ratio(row["primario"], "#FFFFFF")
                self.assertAlmostEqual(claimed, actual, delta=0.15, msg=f"{row['id']}: nota {claimed}, real {actual}")

    def test_stack_names_are_consistent_across_catalogs(self) -> None:
        self.assertEqual({"compose", "web"}, set(catalog.STACKS))
        for stack in catalog.STACKS:
            self.assertTrue((DATA / "stacks" / f"{stack}.csv").is_file())


class RelevanceTests(unittest.TestCase):
    CASES = [
        ("fintech banca confianza", "palette", "fintech-confianza"),
        ("app de salud pacientes", "palette", "salud-calma"),
        ("dashboard interno datos densos", "style", "densidad-operativa"),
        ("landing minimalista", "style", "minimalismo-editorial"),
        ("contraste texto minimo", "ux", "a11y-contraste-texto"),
        ("target tactil 48dp", "ux", "touch-area-minima"),
        ("reduced motion animacion", "motion", "reduced-motion"),
        ("lista larga scroll rendimiento", "stack:compose", "lazycolumn-keys"),
        ("boton icono sin etiqueta accesible", "stack:web", "boton-icono-nombre"),
        ("tipografia lectura larga", "typography", "editorial-lectura"),
        ("landing page saas startup moderna", "style", "minimalismo-editorial"),
        ("landing page saas startup moderna", "palette", "neutral-producto"),
    ]

    def test_known_queries_rank_expected_row_in_top_three(self) -> None:
        for query, domain, expected in self.CASES:
            with self.subTest(query=query):
                stack = None
                if domain.startswith("stack:"):
                    domain, stack = "stack", domain.split(":", 1)[1]
                hits = catalog.search(query, domain, stack=stack, limit=3)
                self.assertIn(expected, [h["id"] for h in hits], [h["id"] for h in hits])

    def test_nonsense_query_returns_nothing_instead_of_noise(self) -> None:
        self.assertEqual([], catalog.search("zzqx wvpt", "style", limit=3))

    def test_query_normalizes_accents(self) -> None:
        plain = catalog.search("tipografia lectura", "typography", limit=3)
        accented = catalog.search("tipografía lectura", "typography", limit=3)
        self.assertEqual([h["id"] for h in plain], [h["id"] for h in accented])


class SearchCliTests(unittest.TestCase):
    def test_help_and_domain_search_json(self) -> None:
        self.assertEqual(0, run_search("--help").returncode)
        result = run_search("fintech banca", "--domain", "palette", "-n", "2", "--json")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("palette", payload["domain"])
        # -n limita; no se rellena con ruido para llegar al limite.
        self.assertTrue(1 <= len(payload["results"]) <= 2)
        self.assertEqual("fintech-confianza", payload["results"][0]["id"])

    def test_empty_result_exits_with_code_one_and_suggestion(self) -> None:
        result = run_search("zzqx wvpt", "--domain", "style", "--json")
        self.assertEqual(1, result.returncode)
        payload = json.loads(result.stdout)
        self.assertEqual([], payload["results"])
        self.assertIn("sugerencia", payload)

    def test_unknown_domain_or_stack_is_a_usage_error(self) -> None:
        self.assertEqual(2, run_search("x", "--domain", "nope").returncode)
        self.assertEqual(2, run_search("x", "--stack", "swiftui").returncode)

    def test_design_system_persists_master_and_refuses_to_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = run_search(
                "app de salud pacientes", "--design-system", "-p", "Mi Salud",
                "--stack", "compose", "--persist", "--output-dir", tmp,
            )
            self.assertEqual(0, first.returncode, first.stderr)
            master = Path(tmp) / "design-system" / "mi-salud" / "MASTER.md"
            self.assertTrue(master.is_file())
            text = master.read_text(encoding="utf-8")
            for section in ("## Estilo", "## Color", "## Tipografia", "## Espaciado", "## Motion",
                            "## Accesibilidad", "## Anti-patrones", "## Stack: compose"):
                self.assertIn(section, text)
            self.assertIn("salud-calma", text)
            self.assertIn("MaterialTheme", text)

            second = run_search(
                "otra cosa", "--design-system", "-p", "Mi Salud", "--stack", "compose",
                "--persist", "--output-dir", tmp,
            )
            self.assertEqual(3, second.returncode)
            self.assertEqual(text, master.read_text(encoding="utf-8"))

            page = run_search(
                "pantalla de historial denso", "--design-system", "-p", "Mi Salud", "--stack", "compose",
                "--persist", "--output-dir", tmp, "--page", "historial",
            )
            self.assertEqual(0, page.returncode, page.stderr)
            self.assertTrue((Path(tmp) / "design-system" / "mi-salud" / "pages" / "historial.md").is_file())
            self.assertEqual(text, master.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


class DesignPluginLayoutTests(unittest.TestCase):
    def frontmatter(self, path: Path) -> dict:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(match, path)
        fields = {}
        for line in match.group(1).splitlines():
            if line and not line.startswith(" ") and ":" in line:
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip()
        return fields

    def test_ui_review_dispatches_a_read_only_agent_with_codex_parity(self) -> None:
        skill = (PLUGIN / "skills" / "ui-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("design:ui-reviewer", skill)
        fm = self.frontmatter(PLUGIN / "agents" / "ui-reviewer.md")
        self.assertEqual("ui-reviewer", fm["name"])
        self.assertNotIn("Write", fm["tools"])
        self.assertNotIn("Edit", fm["tools"])
        self.assertTrue((ROOT / ".codex" / "agents" / "ui-reviewer.toml").is_file())

    def test_plugin_root_references_resolve(self) -> None:
        for path in list(PLUGIN.rglob("SKILL.md")) + list((PLUGIN / "agents").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^`\s\"']+)", text):
                    self.assertTrue((PLUGIN / ref).exists(), ref)

    def test_stack_catalogs_cover_every_stack_named_in_skills(self) -> None:
        for path in PLUGIN.rglob("SKILL.md"):
            text = path.read_text(encoding="utf-8")
            for stack in re.findall(r"--stack (?:<)?([a-z|]+)", text):
                for name in stack.split("|"):
                    self.assertIn(name, catalog.STACKS + ("stack",), path.name)


class SurfaceModeTests(unittest.TestCase):
    def test_styles_declare_valid_modes_and_every_mode_has_a_style(self) -> None:
        import search
        seen = set()
        for row in rows("styles.csv"):
            modes = row["modo"].split("|")
            self.assertTrue(set(modes) <= set(search.MODES), row["id"])
            seen |= set(modes)
        self.assertEqual(set(search.MODES), seen)

    def test_mode_is_inferred_from_query_and_filters_style(self) -> None:
        import search
        self.assertEqual("persuadir", search.infer_mode("landing page saas startup"))
        self.assertEqual("leer", search.infer_mode("documentacion api desarrolladores"))
        self.assertEqual("operar", search.infer_mode("app de salud pacientes"))
        self.assertIsNone(search.infer_mode("zzqx"))
        ds = search.build_design_system("documentacion api desarrolladores", "X", "web")
        self.assertEqual("leer", ds["mode"])
        self.assertEqual("inferido", ds["mode_source"])
        self.assertIn("leer", ds["style"]["modo"])
        forced = search.build_design_system("zzqx", "X", "web", mode="experimentar")
        self.assertEqual(("experimentar", "explicito"), (forced["mode"], forced["mode_source"]))
        default = search.build_design_system("zzqx", "X", "web")
        self.assertEqual(("operar", "por defecto"), (default["mode"], default["mode_source"]))
        self.assertIn("se asumio `operar`", search.render_master(default))

    def test_master_has_mode_section_and_product_file_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = run_search(
                "landing saas startup", "--design-system", "-p", "Acme", "--stack", "web",
                "--persist", "--output-dir", tmp, "--audience", "Compradores tecnicos B2B",
                "--context", "Desktop en horario laboral", "--voice", "Directa",
            )
            self.assertEqual(0, first.returncode, first.stderr)
            base = Path(tmp) / "design-system" / "acme"
            master = (base / "MASTER.md").read_text(encoding="utf-8")
            self.assertIn("## Modo", master)
            self.assertIn("**persuadir** (inferido)", master)
            self.assertIn("PRODUCT.md", master)
            product = (base / "PRODUCT.md").read_text(encoding="utf-8")
            self.assertIn("Compradores tecnicos B2B", product)
            self.assertIn("`persuadir`", product)
            again = run_search(
                "otra", "--design-system", "-p", "Acme", "--stack", "web", "--persist", "--output-dir", tmp,
                "--page", "precios", "--audience", "Otro", "--context", "Otro",
            )
            self.assertEqual(0, again.returncode, again.stderr)
            self.assertEqual(product, (base / "PRODUCT.md").read_text(encoding="utf-8"))
            self.assertIn("ya existe", again.stdout)
            half = run_search("x", "--design-system", "-p", "Acme", "--stack", "web", "--persist",
                              "--output-dir", tmp, "--page", "p2", "--audience", "solo")
            self.assertEqual(2, half.returncode)
