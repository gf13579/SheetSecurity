function loadMusicSheet(url) {
    osmd.load(url).then(function() {
      osmd.render();
    });
  }

var osmd;
  
document.addEventListener("DOMContentLoaded", function() {

    console.log("Initializing...");
    const fileInput = document.getElementById('fileInput');
    fileInput.value = '';

    osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("osmdContainer");
    osmd.setOptions({
      backend: "svg",
      drawUpToMeasureNumber: 12,
      drawTitle: true,
    });
  
    // Load the initial file
    loadMusicSheet("http://127.0.0.1:8000/static/MozaVeilSample.xml");

    console.log("Initialisation complete.");
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
        fileInput.value = '';

        var baseUrl = window.location.origin;
        const contentToLoad = window.location.origin + '/files/' + data['file_hash'];
        console.log("About to load " + contentToLoad)
        loadMusicSheet(contentToLoad);
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        alert('Error uploading file. Please try again.');
    });
    
}