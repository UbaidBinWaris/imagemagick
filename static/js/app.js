class ImageProcessor {
    constructor() {
        this.BACKEND_URL = window.location.protocol + '//' + window.location.host;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkHealth();
        this.toggleAdvancedOptions(); // Initialize text group visibility
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
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.BACKEND_URL}/health`);
            const data = await response.json();
            
            const healthStatus = document.getElementById('healthStatus');
            const installInstructions = document.getElementById('installInstructions');
            const processBtn = document.getElementById('processBtn');
            
            if (data.status === 'healthy' && data.imagemagick_installed) {
                healthStatus.textContent = '✅ Ready';
                healthStatus.className = 'health-status healthy';
                installInstructions.style.display = 'none';
                processBtn.disabled = false;
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
            });

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
