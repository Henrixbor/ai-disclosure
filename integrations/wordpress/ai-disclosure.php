<?php
/**
 * Plugin Name: AI Disclosure (Development)
 * Description: Version-bound text publication checks and notices. Development integration; not legal certification.
 * Version: 0.1.0-alpha.3
 * Requires PHP: 8.3
 * License: MIT
 */
declare(strict_types=1);
namespace AiDisclosure\WordPress;
if (!defined('ABSPATH')) exit;
require_once __DIR__ . '/policy.php';

function supported($post): bool { return $post && in_array($post->post_type, ['post', 'page'], true); }
function snapshot($post): array {
    return ['title' => $post->post_title, 'content' => $post->post_content, 'excerpt' => $post->post_excerpt];
}
function revision(array $source): string {
    return 'sha256:' . hash('sha256', wp_json_encode($source, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
}
function record_key(int $id, string $revision): string {
    return 'ai_disclosure_' . $id . '_' . substr(hash('sha256', \AiDisclosure\POLICY), 0, 12) . '_' . substr($revision, 7);
}
function record_for(int $id, array $source): ?array {
    $record = get_option(record_key($id, revision($source)));
    if (!is_array($record) || ($record['policy'] ?? '') !== \AiDisclosure\POLICY) return null;
    return $record;
}
function supported_text(array $source): bool {
    // Dynamic blocks, shortcodes and independent media need dedicated integrations.
    foreach ([$source['content'], $source['excerpt']] as $html) {
        if (preg_match('/<(?:img|audio|video|iframe|canvas|script|style|object|embed|form)\b|\[(?:[a-zA-Z_][\w-]*)(?:\s|\])/i', $html)) return false;
        if (preg_match('/\s(?:hidden|inert|style|aria-hidden)\s*(?:=|>)/i', $html)) return false;
        if (wp_kses_post($html) !== $html) return false;
        $queue = parse_blocks($html);
        while ($queue) {
            $block = array_pop($queue);
            if ($block['blockName'] !== null && !in_array($block['blockName'],
                ['core/paragraph', 'core/heading', 'core/list', 'core/list-item', 'core/quote', 'core/separator'], true)) return false;
            foreach ($block['innerBlocks'] as $child) $queue[] = $child;
        }
    }
    return true;
}
function permitted($request): bool {
    $post = get_post((int) $request['id']);
    return supported($post) && current_user_can('edit_post', $post->ID)
        && current_user_can(get_post_type_object($post->post_type)->cap->publish_posts);
}
function assessment_route($request) {
    if (!permitted($request)) return new \WP_Error('ai_disclosure_forbidden', 'Permission denied.', ['status' => 403]);
    $post = get_post((int) $request['id']);
    $source = snapshot($post);
    if ($request->get_method() === 'GET') {
        return ['revision' => revision($source), 'recorded' => record_for($post->ID, $source) !== null,
            'supported_text' => supported_text($source), 'policy' => \AiDisclosure\POLICY];
    }
    if (strlen($request->get_body()) > 1048576) return new \WP_Error('ai_disclosure_size', 'Assessment request exceeds 1 MiB.', ['status' => 413]);
    $body = json_decode($request->get_body());
    if (!($body instanceof \stdClass) || array_diff(array_keys(get_object_vars($body)), ['title', 'content', 'excerpt', 'facts', 'role'])) {
        return new \WP_Error('ai_disclosure_input', 'Expected proposed text fields and facts.', ['status' => 400]);
    }
    foreach (array_keys($source) as $key) {
        if (property_exists($body, $key)) {
            if (!is_string($body->$key)) return new \WP_Error('ai_disclosure_input', 'Text fields must be strings.', ['status' => 400]);
            $source[$key] = $body->$key;
        }
    }
    if (!supported_text($source)) return new \WP_Error('ai_disclosure_surface', 'This text adapter cannot cover the proposed markup, media or dynamic content.', ['status' => 422]);
    if (!(($body->facts ?? null) instanceof \stdClass)) return new \WP_Error('ai_disclosure_input', 'Supply evidence-backed facts.', ['status' => 400]);
    $item = clone $body->facts;
    if (array_diff(array_keys(get_object_vars($item)), ['origin', 'applicable', 'public_interest', 'evidence', 'review'])) {
        return new \WP_Error('ai_disclosure_input', 'Supply supported text facts only; identity and revision are computed.', ['status' => 400]);
    }
    foreach (['id', 'kind', 'revision'] as $owned) {
        if (property_exists($item, $owned)) return new \WP_Error('ai_disclosure_input', 'The adapter computes identity, kind and revision.', ['status' => 400]);
    }
    $item->id = 'wp-' . $post->ID;
    $item->kind = 'text';
    $item->revision = revision($source);
    try { $assessment = \AiDisclosure\assess((object) ['version' => 1, 'role' => $body->role ?? 'unknown', 'items' => [$item]]); }
    catch (\InvalidArgumentException $error) { return new \WP_Error('ai_disclosure_input', $error->getMessage(), ['status' => 400]); }
    $decision = $assessment['results'][0];
    if ($assessment['role_gaps']) return new \WP_Error('ai_disclosure_role', 'Provider or unresolved roles need separate assessment.', ['status' => 422]);
    if ($decision['status'] === 'needs_review') return new \WP_Error('ai_disclosure_review', $decision['reason'], ['status' => 422]);
    $record = ['policy' => \AiDisclosure\POLICY, 'origin' => $item->origin, 'status' => $decision['status'],
        'facts' => json_decode(wp_json_encode($item), true), 'actor' => get_current_user_id(), 'recorded_at' => gmdate('c')];
    ksort($record['facts']);
    if (isset($record['facts']['review'])) ksort($record['facts']['review']);
    // One immutable record per content version: concurrent declarations cannot replace each other.
    $key = record_key($post->ID, $item->revision);
    $existing = get_option($key);
    if ($existing) {
        if (($existing['facts'] ?? null) !== $record['facts'] || ($existing['policy'] ?? '') !== $record['policy']) {
            return new \WP_Error('ai_disclosure_conflict', 'This version already has different facts. Reassessment requires an explicit amendment workflow.', ['status' => 409]);
        }
    } elseif (!add_option($key, $record, '', false)) {
        return new \WP_Error('ai_disclosure_conflict', 'Another assessment was recorded; read it before retrying.', ['status' => 409]);
    }
    return ['revision' => $item->revision, 'decision' => $decision['status'], 'policy' => $assessment['policy'], 'implementation_verified' => false];
}

add_action('rest_api_init', static function () {
    register_rest_route('ai-disclosure/v1', '/posts/(?P<id>\d+)/assessment', [
        'methods' => ['GET', 'POST'], 'callback' => __NAMESPACE__ . '\\assessment_route',
        'permission_callback' => __NAMESPACE__ . '\\permitted',
    ]);
});
add_filter('rest_post_dispatch', static function ($response, $server, $request) {
    if (str_starts_with($request->get_route(), '/ai-disclosure/v1/')) {
        $response->header('Cache-Control', 'private, no-store');
    }
    return $response;
}, 10, 3);

function prospective(array $data): array {
    return ['title' => wp_unslash($data['post_title'] ?? ''), 'content' => wp_unslash($data['post_content'] ?? ''),
        'excerpt' => wp_unslash($data['post_excerpt'] ?? '')];
}
function publication_ready(int $id, array $source): bool {
    return $id > 0 && supported_text($source) && record_for($id, $source) !== null;
}
add_filter('wp_insert_post_empty_content', static function ($empty, $data) {
    if (in_array($data['post_type'] ?? 'post', ['post', 'page'], true)
        && in_array($data['post_status'] ?? '', ['publish', 'future'], true)
        && !publication_ready((int) ($data['ID'] ?? 0), prospective($data))) return true;
    return $empty;
}, 10, 2);

foreach (['post', 'page'] as $type) {
    add_filter('rest_pre_insert_' . $type, static function ($prepared, $request) {
        $post = get_post((int) ($request['id'] ?? 0));
        $status = $prepared->post_status ?? ($post->post_status ?? 'draft');
        if (!in_array($status, ['publish', 'future'], true)) return $prepared;
        $source = $post ? snapshot($post) : ['title' => '', 'content' => '', 'excerpt' => ''];
        foreach (['title' => 'post_title', 'content' => 'post_content', 'excerpt' => 'post_excerpt'] as $key => $property) {
            // REST's prepared object already contains unslashed field values.
            if (isset($prepared->$property)) $source[$key] = $prepared->$property;
        }
        if (!publication_ready((int) ($post->ID ?? 0), $source)) return new \WP_Error('ai_disclosure_review',
            'Save as a draft and record current AI disclosure facts before publishing this version.', ['status' => 409]);
        return $prepared;
    }, 10, 2);
}

add_action('publish_future_post', static function ($id) {
    $post = get_post($id);
    if (supported($post) && $post->post_status === 'future' && !publication_ready($id, snapshot($post))) {
        wp_update_post(['ID' => $id, 'post_status' => 'pending']);
    }
}, 1);

function notice(int $id): string {
    $post = get_post($id);
    if (!supported($post)) return '';
    $record = record_for($id, snapshot($post));
    if (!$record || $record['status'] !== 'disclose') return '';
    $label = $record['origin'] === 'ai_modified' ? 'AI-modified' : 'AI-generated';
    return '<span class="aid-wp-notice" data-ai-disclosure="wp-' . $id . '">' . esc_html($label) . '</span> ';
}
function add_notice(string $content): string {
    if (doing_filter('get_the_excerpt')) return $content;
    $id = (int) get_the_ID();
    if (str_contains($content, 'data-ai-disclosure="wp-' . $id . '"')) return $content;
    return notice($id) . $content;
}
add_filter('the_content', __NAMESPACE__ . '\\add_notice', 99);
add_filter('the_excerpt', __NAMESPACE__ . '\\add_notice', 99);
add_filter('the_excerpt_rss', __NAMESPACE__ . '\\add_notice', 99);
add_action('wp_enqueue_scripts', static function () {
    wp_enqueue_style('ai-disclosure', plugins_url('notice.css', __FILE__), [], '0.1.0-alpha.3');
});
