<?php
require_once __DIR__ . '/sc_paths.php';
require_once __DIR__ . '/auth.php';
s3b_require_token();   // worker only: X-Api-Token

header('Content-Type: application/json');

$targetDir = sc_dir('media_raw');
$response = ['status' => 'error', 'message' => 'Invalid request.'];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_FILES['sam3dbodyFile'])) {
        $file = $_FILES['sam3dbodyFile'];

        if ($file['error'] === UPLOAD_ERR_OK) {
            $fileName = basename($file['name']);
            $fileExtension = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));

            if ($fileExtension === 'sam3dbody') {
                if (!is_dir($targetDir) && !mkdir($targetDir, 0777, true) && !is_dir($targetDir)) {
                     $response['message'] = 'Failed to create target directory.';
                } elseif (!is_writable($targetDir)) {
                    $response['message'] = 'Target directory is not writable.';
                } else {
                    $targetPath = $targetDir . $fileName;
                    if (move_uploaded_file($file['tmp_name'], $targetPath)) {
                        $response = ['status' => 'success', 'message' => 'File uploaded successfully.', 'filename' => $fileName];
                    } else {
                        $response['message'] = 'Failed to move uploaded file.';
                    }
                }
            } else {
                $response['message'] = 'Invalid file type. Only .sam3dbody files are allowed.';
            }
        } else {
            $response['message'] = 'File upload error: ' . $file['error'];
        }
    } else {
        $response['message'] = 'No file uploaded or wrong field name.';
    }
}

echo json_encode($response);

?>
