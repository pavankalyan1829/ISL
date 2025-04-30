class Camera {
    constructor(videoElement) {
        this.videoElement = videoElement;
        this.stream = null;
    }

    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });
            this.videoElement.srcObject = this.stream;
            return new Promise((resolve) => {
                this.videoElement.onloadedmetadata = () => {
                    this.videoElement.play();
                    resolve();
                };
            });
        } catch (error) {
            console.error('Error starting camera:', error);
            throw error;
        }
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    captureAsBlob(canvasElement) {
        return new Promise((resolve) => {
            const context = canvasElement.getContext('2d');
            canvasElement.width = this.videoElement.videoWidth;
            canvasElement.height = this.videoElement.videoHeight;
            context.drawImage(this.videoElement, 0, 0, canvasElement.width, canvasElement.height);
            canvasElement.toBlob((blob) => {
                resolve(blob);
            }, 'image/jpeg', 0.95);
        });
    }

    async captureAndSubmit(canvasElement, fileInput, handleFilesCallback) {
        const blob = await this.captureAsBlob(canvasElement);
        const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
        
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;

        handleFilesCallback(fileInput.files);  // Call your upload function
    }
}
