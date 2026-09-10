#!/usr/bin/env python3
"""Compare the native PHP assessment engine with Python over valid and malformed facts."""
import argparse
import copy
import itertools
import json
from pathlib import Path
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ENGINE = runpy.run_path(str(ROOT / "skills/ai-disclosure/scripts/assess.py"))


def cases():
    data = {"version": 1, "role": "publisher", "items": [{
        "id": "article", "revision": "v1", "kind": "text", "origin": "ai_generated",
        "applicable": True, "evidence": "Explicit test declaration", "public_interest": True,
    }]}
    inputs = []
    for kind, origin, scope, interest, deepfake, creative, interaction, evidenced in itertools.product(
            sorted(ENGINE["KINDS"]), sorted(ENGINE["ORIGINS"]), [True, False, None],
            [True, False, None], [True, False, None], [True, False], [True, False, None], [True, False]):
        item = {**data["items"][0], "kind": kind, "origin": origin, "applicable": scope,
                "public_interest": interest, "deepfake": deepfake, "creative_work": creative,
                "direct_ai_interaction": interaction}
        if not evidenced:
            del item["evidence"]
        inputs.append({**data, "items": [item]})
    for role, revision, reviewed in itertools.product(["publisher", "provider", "both", "unknown"],
                                                     ["v1", "old"], [True, False]):
        current = copy.deepcopy(data)
        current["role"] = role
        current["items"][0]["review"] = {"revision": revision, "substantive_human_review": reviewed,
                                          "responsible_entity": "Fixture publisher"}
        inputs.append(current)
    for field in data["items"][0]:
        missing = copy.deepcopy(data)
        del missing["items"][0][field]
        inputs.append(missing)
    for field in ENGINE["FIELDS"]:
        for value in [None, [], {}, 0, 1, "", " \t\n", "\u00a0", "\u2003", "\x1c", "\ufeff", True]:
            malformed = copy.deepcopy(data)
            malformed["items"][0][field] = value
            inputs.append(malformed)
    inputs.extend([None, [], {}, {**data, "version": True}, {**data, "version": 1.0},
                   {**data, "role": []}, {**data, "items": []}, {**data, "items": {}},
                   {**data, "extra": True}, {**data, "items": data["items"] * 2}])
    for review in [{}, [], {"revision": "v1", "substantive_human_review": 1, "responsible_entity": "Publisher"},
                   {"revision": "v1", "substantive_human_review": True, "responsible_entity": " "}]:
        current = copy.deepcopy(data)
        current["items"][0]["review"] = review
        inputs.append(current)
    return inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--php", default="php", help="Local PHP executable")
    choice.add_argument("--docker", help="Explicit PHP image tag or digest; requires Docker")
    args = parser.parse_args()
    inputs = cases()
    expected = []
    for data in inputs:
        try:
            expected.append({"result": ENGINE["assess"](data)})
        except (ValueError, TypeError):
            expected.append({"invalid": True})
    command = [args.php, str(ROOT / "tests/php-policy-runner.php")]
    if args.docker:
        command = ["docker", "run", "--rm", "-i", "--read-only", "--network", "none",
                   "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "32",
                   "--memory", "256m", "--user", "65534:65534",
                   "--mount", "type=bind,src=" + str(ROOT / "integrations") + ",dst=/work/integrations,readonly",
                   "--mount", "type=bind,src=" + str(ROOT / "tests/php-policy-runner.php") + ",dst=/work/tests/php-policy-runner.php,readonly",
                   args.docker, "php", "/work/tests/php-policy-runner.php"]
    result = subprocess.run(command, input=json.dumps(inputs), text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    actual = json.loads(result.stdout)
    if len(actual) != len(expected):
        raise AssertionError("PHP did not assess every input")
    for index, (left, right) in enumerate(zip(expected, actual)):
        if left != right:
            raise AssertionError(json.dumps({"index": index, "input": inputs[index], "python": left, "php": right}))
    print(str(len(inputs)) + " PHP/Python assessments matched, including complete reports and invalid input rejection")


if __name__ == "__main__":
    main()
