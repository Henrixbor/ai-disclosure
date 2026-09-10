<?php
declare(strict_types=1);
namespace AiDisclosure\WordPress;
if (!defined('ABSPATH')) exit;

function editor_select(string $field, string $label, array $options): void {
    echo '<label>' . esc_html($label) . '<select data-aid-field="' . esc_attr($field) . '">';
    foreach ($options as $value => $text) echo '<option value="' . esc_attr($value) . '">' . esc_html($text) . '</option>';
    echo '</select></label>';
}
add_action('add_meta_boxes', static function ($type, $post) {
    if (!supported($post) || !current_user_can('edit_post', $post->ID)
        || !current_user_can(get_post_type_object($type)->cap->publish_posts)) return;
    add_meta_box('ai-disclosure-editor', 'AI disclosure', static function () {
        echo '<div class="aid-editor"><p>Load the text currently in the editor, then record its source and publication context. This does not publish the post.</p>';
        echo '<button type="button" class="button" data-aid-load disabled>Load current text</button>';
        echo '<fieldset data-aid-fields disabled><legend class="screen-reader-text">Disclosure facts</legend><div class="aid-editor-grid">';
        editor_select('role', 'Your role', ['unknown' => 'Not established', 'publisher' => 'Publisher / deployer', 'provider' => 'AI system provider', 'both' => 'Both']);
        editor_select('origin', 'Content source', ['unknown' => 'Unknown', 'human' => 'Human-created', 'ai_generated' => 'AI-generated', 'ai_modified' => 'AI-modified']);
        editor_select('applicable', 'EU AI transparency rules apply', ['unknown' => 'Not established', 'true' => 'Yes — established for this publication', 'false' => 'No — supported by scope evidence']);
        editor_select('public_interest', 'Published to inform on matters of public interest', ['unknown' => 'Not established', 'true' => 'Yes', 'false' => 'No']);
        echo '</div><label>Source and scope evidence<textarea rows="3" data-aid-field="evidence" aria-describedby="aid-evidence-help"></textarea></label>';
        echo '<p id="aid-evidence-help" class="description">Reference the creation record and the basis for these decisions. Private evidence is not added to the public notice.</p>';
        echo '<label class="aid-editor-check"><input type="checkbox" data-aid-field="review"> This exact text has received substantive human review</label>';
        echo '<label data-aid-responsibility hidden>Person or organisation with editorial responsibility<input type="text" data-aid-field="responsible_entity"></label>';
        echo '<label data-aid-amendment hidden>Reason for changing this assessment<textarea rows="2" data-aid-field="amendment_reason"></textarea></label>';
        echo '<p><button type="button" class="button button-primary" data-aid-save>Record assessment</button> <button type="button" class="button" data-aid-withdraw hidden>Withdraw assessment</button></p></fieldset>';
        echo '<p role="status" aria-live="polite" data-aid-status>Load the current text to begin.</p>';
        echo '<noscript><p>These controls require JavaScript. The authenticated assessment API is also available.</p></noscript></div>';
    }, $type, 'normal', 'high', ['__block_editor_compatible_meta_box' => true]);
}, 10, 2);

add_action('admin_enqueue_scripts', static function ($hook) {
    if (!in_array($hook, ['post.php', 'post-new.php'], true)) return;
    global $post;
    if (!supported($post) || !current_user_can('edit_post', $post->ID)
        || !current_user_can(get_post_type_object($post->post_type)->cap->publish_posts)) return;
    wp_enqueue_style('ai-disclosure-editor', plugins_url('editor.css', __FILE__), [], '0.1.0-alpha.3');
    wp_enqueue_script('ai-disclosure-editor', plugins_url('editor.js', __FILE__), ['wp-data', 'wp-dom-ready'], hash_file('sha256', __DIR__ . '/editor.js'), true);
    wp_add_inline_script('ai-disclosure-editor', 'window.aiDisclosureEditor = ' . wp_json_encode([
        'postId' => $post->ID, 'restRoot' => rest_url('ai-disclosure/v1/posts/' . $post->ID . '/'),
        'nonce' => wp_create_nonce('wp_rest'),
    ]) . ';', 'before');
});
