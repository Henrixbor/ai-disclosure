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
$inspection = aid_rest('POST', '/ai-disclosure/v1/posts/' . $id . '/inspection', ['content' => '<p>Proposed, not saved.</p>']);
aid_check($inspection->get_status() === 200 && $inspection->get_data()['assessment'] === null, 'Proposed text can be inspected without recording facts');
aid_check(get_post($id)->post_content === '<p>A fictional reading room opens.</p>', 'Inspection does not mutate content');
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

$current = aid_rest('GET', $reviewRoute)->get_data()['assessment'];
aid_check($current['facts']['review']['responsible_entity'] === 'Fictional test publisher', 'Authorized caller can inspect evidence before amending');
$amendment = ['role' => 'publisher', 'facts' => $facts, 'replaces' => $current['record_id'],
    'amendment_reason' => 'Withdraw the declared review exception; use an explicit notice.'];
$amendmentEvents = 0;
add_action('ai_disclosure_assessment_amended', function () use (&$amendmentEvents) { $amendmentEvents++; });
aid_check(aid_rest('POST', $reviewRoute, ['role' => 'publisher', 'facts' => $facts])->get_status() === 409, 'Changed facts require explicit amendment');
aid_check(aid_rest('POST', $reviewRoute, array_merge($amendment, ['amendment_reason' => ' ']))->get_status() === 400, 'Amendment needs reason');
$unknown = $amendment;
$unknown['facts']['origin'] = 'unknown';
aid_check(aid_rest('POST', $reviewRoute, $unknown)->get_status() === 422, 'Unresolved amendment does not replace active record');
aid_check(aid_rest('GET', $reviewRoute)->get_data()['assessment']['record_id'] === $current['record_id'], 'Rejected amendment preserves active record');
$amended = aid_rest('POST', $reviewRoute, $amendment);
aid_check($amended->get_status() === 200 && $amended->get_data()['decision'] === 'disclose', 'Explicit amendment changes the decision');
aid_check(str_contains(\AiDisclosure\WordPress\notice($reviewed), 'AI-generated'), 'Amended notice takes effect without a content edit');
aid_check(get_post($reviewed)->post_content === '<p>Reviewed text.</p>', 'Amendment does not change post content');
$retry = aid_rest('POST', $reviewRoute, $amendment);
aid_check($retry->get_status() === 200 && $retry->get_data()['record_id'] === $amended->get_data()['record_id'], 'Amendment retry is idempotent');
aid_check($amendmentEvents === 1, 'Cache integration event fires once, after committed amendment');
$stale = $amendment;
$stale['facts']['evidence'] = 'Another correction based on an old record';
aid_check(aid_rest('POST', $reviewRoute, $stale)->get_status() === 409, 'Stale amendment cannot overwrite winner');
$historyRoute = '/ai-disclosure/v1/posts/' . $reviewed . '/assessments/' . $current['record_id'];
$history = aid_rest('GET', $historyRoute);
aid_check($history->get_status() === 200 && $history->get_data() === $current, 'Previous record is retained unchanged');
wp_set_current_user(0);
aid_check(aid_rest('GET', $historyRoute)->get_status() >= 400, 'Archived evidence remains private');
wp_set_current_user(1);
aid_check(aid_rest('GET', '/ai-disclosure/v1/posts/' . $id . '/assessments/' . $current['record_id'])->get_status() === 404, 'History record is bound to its post');

$storageAttempt = $amendment;
$storageAttempt['replaces'] = $amended->get_data()['record_id'];
$storageAttempt['facts']['evidence'] = 'Revised private source reference';
$storageAttempt['amendment_reason'] = 'Update the evidence reference.';
$failUpdate = static function ($query) {
    return str_contains($query, 'HEX(option_value)') ? 'UPDATE ai_disclosure_missing_table SET value = 1' : $query;
};
global $wpdb;
$previousErrors = $wpdb->suppress_errors(true);
add_filter('query', $failUpdate);
try { $storageFailure = aid_rest('POST', $reviewRoute, $storageAttempt); }
finally { remove_filter('query', $failUpdate); $wpdb->suppress_errors($previousErrors); }
aid_check($storageFailure->get_status() === 503, 'Database failure is not reported as a successful amendment');
aid_check(aid_rest('GET', $reviewRoute)->get_data()['assessment']['record_id'] === $amended->get_data()['record_id'], 'Failed database write preserves active record');
aid_check($amendmentEvents === 1, 'Failed database write emits no committed event');

// Withdrawal retains evidence but invalidates publication permission.
$withdrawRoute = '/ai-disclosure/v1/posts/' . $reviewed . '/withdrawal';
$beforeWithdraw = aid_rest('GET', $reviewRoute)->get_data();
$rawBeforeWithdraw = \AiDisclosure\WordPress\record_for($reviewed, \AiDisclosure\WordPress\snapshot(get_post($reviewed)));
$withdrawBody = ['revision' => $beforeWithdraw['revision'], 'replaces' => $beforeWithdraw['assessment']['record_id'], 'reason' => 'Origin evidence was found to be unreliable.'];
wp_set_current_user(0);
aid_check(aid_rest('POST', $withdrawRoute, $withdrawBody)->get_status() >= 400, 'Withdrawal requires authentication');
wp_set_current_user(1);
aid_check(aid_rest('POST', $withdrawRoute, $withdrawBody)->get_status() === 409, 'Published article must be made draft before withdrawal');
wp_update_post(['ID' => $reviewed, 'post_status' => 'draft']);
aid_check(aid_rest('POST', $withdrawRoute, array_merge($withdrawBody, ['reason' => ' ']))->get_status() === 400, 'Withdrawal requires meaningful reason');
$withdrawEvents = 0;
add_action('ai_disclosure_assessment_withdrawn', function () use (&$withdrawEvents) { $withdrawEvents++; });
$withdrawn = aid_rest('POST', $withdrawRoute, $withdrawBody);
aid_check($withdrawn->get_status() === 200 && $withdrawn->get_data()['decision'] === 'withdrawn', 'Draft assessment can be withdrawn');
aid_check(aid_rest('POST', $withdrawRoute, $withdrawBody)->get_data() === $withdrawn->get_data(), 'Withdrawal retry returns same audit record');
aid_check($withdrawEvents === 1, 'Withdrawal event emitted once');
aid_check(aid_rest('POST', '/wp/v2/posts/' . $reviewed, ['status' => 'publish'])->get_status() === 409, 'Withdrawn assessment cannot publish');
aid_check(is_wp_error(wp_update_post(['ID' => $reviewed, 'post_status' => 'publish'], true)), 'Native path rejects withdrawn version');
aid_check(aid_rest('POST', $reviewRoute, ['role' => 'publisher', 'facts' => $facts])->get_status() === 409, 'Old facts cannot silently reactivate withdrawal');
$withdrawArchive = aid_rest('GET', '/ai-disclosure/v1/posts/' . $reviewed . '/assessments/' . $withdrawBody['replaces']);
aid_check($withdrawArchive->get_data() === $beforeWithdraw['assessment'], 'Withdrawal preserves exact prior record');
// Simulate publication already past its precheck when withdrawal committed.
$wpdb->update($wpdb->posts, ['post_status' => 'publish'], ['ID' => $reviewed]);
clean_post_cache($reviewed);
wp_cache_set(\AiDisclosure\WordPress\record_key($reviewed, $withdrawBody['revision']), $rawBeforeWithdraw, 'options');
do_action('wp_after_insert_post', $reviewed, get_post($reviewed), true, null);
aid_check(get_post_status($reviewed) === 'draft', 'Post-write check returns raced publication to draft');
$restored = aid_rest('POST', $reviewRoute, ['role' => 'publisher', 'facts' => $facts,
    'replaces' => $withdrawn->get_data()['record_id'], 'amendment_reason' => 'Re-established the source evidence.']);
aid_check($restored->get_status() === 200 && $restored->get_data()['decision'] === 'disclose', 'Explicit reassessment can restore identical newly established facts');
aid_check(aid_rest('POST', $withdrawRoute, $withdrawBody)->get_status() === 409, 'Old withdrawal retry cannot invalidate restored assessment');
aid_check(!is_wp_error(wp_update_post(['ID' => $reviewed, 'post_status' => 'publish'], true)), 'Explicitly restored assessment permits publication');

// Exercise an actual database CAS with two writers holding the same old value.
$casKey = 'ai_disclosure_cas_fixture';
$previous = ['token' => 'original'];
add_option($casKey, $previous, '', false);
aid_check(\AiDisclosure\WordPress\replace_record($casKey, $previous, ['token' => 'ORIGINAL']), 'First database writer succeeds with a case-only change');
aid_check(!\AiDisclosure\WordPress\replace_record($casKey, $previous, ['token' => 'stale-writer']), 'Second database writer is rejected');
aid_check(get_option($casKey) === ['token' => 'ORIGINAL'], 'Object cache reflects the committed winner');
delete_option($casKey);

// Historical discovery is bounded, private, and never guesses source facts.
function aid_inventory(array $query = []) {
    $request = new WP_REST_Request('GET', '/ai-disclosure/v1/inventory');
    $request->set_query_params($query);
    return rest_do_request($request);
}
wp_set_current_user(0);
aid_check(aid_inventory()->get_status() >= 400, 'Anonymous inventory denied');
wp_set_current_user($subscriber);
aid_check(aid_inventory()->get_status() === 403, 'Subscriber inventory denied');
wp_set_current_user(1);
foreach ([['limit' => 101], ['limit' => 0], ['after' => -1], ['after' => '1e2'], ['through_id' => []], ['after' => '999999999999999999999999'], ['after' => 2, 'through_id' => 1]] as $invalid) {
    aid_check(aid_inventory($invalid)->get_status() === 400, 'Invalid inventory range rejected');
}
$historical = wp_insert_post(['post_title' => 'Historical unknown origin', 'post_content' => '<p>Unclassified archive text.</p>', 'post_status' => 'draft'], true);
// Model a publication predating activation; discovery must not relabel it.
$wpdb->update($wpdb->posts, ['post_status' => 'publish'], ['ID' => $historical]);
clean_post_cache($historical);
$mediaArchive = wp_insert_post(['post_type' => 'page', 'post_title' => 'Historical media', 'post_content' => '<img src="example.png" alt="Unknown source">', 'post_status' => 'draft'], true);
$withdrawArchiveId = wp_insert_post(['post_title' => 'Withdrawn archive', 'post_content' => '<p>Withdrawn archive text.</p>', 'post_status' => 'draft'], true);
$withdrawArchiveRoute = '/ai-disclosure/v1/posts/' . $withdrawArchiveId;
$archiveAssessment = aid_rest('POST', $withdrawArchiveRoute . '/assessment', $declaration)->get_data();
aid_check(aid_rest('POST', $withdrawArchiveRoute . '/withdrawal', ['revision' => $archiveAssessment['revision'], 'replaces' => $archiveAssessment['record_id'], 'reason' => 'Inventory fixture withdrawn.'])->get_status() === 200, 'Create withdrawn inventory fixture');
$firstPage = aid_inventory(['limit' => 2])->get_data();
$newAfterBoundary = wp_insert_post(['post_title' => 'Created during inventory', 'post_status' => 'draft'], true);
$allItems = $firstPage['items'];
$page = $firstPage;
$pages = 0;
while ($page['next_after'] !== null) {
    aid_check(++$pages < 100, 'Inventory cursor makes progress');
    $page = aid_inventory(['limit' => 2, 'after' => $page['next_after'], 'through_id' => $firstPage['through_id']])->get_data();
    aid_check(count($page['items']) <= 2 && $page['through_id'] === $firstPage['through_id'], 'Bounded pages preserve scan boundary');
    $allItems = array_merge($allItems, $page['items']);
}
$indexed = array_column($allItems, null, 'id');
aid_check(count($indexed) === count($allItems), 'Inventory has no duplicate IDs');
aid_check(!isset($indexed[$newAfterBoundary]), 'New posts do not extend an in-progress scan');
aid_check($indexed[$historical]['decision'] === 'unassessed', 'Historical content retains unknown assessment state');
aid_check($indexed[$historical]['status'] === 'publish' && \AiDisclosure\WordPress\notice($historical) === '', 'Published legacy content is found without an invented label');
aid_check($indexed[$mediaArchive]['supported_text'] === false, 'Unsupported archived media remains visible as a coverage gap');
aid_check($indexed[$withdrawArchiveId]['decision'] === 'withdrawn', 'Withdrawn archive cannot look approved');
aid_check($indexed[$id]['decision'] === 'disclose', 'Recorded publication is distinguished from gaps');
aid_check(!str_contains(wp_json_encode($allItems), 'WORDPRESS_PRIVATE_EVIDENCE'), 'Inventory does not return evidence bodies');
aid_check(aid_rest('GET', '/ai-disclosure/v1/posts/' . $historical . '/assessment')->get_data()['recorded'] === false, 'Inventory does not create assessment records');
$author = wp_create_user('inventory-author', wp_generate_password(), 'inventory-author@example.invalid');
(new WP_User($author))->set_role('author');
$ownDraft = wp_insert_post(['post_title' => 'Author own draft', 'post_status' => 'draft', 'post_author' => $author], true);
wp_set_current_user($author);
$emptyAuthorizedPage = aid_inventory(['limit' => 1])->get_data();
aid_check($emptyAuthorizedPage['items'] === [] && $emptyAuthorizedPage['next_after'] !== null, 'Empty authorized page can still have a continuation cursor');
$authorPage = aid_inventory(['after' => $ownDraft - 1, 'through_id' => $ownDraft])->get_data();
aid_check(array_column($authorPage['items'], 'id') === [$ownDraft], 'Author can discover own content');
wp_set_current_user(1);

$failInventory = static function ($query) {
    return str_contains($query, "post_type IN ('post', 'page')") ? 'SELECT ID FROM ai_disclosure_missing_table' : $query;
};
$previousErrors = $wpdb->suppress_errors(true);
add_filter('query', $failInventory);
try { $failedInventory = aid_inventory(); }
finally { remove_filter('query', $failInventory); $wpdb->suppress_errors($previousErrors); }
aid_check($failedInventory->get_status() === 503, 'Database failure must not masquerade as an empty completed inventory');

$uiClassic = wp_insert_post(['post_title' => 'Classic editor fixture', 'post_content' => 'Fictional editor test text.', 'post_status' => 'draft'], true);
$uiBlock = wp_insert_post(['post_title' => 'Block editor fixture', 'post_content' => '<!-- wp:paragraph --><p>Fictional block editor text.</p><!-- /wp:paragraph -->', 'post_status' => 'draft'], true);
update_post_meta($uiClassic, 'aid_classic_fixture', true);
wp_mkdir_p('/wordpress/wp-content/mu-plugins');
file_put_contents('/wordpress/wp-content/mu-plugins/aid-editor-fixture.php', '<?php add_filter("use_block_editor_for_post", static function($use, $post) { return get_post_meta($post->ID, "aid_classic_fixture", true) ? false : $use; }, 10, 2);');
file_put_contents('/wordpress/aid-test-result.json', wp_json_encode(['id' => $id, 'classic_id' => $uiClassic, 'block_id' => $uiBlock, 'history_route' => $historyRoute, 'checks' => 'passed']));
echo "WordPress publishing, amendment, database conflict and evidence checks passed\n";
