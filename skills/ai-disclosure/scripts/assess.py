#!/usr/bin/env python3
"""Assess declared publisher facts. No network, file mutations or compliance verdict."""
import argparse
import json
import sys
from pathlib import Path

POLICY = "eu-article50-publisher-prototype-2026-09-10"
KINDS = {"text", "image", "audio", "video", "code", "chatbot", "other"}
ORIGINS = {"human", "ai_generated", "ai_modified", "unknown"}
FIELDS = {"id", "revision", "kind", "origin", "applicable", "evidence",
          "public_interest", "deepfake", "creative_work", "review"}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate(data):
    if not isinstance(data, dict) or set(data) != {"version", "role", "items"}:
        raise ValueError("Expected version, role and items only")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("Expected version 1")
    if data["role"] not in ("publisher", "provider", "both", "unknown"):
        raise ValueError("Invalid role")
    if not isinstance(data["items"], list) or not data["items"]:
        raise ValueError("A nonempty items list is required; an empty inventory proves nothing")
    seen = set()
    for item in data["items"]:
        if not isinstance(item, dict) or set(item) - FIELDS:
            raise ValueError("Item is not an object or contains unsupported fields")
        if not all(nonempty(item.get(key)) for key in ("id", "revision", "kind", "origin")):
            raise ValueError("Each item needs id, revision, kind and origin strings")
        if item["id"] in seen:
            raise ValueError("Duplicate item id: " + item["id"])
        seen.add(item["id"])
        if item["kind"] not in KINDS or item["origin"] not in ORIGINS:
            raise ValueError("Unsupported kind or origin: " + item["id"])
        for key in ("applicable", "public_interest", "deepfake", "creative_work"):
            if item.get(key) is not None and type(item[key]) is not bool:
                raise ValueError(key + " must be boolean or null")
        if "evidence" in item and not nonempty(item["evidence"]):
            raise ValueError("Evidence must be a nonempty string when supplied")
        if "review" in item:
            review = item["review"]
            if not isinstance(review, dict) or set(review) != {
                "revision", "substantive_human_review", "responsible_entity"
            }:
                raise ValueError("Invalid review fields")
            if (not nonempty(review["revision"])
                    or type(review["substantive_human_review"]) is not bool
                    or not nonempty(review["responsible_entity"])):
                raise ValueError("Invalid review values")
            if item["kind"] != "text":
                raise ValueError("Editorial review is only supported for text")


def decide(item):
    def result(status, reason, presentation=None):
        return {"id": item["id"], "revision": item["revision"],
                "status": status, "reason": reason, "presentation": presentation}

    if item["kind"] == "other":
        return result("needs_review", "Unsupported surface or content type")
    if item["kind"] == "chatbot":
        return result("needs_review", "Assess Article 50(1) separately; normally show a session-start AI notice")
    if not nonempty(item.get("evidence")):
        return result("needs_review", "Supply evidence for declared origin and scope facts")
    if item.get("applicable") is None:
        return result("needs_review", "Establish jurisdiction, role and temporal scope")
    if item["applicable"] is False:
        return result("outside_declared_scope", "Based on supplied scope evidence, not independently verified")
    if item["kind"] == "code":
        return result("no_publisher_label", "Source-code authorship alone is not displayed-content disclosure")
    if item["origin"] == "unknown":
        return result("needs_review", "Unknown origin must not become a guessed label or exemption")
    if item["origin"] == "human":
        return result("no_publisher_label", "Based on supplied human-origin evidence")
    if item["kind"] == "text":
        if item.get("public_interest") is None:
            return result("needs_review", "Assess publication purpose and public-interest subject matter")
        if item["public_interest"] is False:
            return result("no_publisher_label", "Outside declared public-interest text test")
        review = item.get("review", {})
        if (review.get("revision") == item["revision"]
                and review.get("substantive_human_review") is True
                and nonempty(review.get("responsible_entity"))):
            return result("exception_declared", "Version-matched human review and editorial responsibility declared")
        return result("disclose", "In-scope AI public-interest text without a current declared review exception",
                      "Label at publication headline/start; retain required visibility")
    if item.get("deepfake") is None:
        return result("needs_review", "Assess resemblance and misleading authenticity in context")
    if item["deepfake"] is False:
        return result("no_publisher_label", "Outside declared deepfake test; provider duties are separate")
    if item.get("creative_work") is True:
        return result("disclose", "Qualifying creative-work treatment declared; disclosure still required",
                      "Tailored contextual disclosure by first exposure; check modality and Code conditions")
    presentation = {
        "image": "Embedded or equivalent on-content visual AI label",
        "audio": "Audible disclosure; visual label when a screen is available; account for late entry/reuse",
        "video": "On-content visual AI label; account for late entry, interruptions, audio and reuse",
    }
    return result("disclose", "In-scope deepfake declared", presentation[item["kind"]])


def assess(data):
    validate(data)
    results = [decide(item) for item in data["items"]]
    gaps = []
    if data["role"] != "publisher":
        gaps.append("Provider or unresolved roles require separate assessment; marking is not implemented")
    return {"policy": POLICY, "basis": "declared facts only",
            "implementation_verified": False, "inventory_completeness_verified": False,
            "role_gaps": gaps, "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = assess(json.loads(args.manifest.read_text(encoding="utf-8")))
    except (ValueError, OSError, TypeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return int(bool(result["role_gaps"]) or any(
        row["status"] == "needs_review" for row in result["results"]))


if __name__ == "__main__":
    sys.exit(main())
