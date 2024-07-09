console.log("Initializing...");



document.addEventListener("DOMContentLoaded", function() {
    const fileInput = document.getElementById('fileInput');
    fileInput.value = '';
    console.log("Done.");
});

function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput.files.length === 0) {
        alert('Please select a file to upload.');
        return;
    }

    const file = fileInput.files[0];
    const fileType = file.type;

    if (fileType !== 'application/vnd.recordare.musicxml' || !file.name.endsWith('.mxl')) {
        alert('Please upload a MusicXML file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    // Replace the URL with your actual upload endpoint
    const uploadUrl = '/upload';

    fetch(uploadUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to upload file');
        }
        return response.json();
    })
    .then(data => {
        console.log('File uploaded successfully:', data);
        console.log('URL is ' + window.location.href + '/files/' + data['file_hash']);
        fileInput.value = '';
        alert('File uploaded successfully!\n' + 'URL is ' + window.location.href + 'files/' + data['file_hash']);
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        alert('Error uploading file. Please try again.');
    });
    
}