import io
import json
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from test_tooling import load, ROOT

packager = load("packager", ROOT / "scripts/package_skill.py")


class PackagingTests(unittest.TestCase):
    def test_wordpress_archive_is_reproducible_and_contains_runtime_only(self):
        payload = packager.package(kind="wordpress")
        self.assertEqual(payload, packager.package(kind="wordpress"))
        source = ROOT / "integrations/wordpress"
        runtime = {p.name for p in source.iterdir() if p.suffix in {".php", ".js", ".css"}}
        expected = runtime | {"LICENSE", "readme.txt"}
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            self.assertEqual(set(archive.namelist()), {"ai-disclosure/" + name for name in expected})
            for name in expected:
                self.assertEqual(archive.read("ai-disclosure/" + name), (source / name).read_bytes())
            for info in archive.infolist():
                self.assertEqual(info.external_attr >> 16, 0o100644)
                self.assertEqual(info.date_time, (2026, 1, 1, 0, 0, 0))
        header = (source / "ai-disclosure.php").read_text()
        readme = (source / "readme.txt").read_text()
        self.assertEqual(re.search(r"Version: (.+)", header)[1], re.search(r"Stable tag: (.+)", readme)[1])
        for field in ["Requires at least", "Requires PHP"]:
            self.assertEqual(re.search(field + r": (.+)", header)[1], re.search(field + r": (.+)", readme)[1])

    def test_wordpress_archive_omits_unlisted_files_and_rejects_missing_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = Path(tmp)
            source = repository / "integrations/wordpress"
            shutil.copytree(ROOT / "integrations/wordpress", source)
            (source / "private-evidence.json").write_text("PRIVATE_PACKAGE_SENTINEL")
            payload = packager.package(kind="wordpress", repository=repository)
            self.assertEqual(payload, packager.package(kind="wordpress"))
            (source / "cache.php").unlink()
            with self.assertRaisesRegex(ValueError, "Missing required WordPress file: cache.php"):
                packager.package(kind="wordpress", repository=repository)

    def test_wordpress_archive_rejects_symlinked_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = Path(tmp)
            source = repository / "integrations/wordpress"
            shutil.copytree(ROOT / "integrations/wordpress", source)
            (source / "policy.php").unlink()
            (source / "policy.php").symlink_to(ROOT / "integrations/wordpress/policy.php")
            with self.assertRaisesRegex(ValueError, "symlinks"):
                packager.package(kind="wordpress", repository=repository)

    @unittest.skipUnless(shutil.which("node"), "Node is optional for Python-only installations")
    def test_extracted_node_client_uses_only_bundled_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(io.BytesIO(packager.package())) as archive:
                archive.extractall(tmp)
            env = {**os.environ, "AI_DISCLOSURE_PYTHON": sys.executable,
                   "AI_DISCLOSURE_MODULE": str(Path(tmp) / "ai-disclosure/scripts/node.cjs")}
            proc = subprocess.run([shutil.which("node"), "--test", str(ROOT / "tests/node-publishing.cjs")],
                                  cwd=tmp, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_reproducible_archive_is_self_contained(self):
        first = packager.package()
        self.assertEqual(first, packager.package())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with zipfile.ZipFile(io.BytesIO(first)) as archive:
                self.assertEqual(len(archive.namelist()), 11)
                self.assertTrue(all(name.startswith("ai-disclosure/") and ".." not in name.split("/") for name in archive.namelist()))
                archive.extractall(root)
            skill = root / "ai-disclosure"
            manifest = root / "input.json"
            manifest.write_text(json.dumps({"version": 1, "role": "publisher", "items": [
                {"id": "example", "revision": "v1", "kind": "text", "origin": "ai_generated",
                 "applicable": True, "public_interest": True, "evidence": "Publishing record"}
            ]}))
            proc = subprocess.run([sys.executable, str(skill / "scripts/assess.py"), str(manifest)],
                                  cwd=root, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["results"][0]["status"], "disclose")
            proc = subprocess.run([sys.executable, str(skill / "scripts/site.py"), "--help"],
                                  cwd=root, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_plugin_archive_reuses_skill_and_has_consistent_manifests(self):
        payload = packager.package(kind="plugin")
        self.assertEqual(payload, packager.package(kind="plugin"))
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                self.assertEqual(len(archive.namelist()), 15)
                archive.extractall(tmp)
            root = Path(tmp) / "ai-disclosure"
            codex = json.loads((root / ".codex-plugin/plugin.json").read_text())
            claude = json.loads((root / ".claude-plugin/plugin.json").read_text())
            self.assertEqual(codex["name"], root.name)
            self.assertEqual(codex["version"], claude["version"])
            self.assertEqual(codex["skills"], claude["skills"])
            skill = root / "skills/ai-disclosure"
            self.assertEqual((skill / "SKILL.md").read_bytes(), (packager.SOURCE / "SKILL.md").read_bytes())
            self.assertEqual((skill / "assets/players.js").read_bytes(), (packager.SOURCE / "assets/players.js").read_bytes())
            proc = subprocess.run([sys.executable, str(skill / "scripts/site.py"), "--help"],
                                  cwd=tmp, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_missing_reference_cannot_be_packaged(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                packager.package(Path(tmp))
