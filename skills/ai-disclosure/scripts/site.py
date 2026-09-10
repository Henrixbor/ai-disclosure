#!/usr/bin/env python3
"""Inventory and publish explicitly bound HTML with local AI disclosures."""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

from assess import assess

VOID = set("area base br col embed hr img input link meta param source track wbr".split())
CANDIDATES = {"article", "img", "video", "audio", "iframe", "canvas"}
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}\Z")
SLOT = "<!-- ai-disclosure -->"
STYLE = """/* AI Disclosure: local, visible without JavaScript. */
.aid-notice{display:inline-flex;align-items:center;gap:.35em;max-width:100%;box-sizing:border-box;font:500 .8125rem/1.5 system-ui,sans-serif;color:#183d33;background:#f2faf6;border:1px solid #55776c;border-radius:.3rem;padding:.2rem .5rem;text-decoration:none;vertical-align:middle}
.aid-notice:focus-visible{outline:3px solid #145acc;outline-offset:3px}
.aid-media{position:relative;display:block}.aid-media>.aid-notice{position:absolute;inset:.6rem auto auto .6rem;z-index:2}
.aid-media>img,.aid-media>video{display:block;max-width:100%;height:auto}
@media(forced-colors:active){.aid-notice{color:CanvasText;background:Canvas;border-color:CanvasText}}
"""


class Element:
    def __init__(self, tag, attrs, start, parent):
        self.tag, self.attrs, self.start, self.parent = tag, dict(attrs), start, parent
        self.end = None
        self.children = []
        if parent:
            parent.children.append(self)

    def descendants(self):
        for child in self.children:
            yield child
            yield from child.descendants()


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source, self.stack, self.elements, self.slots = source, [], [], []
        self.offsets = [0]
        self.offsets.extend(m.end() for m in re.finditer("\n", source))
        self.feed(source)
        self.close()

    def source_offset(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if len({key for key, _ in attrs}) != len(attrs):
            raise ValueError("Duplicate HTML attributes are not supported")
        element = Element(tag, attrs, self.source_offset(), self.stack[-1] if self.stack else None)
        self.elements.append(element)
        if tag in VOID:
            element.end = element.start + len(self.get_starttag_text())
        else:
            self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop().end = self.source_offset() + len(self.get_starttag_text())

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag:
                element = self.stack[index]
                # A bound region must have explicit, unambiguous closing markup.
                if any("data-ai-content" in e.attrs for e in self.stack[index + 1:]):
                    raise ValueError("A bound content region was not explicitly closed")
                element.end = self.source.index(">", self.source_offset()) + 1
                del self.stack[index:]
                break

    def handle_comment(self, data):
        if data.strip() == "ai-disclosure":
            start = self.source_offset()
            self.slots.append((start, self.source.index("-->", start) + 3,
                               self.stack[-1] if self.stack else None))


def nearest_binding(element):
    while element:
        if "data-ai-content" in element.attrs:
            return element
        element = element.parent
    return None


def inventory(root):
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("Input root must be an existing public HTML build directory")
    documents, records, gaps, ignored = {}, [], [], []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinks are not supported in the public input: " + str(path))
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if not path.is_file() or path.suffix.lower() != ".html":
            continue
        relative = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        doc = Document(source)
        documents[relative] = doc
        for element in doc.elements:
            binding = element.attrs.get("data-ai-content")
            if binding is not None:
                if not ID.fullmatch(binding):
                    raise ValueError("Invalid data-ai-content id in " + relative)
                if element.end is None:
                    raise ValueError("Unclosed bound region in " + relative)
                fragment = source[element.start:element.end]
                revision = "sha256:" + hashlib.sha256(fragment.encode()).hexdigest()
                owned_slots = [(a, b) for a, b, parent in doc.slots if nearest_binding(parent) is element]
                records.append({"id": binding, "revision": revision, "file": relative,
                                "tag": element.tag, "slots": len(owned_slots)})
            if element.tag not in CANDIDATES:
                continue
            if element.attrs.get("data-ai-ignore") == "decorative" and element.tag == "img":
                if element.attrs.get("alt") != "":
                    gaps.append({"file": relative, "reason": "Decorative image exclusion requires empty alt"})
                else:
                    ignored.append({"file": relative, "reason": "Publisher-declared decorative image"})
                continue
            owner = nearest_binding(element)
            # An article binding cannot also cover independently encountered media.
            covered = owner is not None and (element.tag == "article" or owner is element
                       or owner.tag != "article" and element.tag in {"img", "video", "audio"})
            if not covered:
                gaps.append({"file": relative, "tag": element.tag,
                             "reason": "Candidate has no dedicated data-ai-content region"})
        for _, _, parent in doc.slots:
            if nearest_binding(parent) is None:
                gaps.append({"file": relative, "reason": "Disclosure slot is outside a bound region"})
    if not documents:
        raise ValueError("No HTML files found")
    return documents, {"records": records, "gaps": gaps, "exclusions": ignored,
                       "coverage": "HTML candidates and explicit bindings only; not complete discovery"}


def plan(root, manifest):
    if root.resolve() in manifest.resolve().parents:
        raise ValueError("Keep the private manifest outside the public input directory")
    docs, found = inventory(root)
    declared = json.loads(manifest.read_text(encoding="utf-8"))
    # Validate before relying on IDs or mutating our in-memory version snapshot.
    assess(declared)
    items = {item["id"]: dict(item) for item in declared["items"]}
    revisions = {}
    for record in found["records"]:
        key = record["id"]
        if key not in items:
            found["gaps"].append({"file": record["file"], "id": key, "reason": "Missing manifest entry"})
            continue
        if key in revisions and revisions[key] != record["revision"]:
            found["gaps"].append({"id": key, "reason": "Same id has different content; use distinct ids"})
        revisions[key] = record["revision"]
        if items[key]["revision"] != record["revision"]:
            found["gaps"].append({"id": key, "reason": "Content changed; refresh origin and context evidence for this revision"})
        items[key]["revision"] = record["revision"]
    for key in items.keys() - revisions.keys():
        found["gaps"].append({"id": key, "reason": "Manifest entry has no rendered binding"})
    result = assess({**declared, "items": list(items.values())})
    decisions = {row["id"]: row for row in result["results"]}
    edits = {}
    for relative, doc in docs.items():
        replacements = []
        for element in doc.elements:
            key = element.attrs.get("data-ai-content")
            if key not in decisions:
                continue
            row, item = decisions[key], items[key]
            owned = [(a, b) for a, b, parent in doc.slots if nearest_binding(parent) is element]
            if row["status"] == "disclose":
                if len(owned) != 1:
                    found["gaps"].append({"file": relative, "id": key, "reason": "Disclosure needs exactly one owned slot"})
                    continue
                descendants = list(element.descendants())
                if item["kind"] in {"audio", "video"}:
                    found["gaps"].append({"file": relative, "id": key,
                                         "reason": "Media playback/audible disclosure integration requires verification; not built by this adapter yet"})
                    continue
                if item["kind"] == "image":
                    images = [e for e in descendants if e.tag == "img"]
                    if (element.tag != "figure" or len(images) != 1
                            or "aid-media" not in element.attrs.get("class", "").split()):
                        found["gaps"].append({"file": relative, "id": key,
                                             "reason": "Image binding needs figure.aid-media containing one image"})
                        continue
                elif item["kind"] == "text":
                    # Placement is deterministic: disclosure must precede substantive content.
                    first = min((e.start for e in descendants if e.tag in {"p", "ul", "ol", "table"}), default=element.end)
                    if owned[0][0] > first:
                        found["gaps"].append({"file": relative, "id": key, "reason": "Text disclosure slot must precede body content"})
                        continue
                label = "AI-generated" if item["origin"] == "ai_generated" else "AI-modified"
                notice = '<span class="aid-notice" data-ai-disclosure="' + html.escape(key, quote=True) + '">' + label + '</span>'
                replacements.append((*owned[0], notice))
            else:
                replacements.extend((a, b, "") for a, b in owned)
        source = doc.source
        for start, end, replacement in sorted(replacements, reverse=True):
            source = source[:start] + replacement + source[end:]
        depth = len(Path(relative).parts) - 1
        css_url = "../" * depth + "ai-disclosure.css"
        match = re.search(r"</head\s*>", source, flags=re.I)
        if not match:
            found["gaps"].append({"file": relative, "reason": "HTML document needs an explicit head closing tag"})
        else:
            source = source[:match.start()] + '<link rel="stylesheet" href="' + css_url + '">\n' + source[match.start():]
        edits[relative] = source
    result["inventory"] = found
    result["ready_to_render"] = not (found["gaps"] or result["role_gaps"] or any(
        row["status"] == "needs_review" for row in result["results"]))
    result["visual_verification_required"] = True
    return result, edits


def build(root, manifest, output):
    root, output = root.resolve(), output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("Output must not exist; publish to a fresh staging directory")
    if root == output.resolve() or root in output.resolve().parents:
        raise ValueError("Output cannot be inside the public input")
    result, edits = plan(root, manifest)
    if not result["ready_to_render"]:
        return result
    if (root / "ai-disclosure.css").exists():
        raise ValueError("Input already contains ai-disclosure.css; build from original input")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".ai-disclosure-", dir=output.parent))
    try:
        shutil.copytree(root, stage, dirs_exist_ok=True,
                        ignore=lambda directory, names: [name for name in names if name.startswith(".")])
        for relative, source in edits.items():
            (stage / relative).write_text(source, encoding="utf-8")
        (stage / "ai-disclosure.css").write_text(STYLE, encoding="utf-8")
        # Evidence belongs outside the public directory: never publish private manifest facts.
        os.rename(stage, output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    result["output"] = str(output)
    return result


def record(root, manifest, facts_path, role=None):
    """Record a publishing hook's explicit facts against the actual rendered version."""
    root = root.resolve()
    manifest = manifest.absolute()
    if manifest.is_symlink() or root == manifest.resolve() or root in manifest.resolve().parents:
        raise ValueError("Keep the manifest outside the public input; symlink manifests are unsupported")
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    if not isinstance(facts, dict) or "revision" in facts or not nonempty_fact(facts.get("evidence")):
        raise ValueError("Facts must be an item object with evidence and no revision field")
    matches = [r for r in inventory(root)[1]["records"] if r["id"] == facts.get("id")]
    if not matches or len({r["revision"] for r in matches}) != 1:
        raise ValueError("Facts need an existing unambiguous rendered content id")
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assess(data)
        if role is not None and role != data["role"]:
            raise ValueError("Role differs from existing manifest; assess the role change separately")
    else:
        data = {"version": 1, "role": role or "unknown", "items": []}
    item = {**facts, "revision": matches[0]["revision"]}
    # Replace, do not merge: old evidence and review must not leak into new content.
    data["items"] = [i for i in data["items"] if i["id"] != item["id"]] + [item]
    data["items"].sort(key=lambda i: i["id"])
    assess(data)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2) + "\n"
    if manifest.exists() and manifest.read_text(encoding="utf-8") == payload:
        return {"id": item["id"], "revision": item["revision"], "changed": False}
    handle, temporary = tempfile.mkstemp(prefix=".ai-disclosure-facts-", dir=manifest.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, manifest)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"id": item["id"], "revision": item["revision"], "changed": True,
            "basis": "Publishing hook declaration; not origin detection"}


def nonempty_fact(value):
    return isinstance(value, str) and bool(value.strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inventory", "record", "plan", "build"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--facts", type=Path)
    parser.add_argument("--role", choices=("publisher", "provider", "both", "unknown"))
    args = parser.parse_args()
    try:
        if args.command == "inventory":
            result = inventory(args.root)[1]
            code = int(bool(result["gaps"]))
        elif args.command == "record":
            if args.manifest is None or args.facts is None:
                raise ValueError("record needs --manifest and --facts")
            result = record(args.root, args.manifest, args.facts, args.role)
            code = 0
        else:
            if args.manifest is None or args.command == "build" and args.output is None:
                raise ValueError("plan needs --manifest; build also needs --output")
            result = (build(args.root, args.manifest, args.output) if args.command == "build"
                      else plan(args.root, args.manifest)[0])
            code = int(not result["ready_to_render"])
        print(json.dumps(result, indent=2))
        return code
    except (ValueError, OSError, TypeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
