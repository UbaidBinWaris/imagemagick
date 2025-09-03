// Global variables
const BACKEND_URL = window.location.protocol + '//' + window.location.host;
let selectedDefaultImage = null;
let currentTab = 'upload';

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    checkHealth();
    setupEventListeners();
    toggleAdvancedOptions();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('imageInput').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            displayOriginalImage(e.target.files[0]);
        }
    });
}

// Check backend health and ImageMagick installation
function checkHealth() {
    fetch(`${BACKEND_URL}/health`)
        .then(response => response.json())
        .then(data => {
            const healthStatus = document.getElementById('healthStatus');
            const installInstructions = document.getElementById('installInstructions');
            const processBtn = document.getElementById('processBtn');
            const processDefaultBtn = document.getElementById('processDefaultBtn');
            
            if (data.status === 'healthy' && data.imagemagick_installed) {
                healthStatus.textContent = '✅ Ready';
                healthStatus.className = 'health-status healthy';
                installInstructions.style.display = 'none';
                processBtn.disabled = false;
                processDefaultBtn.disabled = false;
            } else if (data.status === 'healthy' && !data.imagemagick_installed) {
                healthStatus.textContent = '⚠️ ImageMagick Missing';
                healthStatus.className = 'health-status warning';
                installInstructions.style.display = 'block';
                processBtn.disabled = true;
                processDefaultBtn.disabled = true;
                showError('ImageMagick is not installed. Please see installation instructions above.');
            } else {
                healthStatus.textContent = '❌ Backend Issues';
                healthStatus.className = 'health-status unhealthy';
                installInstructions.style.display = 'none';
                processBtn.disabled = true;
                processDefaultBtn.disabled = true;
                showError('Backend server is not running.');
            }
        })
        .catch(error => {
            console.error('Health check failed:', error);
            const healthStatus = document.getElementById('healthStatus');
            healthStatus.textContent = '❌ Connection Failed';
            healthStatus.className = 'health-status unhealthy';
            showError('Cannot connect to backend server.');
        });
}

// Tab switching functionality
function switchTab(tab) {
    const uploadTab = document.querySelector('.tab-button:first-child');
    const defaultTab = document.querySelector('.tab-button:last-child');
    const uploadSection = document.getElementById('uploadSection');
    const defaultSection = document.getElementById('defaultSection');
    const processBtn = document.getElementById('processBtn');
    const processDefaultBtn = document.getElementById('processDefaultBtn');

    currentTab = tab;

    if (tab === 'default') {
        uploadTab.classList.remove('active');
        defaultTab.classList.add('active');
        uploadSection.style.display = 'none';
        defaultSection.style.display = 'block';
        processBtn.style.display = 'none';
        processDefaultBtn.style.display = 'inline-block';
        loadDefaultImages();
    } else {
        uploadTab.classList.add('active');
        defaultTab.classList.remove('active');
        uploadSection.style.display = 'block';
        defaultSection.style.display = 'none';
        processBtn.style.display = 'inline-block';
        processDefaultBtn.style.display = 'none';
        clearDefaultImageSelection();
    }
}

// Load default images from server
function loadDefaultImages() {
    fetch(`${BACKEND_URL}/default-images`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayDefaultImages(data.images);
            } else {
                showError('Failed to load default images.');
            }
        })
        .catch(error => {
            console.error('Error loading default images:', error);
            showError('Failed to load default images.');
        });
}

// Display default images in grid
function displayDefaultImages(images) {
    const grid = document.getElementById('defaultImagesGrid');
    grid.innerHTML = '';

    if (images.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: #666;">No default images available.</p>';
        return;
    }

    images.forEach(image => {
        const imageItem = document.createElement('div');
        imageItem.className = 'default-image-item';
        imageItem.onclick = () => selectDefaultImage(image, imageItem);
        
        imageItem.innerHTML = `
            <img src="${BACKEND_URL}/default-images/${image}" alt="${image}" />
            <div class="image-name">${image}</div>
        `;
        
        grid.appendChild(imageItem);
    });
}

// Select a default image
function selectDefaultImage(imageName, element) {
    // Clear previous selection
    document.querySelectorAll('.default-image-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Select new image
    element.classList.add('selected');
    selectedDefaultImage = imageName;
    
    // Display selected image in preview
    const originalImage = document.getElementById('originalImage');
    const originalPlaceholder = document.getElementById('originalPlaceholder');
    originalImage.src = `${BACKEND_URL}/default-images/${imageName}`;
    originalImage.style.display = 'block';
    originalPlaceholder.style.display = 'none';
}

// Clear default image selection
function clearDefaultImageSelection() {
    selectedDefaultImage = null;
    document.querySelectorAll('.default-image-item').forEach(item => {
        item.classList.remove('selected');
    });
}

// Display original uploaded image
function displayOriginalImage(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const originalImage = document.getElementById('originalImage');
        const originalPlaceholder = document.getElementById('originalPlaceholder');
        originalImage.src = e.target.result;
        originalImage.style.display = 'block';
        originalPlaceholder.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

// Toggle advanced options
function toggleAdvanced() {
    const advancedOptions = document.getElementById('advancedOptions');
    advancedOptions.classList.toggle('expanded');
}

// Toggle advanced options based on selected action
function toggleAdvancedOptions() {
    const action = document.getElementById('action').value;
    const textGroup = document.getElementById('textGroup');
    
    if (action === 'text') {
        textGroup.style.display = 'block';
    } else {
        textGroup.style.display = 'none';
    }
}

// Process uploaded image
function processImage() {
    const fileInput = document.getElementById('imageInput');
    const action = document.getElementById('action').value;
    
    if (!fileInput.files[0]) {
        showError('Please select an image file first.');
        return;
    }

    if (action === 'text') {
        const text = document.getElementById('textInput').value.trim();
        if (!text) {
            showError('Please enter text to add to the image.');
            return;
        }
    }

    // Show loading indicator
    document.getElementById('loadingIndicator').style.display = 'block';
    hideMessages();

    // Prepare form data
    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    formData.append('action', action);
    formData.append('text', document.getElementById('textInput').value);
    formData.append('resize_percentage', document.getElementById('resizePercentage').value);
    formData.append('rotation_angle', document.getElementById('rotationAngle').value);
    formData.append('text_size', document.getElementById('textSize').value);
    formData.append('text_color', document.getElementById('textColor').value);
    formData.append('text_font', document.getElementById('textFont').value);
    formData.append('text_position', document.getElementById('textPosition').value);
    formData.append('blur_radius', document.getElementById('blurRadius').value);

    // Send request
    fetch(`${BACKEND_URL}/process`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.blob();
    })
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const outputImage = document.getElementById('outputImage');
        const processedPlaceholder = document.getElementById('processedPlaceholder');
        outputImage.src = url;
        outputImage.style.display = 'block';
        processedPlaceholder.style.display = 'none';
        showStatus('✅ Image processed successfully!');
    })
    .catch(error => {
        console.error('Error:', error);
        showError(error.error || 'Failed to process image. Please try again.');
    })
    .finally(() => {
        document.getElementById('loadingIndicator').style.display = 'none';
    });
}

// Process default image with text
function processDefaultImage() {
    if (!selectedDefaultImage) {
        showError('Please select a default image first.');
        return;
    }

    const text = document.getElementById('defaultText').value.trim();
    if (!text) {
        showError('Please enter text to add to the image.');
        return;
    }

    // Show loading indicator
    document.getElementById('loadingIndicator').style.display = 'block';
    hideMessages();

    // Get text styling options from the advanced settings
    const requestData = {
        default_image: selectedDefaultImage,
        text: text,
        text_size: document.getElementById('textSize').value,
        text_color: document.getElementById('textColor').value,
        text_font: document.getElementById('textFont').value,
        text_position: document.getElementById('textPosition').value
    };

    fetch(`${BACKEND_URL}/process-default`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.blob();
    })
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const outputImage = document.getElementById('outputImage');
        const processedPlaceholder = document.getElementById('processedPlaceholder');
        outputImage.src = url;
        outputImage.style.display = 'block';
        processedPlaceholder.style.display = 'none';
        showStatus('✅ Text added to default image successfully!');
    })
    .catch(error => {
        console.error('Error:', error);
        showError(error.error || 'Failed to process default image. Please try again.');
    })
    .finally(() => {
        document.getElementById('loadingIndicator').style.display = 'none';
    });
}

// Reset all form fields and images
function resetAll() {
    document.getElementById('imageInput').value = '';
    document.getElementById('action').selectedIndex = 3; // Add Text Overlay option
    document.getElementById('textInput').value = '';
    document.getElementById('defaultText').value = '';
    document.getElementById('resizePercentage').value = '50';
    document.getElementById('rotationAngle').value = '90';
    document.getElementById('textSize').value = '120';
    document.getElementById('textColor').selectedIndex = 1; // Black option
    document.getElementById('textFont').selectedIndex = 0; // Arial option
    document.getElementById('textPosition').selectedIndex = 2; // Center option
    document.getElementById('blurRadius').value = '0x1';
    document.getElementById('originalImage').style.display = 'none';
    document.getElementById('outputImage').style.display = 'none';
    document.getElementById('originalPlaceholder').style.display = 'block';
    document.getElementById('processedPlaceholder').style.display = 'block';
    document.getElementById('textGroup').style.display = 'block'; // Show text group for default action
    clearDefaultImageSelection();
    switchTab('upload'); // Switch back to upload tab
    hideMessages();
    showStatus('🔄 All settings reset');
}

// Show status message
function showStatus(message) {
    const statusMessage = document.getElementById('statusMessage');
    statusMessage.textContent = message;
    statusMessage.style.display = 'block';
    setTimeout(() => {
        statusMessage.style.display = 'none';
    }, 3000);
}

// Show error message
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

// Hide all messages
function hideMessages() {
    document.getElementById('statusMessage').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';
}
