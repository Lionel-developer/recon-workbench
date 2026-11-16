
const button = document.querySelector("#check-health");
const output = document.querySelector("#status");
button.addEventListener("click", async () => {
    button.disabled = true;
    output.textContent = "Checking health...";
    try{
        const response = await fetch("/api/health");

        if (!response.ok){
            throw new Error(`HTTP ${response.status}`)
        }
        const data = await response.json();
        output.textContent = `Status: ${data.status}`;
    } catch (error) {
        output.textContent = `Request failed: ${error.message}`;
    }finally {
        button.disabled = false;
    }
});

const fileInput = document.querySelector("#scan-file");
const fileInfo = document.querySelector("#file-info");
const MAX_FILE_SIZE = 1024 * 1024; // 1 MiB

fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file){
        fileInfo.textContent = "No file selected.";
        return;
    }
    if (file.size === 0){
        fileInfo.textContent = "File is empty.";
        fileInput.value = "";
        return;
    }
    if (file.size > MAX_FILE_SIZE){
        fileInfo.textContent = "File is too large. Choose a file no larger than 1 MiB.";

        fileInput.value = "";
        return;
    }
    fileInfo.textContent = 
    `Selected: ${file.name} (${file.size} bytes)`;
});
const uploadButton = document.querySelector("#upload-scan");
const uploadStatus = document.querySelector("#upload-status");

uploadButton.addEventListener("click", async ()=> {
    const file = fileInput.files[0];
    if (!file){
        uploadStatus.textContent = "Choose an XML file first.";
        return;
    }
    uploadButton.disabled = true;
    uploadStatus.textContent = "Uploading scan...";
    try {
        const response = await fetch("/api/scans/preview", {
            method: "POST",
            headers: {
                "Content-Type": "application/xml"
            },
            body: file
        });

        const data = await response.json();
        if (!response.ok){
            throw new Error(
                `HTTP ${response.status}: ${data.detail || "Upload rejected"}`
            );
        }
        uploadStatus.textContent = `Host records: ${data.host_count}. Received ${data.received_bytes} bytes.`;
    } catch (error) {
        uploadStatus.textContent = `Upload failed: ${error.message}`;
    } finally {
        uploadButton.disabled = false;
    }
})