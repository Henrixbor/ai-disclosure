<?php
declare(strict_types=1);
require __DIR__ . '/../integrations/wordpress/policy.php';

// Test-only batch protocol, not an HTTP endpoint or part of the installed skill.
$inputs = json_decode(stream_get_contents(STDIN), false, 512, JSON_THROW_ON_ERROR);
$outputs = [];
foreach ($inputs as $input) {
    try { $outputs[] = ['result' => \AiDisclosure\assess($input)]; }
    catch (\InvalidArgumentException $error) { $outputs[] = ['invalid' => true]; }
}
echo json_encode($outputs, JSON_THROW_ON_ERROR);
