<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$cacheFile = __DIR__ . '/cache.json';
$cacheMaxAge = 7 * 24 * 3600; // 7 days

// Serve from cache if fresh
if (file_exists($cacheFile) && (time() - filemtime($cacheFile)) < $cacheMaxAge) {
    readfile($cacheFile);
    exit;
}

// Scan for .sam3dbody files
$dir = '/web/gebarenoverleg_media/studioFilesMini/raw/';
$files = glob($dir . '*.sam3dbody');

$tree = [];

foreach ($files as $path) {
    $basename = basename($path, '.sam3dbody');
    // Pattern: [A-Z]YYYYMMDD_NNNN
    if (preg_match('/^[A-Z](\d{4})(\d{2})(\d{2})_(\d+)$/', $basename, $m)) {
        $year  = $m[1];
        $month = $m[2];
        $day   = $m[3];
        $tree[$year][$month][$day][] = $basename;
    }
}

// Sort keys descending (newest first), file lists alphabetically
krsort($tree);
foreach ($tree as $year => &$months) {
    krsort($months);
    foreach ($months as $month => &$days) {
        krsort($days);
        foreach ($days as $day => &$fileList) {
            sort($fileList);
        }
    }
}
unset($months, $days, $fileList);

$json = json_encode($tree, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
file_put_contents($cacheFile, $json);
echo $json;
