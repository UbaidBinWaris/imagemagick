// Global variables
let processedImageData = null;
const API_BASE_URL = '/api';
const API_KEY = '{{ api_key }}'; // This will be templated from Flask

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    checkHealth();
    setupEventListeners();
});

function setupEventListeners() {
    // File input change
    document.getElementById('imageInput').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            showOriginalImage(e.target.files[0]);
        }
    });

    // Action change
    document.getElementById('action').addEventListener('change', toggleAdvancedOptions);
}

function checkHealth() {
    const healthStatus = document.getElementById('healthStatus');
    const installInstructions = document.getElementById('installInstructions');
    
    healthStatus.textContent = 'Checking...';
    healthStatus.className = 'health-status warning';
    
    fetch(`${API_BASE_URL}/health`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'healthy' && data.imagemagick_installed) {
                healthStatus.textContent = 'Backend Healthy';
                healthStatus.className = 'health-status healthy';
                installInstructions.style.display = 'none';
            } else {
                healthStatus.textContent = 'Backend Issues';
                healthStatus.className = 'health-status warning';
                if (!data.imagemagick_installed) {
                    installInstructions.style.display = 'block';
                }
            }
        })
        .catch(error => {
            console.error('Health check failed:', error);
            healthStatus.textContent = 'Backend server is not running';
            healthStatus.className = 'health-status unhealthy';
            installInstructions.style.display = 'block';
        });
}

function showOriginalImage(file) {
    const container = document.getElementById('originalImageContainer');
    const reader = new FileReader();
    
    reader.onload = function(e) {
        container.innerHTML = `<img src="${e.target.result}" alt="Original Image">`;
    };
    
    reader.readAsDataURL(file);
}

function toggleAdvanced() {
    const advancedOptions = document.getElementById('advancedOptions');
    advancedOptions.classList.toggle('expanded');
}

function toggleAdvancedOptions() {
    const action = document.getElementById('action').value;
    const textGroup = document.getElementById('textGroup');
    
    // Show/hide text input based on action
    if (action === 'text') {
        textGroup.style.display = 'block';
    } else {
        textGroup.style.display = 'none';
    }
}

function showMessage(message, isError = false) {
    const messageEl = document.getElementById(isError ? 'errorMessage' : 'statusMessage');
    const otherEl = document.getElementById(isError ? 'statusMessage' : 'errorMessage');
    
    messageEl.textContent = message;
    messageEl.style.display = 'block';
    otherEl.style.display = 'none';
    
    // Hide message after 5 seconds
    setTimeout(() => {
        messageEl.style.display = 'none';
    }, 5000);
}

function showLoading(show = true) {
    const button = document.querySelector('.btn-primary');
    
    if (show) {
        button.disabled = true;
        button.innerHTML = '<div class="spinner"></div> Processing...';
    } else {
        button.disabled = false;
        button.innerHTML = '🚀 Process Image';
    }
}

async function processImage() {
    const fileInput = document.getElementById('imageInput');
    const action = document.getElementById('action').value;
    
    // Validate inputs
    if (!fileInput.files || fileInput.files.length === 0) {
        showMessage('Please select an image file first!', true);
        return;
    }
    
    if (action === 'text' && !document.getElementById('textInput').value.trim()) {
        showMessage('Please enter text for the text overlay action!', true);
        return;
    }
    
    const file = fileInput.files[0];
    
    // Check file size (16MB limit)
    if (file.size > 16 * 1024 * 1024) {
        showMessage('File size too large. Maximum size is 16MB.', true);
        return;
    }
    
    // Prepare form data
    const formData = new FormData();
    formData.append('image', file);
    formData.append('action', action);
    
    // Add parameters based on action
    switch(action) {
        case 'resize':
            formData.append('resize_percentage', document.getElementById('resizePercentage').value);
            break;
        case 'rotate':
            formData.append('rotation_angle', document.getElementById('rotationAngle').value);
            break;
        case 'text':
            formData.append('text', document.getElementById('textInput').value);
            formData.append('text_size', document.getElementById('textSize').value);
            formData.append('text_color', document.getElementById('textColor').value);
            formData.append('text_font', document.getElementById('textFont').value);
            formData.append('text_position', document.getElementById('textPosition').value);
            break;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/process`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Display processed image
            displayProcessedImage(result.data);
            showMessage(`Image processed successfully! Processing time: ${result.data.processing_time_seconds}s`);
            
            // Show results section
            document.getElementById('resultsSection').style.display = 'grid';
            
        } else {
            showMessage(result.message || 'Processing failed', true);
        }
        
    } catch (error) {
        console.error('Processing error:', error);
        showMessage('Failed to process image. Please check the console for details.', true);
    } finally {
        showLoading(false);
    }
}

function displayProcessedImage(data) {
    const container = document.getElementById('processedImageContainer');
    const downloadSection = document.getElementById('downloadSection');
    
    // Store processed image data
    processedImageData = data;
    
    // Create image element
    const img = document.createElement('img');
    img.src = `data:image/${data.format};base64,${data.image}`;
    img.alt = 'Processed Image';
    
    // Create info element
    const info = document.createElement('div');
    info.style.marginTop = '10px';
    info.style.fontSize = '12px';
    info.style.color = '#666';
    info.innerHTML = `
        <strong>Action:</strong> ${data.action}<br>
        <strong>Size:</strong> ${(data.size_bytes / 1024).toFixed(1)} KB<br>
        <strong>Format:</strong> ${data.format.toUpperCase()}<br>
        <strong>Time:</strong> ${data.processing_time_seconds}s
    `;
    
    container.innerHTML = '';
    container.appendChild(img);
    container.appendChild(info);
    
    // Show download section
    downloadSection.style.display = 'block';
}

function downloadImage() {
    if (!processedImageData) {
        showMessage('No processed image to download', true);
        return;
    }
    
    // Convert base64 to blob
    const byteCharacters = atob(processedImageData.image);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: `image/${processedImageData.format}` });
    
    // Create download link
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `processed_image_${Date.now()}.${processedImageData.format}`;
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
    
    showMessage('Image downloaded successfully!');
}

function resetForm() {
    // Reset file input
    document.getElementById('imageInput').value = '';
    
    // Reset all form controls to default values
    document.getElementById('action').value = 'text';
    document.getElementById('textInput').value = '';
    document.getElementById('resizePercentage').value = '50';
    document.getElementById('rotationAngle').value = '90';
    document.getElementById('textSize').value = '120';
    document.getElementById('textColor').value = 'black';
    document.getElementById('textFont').value = 'Arial';
    document.getElementById('textPosition').value = 'Center';
    
    // Clear images and hide results
    document.getElementById('originalImageContainer').innerHTML = '';
    document.getElementById('processedImageContainer').innerHTML = '';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('downloadSection').style.display = 'none';
    
    // Hide messages
    document.getElementById('statusMessage').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';
    
    // Reset advanced options
    document.getElementById('advancedOptions').classList.remove('expanded');
    
    // Reset text group visibility
    toggleAdvancedOptions();
    
    showMessage('Form reset successfully!');
}
