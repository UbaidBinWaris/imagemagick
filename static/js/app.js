class ImageProcessor {
    constructor() {
        this.BACKEND_URL = window.location.protocol + '//' + window.location.host;
        this.API_KEY = this.getStoredApiKey();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkHealth();
        this.toggleAdvancedOptions(); // Initialize text group visibility
        this.setupApiKeyInterface();
    }

    getStoredApiKey() {
        return localStorage.getItem('imagemagick_api_key') || '';
    }

    setApiKey(apiKey) {
        this.API_KEY = apiKey;
        if (apiKey) {
            localStorage.setItem('imagemagick_api_key', apiKey);
        } else {
            localStorage.removeItem('imagemagick_api_key');
        }
        this.updateApiKeyDisplay();
    }

    setupApiKeyInterface() {
        // Add API key input section if it doesn't exist
        const container = document.querySelector('.container');
        const header = container.querySelector('.header');
        
        if (!document.getElementById('apiKeySection')) {
            const apiKeySection = document.createElement('div');
            apiKeySection.id = 'apiKeySection';
            apiKeySection.className = 'api-key-section';
            apiKeySection.innerHTML = `
                <div class="api-key-controls" style="display: none;">
                    <h3>🔐 API Authentication</h3>
                    <div class="api-key-input-group">
                        <input type="password" id="apiKeyInput" placeholder="Enter your API key..." />
                        <button type="button" id="saveApiKeyBtn" class="btn btn-primary">Save</button>
                        <button type="button" id="clearApiKeyBtn" class="btn btn-secondary">Clear</button>
                    </div>
                    <div class="api-key-status" id="apiKeyStatus">
                        <span id="apiKeyStatusText">No API key configured</span>
                    </div>
                </div>
            `;
            
            header.insertAdjacentElement('afterend', apiKeySection);
        }
        
        this.updateApiKeyDisplay();
    }

    updateApiKeyDisplay() {
        const apiKeySection = document.getElementById('apiKeySection');
        const apiKeyControls = apiKeySection?.querySelector('.api-key-controls');
        const apiKeyInput = document.getElementById('apiKeyInput');
        const apiKeyStatusText = document.getElementById('apiKeyStatusText');
        
        if (this.API_KEY) {
            if (apiKeyInput) apiKeyInput.value = this.API_KEY;
            if (apiKeyStatusText) {
                apiKeyStatusText.textContent = `API key configured (${this.API_KEY.substring(0, 8)}...)`;
                apiKeyStatusText.className = 'api-key-configured';
            }
        } else {
            if (apiKeyInput) apiKeyInput.value = '';
            if (apiKeyStatusText) {
                apiKeyStatusText.textContent = 'No API key configured';
                apiKeyStatusText.className = 'api-key-missing';
            }
        }
    }

    showApiKeyControls() {
        const apiKeyControls = document.querySelector('.api-key-controls');
        if (apiKeyControls) {
            apiKeyControls.style.display = 'block';
        }
    }

    hideApiKeyControls() {
        const apiKeyControls = document.querySelector('.api-key-controls');
        if (apiKeyControls) {
            apiKeyControls.style.display = 'none';
        }
    }

    setupEventListeners() {
        // File input change
        document.getElementById('imageInput').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.displayOriginalImage(e.target.files[0]);
            }
        });

        // Action change
        document.getElementById('action').addEventListener('change', () => {
            this.toggleAdvancedOptions();
        });

        // Process button
        document.getElementById('processBtn').addEventListener('click', () => {
            this.processImage();
        });

        // Reset button
        document.getElementById('resetBtn').addEventListener('click', () => {
            this.resetAll();
        });

        // Advanced options toggle
        document.querySelector('.advanced-options h3').addEventListener('click', () => {
            this.toggleAdvanced();
        });

        // API key controls
        document.addEventListener('click', (e) => {
            if (e.target.id === 'saveApiKeyBtn') {
                const apiKey = document.getElementById('apiKeyInput').value.trim();
                this.setApiKey(apiKey);
                this.showStatus('API key saved');
            } else if (e.target.id === 'clearApiKeyBtn') {
                this.setApiKey('');
                this.showStatus('API key cleared');
            }
        });
    }

    getHeaders() {
        const headers = {};
        if (this.API_KEY) {
            headers['X-API-Key'] = this.API_KEY;
        }
        return headers;
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.BACKEND_URL}/health`, {
                headers: this.getHeaders()
            });
            const data = await response.json();
            
            const healthStatus = document.getElementById('healthStatus');
            const installInstructions = document.getElementById('installInstructions');
            const processBtn = document.getElementById('processBtn');
            
            if (response.status === 401) {
                // API key required but not provided or invalid
                healthStatus.textContent = '🔐 Auth Required';
                healthStatus.className = 'health-status warning';
                this.showApiKeyControls();
                processBtn.disabled = true;
                this.showError('API key authentication required. Please configure your API key.');
                return;
            }
            
            if (data.status === 'healthy' && data.imagemagick_installed) {
                healthStatus.textContent = '✅ Ready';
                healthStatus.className = 'health-status healthy';
                installInstructions.style.display = 'none';
                processBtn.disabled = false;
                
                // Show auth status if API auth is enabled
                if (data.api_auth_enabled) {
                    this.showApiKeyControls();
                    if (data.authenticated_as) {
                        this.showStatus(`Authenticated as: ${data.authenticated_as}`);
                    }
                } else {
                    this.hideApiKeyControls();
                }
            } else if (data.status === 'healthy' && !data.imagemagick_installed) {
                healthStatus.textContent = '⚠️ ImageMagick Missing';
                healthStatus.className = 'health-status warning';
                installInstructions.style.display = 'block';
                processBtn.disabled = true;
                this.showError('ImageMagick is not installed. Please see installation instructions above.');
            } else {
                healthStatus.textContent = '❌ Backend Issues';
                healthStatus.className = 'health-status unhealthy';
                installInstructions.style.display = 'none';
                processBtn.disabled = true;
                this.showError('Backend server is not running.');
            }
        } catch (error) {
            const healthStatus = document.getElementById('healthStatus');
            const processBtn = document.getElementById('processBtn');
            healthStatus.textContent = '🔌 Disconnected';
            healthStatus.className = 'health-status unhealthy';
            processBtn.disabled = true;
            this.showError('Cannot connect to backend. Please start the Flask server.');
        }
    }

    displayOriginalImage(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const originalImage = document.getElementById('originalImage');
            const originalPlaceholder = document.getElementById('originalPlaceholder');
            originalImage.src = e.target.result;
            originalImage.style.display = 'block';
            originalPlaceholder.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    toggleAdvancedOptions() {
        const action = document.getElementById('action').value;
        const textGroup = document.getElementById('textGroup');
        
        if (action === 'text') {
            textGroup.style.display = 'block';
        } else {
            textGroup.style.display = 'none';
        }
    }

    toggleAdvanced() {
        const advancedOptions = document.getElementById('advancedOptions');
        advancedOptions.classList.toggle('expanded');
    }

    showStatus(message) {
        const statusEl = document.getElementById('statusMessage');
        const errorEl = document.getElementById('errorMessage');
        
        errorEl.style.display = 'none';
        statusEl.textContent = message;
        statusEl.style.display = 'block';
        
        setTimeout(() => {
            statusEl.style.display = 'none';
        }, 3000);
    }

    showError(message) {
        const statusEl = document.getElementById('statusMessage');
        const errorEl = document.getElementById('errorMessage');
        
        statusEl.style.display = 'none';
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }

    hideMessages() {
        document.getElementById('statusMessage').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'none';
    }

    validateInputs() {
        const fileInput = document.getElementById('imageInput');
        const action = document.getElementById('action').value;
        const text = document.getElementById('textInput').value;

        if (!fileInput.files.length) {
            this.showError('Please upload an image first.');
            return false;
        }

        if (action === 'text' && !text.trim()) {
            this.showError('Please enter text to add to the image.');
            return false;
        }

        return true;
    }

    collectFormData() {
        const formData = new FormData();
        const fileInput = document.getElementById('imageInput');
        
        formData.append('image', fileInput.files[0]);
        formData.append('action', document.getElementById('action').value);
        formData.append('text', document.getElementById('textInput').value);
        formData.append('resize_percentage', document.getElementById('resizePercentage').value);
        formData.append('rotation_angle', document.getElementById('rotationAngle').value);
        formData.append('text_size', document.getElementById('textSize').value);
        formData.append('text_color', document.getElementById('textColor').value);
        formData.append('text_font', document.getElementById('textFont').value);
        formData.append('text_position', document.getElementById('textPosition').value);
        formData.append('blur_radius', document.getElementById('blurRadius').value);

        return formData;
    }

    async processImage() {
        if (!this.validateInputs()) {
            return;
        }

        const loadingIndicator = document.getElementById('loadingIndicator');
        loadingIndicator.style.display = 'block';
        this.hideMessages();

        try {
            const formData = this.collectFormData();
            
            const response = await fetch(`${this.BACKEND_URL}/process`, {
                method: 'POST',
                body: formData,
                headers: this.getHeaders()
            });

            if (response.status === 401) {
                throw new Error('Authentication required. Please check your API key.');
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Processing failed');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            const outputImage = document.getElementById('outputImage');
            const processedPlaceholder = document.getElementById('processedPlaceholder');
            
            outputImage.src = url;
            outputImage.style.display = 'block';
            processedPlaceholder.style.display = 'none';
            
            this.showStatus('✅ Image processed successfully!');
            
        } catch (error) {
            console.error('Error:', error);
            this.showError(error.message || 'Failed to process image. Please try again.');
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }

    resetAll() {
        // Reset form values
        document.getElementById('imageInput').value = '';
        document.getElementById('action').selectedIndex = 3; // Add Text Overlay option
        document.getElementById('textInput').value = '';
        document.getElementById('resizePercentage').value = '50';
        document.getElementById('rotationAngle').value = '90';
        document.getElementById('textSize').value = '120';
        document.getElementById('textColor').selectedIndex = 1; // Black option
        document.getElementById('textFont').selectedIndex = 0; // Arial option
        document.getElementById('textPosition').selectedIndex = 2; // Center option
        document.getElementById('blurRadius').value = '0x1';

        // Reset image displays
        document.getElementById('originalImage').style.display = 'none';
        document.getElementById('outputImage').style.display = 'none';
        document.getElementById('originalPlaceholder').style.display = 'block';
        document.getElementById('processedPlaceholder').style.display = 'block';

        // Reset text group visibility
        document.getElementById('textGroup').style.display = 'block'; // Show text group for default action

        // Clear messages
        this.hideMessages();
        this.showStatus('🔄 All settings reset');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ImageProcessor();
});
