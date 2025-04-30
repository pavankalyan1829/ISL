document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // File upload preview
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');
    const predictionCard = document.getElementById('prediction-card');
    const resultLetter = document.getElementById('result-letter');
    const confidenceProgress = document.getElementById('confidence-progress');
    const confidenceText = document.getElementById('confidence-text');
    const resultImage = document.getElementById('result-image');
    const uploadSpinner = document.getElementById('upload-spinner');
    
    // Skip if elements don't exist (non-dashboard pages)
    if (!uploadForm) return;
    
    // Handle drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        uploadArea.classList.add('border-primary', 'bg-light');
    }
    
    function unhighlight() {
        uploadArea.classList.remove('border-primary', 'bg-light');
    }
    
    // Handle file drop
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            fileInput.files = files;
            handleFiles(files);
        }
    }
    
    // Handle file selection
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length) {
            handleFiles(fileInput.files);
        }
    });
    
    function handleFiles(files) {
        const file = files[0];
        
        // Check if the file is an image
        if (!file.type.match('image.*')) {
            alert('Please select an image file');
            return;
        }
        
        // Display preview
        const reader = new FileReader();
        reader.onload = function(e) {
            resultImage.src = e.target.result;
            resultImage.style.display = 'block';
        };
        reader.readAsDataURL(file);
        
        // Submit form
        const formData = new FormData();
        formData.append('file', file);
        
        uploadSpinner.style.display = 'block';
        
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            // Display results
            resultLetter.textContent = data.predicted_class;
            const confidence = Math.round(data.confidence * 100);
            confidenceProgress.style.width = confidence + '%';
            confidenceText.textContent = confidence + '%';
            
            // Set confidence color based on value
            if (confidence >= 80) {
                confidenceProgress.className = 'confidence-progress bg-success';
            } else if (confidence >= 60) {
                confidenceProgress.className = 'confidence-progress bg-info';
            } else if (confidence >= 40) {
                confidenceProgress.className = 'confidence-progress bg-warning';
            } else {
                confidenceProgress.className = 'confidence-progress bg-danger';
            }
            
            predictionCard.style.display = 'block';
            uploadSpinner.style.display = 'none';
            
            // Scroll to results
            predictionCard.scrollIntoView({behavior: 'smooth'});
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
            uploadSpinner.style.display = 'none';
        });
    }
    
    // Camera functionality
    const cameraButton = document.getElementById('camera-button');
    const cameraPreview = document.getElementById('camera-preview');
    const captureButton = document.getElementById('capture-button');
    const closeCamera = document.getElementById('close-camera');
    
    if (cameraButton) {
        let stream = null;
        
        cameraButton.addEventListener('click', async function() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
                cameraPreview.srcObject = stream;
                cameraPreview.style.display = 'block';
                captureButton.style.display = 'block';
                closeCamera.style.display = 'block';
                cameraButton.style.display = 'none';
                
                // Show camera interface
                document.getElementById('camera-interface').style.display = 'block';
                document.getElementById('upload-interface').style.display = 'none';
            } catch (err) {
                console.error('Error accessing camera: ', err);
                alert('Could not access camera. Please make sure camera access is enabled.');
            }
        });
        
        captureButton.addEventListener('click', function() {
            const canvas = document.createElement('canvas');
            canvas.width = cameraPreview.videoWidth;
            canvas.height = cameraPreview.videoHeight;
            canvas.getContext('2d').drawImage(cameraPreview, 0, 0);
            
            // Convert canvas to blob
            canvas.toBlob(function(blob) {
                const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
                
                // Create a FileList-like object
                const dT = new DataTransfer();
                dT.items.add(file);
                fileInput.files = dT.files;
                
                handleFiles(fileInput.files);
                
                // Close camera
                stopCamera();
            }, 'image/jpeg');
        });
        
        closeCamera.addEventListener('click', stopCamera);
        
        function stopCamera() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            cameraPreview.style.display = 'none';
            captureButton.style.display = 'none';
            closeCamera.style.display = 'none';
            cameraButton.style.display = 'block';
            
            // Show upload interface again
            document.getElementById('camera-interface').style.display = 'none';
            document.getElementById('upload-interface').style.display = 'block';
        }
    }
    
    // Toggle between upload and camera modes
    const uploadTab = document.getElementById('upload-tab');
    const cameraTab = document.getElementById('camera-tab');
    
    if (uploadTab && cameraTab) {
        uploadTab.addEventListener('click', function() {
            document.getElementById('upload-interface').style.display = 'block';
            document.getElementById('camera-interface').style.display = 'none';
            uploadTab.classList.add('active');
            cameraTab.classList.remove('active');
        });
        
        cameraTab.addEventListener('click', function() {
            document.getElementById('upload-interface').style.display = 'none';
            document.getElementById('camera-interface').style.display = 'block';
            cameraTab.classList.add('active');
            uploadTab.classList.remove('active');
        });
    }
});