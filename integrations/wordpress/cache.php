<?php
declare(strict_types=1);
namespace AiDisclosure\WordPress;
if (!defined('ABSPATH')) exit;

function purge_page_cache(int $id, string $revision): void {
    if (!defined('WPCACHEHOME') || !function_exists('wp_cache_clear_cache')) return;
    // Notices can occur in home/archive/feed output as well as the post itself.
    // The full-clear API also handles withdrawn drafts and repeated changes,
    // unlike the provider's post-change helper, which can skip those cases.
    \wp_cache_clear_cache(is_multisite() ? get_current_blog_id() : 0);
}
foreach (['recorded', 'amended', 'withdrawn'] as $event) {
    add_action('ai_disclosure_assessment_' . $event, __NAMESPACE__ . '\\purge_page_cache', 10, 2);
}
