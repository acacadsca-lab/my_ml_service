const dropZone = document.getElementById('dropZone');
const audioInput = document.getElementById('audioInput');
const fileInfo = document.getElementById('fileInfo');
const textInput = document.getElementById('textInput');
const form = document.getElementById('voiceForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = document.getElementById('btnText');
const clearBtn = document.getElementById('clearBtn');
const responseContainer = document.getElementById('responseContainer');
const outputAudio = document.getElementById('outputAudio');
const errorMessage = document.getElementById('errorMessage');


function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Drag and drop functionality
dropZone.addEventListener('click', () => audioInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        audioInput.files = files;
        displayFileInfo(files[0]);
    }
});

audioInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        displayFileInfo(e.target.files[0]);
    }
});

function displayFileInfo(file) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    fileInfo.textContent = `✓ ${file.name} (${sizeMB} MB)`;
    fileInfo.style.display = 'block';
}

// Clear form
clearBtn.addEventListener('click', () => {
    form.reset();
    audioInput.value = '';
    fileInfo.style.display = 'none';
    responseContainer.classList.remove('show');
    errorMessage.classList.remove('show');
});

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMessage.classList.remove('show');

    if (!audioInput.files.length) {
        showError('Please upload an audio file');
        return;
    }

    if (!textInput.value.trim()) {
        showError('Please enter text to clone');
        return;
    }

    // Disable submit button and show loader
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    btnText.textContent = '';
    const loader = document.createElement('div');
    loader.className = 'loader';
    btnText.parentElement.insertBefore(loader, btnText);


    try {
        const formData = new FormData();
        formData.append('audio', audioInput.files[0]);
        formData.append('text', textInput.value);
        formData.append('X-CSRFToken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        // Replace with your actual API endpoint
        const csrfToken=getCookie('csrftoken')
        const response = await fetch('/voice_clone/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },

            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to process audio');
        }

        const data = await response.json();

        if (data.audio_url) {
            outputAudio.src = data.audio_url;
            responseContainer.classList.add('show');
        } else {
            showError('No audio output received');
        }
    } catch (error) {
        showError(error.message || 'An error occurred');
    } finally {
        // Re-enable submit button and hide loader
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
        btnText.textContent = 'Submit';
        loader.remove();
    }
});

function showError(message) {
    errorMessage.textContent = `⚠️ ${message}`;
    errorMessage.classList.add('show');
}

