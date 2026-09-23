<?php
require_once __DIR__ . '/sc_paths.php';
header('Content-Type: application/json');

$uploadsDir = sc_path('media_raw');
$filesAvailable = [];

if (!is_dir($uploadsDir) || !is_readable($uploadsDir)) {
    echo json_encode(['error' => 'Uploads directory not found or not readable.']);
    exit;
}

$allFiles = scandir($uploadsDir);

if ($allFiles === false) {
    echo json_encode(['error' => 'Failed to read uploads directory contents.']);
    exit;
}

foreach ($allFiles as $file) {
    if ($file === '.' || $file === '..') {
        continue;
    }
    
    $extension = strtolower(pathinfo($file, PATHINFO_EXTENSION));
    
    if ($extension === 'mp4') {
        $filesAvailable[] = $file;
    }
}

echo json_encode($filesAvailable);
?>