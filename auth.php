<?php
/**
 * Shared-token check for the GPU worker's write endpoints.
 *
 * The worker is a machine client (no browser, no login), so it sends
 * `X-Api-Token: <S3B_WORKER_TOKEN>`. The expected value comes from the
 * signcollect-lib env file (sc_env()) when /web/lib is installed, else from
 * the process environment (Apache SetEnv) - production has no /web/lib.
 * Unset token = every request refused (fail closed).
 */

function s3b_expected_token(): string {
    if (!function_exists('sc_env')) {
        foreach ([__DIR__ . '/../lib/db_config.php', '/web/lib/db_config.php'] as $lib) {
            if (is_file($lib)) { require_once $lib; break; }
        }
    }
    if (function_exists('sc_env')) {
        try {
            $v = (string)(sc_env()['S3B_WORKER_TOKEN'] ?? '');
            if ($v !== '') return $v;
        } catch (RuntimeException $e) {
            // no env file: fall through to getenv()
        }
    }
    return (string)getenv('S3B_WORKER_TOKEN');
}

function s3b_require_token(): void {
    $want = s3b_expected_token();
    $given = (string)($_SERVER['HTTP_X_API_TOKEN'] ?? '');
    if ($want === '') {
        error_log('s3b_server: S3B_WORKER_TOKEN is not set - ' . basename($_SERVER['SCRIPT_NAME'] ?? '') . ' refuses all requests');
    }
    if ($want === '' || $given === '' || !hash_equals($want, $given)) {
        http_response_code(401);
        header('Content-Type: application/json');
        echo json_encode(['success' => false, 'status' => 'error', 'message' => 'Invalid or missing X-Api-Token']);
        exit;
    }
}
