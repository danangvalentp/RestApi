<?php
/**
 * Contoh Integrasi API Video Downloader dengan PHP
 * 
 * File ini menunjukkan cara mengintegrasikan Video Downloader API
 * ke dalam website PHP Anda.
 */

class VideoDownloaderAPI {
    private $baseUrl;
    
    public function __construct($baseUrl = 'http://localhost:5000') {
        $this->baseUrl = rtrim($baseUrl, '/');
    }
    
    /**
     * Make HTTP request to API
     */
    private function makeRequest($endpoint, $data = null, $method = 'GET') {
        $ch = curl_init();
        $url = $this->baseUrl . $endpoint;
        
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'Accept: application/json'
        ]);
        
        if ($method === 'POST' && $data) {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($response === false) {
            throw new Exception('Gagal terhubung ke API');
        }
        
        $result = json_decode($response, true);
        
        if ($httpCode >= 400) {
            $message = isset($result['message']) ? $result['message'] : 'Terjadi kesalahan';
            throw new Exception($message, $httpCode);
        }
        
        return $result;
    }
    
    /**
     * Check API health
     */
    public function checkHealth() {
        return $this->makeRequest('/api/health');
    }
    
    /**
     * Get supported platforms
     */
    public function getSupportedPlatforms() {
        return $this->makeRequest('/api/supported-platforms');
    }
    
    /**
     * Validate video URL
     */
    public function validateUrl($url) {
        return $this->makeRequest('/api/video/validate', ['url' => $url], 'POST');
    }
    
    /**
     * Get video information
     */
    public function getVideoInfo($url) {
        return $this->makeRequest('/api/video/info', ['url' => $url], 'POST');
    }
    
    /**
     * Get video download link
     */
    public function getDownloadLink($url, $quality = 'best') {
        return $this->makeRequest('/api/video/download', [
            'url' => $url,
            'quality' => $quality
        ], 'POST');
    }
    
    /**
     * Get rate limit status
     */
    public function getRateLimitStatus() {
        return $this->makeRequest('/api/rate-limit/status');
    }
}

// Contoh penggunaan
try {
    // Inisialisasi API client
    $api = new VideoDownloaderAPI('http://localhost:5000');
    
    // Handle form submission
    if ($_POST['action'] === 'download' && !empty($_POST['video_url'])) {
        $url = $_POST['video_url'];
        $quality = $_POST['quality'] ?? 'best';
        
        // Validasi URL terlebih dahulu
        $validation = $api->validateUrl($url);
        
        if (!$validation['valid']) {
            throw new Exception('URL tidak valid atau platform tidak didukung');
        }
        
        // Dapatkan informasi video
        $videoInfo = $api->getVideoInfo($url);
        
        // Dapatkan link download
        $downloadInfo = $api->getDownloadLink($url, $quality);
        
        $result = [
            'success' => true,
            'video_info' => $videoInfo['data'],
            'download_info' => $downloadInfo['data']
        ];
    }
    
} catch (Exception $e) {
    $result = [
        'success' => false,
        'error' => $e->getMessage()
    ];
}
?>

<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Downloader - PHP Integration</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white">
                        <h3 class="mb-0">
                            <i class="fas fa-video me-2"></i>
                            Video Downloader - PHP
                        </h3>
                    </div>
                    <div class="card-body">
                        
                        <?php if (isset($result) && !$result['success']): ?>
                            <div class="alert alert-danger">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                <?= htmlspecialchars($result['error']) ?>
                            </div>
                        <?php endif; ?>
                        
                        <?php if (isset($result) && $result['success']): ?>
                            <div class="alert alert-success">
                                <i class="fas fa-check-circle me-2"></i>
                                Video berhasil diproses!
                            </div>
                            
                            <div class="card mb-4">
                                <div class="row g-0">
                                    <div class="col-md-4">
                                        <img src="<?= htmlspecialchars($result['video_info']['thumbnail']) ?>" 
                                             class="img-fluid rounded-start h-100 object-fit-cover" 
                                             alt="Thumbnail">
                                    </div>
                                    <div class="col-md-8">
                                        <div class="card-body">
                                            <h5 class="card-title"><?= htmlspecialchars($result['video_info']['title']) ?></h5>
                                            <p class="card-text">
                                                <small class="text-muted">
                                                    <i class="fas fa-user me-1"></i>
                                                    <?= htmlspecialchars($result['video_info']['uploader']) ?>
                                                    <i class="fas fa-clock ms-3 me-1"></i>
                                                    <?= htmlspecialchars($result['video_info']['duration_string']) ?>
                                                </small>
                                            </p>
                                            <a href="<?= htmlspecialchars($result['download_info']['download_url']) ?>" 
                                               class="btn btn-success" target="_blank">
                                                <i class="fas fa-download me-2"></i>
                                                Download <?= strtoupper($result['download_info']['file_extension'] ?? 'VIDEO') ?>
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        <?php endif; ?>
                        
                        <form method="POST" action="">
                            <input type="hidden" name="action" value="download">
                            
                            <div class="mb-3">
                                <label for="video_url" class="form-label">
                                    <i class="fas fa-link me-1"></i>
                                    URL Video
                                </label>
                                <input type="url" 
                                       class="form-control" 
                                       id="video_url" 
                                       name="video_url" 
                                       placeholder="Masukkan URL video YouTube, TikTok, atau Instagram"
                                       value="<?= htmlspecialchars($_POST['video_url'] ?? '') ?>"
                                       required>
                            </div>
                            
                            <div class="mb-3">
                                <label for="quality" class="form-label">
                                    <i class="fas fa-cog me-1"></i>
                                    Kualitas Video
                                </label>
                                <select class="form-select" id="quality" name="quality">
                                    <option value="best" <?= ($_POST['quality'] ?? '') === 'best' ? 'selected' : '' ?>>Terbaik</option>
                                    <option value="720p" <?= ($_POST['quality'] ?? '') === '720p' ? 'selected' : '' ?>>HD 720p</option>
                                    <option value="480p" <?= ($_POST['quality'] ?? '') === '480p' ? 'selected' : '' ?>>SD 480p</option>
                                    <option value="360p" <?= ($_POST['quality'] ?? '') === '360p' ? 'selected' : '' ?>>SD 360p</option>
                                    <option value="240p" <?= ($_POST['quality'] ?? '') === '240p' ? 'selected' : '' ?>>240p</option>
                                </select>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-download me-2"></i>
                                    Download Video
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
                
                <!-- API Status -->
                <div class="card mt-4">
                    <div class="card-body">
                        <h6 class="card-title">
                            <i class="fas fa-info-circle me-2"></i>
                            Status API
                        </h6>
                        <?php 
                        try {
                            $health = $api->checkHealth();
                            echo '<span class="badge bg-success">API Online</span>';
                            echo '<small class="text-muted ms-2">Service: ' . htmlspecialchars($health['service']) . '</small>';
                        } catch (Exception $e) {
                            echo '<span class="badge bg-danger">API Offline</span>';
                            echo '<small class="text-muted ms-2">' . htmlspecialchars($e->getMessage()) . '</small>';
                        }
                        ?>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>