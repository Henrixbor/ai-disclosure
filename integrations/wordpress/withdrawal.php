<?php
declare(strict_types=1);
namespace AiDisclosure\WordPress;
if (!defined('ABSPATH')) exit;

function withdrawal_route($request) {
    if (!permitted($request)) return new \WP_Error('ai_disclosure_forbidden', 'Permission denied.', ['status' => 403]);
    if (strlen($request->get_body()) > 1048576) return new \WP_Error('ai_disclosure_size', 'Request exceeds 1 MiB.', ['status' => 413]);
    $body = json_decode($request->get_body());
    if (!($body instanceof \stdClass) || array_diff(array_keys(get_object_vars($body)), ['revision', 'replaces', 'reason'])
        || !is_string($body->revision ?? null) || !preg_match('/^sha256:[a-f0-9]{64}$/D', $body->revision)
        || !is_string($body->replaces ?? null) || !preg_match('/^[a-f0-9]{64}$/D', $body->replaces)
        || !\AiDisclosure\nonempty($body->reason ?? null) || strlen($body->reason) > 1000) {
        return new \WP_Error('ai_disclosure_input', 'Supply the saved revision, current record ID and a reason of at most 1000 bytes.', ['status' => 400]);
    }
    $post = get_post((int) $request['id']);
    if ($post->post_status !== 'draft' || revision(snapshot($post)) !== $body->revision) {
        return new \WP_Error('ai_disclosure_conflict', 'Save this exact text as a draft before withdrawing its assessment.', ['status' => 409]);
    }
    $existing = record_for($post->ID, snapshot($post));
    if (!$existing) return new \WP_Error('ai_disclosure_conflict', 'No assessment exists for this saved version.', ['status' => 409]);
    if ($existing['status'] === 'withdrawn' && ($existing['supersedes'] ?? null) === $body->replaces
        && ($existing['amendment_reason'] ?? null) === $body->reason) return private_record($existing);
    if ($existing['status'] === 'withdrawn' || !hash_equals(record_id($existing), $body->replaces)) {
        return new \WP_Error('ai_disclosure_conflict', 'Read the current assessment before withdrawing it.', ['status' => 409]);
    }
    $record = $existing;
    $record['status'] = 'withdrawn';
    $record['supersedes'] = record_id($existing);
    $record['amendment_reason'] = $body->reason;
    $record['actor'] = get_current_user_id();
    $record['recorded_at'] = gmdate('c');
    $auditKey = audit_key($post->ID, $record['supersedes']);
    if (!add_option($auditKey, $existing, '', false) && get_option($auditKey) !== $existing) {
        return new \WP_Error('ai_disclosure_storage', 'Could not retain the previous assessment; no withdrawal applied.', ['status' => 503]);
    }
    try { $changed = replace_record(record_key($post->ID, $body->revision), $existing, $record, $post->ID); }
    catch (\RuntimeException $error) {
        return new \WP_Error('ai_disclosure_storage', 'Could not confirm withdrawal. Read the assessment before retrying.', ['status' => 503]);
    }
    if (!$changed) return new \WP_Error('ai_disclosure_conflict', 'The assessment or draft status changed; read it before retrying.', ['status' => 409]);
    clean_post_cache($post->ID);
    do_action('ai_disclosure_assessment_withdrawn', $post->ID, $body->revision);
    return private_record($record);
}
add_action('rest_api_init', static function () {
    register_rest_route('ai-disclosure/v1', '/posts/(?P<id>\d+)/withdrawal', [
        'methods' => 'POST', 'permission_callback' => __NAMESPACE__ . '\\permitted',
        'callback' => __NAMESPACE__ . '\\withdrawal_route',
    ]);
});

// A publisher may have passed the pre-insert check immediately before withdrawal.
// Recheck after the core write; never leave that withdrawn version published.
add_action('wp_after_insert_post', static function ($id, $post) {
    if (!supported($post) || !in_array($post->post_status, ['publish', 'future'], true)) return;
    // Discard a process-local value read by the pre-insert check before another
    // request withdrew it. The post-write check must read the committed record.
    wp_cache_delete(record_key($id, revision(snapshot($post))), 'options');
    $record = record_for($id, snapshot($post));
    if (($record['status'] ?? null) === 'withdrawn') wp_update_post(['ID' => $id, 'post_status' => 'draft']);
}, 10, 2);
