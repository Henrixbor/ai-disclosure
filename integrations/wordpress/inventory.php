<?php
declare(strict_types=1);
namespace AiDisclosure\WordPress;
if (!defined('ABSPATH')) exit;

function inventory_permitted(): bool {
    return current_user_can('publish_posts') || current_user_can('publish_pages');
}
function inventory_route($request) {
    if (!inventory_permitted()) return new \WP_Error('ai_disclosure_forbidden', 'Permission denied.', ['status' => 403]);
    $params = $request->get_query_params();
    $numbers = ['after' => 0, 'limit' => 25, 'through_id' => null];
    foreach ($numbers as $key => $default) {
        if (!array_key_exists($key, $params)) continue;
        $value = $params[$key];
        if ((!is_string($value) && !is_int($value)) || !preg_match('/^(0|[1-9][0-9]*)$/D', (string) $value)
            || strlen((string) $value) > strlen((string) PHP_INT_MAX)
            || (strlen((string) $value) === strlen((string) PHP_INT_MAX) && strcmp((string) $value, (string) PHP_INT_MAX) > 0)) {
            return new \WP_Error('ai_disclosure_input', 'Inventory cursors and limit must be nonnegative integers.', ['status' => 400]);
        }
        $numbers[$key] = (int) $value;
    }
    ['after' => $after, 'limit' => $limit, 'through_id' => $through] = $numbers;
    if ($limit < 1 || $limit > 100 || ($through !== null && $after > $through)) {
        return new \WP_Error('ai_disclosure_input', 'Limit must be 1–100 and after must not exceed through_id.', ['status' => 400]);
    }
    global $wpdb;
    if ($through === null) {
        $through = $wpdb->get_var("SELECT MAX(ID) FROM {$wpdb->posts} WHERE post_type IN ('post', 'page')");
        if ($wpdb->last_error) return new \WP_Error('ai_disclosure_storage', 'Could not read the inventory boundary.', ['status' => 503]);
        $through = (int) $through;
    }
    $ids = $wpdb->get_col($wpdb->prepare(
        "SELECT ID FROM {$wpdb->posts} WHERE post_type IN ('post', 'page') AND ID > %d AND ID <= %d ORDER BY ID ASC LIMIT %d",
        $after, $through, $limit + 1));
    if ($wpdb->last_error) return new \WP_Error('ai_disclosure_storage', 'Could not read the inventory page.', ['status' => 503]);
    $more = count($ids) > $limit;
    $ids = array_slice($ids, 0, $limit);
    $items = [];
    foreach ($ids as $id) {
        $post = get_post((int) $id);
        if (!supported($post) || !current_user_can('edit_post', $post->ID)
            || !current_user_can(get_post_type_object($post->post_type)->cap->publish_posts)) continue;
        $source = snapshot($post);
        $record = record_for($post->ID, $source);
        $items[] = ['id' => $post->ID, 'type' => $post->post_type, 'status' => $post->post_status,
            'title_excerpt' => wp_html_excerpt($post->post_title, 160, '…'), 'revision' => revision($source),
            'supported_text' => supported_text($source), 'decision' => $record['status'] ?? 'unassessed'];
    }
    return ['items' => $items, 'through_id' => $through, 'next_after' => $more ? (int) end($ids) : null,
        'policy' => \AiDisclosure\POLICY, 'coverage' => 'post-page-source-only'];
}
add_action('rest_api_init', static function () {
    register_rest_route('ai-disclosure/v1', '/inventory', [
        'methods' => 'GET', 'permission_callback' => __NAMESPACE__ . '\\inventory_permitted',
        'callback' => __NAMESPACE__ . '\\inventory_route',
    ]);
});
