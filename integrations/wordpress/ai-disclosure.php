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
require_once __DIR__ . '/editor.php';
require_once __DIR__ . '/withdrawal.php';
require_once __DIR__ . '/inventory.php';
require_once __DIR__ . '/publication.php';
require_once __DIR__ . '/cache.php';

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
function record_id(array $record): string { return hash('sha256', wp_json_encode($record)); }
function audit_key(int $id, string $record_id): string { return 'ai_disclosure_audit_' . $id . '_' . $record_id; }
function retain_record(string $key, array $record): bool {
    if (add_option($key, $record, '', false)) return true;
    // A competing insert may have won after this request cached a missing key.
    // Re-read the committed row before distinguishing reuse from storage failure.
    wp_cache_delete($key, 'options');
    wp_cache_delete('notoptions', 'options');
    return get_option($key) === $record;
}
function replace_record(string $key, array $previous, array $replacement, ?int $draft_id = null): bool {
    global $wpdb;
    // WordPress's update_option has no compare-and-swap argument. Compare the full
    // stored value so a writer using an old record cannot overwrite a newer one.
    $draft_guard = $draft_id === null ? '' : $wpdb->prepare(
        " AND EXISTS (SELECT 1 FROM {$wpdb->posts} WHERE ID = %d AND post_status = 'draft')", $draft_id);
    $changed = $wpdb->query($wpdb->prepare(
        "UPDATE {$wpdb->options} SET option_value = %s WHERE option_name = %s AND HEX(option_value) = HEX(%s)" . $draft_guard,
        maybe_serialize($replacement), $key, maybe_serialize($previous)));
    wp_cache_delete($key, 'options');
    if ($changed === false) throw new \RuntimeException('Assessment storage update could not be confirmed');
    return $changed === 1;
}
function private_record(array $record): array {
    return ['record_id' => record_id($record), 'policy' => $record['policy'], 'decision' => $record['status'], 'facts' => $record['facts'],
        'actor' => $record['actor'], 'recorded_at' => $record['recorded_at'],
        'supersedes' => $record['supersedes'] ?? null, 'amendment_reason' => $record['amendment_reason'] ?? null];
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
        $current = record_for($post->ID, $source);
        return ['revision' => revision($source), 'recorded' => $current !== null,
            'assessment' => $current ? private_record($current) : null,
            'supported_text' => supported_text($source), 'policy' => \AiDisclosure\POLICY];
    }
    if (strlen($request->get_body()) > 1048576) return new \WP_Error('ai_disclosure_size', 'Assessment request exceeds 1 MiB.', ['status' => 413]);
    $body = json_decode($request->get_body());
    if (!($body instanceof \stdClass) || array_diff(array_keys(get_object_vars($body)), ['title', 'content', 'excerpt', 'facts', 'role', 'replaces', 'amendment_reason'])) {
        return new \WP_Error('ai_disclosure_input', 'Expected proposed text fields and facts.', ['status' => 400]);
    }
    $amending = property_exists($body, 'replaces') || property_exists($body, 'amendment_reason');
    if ($amending && (!is_string($body->replaces ?? null) || !preg_match('/^[a-f0-9]{64}$/D', $body->replaces)
        || !\AiDisclosure\nonempty($body->amendment_reason ?? null) || strlen($body->amendment_reason) > 1000)) {
        return new \WP_Error('ai_disclosure_input', 'Amendments require the current record ID and a reason of at most 1000 bytes.', ['status' => 400]);
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
    $key = record_key($post->ID, $item->revision);
    $existing = get_option($key);
    if ($existing) {
        $same = ($existing['status'] ?? null) === $record['status'] && ($existing['facts'] ?? null) === $record['facts'] && ($existing['policy'] ?? '') === $record['policy'];
        $retry = $amending && $same && ($existing['supersedes'] ?? null) === $body->replaces
            && ($existing['amendment_reason'] ?? null) === $body->amendment_reason;
        if ($retry || (!$amending && $same)) {
            $record = $existing;
        } elseif (!$amending || !hash_equals(record_id($existing), $body->replaces)) {
            return new \WP_Error('ai_disclosure_conflict', 'Read the current assessment and explicitly amend that record.', ['status' => 409]);
        } elseif ($same) {
            $record = $existing;
        } else {
            $record['supersedes'] = record_id($existing);
            $record['amendment_reason'] = $body->amendment_reason;
            $auditKey = audit_key($post->ID, $record['supersedes']);
            if (!retain_record($auditKey, $existing)) {
                return new \WP_Error('ai_disclosure_storage', 'Could not retain the previous assessment; no amendment applied.', ['status' => 503]);
            }
            try { $changed = replace_record($key, $existing, $record); }
            catch (\RuntimeException $error) {
                return new \WP_Error('ai_disclosure_storage', 'Could not confirm the storage update. Read the current assessment before retrying.', ['status' => 503]);
            }
            if (!$changed) {
                return new \WP_Error('ai_disclosure_conflict', 'The assessment changed during this request; read it before retrying.', ['status' => 409]);
            }
            clean_post_cache($post->ID);
            do_action('ai_disclosure_assessment_amended', $post->ID, $item->revision);
        }
    } elseif ($amending) {
        return new \WP_Error('ai_disclosure_conflict', 'There is no current assessment for this proposed version to amend.', ['status' => 409]);
    } elseif (!add_option($key, $record, '', false)) {
        return new \WP_Error('ai_disclosure_conflict', 'Another assessment was recorded; read it before retrying.', ['status' => 409]);
    } else {
        clean_post_cache($post->ID);
        do_action('ai_disclosure_assessment_recorded', $post->ID, $item->revision);
    }
    return ['revision' => $item->revision, 'record_id' => record_id($record), 'decision' => $record['status'],
        'policy' => $assessment['policy'], 'implementation_verified' => false];
}

add_action('rest_api_init', static function () {
    register_rest_route('ai-disclosure/v1', '/posts/(?P<id>\d+)/inspection', [
        'methods' => 'POST', 'permission_callback' => __NAMESPACE__ . '\\permitted',
        'callback' => static function ($request) {
            if (!permitted($request)) return new \WP_Error('ai_disclosure_forbidden', 'Permission denied.', ['status' => 403]);
            if (strlen($request->get_body()) > 1048576) return new \WP_Error('ai_disclosure_size', 'Inspection request exceeds 1 MiB.', ['status' => 413]);
            $body = json_decode($request->get_body());
            if (!($body instanceof \stdClass) || array_diff(array_keys(get_object_vars($body)), ['title', 'content', 'excerpt'])) {
                return new \WP_Error('ai_disclosure_input', 'Expected proposed title, content and excerpt fields only.', ['status' => 400]);
            }
            $post = get_post((int) $request['id']);
            $source = snapshot($post);
            foreach ($body as $key => $value) {
                if (!is_string($value)) return new \WP_Error('ai_disclosure_input', 'Text fields must be strings.', ['status' => 400]);
                $source[$key] = $value;
            }
            $record = record_for($post->ID, $source);
            return ['revision' => revision($source), 'supported_text' => supported_text($source),
                'assessment' => $record ? private_record($record) : null, 'policy' => \AiDisclosure\POLICY];
        },
    ]);
    register_rest_route('ai-disclosure/v1', '/posts/(?P<id>\d+)/assessment', [
        'methods' => ['GET', 'POST'], 'callback' => __NAMESPACE__ . '\\assessment_route',
        'permission_callback' => __NAMESPACE__ . '\\permitted',
    ]);
    register_rest_route('ai-disclosure/v1', '/posts/(?P<id>\d+)/assessments/(?P<record_id>[a-f0-9]{64})', [
        'methods' => 'GET', 'permission_callback' => __NAMESPACE__ . '\\permitted',
        'callback' => static function ($request) {
            if (!permitted($request)) return new \WP_Error('ai_disclosure_forbidden', 'Permission denied.', ['status' => 403]);
            $record = get_option(audit_key((int) $request['id'], $request['record_id']));
            if (!$record) return new \WP_Error('ai_disclosure_missing', 'No archived assessment with that ID.', ['status' => 404]);
            return private_record($record);
        },
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
    return $id > 0 && supported_text($source) && in_array(record_for($id, $source)['status'] ?? null,
        ['disclose', 'exception_declared', 'no_publisher_label', 'outside_declared_scope'], true);
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
    if (supported($post)) $GLOBALS['ai_disclosure_scheduled_posts'][$id] = clone $post;
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
