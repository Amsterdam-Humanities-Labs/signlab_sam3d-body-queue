<?php
header('Content-Type: application/json');

// Directory containing the .mp4 files
$directory = '/web/gebarenoverleg_media/studioFilesMini/raw';
$url = 'https://signcollect.nl/gebarenoverleg_media/studioFilesMini/raw/';

// Get all .mp4 files
$files = array();
if (is_dir($directory)) {
    $scan = scandir($directory);
    foreach ($scan as $file) {
        if (pathinfo($file, PATHINFO_EXTENSION) === 'mp4' && substr($file, 0, 1) !== '#') {
            $files[] = array(
                'name' => $file,
                'path' => $url . $file,
                'videoPath' => $url . $file
            );
        }
    }
}

// Return the files as JSON
echo json_encode($files);
?>
