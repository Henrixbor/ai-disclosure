<?php
// Disposable MySQL fixture only. Each invocation has its own PHP/DB connection.
require '/wordpress/wp-load.php';
wp_set_current_user(1);
$mode = getenv('AID_RACE_MODE');
$phase = getenv('AID_RACE_PHASE');
if (!in_array($phase, ['amend', 'withdraw-first', 'publish-first', 'cron'], true)) throw new Exception('Invalid race phase');
$file = '/tmp/aid-race-' . $phase;
function race_request(string $method, string $route, ?array $body = null) {
    $request = new WP_REST_Request($method, $route);
    if ($body !== null) {
        $request->set_header('content-type', 'application/json');
        $request->set_body(wp_json_encode($body));
    }
    return rest_do_request($request);
}
function race_pause(string $marker): void {
    touch($marker . '.ready');
    $deadline = microtime(true) + 25;
    do {
        clearstatcache(true, $marker . '.go');
        if (is_file($marker . '.go')) return;
        if (microtime(true) > $deadline) throw new Exception('Race barrier timed out: ' . basename($marker));
        usleep(10000);
    } while (true);
}
if ($mode === 'setup') {
    $id = wp_insert_post(['post_title' => 'Concurrent fixture ' . $phase, 'post_content' => '<p>Fictional concurrency test: 50% — café and "quotes".</p>', 'post_status' => 'draft'], true);
    if (is_wp_error($id)) throw new Exception($id->get_error_message());
    $facts = ['origin' => 'ai_generated', 'applicable' => true, 'public_interest' => true, 'evidence' => 'CONCURRENCY_PRIVATE_FIXTURE 50%'];
    $response = race_request('POST', '/ai-disclosure/v1/posts/' . $id . '/assessment', ['role' => 'publisher', 'facts' => $facts]);
    if ($response->get_status() !== 200) throw new Exception('Could not assess race fixture');
    if ($phase === 'cron') {
        wp_update_post(['ID' => $id, 'post_status' => 'future', 'edit_date' => true,
            'post_date' => gmdate('Y-m-d H:i:s', time() + 3600), 'post_date_gmt' => gmdate('Y-m-d H:i:s', time() + 3600)]);
        $wpdb->update($wpdb->posts, ['post_date' => gmdate('Y-m-d H:i:s', time() - 60), 'post_date_gmt' => gmdate('Y-m-d H:i:s', time() - 60)], ['ID' => $id]);
        clean_post_cache($id);
    }
    $state = ['id' => $id, 'facts' => $facts, 'record' => $response->get_data()];
    file_put_contents($file . '.json', wp_json_encode($state));
    echo wp_json_encode($state);
    return;
}
$state = json_decode(file_get_contents($file . '.json'), true, 512, JSON_THROW_ON_ERROR);
$route = '/ai-disclosure/v1/posts/' . $state['id'];
if (in_array($mode, ['amend-a', 'amend-b'], true)) {
    // Force the losing archive inserter to confront a process-local missing-key cache.
    get_option(\AiDisclosure\WordPress\audit_key($state['id'], $state['record']['record_id']));
}
if (in_array($mode, ['amend-a', 'amend-b', 'withdraw-wait'], true)) {
    $waited = false;
    add_filter('query', static function ($query) use (&$waited, $file, $mode) {
        if (!$waited && str_contains($query, 'HEX(option_value)')) {
            $waited = true;
            race_pause($file . '-' . $mode);
        }
        return $query;
    });
}
if (in_array($mode, ['amend-a', 'amend-b'], true)) {
    $facts = $state['facts'];
    $facts['evidence'] .= '-' . $mode;
    $response = race_request('POST', $route . '/assessment', ['role' => 'publisher', 'facts' => $facts,
        'replaces' => $state['record']['record_id'], 'amendment_reason' => $mode]);
} elseif (in_array($mode, ['withdraw', 'withdraw-wait', 'cancel-withdraw'], true)) {
    if ($mode === 'cancel-withdraw') wp_update_post(['ID' => $state['id'], 'post_status' => 'draft']);
    $response = race_request('POST', $route . '/withdrawal', ['revision' => $state['record']['revision'],
        'replaces' => $state['record']['record_id'], 'reason' => 'Withdraw concurrent fixture']);
} elseif (in_array($mode, ['publish', 'publish-wait'], true)) {
    if ($mode === 'publish-wait') {
        add_action('pre_post_update', static function ($id, $data) use ($state, $file) {
            if ($id === $state['id'] && $data['post_status'] === 'publish') race_pause($file . '-publish-wait');
        }, 10, 2);
        add_action('post_updated', static function ($id) use ($state, $file) {
            if ($id === $state['id']) race_pause($file . '-after-write');
        }, 1);
    }
    $result = wp_update_post(['ID' => $state['id'], 'post_status' => 'publish'], true);
    echo wp_json_encode(['error' => is_wp_error($result), 'status' => get_post_status($state['id'])]);
    return;
} elseif ($mode === 'cron-wait') {
    add_filter('query', static function ($query) use ($file) {
        global $wpdb;
        if (str_starts_with($query, "UPDATE `{$wpdb->posts}` SET `post_status` = 'publish' WHERE `ID` = ") && str_contains($query, 'AND EXISTS')) race_pause($file . '-cron-wait');
        return $query;
    }, PHP_INT_MAX);
    add_action('edit_post', static function ($id) use ($state, $file) {
        if ($id === $state['id']) race_pause($file . '-after-write');
    }, 1);
    do_action('publish_future_post', $state['id']);
    echo wp_json_encode(['status' => get_post_status($state['id'])]);
    return;
} elseif ($mode === 'inspect') {
    $current = race_request('GET', $route . '/assessment')->get_data();
    $history = race_request('GET', $route . '/assessments/' . $state['record']['record_id']);
    echo wp_json_encode(['status' => get_post_status($state['id']), 'current' => $current,
        'history_status' => $history->get_status(), 'history' => $history->get_data()]);
    return;
} else throw new Exception('Invalid race mode');
echo wp_json_encode(['status' => $response->get_status(), 'body' => $response->get_data(),
    'connection_id' => (int) $wpdb->get_var('SELECT CONNECTION_ID()')]);
