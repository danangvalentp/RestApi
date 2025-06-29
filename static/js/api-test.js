document.addEventListener('DOMContentLoaded', function() {
    const getInfoBtn = document.getElementById('getInfoBtn');
    const getDownloadBtn = document.getElementById('getDownloadBtn');
    const responseArea = document.getElementById('responseArea');
    const videoUrlInput = document.getElementById('videoUrl');
    const qualitySelect = document.getElementById('quality');

    function showResponse(response, isError = false) {
        responseArea.innerHTML = `<pre>${JSON.stringify(response, null, 2)}</pre>`;
        if (isError) {
            responseArea.classList.add('text-danger');
        } else {
            responseArea.classList.remove('text-danger');
        }
    }

    function showLoading() {
        responseArea.innerHTML = '<div class="d-flex align-items-center"><div class="spinner-border spinner-border-sm me-2" role="status"></div>Loading...</div>';
        responseArea.classList.remove('text-danger');
    }

    function validateUrl() {
        const url = videoUrlInput.value.trim();
        if (!url) {
            showResponse({ error: 'Please enter a video URL' }, true);
            return false;
        }

        const supportedDomains = [
            'youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com',
            'tiktok.com', 'www.tiktok.com', 'vm.tiktok.com',
            'instagram.com', 'www.instagram.com'
        ];

        try {
            const urlObj = new URL(url);
            const domain = urlObj.hostname.toLowerCase();
            const isSupported = supportedDomains.some(d => domain.includes(d));
            
            if (!isSupported) {
                showResponse({ 
                    error: 'Unsupported platform', 
                    message: 'Please enter a URL from YouTube, TikTok, or Instagram' 
                }, true);
                return false;
            }
        } catch (e) {
            showResponse({ 
                error: 'Invalid URL', 
                message: 'Please enter a valid URL' 
            }, true);
            return false;
        }

        return true;
    }

    async function makeRequest(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (!response.ok) {
                showResponse(result, true);
            } else {
                showResponse(result);
            }
        } catch (error) {
            showResponse({ 
                error: 'Network error', 
                message: 'Failed to connect to the API. Please try again.' 
            }, true);
        }
    }

    getInfoBtn.addEventListener('click', async function() {
        if (!validateUrl()) return;

        const url = videoUrlInput.value.trim();
        
        // Disable buttons and show loading
        getInfoBtn.disabled = true;
        getDownloadBtn.disabled = true;
        getInfoBtn.classList.add('loading');
        showLoading();

        await makeRequest('/api/video/info', { url });

        // Re-enable buttons
        getInfoBtn.disabled = false;
        getDownloadBtn.disabled = false;
        getInfoBtn.classList.remove('loading');
    });

    getDownloadBtn.addEventListener('click', async function() {
        if (!validateUrl()) return;

        const url = videoUrlInput.value.trim();
        const quality = qualitySelect.value;
        
        // Disable buttons and show loading
        getInfoBtn.disabled = true;
        getDownloadBtn.disabled = true;
        getDownloadBtn.classList.add('loading');
        showLoading();

        await makeRequest('/api/video/download', { url, quality });

        // Re-enable buttons
        getInfoBtn.disabled = false;
        getDownloadBtn.disabled = false;
        getDownloadBtn.classList.remove('loading');
    });

    // Add enter key support for the URL input
    videoUrlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            getInfoBtn.click();
        }
    });

    // Add some example URLs for easy testing
    const exampleUrls = [
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'https://youtu.be/dQw4w9WgXcQ'
    ];

    // Add placeholder with rotating examples
    let currentExample = 0;
    setInterval(() => {
        if (!videoUrlInput.value) {
            videoUrlInput.placeholder = `Example: ${exampleUrls[currentExample]}`;
            currentExample = (currentExample + 1) % exampleUrls.length;
        }
    }, 3000);
});
