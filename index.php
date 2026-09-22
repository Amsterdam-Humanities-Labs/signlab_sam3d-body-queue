<?php
require_once __DIR__ . '/sc_paths.php';

header('Content-Type: application/json');

$mediaDir = sc_path('media_raw');
$filesAvailable = [];
$limit = 1000; // Increased limit to 1000
$count = 0;

if (!is_dir($mediaDir) || !is_readable($mediaDir)) {
    echo json_encode(['error' => 'Media directory not found or not readable.']);
    exit;
}

$mp4Files = glob($mediaDir . '/*.mp4');

if ($mp4Files === false) {
    echo json_encode(['error' => 'Failed to read media directory contents.']);
    exit;
}

// Shuffle will be done within categories for proper prioritization
// shuffle($mp4Files);

$categorizedFiles = [
    'M20' => [],
    'M' => [],
    'LR' => [],
    'AB' => [],
    'Other' => []
];

foreach ($mp4Files as $mp4File) {
    $baseName = pathinfo($mp4File, PATHINFO_FILENAME);
    $sam3dbodyFile = $mediaDir . '/' . $baseName . '.sam3dbody';
    $lockFile = $mediaDir . '/' . $baseName . '.s3b_lock';

    // Skip files with parentheses or "_h264" in the name
    if (strpos($baseName, '(') !== false || strpos($baseName, '_h264') !== false) {
        continue;
    }

    // Skip files larger than 20MB
    if (filesize($mp4File) > 20 * 1024 * 1024) {
        continue;
    }

    if (!file_exists($sam3dbodyFile) && !file_exists($lockFile)) {
        $fileName = basename($mp4File);
        $firstChar = strtoupper(substr($fileName, 0, 1));

        // Check for M20 pattern first (highest priority)
        if (substr($fileName, 0, 3) === 'M20') {
            $categorizedFiles['M20'][] = $fileName;
        } elseif ($firstChar === 'M') {
            $categorizedFiles['M'][] = $fileName;
        } elseif ($firstChar === 'L' || $firstChar === 'R') {
            $categorizedFiles['LR'][] = $fileName;
        } elseif ($firstChar === 'A' || $firstChar === 'B') {
            $categorizedFiles['AB'][] = $fileName;
        } else {
            $categorizedFiles['Other'][] = $fileName;
        }
    }
}

$priorityOrder = ['M20', 'M', 'LR', 'AB', 'Other'];

// Shuffle each category independently for randomization within priority groups
foreach ($categorizedFiles as &$categoryFiles) {
    shuffle($categoryFiles);
}
unset($categoryFiles); // Break reference

foreach ($priorityOrder as $category) {
    foreach ($categorizedFiles[$category] as $file) {
        if ($count < $limit) {
            $filesAvailable[] = $file;
            $count++;
        } else {
            break 2; // Break both loops if limit is reached
        }
    }
}

echo json_encode($filesAvailable);

?>
