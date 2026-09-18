import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "design"
DETECT = PLUGIN / "scripts" / "detect.py"

sys.path.insert(0, str(PLUGIN / "scripts"))
import detect  # noqa: E402

COMPOSE_BAD = '''
@Composable
fun Pantalla(items: List<Item>) {
    Column(Modifier.verticalScroll(rememberScrollState())) {
        items.forEach { Fila(it) }
    }
    Text("Titulo", fontSize = 18.sp, color = Color(0xFF2563EB))
    Text("Mal", fontSize = 14.dp)
    IconButton(onClick = {}) {
        Icon(Icons.Default.Delete, contentDescription = null)
    }
    Row(Modifier.height(48.dp)) {
        Text("Nombre largo")
    }
    Icon(Icons.Default.Close, null, Modifier.size(20.dp).clickable { })
    LazyColumn { items(items) { Fila(it) } }
    Toast.makeText(ctx, "error", Toast.LENGTH_SHORT).show()
}
'''

COMPOSE_GOOD = '''
@Composable
fun Pantalla(items: List<Item>) {
    LazyColumn { items(items, key = { it.id }) { Fila(it) } }
    Text("Titulo", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
    IconButton(onClick = {}) {
        Icon(Icons.Default.Delete, contentDescription = "Eliminar nota")
    }
    Row(Modifier.heightIn(min = 48.dp)) { Text("Nombre largo") }
    val c = Color(0xFF000000) // design-detect: ignore compose-color-literal
}
'''

WEB_BAD = '''
<section>
  <p class="text-xs uppercase tracking-widest">Eyebrow</p>
  <img src="a.png">
  <div onClick={go}>Ir</div>
  <button><svg/></button>
  <input placeholder="Correo" />
  <span style="color:#2563EB">x</span>
  <h1 class="bg-clip-text">Grad</h1>
  <a tabindex="3">z</a>
</section>
<section class="flex md:flex-row-reverse"><p class="uppercase tracking-wide">Eyebrow 2</p></section>
<section class="flex md:flex-row-reverse"></section>
<section><p class="uppercase tracking-wide">Otro</p></section>
<meta name="viewport" content="width=device-width, user-scalable=no">
'''

CSS_BAD = '''
.btn { outline: none; transition: all 300ms cubic-bezier(.2,.8,.4,1.4); }
@keyframes pop { from { opacity: 0 } }
'''

CSS_GOOD = '''
:root { --color-primary: #2563EB; }
.btn { transition: transform 200ms, opacity 200ms; }
.btn:focus-visible { outline: 2px solid var(--color-primary); }
@keyframes pop { from { opacity: 0 } }
@media (prefers-reduced-motion: reduce) { .btn { transition: none } }
'''


def run(*args, stdin=None):
    return subprocess.run([sys.executable, str(DETECT), *args], text=True, capture_output=True,
                          check=False, encoding="utf-8", input=stdin)


def rules_of(findings):
    return {f["rule"] for f in findings}


class DetectorRuleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        p = self.dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_compose_rules_fire_on_bad_screen(self):
        rules = rules_of(detect.check_file(self.write("ui/Pantalla.kt", COMPOSE_BAD)))
        expected = {
            "compose-color-literal", "compose-sp-literal", "compose-dp-font",
            "compose-icon-button-no-description", "compose-fixed-height-text",
            "compose-scroll-column-list", "compose-items-no-key", "compose-toast-error",
            "compose-small-clickable",
        }
        self.assertEqual(expected, rules)

    def test_compose_clean_screen_and_inline_ignore(self):
        self.assertEqual([], detect.check_file(self.write("ui/Pantalla.kt", COMPOSE_GOOD)))

    def test_compose_theme_directory_allows_color_literals(self):
        text = "@Composable\nfun T() { val p = Color(0xFF2563EB); Text(\"a\", fontSize = 16.sp) }\n"
        self.assertEqual([], detect.check_file(self.write("ui/theme/Color.kt", text)))

    def test_kotlin_without_composables_is_ignored(self):
        self.assertEqual([], detect.check_file(self.write("data/Repo.kt", "val c = Color(0xFF000000)\n")))

    def test_web_markup_rules_fire(self):
        rules = rules_of(detect.check_file(self.write("src/Landing.tsx", WEB_BAD)))
        expected = {
            "web-img-no-alt", "web-img-no-dimensions", "web-div-onclick", "web-icon-button-no-label",
            "web-placeholder-only-label", "web-hex-in-component", "web-gradient-text",
            "web-tabindex-positive", "web-eyebrow-density", "web-zigzag-cap", "web-user-scalable",
        }
        self.assertEqual(expected, rules)

    def test_css_rules_fire_and_clean_css_passes(self):
        rules = rules_of(detect.check_file(self.write("src/styles.css", CSS_BAD)))
        self.assertEqual({"web-outline-none", "web-transition-all", "web-bounce-easing", "web-reduced-motion-missing"}, rules)
        self.assertEqual([], detect.check_file(self.write("src/tokens.css", CSS_GOOD)))
        # El mismo CSS limpio fuera de un archivo de tokens tampoco marca el hex de :root.
        self.assertEqual([], detect.check_file(self.write("src/app.css", CSS_GOOD)))

    def test_every_rule_cites_an_existing_catalog_guide(self):
        ids = set()
        for name in ("ux-guidelines.csv", "stacks/compose.csv", "stacks/web.csv"):
            with (PLUGIN / "data" / name).open(encoding="utf-8", newline="") as fh:
                ids |= {r["id"] for r in csv.DictReader(fh)}
        for rule, (_stack, severity, guide, _msg) in detect.RULES.items():
            with self.subTest(rule=rule):
                self.assertIn(guide, ids)
                self.assertIn(severity, {"critico", "importante", "menor"})


class DetectorCliTests(unittest.TestCase):
    def test_cli_exit_codes_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "a.css"
            bad.write_text(CSS_BAD, encoding="utf-8")
            good = Path(tmp) / "b.css"
            good.write_text(CSS_GOOD, encoding="utf-8")
            self.assertEqual(0, run("--help").returncode)
            self.assertEqual(0, run("--list-rules").returncode)
            self.assertEqual(0, run(str(good)).returncode)
            result = run(str(bad), "--json")
            self.assertEqual(1, result.returncode)
            payload = json.loads(result.stdout)
            self.assertEqual(4, payload["count"])
            self.assertEqual(2, run(str(bad), "--ignore-rule", "nope").returncode)
            ignored = run(str(bad), "--json", "--ignore-rule", "web-outline-none")
            self.assertNotIn("web-outline-none", ignored.stdout)
            self.assertEqual(2, run().returncode)

    def test_hook_mode_emits_additional_context_only_with_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "a.css"
            bad.write_text(CSS_BAD, encoding="utf-8")
            payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(bad)}})
            result = run("--hook", stdin=payload)
            self.assertEqual(0, result.returncode, result.stderr)
            out = json.loads(result.stdout)
            self.assertEqual("PostToolUse", out["hookSpecificOutput"]["hookEventName"])
            self.assertIn("web-outline-none", out["hookSpecificOutput"]["additionalContext"])
            clean = run("--hook", stdin=json.dumps({"tool_input": {"file_path": str(Path(tmp) / "x.py")}}))
            self.assertEqual("", clean.stdout)
            self.assertEqual(0, run("--hook", stdin="no json").returncode)


class HookRegistrationTests(unittest.TestCase):
    def test_plugin_hook_runs_detector_on_edits(self):
        hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertIn("PostToolUse", hooks)
        group = hooks["PostToolUse"][0]
        self.assertRegex(group["matcher"], r"Edit")
        self.assertRegex(group["matcher"], r"Write")
        command = group["hooks"][0]["command"]
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", command)
        script = (PLUGIN / "hooks" / "detect-ui.sh").read_text(encoding="utf-8")
        self.assertIn("detect.py", script)
        self.assertIn("--hook", script)
        for candidate in ("python", "python3", "py"):
            self.assertIn(candidate, script)

    def test_codex_hook_mirrors_the_detector(self):
        hooks = json.loads((ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertIn("PostToolUse", hooks)
        handler = hooks["PostToolUse"][0]["hooks"][0]
        self.assertIn("ui-detect", handler["command"])
        self.assertIn("ui-detect", handler["commandWindows"])
        source = (ROOT / ".codex" / "hooks" / "codex_hooks.py").read_text(encoding="utf-8")
        self.assertIn("plugins/design/scripts/detect.py", source)


if __name__ == "__main__":
    unittest.main()


class CodexUiDetectTests(unittest.TestCase):
    def test_codex_handler_reports_findings_for_edited_ui_file(self):
        hook = ROOT / ".codex" / "hooks" / "codex_hooks.py"
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "a.css"
            bad.write_text(CSS_BAD, encoding="utf-8")
            payload = json.dumps({"cwd": str(ROOT), "tool_name": "Edit", "tool_input": {"file_path": str(bad)}})
            result = subprocess.run([sys.executable, str(hook), "ui-detect"], input=payload, text=True,
                                    capture_output=True, encoding="utf-8", check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            out = json.loads(result.stdout)
            self.assertIn("web-outline-none", out["hookSpecificOutput"]["additionalContext"])
            patch = "*** Begin Patch\n*** Update File: " + str(bad) + "\n*** End Patch\n"
            payload = json.dumps({"cwd": str(ROOT), "tool_name": "apply_patch", "tool_input": {"command": patch}})
            result = subprocess.run([sys.executable, str(hook), "ui-detect"], input=payload, text=True,
                                    capture_output=True, encoding="utf-8", check=False)
            self.assertIn("web-outline-none", result.stdout)
            clean = subprocess.run([sys.executable, str(hook), "ui-detect"], text=True, capture_output=True,
                                   input=json.dumps({"cwd": str(ROOT), "tool_name": "Edit", "tool_input": {"file_path": str(Path(tmp) / "x.py")}}),
                                   encoding="utf-8", check=False)
            self.assertEqual("", clean.stdout)
