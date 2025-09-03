// Global variables
let processedImageData = null;
let selectedImageFromServer = null;
const API_BASE_URL = '/api';
const API_KEY = '{{ api_key }}'; // This will be templated from Flask

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    checkHealth();
    setupEventListeners();
    loadAvailableImages(); // Load images on startup
});

function setupEventListeners() {
    // File input change
    document.getElementById('imageInput').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            showOriginalImage(e.target.files[0]);
            selectedImageFromServer = null; // Clear server selection when uploading new file
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
    
    // Validate inputs - check for either uploaded file or selected server image
    const hasUploadedFile = fileInput.files && fileInput.files.length > 0;
    const hasSelectedServerImage = selectedImageFromServer;
    
    if (!hasUploadedFile && !hasSelectedServerImage) {
        showMessage('Please select an image file or choose an image from the server!', true);
        return;
    }
    
    if (action === 'text' && !document.getElementById('textInput').value.trim()) {
        showMessage('Please enter text for the text overlay action!', true);
        return;
    }
    
    // Prepare form data
    const formData = new FormData();
    
    if (hasUploadedFile) {
        const file = fileInput.files[0];
        
        // Check file size (16MB limit)
        if (file.size > 16 * 1024 * 1024) {
            showMessage('File size too large. Maximum size is 16MB.', true);
            return;
        }
        
        formData.append('image', file);
    } else if (hasSelectedServerImage) {
        formData.append('existing_image', selectedImageFromServer);
    }
    
    formData.append('action', action);
    formData.append('show_link', 'true'); // Always show links for web interface
    
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
        // Use the enhanced webhook endpoint that supports both upload and existing images
        const response = await fetch('/webhook/enhanced-upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        console.log('Webhook response:', result); // Debug log
        
        if (result.success) {
            // The webhook returns the image data in result.data
            const imageData = result.data || result.image_data;
            if (imageData) {
                // Display processed image
                displayProcessedImage(imageData);
                
                // Show success message
                const processingTime = imageData.processing_time_seconds || 'N/A';
                showMessage(`Image processed successfully! Processing time: ${processingTime}s`);
                
                // Show results section
                document.getElementById('resultsSection').style.display = 'grid';
                
                // Enable export button
                document.getElementById('exportButton').disabled = false;
                document.getElementById('exportButton').parentElement.querySelector('p').textContent = 'Ready to export processed image';
            } else {
                showMessage('Error: No image data received from server', true);
                console.error('Missing data/image_data in response:', result);
            }
            
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
    
    console.log('displayProcessedImage received data:', data); // Debug log
    
    // Handle undefined data
    if (!data) {
        showMessage('Error: No image data received from server', true);
        return;
    }
    
    // Store processed image data
    processedImageData = data;
    
    // The webhook returns base64_data field, try both field names for compatibility
    const base64Data = data.base64_data || data.processed_image;
    if (!base64Data) {
        showMessage('Error: No base64_data or processed_image found in response', true);
        console.error('Missing base64_data/processed_image in:', data);
        return;
    }
    
    // Create image element
    const img = document.createElement('img');
    img.src = `data:image/png;base64,${base64Data}`;
    img.alt = 'Processed Image';
    
    // Create info element with data from the response
    const info = document.createElement('div');
    info.style.marginTop = '10px';
    info.style.fontSize = '12px';
    info.style.color = '#666';
    info.innerHTML = `
        <strong>Source:</strong> ${data.source || 'upload'}<br>
        <strong>Time:</strong> ${data.processing_time_seconds || 'N/A'}s<br>
        <strong>Resize:</strong> ${data.resize_percentage || 'N/A'}<br>
        <strong>Timestamp:</strong> ${data.upload_timestamp || 'N/A'}
    `;
    
    container.innerHTML = '';
    container.appendChild(img);
    container.appendChild(info);
    
    // Show download section
    downloadSection.style.display = 'block';
    
    // Update processed image data format for compatibility with download function
    processedImageData.image = base64Data;
    processedImageData.format = 'png'; // Default format from enhanced webhook
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
    
    // Clear server image selection
    selectedImageFromServer = null;
    clearServerImageSelection();
    
    // Reset all form controls to default values
    document.getElementById('action').value = 'text';
    document.getElementById('textInput').value = '';
    document.getElementById('resizePercentage').value = '50';
    document.getElementById('rotationAngle').value = '90';
    document.getElementById('textSize').value = '120';
    document.getElementById('textColor').value = 'black';
    document.getElementById('textFont').value = 'Arial';
    document.getElementById('textPosition').value = 'Center';
    
    // Reset export controls
    document.getElementById('exportFormat').value = 'png';
    document.getElementById('exportQuality').value = '90';
    
    // Clear images and hide results
    document.getElementById('originalImageContainer').innerHTML = '';
    document.getElementById('processedImageContainer').innerHTML = '';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('downloadSection').style.display = 'none';
    
    // Disable export button
    document.getElementById('exportButton').disabled = true;
    document.getElementById('exportButton').parentElement.querySelector('p').textContent = 'Process an image first to enable export';
    
    // Hide messages
    document.getElementById('statusMessage').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';
    
    // Reset advanced options
    document.getElementById('advancedOptions').classList.remove('expanded');
    
    // Reset text group visibility
    toggleAdvancedOptions();
    
    // Reset to upload tab
    switchTabProgrammatically('upload');
    
    // Clear processed image data
    processedImageData = null;
    
    showMessage('Form reset successfully!');
}

function switchTabProgrammatically(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName + 'Tab').classList.add('active');
    
    // Add active class to corresponding button
    document.querySelectorAll('.tab-button').forEach(button => {
        if (button.textContent.includes(tabName === 'upload' ? 'Upload New' : 
                                           tabName === 'import' ? 'Import Existing' : 
                                           'Export Images')) {
            button.classList.add('active');
        }
    });
}

// Tab switching functionality
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName + 'Tab').classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // Clear selections when switching tabs
    if (tabName === 'upload') {
        selectedImageFromServer = null;
        clearServerImageSelection();
    } else if (tabName === 'import') {
        document.getElementById('imageInput').value = '';
        document.getElementById('originalImageContainer').innerHTML = '';
    }
}

// Load available images from server
async function loadAvailableImages() {
    const container = document.getElementById('availableImagesContainer');
    
    try {
        showMessage('Loading available images...');
        
        const response = await fetch(`${API_BASE_URL}/uploads/names`);
        const data = await response.json();
        
        if (data.success && data.filenames && data.filenames.length > 0) {
            container.innerHTML = '';
            
            for (const filename of data.filenames) {
                const imageOption = document.createElement('div');
                imageOption.className = 'image-option';
                imageOption.onclick = () => selectServerImage(filename, imageOption);
                
                imageOption.innerHTML = `
                    <img src="/uploads/${filename}" alt="${filename}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2U8L3RleHQ+PC9zdmc+'" />
                    <div class="filename">${filename}</div>
                `;
                
                container.appendChild(imageOption);
            }
            
            showMessage(`Loaded ${data.filenames.length} available images`);
        } else {
            container.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">No images available on server</p>';
            showMessage('No images found on server');
        }
        
    } catch (error) {
        console.error('Error loading available images:', error);
        container.innerHTML = '<p style="color: #dc3545; text-align: center; padding: 20px;">Error loading images from server</p>';
        showMessage('Failed to load available images', true);
    }
}

// Select an image from server
function selectServerImage(filename, element) {
    // Clear previous selection
    clearServerImageSelection();
    
    // Mark as selected
    element.classList.add('selected');
    selectedImageFromServer = filename;
    
    // Show original image
    const container = document.getElementById('originalImageContainer');
    container.innerHTML = `<img src="/uploads/${filename}" alt="Selected Image">`;
    
    // Clear file input since we're using server image
    document.getElementById('imageInput').value = '';
    
    showMessage(`Selected image: ${filename}`);
}

// Clear server image selection
function clearServerImageSelection() {
    document.querySelectorAll('.image-option').forEach(option => {
        option.classList.remove('selected');
    });
}

// Export current processed image
async function exportCurrentImage() {
    if (!processedImageData) {
        showMessage('No processed image to export. Process an image first.', true);
        return;
    }
    
    const format = document.getElementById('exportFormat').value;
    const quality = parseInt(document.getElementById('exportQuality').value);
    
    try {
        showMessage('Exporting image...');
        
        // Prepare form data for conversion if needed
        const formData = new FormData();
        
        // Convert base64 to blob
        const byteCharacters = atob(processedImageData.image);
        const byteNumbers = new Array(byteCharacters.length);
        
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: `image/${processedImageData.format}` });
        
        formData.append('image', blob, `processed_image.${processedImageData.format}`);
        formData.append('convert_format', format);
        formData.append('quality', quality);
        
        const response = await fetch(`${API_BASE_URL}/convert`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY
            },
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            
            if (result.success) {
                // Download the converted image
                const convertedByteCharacters = atob(result.data.image);
                const convertedByteNumbers = new Array(convertedByteCharacters.length);
                
                for (let i = 0; i < convertedByteCharacters.length; i++) {
                    convertedByteNumbers[i] = convertedByteCharacters.charCodeAt(i);
                }
                
                const convertedByteArray = new Uint8Array(convertedByteNumbers);
                const convertedBlob = new Blob([convertedByteArray], { type: `image/${format}` });
                
                // Create download link
                const url = URL.createObjectURL(convertedBlob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `exported_image_${Date.now()}.${format}`;
                
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                URL.revokeObjectURL(url);
                
                showMessage(`Image exported successfully as ${format.toUpperCase()}!`);
            } else {
                showMessage(result.message || 'Export failed', true);
            }
        } else {
            // Fallback: download original processed image
            downloadImage();
        }
        
    } catch (error) {
        console.error('Export error:', error);
        // Fallback: download original processed image
        downloadImage();
        showMessage('Used fallback export method');
    }
}
