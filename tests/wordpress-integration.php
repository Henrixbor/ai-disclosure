<?php
require '/wordpress/wp-load.php';
function aid_check($condition, $message) { if (!$condition) throw new Exception($message); }
function aid_rest($method, $path, $body = null) {
    $request = new WP_REST_Request($method, $path);
    if ($body !== null) {
        $request->set_header('content-type', 'application/json');
        $request->set_body(wp_json_encode($body));
    }
    return rest_do_request($request);
}
wp_set_current_user(1);
$id = wp_insert_post(['post_title' => 'Fictional town news', 'post_content' => '<p>A fictional reading room opens.</p>', 'post_status' => 'draft'], true);
aid_check(is_int($id) && $id > 0, 'Create draft');
$route = '/ai-disclosure/v1/posts/' . $id . '/assessment';
$facts = ['origin' => 'ai_generated', 'applicable' => true, 'public_interest' => true,
    'evidence' => 'WORDPRESS_PRIVATE_EVIDENCE: explicit fictional test declaration'];
$declaration = ['role' => 'publisher', 'facts' => $facts];
wp_set_current_user(0);
aid_check(aid_rest('GET', $route)->get_status() >= 400, 'Anonymous inspection denied');
aid_check(aid_rest('POST', $route, $declaration)->get_status() >= 400, 'Anonymous recording denied');
$subscriber = wp_create_user('subscriber-fixture', wp_generate_password(), 'subscriber@example.invalid');
(new WP_User($subscriber))->set_role('subscriber');
wp_set_current_user($subscriber);
aid_check(aid_rest('POST', $route, $declaration)->get_status() === 403, 'Insufficient capabilities denied');
wp_set_current_user(1);
aid_check(aid_rest('POST', '/wp/v2/posts/' . $id, ['status' => 'publish'])->get_status() === 409, 'REST blocks missing facts');
aid_check(is_wp_error(wp_update_post(['ID' => $id, 'post_status' => 'publish'], true)), 'Native update blocks missing facts');
aid_check(aid_rest('POST', $route, ['facts' => $facts])->get_status() === 422, 'Role cannot be assumed');
aid_check(aid_rest('POST', $route, $declaration + ['content' => '<img src="image.jpg" alt="Photo">'])->get_status() === 422, 'Unsupported independent media held');
aid_check(aid_rest('POST', $route, $declaration)->get_status() === 200, 'Record declared version');
aid_check(aid_rest('POST', $route, $declaration)->get_status() === 200, 'Recording is idempotent');
aid_check(aid_rest('POST', $route, ['role' => 'publisher', 'facts' => array_reverse($facts, true)])->get_status() === 200, 'JSON property order does not change facts');
aid_check(aid_rest('POST', '/wp/v2/posts/' . $id, ['status' => 'publish'])->get_status() === 200, 'Publish recorded version');
$original = get_post($id)->post_content;
aid_check(aid_rest('POST', '/wp/v2/posts/' . $id, ['content' => '<p>Unrecorded change.</p>'])->get_status() === 409, 'REST stale edit rejected');
aid_check(is_wp_error(wp_update_post(['ID' => $id, 'post_title' => 'Unrecorded headline'], true)), 'Native stale edit rejected');
aid_check(get_post($id)->post_content === $original && get_post($id)->post_title === 'Fictional town news', 'Old publication retained');
$changed = '<p>The fictional room opens on Friday. Café "notes" at C:\\news.</p>';
$newFacts = $facts;
$newFacts['origin'] = 'ai_modified';
aid_check(aid_rest('POST', $route, ['role' => 'publisher', 'content' => $changed, 'facts' => $newFacts])->get_status() === 200, 'Assess proposed update');
aid_check(get_post($id)->post_content === $original, 'Assessment does not publish');
aid_check(aid_rest('POST', '/wp/v2/posts/' . $id, ['content' => $changed])->get_status() === 200, 'Publish assessed update');
aid_check(str_contains(\AiDisclosure\WordPress\notice($id), 'AI-modified'), 'New version has new notice');
aid_check(aid_rest('POST', $route, $declaration)->get_status() === 409, 'Conflicting facts cannot overwrite a version');
$GLOBALS['post'] = get_post($id);
setup_postdata($GLOBALS['post']);
$rendered = apply_filters('the_content', get_post($id)->post_content);
aid_check(substr_count($rendered, 'data-ai-disclosure=') === 1, 'One content notice');
$excerpt = apply_filters('the_excerpt', get_the_excerpt($id));
aid_check(substr_count($excerpt, 'AI-modified') === 1, 'Generated excerpt has one notice');
$public = aid_rest('GET', '/wp/v2/posts/' . $id)->get_data();
aid_check(!str_contains(wp_json_encode($public), 'WORDPRESS_PRIVATE_EVIDENCE'), 'REST does not expose evidence');
aid_check(str_contains($public['content']['rendered'], 'AI-modified'), 'REST content includes notice');
aid_check(str_contains($public['excerpt']['rendered'], 'AI-modified'), 'REST excerpt includes notice');

$scheduled = wp_insert_post(['post_title' => 'Scheduled fixture', 'post_content' => '<p>Scheduled text.</p>', 'post_status' => 'draft'], true);
$scheduledRoute = '/ai-disclosure/v1/posts/' . $scheduled . '/assessment';
aid_check(aid_rest('POST', $scheduledRoute, $declaration)->get_status() === 200, 'Record scheduled text');
$date = gmdate('Y-m-d H:i:s', time() + 3600);
aid_check(!is_wp_error(wp_update_post(['ID' => $scheduled, 'post_status' => 'future', 'post_date' => $date, 'post_date_gmt' => $date, 'edit_date' => true], true)), 'Schedule recorded text');
aid_check(get_post_status($scheduled) === 'future', 'Expected future status, got ' . get_post_status($scheduled));
$key = \AiDisclosure\WordPress\record_key($scheduled, \AiDisclosure\WordPress\revision(\AiDisclosure\WordPress\snapshot(get_post($scheduled))));
$record = get_option($key);
$record['policy'] = 'superseded-test-policy';
update_option($key, $record, false);
do_action('publish_future_post', $scheduled);
aid_check(get_post_status($scheduled) === 'pending', 'Cron holds superseded policy; got ' . get_post_status($scheduled));

$reviewed = wp_insert_post(['post_title' => 'Reviewed fixture', 'post_content' => '<p>Reviewed text.</p>', 'post_status' => 'draft'], true);
$reviewRoute = '/ai-disclosure/v1/posts/' . $reviewed . '/assessment';
$reviewFacts = $facts;
$reviewFacts['review'] = ['revision' => aid_rest('GET', $reviewRoute)->get_data()['revision'],
    'substantive_human_review' => true, 'responsible_entity' => 'Fictional test publisher'];
$response = aid_rest('POST', $reviewRoute, ['role' => 'publisher', 'facts' => $reviewFacts]);
aid_check($response->get_status() === 200 && $response->get_data()['decision'] === 'exception_declared', 'Current declared review exception');
aid_check(!is_wp_error(wp_update_post(['ID' => $reviewed, 'post_status' => 'publish'], true)), 'Publish reviewed fixture');
aid_check(\AiDisclosure\WordPress\notice($reviewed) === '', 'No unnecessary notice for current review');
aid_check(aid_rest('POST', '/wp/v2/posts/' . $reviewed, ['content' => '<p>Changed after review.</p>'])->get_status() === 409, 'Review cannot silently cover edits');

file_put_contents('/wordpress/aid-test-result.json', wp_json_encode(['id' => $id, 'checks' => 'passed']));
echo "WordPress REST, native-update, scheduling and evidence checks passed\n";
