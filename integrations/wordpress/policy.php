<?php
/** Native assessment engine for the developing WordPress adapter. No WordPress hooks yet. */
declare(strict_types=1);

namespace AiDisclosure;

const POLICY = 'eu-article50-transparency-development-2026-09-10.2';

function nonempty($value): bool {
    return is_string($value) && preg_match('/[^\s\x1c-\x1f]/u', $value) === 1;
}

function keys_equal(object $value, array $keys): bool {
    $actual = array_keys(get_object_vars($value));
    sort($actual);
    sort($keys);
    return $actual === $keys;
}

function validate($data): void {
    if (!($data instanceof \stdClass) || !keys_equal($data, ['version', 'role', 'items'])) {
        throw new \InvalidArgumentException('Expected version, role and items only');
    }
    if ($data->version !== 1) throw new \InvalidArgumentException('Expected version 1');
    if (!in_array($data->role, ['publisher', 'provider', 'both', 'unknown'], true)) {
        throw new \InvalidArgumentException('Invalid role');
    }
    if (!is_array($data->items) || !$data->items) {
        throw new \InvalidArgumentException('A nonempty items list is required; an empty inventory proves nothing');
    }
    $fields = ['id', 'revision', 'kind', 'origin', 'applicable', 'evidence', 'public_interest',
        'deepfake', 'creative_work', 'review', 'audio_deepfake', 'direct_ai_interaction'];
    $seen = [];
    foreach ($data->items as $item) {
        if (!($item instanceof \stdClass) || array_diff(array_keys(get_object_vars($item)), $fields)) {
            throw new \InvalidArgumentException('Item is not an object or contains unsupported fields');
        }
        foreach (['id', 'revision', 'kind', 'origin'] as $key) {
            if (!nonempty($item->$key ?? null)) throw new \InvalidArgumentException('Each item needs id, revision, kind and origin strings');
        }
        if (in_array($item->id, $seen, true)) throw new \InvalidArgumentException('Duplicate item id: ' . $item->id);
        $seen[] = $item->id;
        if (!in_array($item->kind, ['text', 'image', 'audio', 'video', 'code', 'chatbot', 'other'], true)
            || !in_array($item->origin, ['human', 'ai_generated', 'ai_modified', 'unknown'], true)) {
            throw new \InvalidArgumentException('Unsupported kind or origin: ' . $item->id);
        }
        foreach (['applicable', 'public_interest', 'deepfake', 'creative_work', 'audio_deepfake', 'direct_ai_interaction'] as $key) {
            if (isset($item->$key) && !is_bool($item->$key)) throw new \InvalidArgumentException($key . ' must be boolean or null');
        }
        if (property_exists($item, 'evidence') && !nonempty($item->evidence)) throw new \InvalidArgumentException('Evidence must be a nonempty string when supplied');
        if (property_exists($item, 'review')) {
            $review = $item->review;
            if (!($review instanceof \stdClass) || !keys_equal($review, ['revision', 'substantive_human_review', 'responsible_entity'])) {
                throw new \InvalidArgumentException('Invalid review fields');
            }
            if (!nonempty($review->revision) || !is_bool($review->substantive_human_review) || !nonempty($review->responsible_entity)) {
                throw new \InvalidArgumentException('Invalid review values');
            }
            if ($item->kind !== 'text') throw new \InvalidArgumentException('Editorial review is only supported for text');
        }
    }
}

function decide(object $item): array {
    $result = static function (string $status, string $reason, ?string $presentation = null) use ($item): array {
        return ['id' => $item->id, 'revision' => $item->revision, 'status' => $status,
            'reason' => $reason, 'presentation' => $presentation];
    };
    if ($item->kind === 'other') return $result('needs_review', 'Unsupported surface or content type');
    if (!nonempty($item->evidence ?? null)) return $result('needs_review', 'Supply evidence for declared origin and scope facts');
    if (!isset($item->applicable)) return $result('needs_review', 'Establish jurisdiction, role and temporal scope');
    if ($item->applicable === false) return $result('outside_declared_scope', 'Based on supplied scope evidence, not independently verified');
    if ($item->kind === 'chatbot') {
        if (($item->direct_ai_interaction ?? null) !== true) {
            return $result('needs_review', 'Establish direct AI interaction; this helper does not grant obvious-interaction exceptions');
        }
        return $result('disclose', 'Direct AI interaction declared; render an explicit interaction notice',
            'Visible at session start before conversation or composer; retain on resumed sessions');
    }
    if ($item->kind === 'code') return $result('no_publisher_label', 'Source-code authorship alone is not displayed-content disclosure');
    if ($item->origin === 'unknown') return $result('needs_review', 'Unknown origin must not become a guessed label or exemption');
    if ($item->origin === 'human') return $result('no_publisher_label', 'Based on supplied human-origin evidence');
    if ($item->kind === 'text') {
        if (!isset($item->public_interest)) return $result('needs_review', 'Assess publication purpose and public-interest subject matter');
        if ($item->public_interest === false) return $result('no_publisher_label', 'Outside declared public-interest text test');
        $review = $item->review ?? new \stdClass();
        if (($review->revision ?? null) === $item->revision && ($review->substantive_human_review ?? null) === true
            && nonempty($review->responsible_entity ?? null)) {
            return $result('exception_declared', 'Version-matched human review and editorial responsibility declared');
        }
        return $result('disclose', 'In-scope AI public-interest text without a current declared review exception',
            'Label at publication headline/start; retain required visibility');
    }
    if (!isset($item->deepfake)) return $result('needs_review', 'Assess resemblance and misleading authenticity in context');
    if ($item->deepfake === false) return $result('no_publisher_label', 'Outside declared deepfake test; provider duties are separate');
    if (($item->creative_work ?? null) === true) return $result('disclose', 'Qualifying creative-work treatment declared; disclosure still required',
        'Tailored contextual disclosure by first exposure; check modality and Code conditions');
    $presentation = [
        'image' => 'Embedded or equivalent on-content visual AI label',
        'audio' => 'Audible disclosure; visual label when a screen is available; account for late entry/reuse',
        'video' => 'On-content visual AI label; account for late entry, interruptions, audio and reuse',
    ];
    return $result('disclose', 'In-scope deepfake declared', $presentation[$item->kind]);
}

function assess($data): array {
    validate($data);
    return ['policy' => POLICY, 'basis' => 'declared facts only', 'implementation_verified' => false,
        'inventory_completeness_verified' => false,
        'role_gaps' => $data->role === 'publisher' ? [] : ['Provider or unresolved roles require separate assessment; marking is not implemented'],
        'results' => array_map(__NAMESPACE__ . '\\decide', $data->items)];
}
