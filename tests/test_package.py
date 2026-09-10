import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from test_tooling import load, ROOT

packager = load("packager", ROOT / "scripts/package_skill.py")


class PackagingTests(unittest.TestCase):
    def test_reproducible_archive_is_self_contained(self):
        first = packager.package()
        self.assertEqual(first, packager.package())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with zipfile.ZipFile(io.BytesIO(first)) as archive:
                self.assertEqual(len(archive.namelist()), 7)
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

    def test_missing_reference_cannot_be_packaged(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                packager.package(Path(tmp))
