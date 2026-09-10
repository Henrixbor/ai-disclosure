<?php
declare(strict_types=1);
namespace AiDisclosure\WordPress;
if (!defined('ABSPATH')) exit;

// Bind the supported core UPDATE to the exact assessment at its database write.
// The query shape is verified against wpdb::update in the pinned WP runtimes.
add_action('pre_post_update', static function ($id, $data) {
    if (!in_array($data['post_type'] ?? '', ['post', 'page'], true)
        || !in_array($data['post_status'] ?? '', ['publish', 'future'], true)) return;
    global $wpdb;
    $source = ['title' => $data['post_title'], 'content' => $data['post_content'], 'excerpt' => $data['post_excerpt']];
    $record = record_for($id, $source);
    $fields = [];
    $values = [];
    foreach ($data as $field => $value) {
        if ($value === null) $fields[] = "`$field` = NULL";
        else {
            $fields[] = "`$field` = " . ($wpdb->field_types[$field] ?? '%s');
            $values[] = $value;
        }
    }
    $values[] = $id;
    $query = $wpdb->prepare("UPDATE `{$wpdb->posts}` SET " . implode(', ', $fields) . " WHERE `ID` = " . ($wpdb->field_types['ID'] ?? '%s'), $values);
    $guard = ' AND 1 = 0';
    if (publication_ready($id, $source)) {
        $guard = $wpdb->prepare(" AND EXISTS (SELECT 1 FROM {$wpdb->options} WHERE option_name = %s AND HEX(option_value) = HEX(%s))",
            record_key($id, revision($source)), maybe_serialize($record));
    }
    // Keep exact-query bindings for this request. Nested updates cannot consume
    // another update's guard; a later assessment refresh can replace its binding.
    $GLOBALS['ai_disclosure_publication_queries'][$wpdb->remove_placeholder_escape($query)] = $wpdb->remove_placeholder_escape($guard);
}, 1, 2);
add_filter('query', static function ($query) {
    return $query . ($GLOBALS['ai_disclosure_publication_queries'][$query] ?? '');
}, PHP_INT_MAX);
