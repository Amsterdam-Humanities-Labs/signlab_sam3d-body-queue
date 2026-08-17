<?php
header('Content-Type: application/json');

// Get the filename from the request
$filename = isset($_POST['filename']) ? $_POST['filename'] : null;

if (!$filename) {
    echo json_encode(['success' => false, 'message' => 'No filename provided']);
    exit;
}

$mediaDir = '/web/gebarenoverleg_media/studioFilesMini/raw';

// Ensure the filename is sanitized (only allow mp4 files)
if (!preg_match('/^[a-zA-Z0-9_\-]+\.mp4$/', $filename)) {
    echo json_encode(['success' => false, 'message' => 'Invalid filename format']);
    exit;
}

$mp4Path = $mediaDir . '/' . $filename;
$lockPath = $mediaDir . '/' . pathinfo($filename, PATHINFO_FILENAME) . '.s3b_lock';
$sam3dbodyPath = $mediaDir . '/' . pathinfo($filename, PATHINFO_FILENAME) . '.sam3dbody';

// Check if the mp4 file exists
if (!file_exists($mp4Path)) {
    echo json_encode(['success' => false, 'message' => 'MP4 file does not exist']);
    exit;
}

// Check if a sam3dbody file already exists
if (file_exists($sam3dbodyPath)) {
    echo json_encode(['success' => false, 'message' => 'sam3dbody file already exists for this file']);
    exit;
}

// Check if a lock file already exists
if (file_exists($lockPath)) {
    echo json_encode(['success' => false, 'message' => 'This file is already being processed']);
    exit;
}

// Create a new lock file
if (file_put_contents($lockPath, date('Y-m-d H:i:s')) !== false) {
    echo json_encode(['success' => true, 'message' => 'Lock file created successfully']);
} else {
    echo json_encode(['success' => false, 'message' => 'Failed to create lock file']);
}
?>
