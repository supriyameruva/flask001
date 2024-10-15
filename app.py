import os
from flask import Flask, render_template, request, redirect, url_for
from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient
from azure.storage.fileshare import ShareClient

app = Flask(__name__)

# Load environment variables
STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
BLOB_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME')
SHARE_NAME = os.getenv('AZURE_FILE_SHARE_NAME')

# Use Managed Identity to authenticate with Azure Storage
credential = ManagedIdentityCredential()

# Blob Storage client
blob_service_client = BlobServiceClient(
    f"https://myflaskwebappstorage.blob.core.windows.net", credential=credential)

# Azure File Share client
share_client = ShareClient(
    f"https://myflaskwebappstorage.file.core.windows.net/myfileshare", credential=credential)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    # Upload to Azure Blob Storage
    try:
        blob_client = blob_service_client.get_blob_client(container=BLOB_CONTAINER_NAME, blob=file.filename)
        blob_client.upload_blob(file)
        return f"File {file.filename} uploaded to Blob Storage!"
    except Exception as e:
        return f"Failed to upload to Blob Storage: {e}"

@app.route('/list')
def list_files():
    try:
        # List files in Azure Blob Storage container
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        blobs = container_client.list_blobs()
        blob_names = [blob.name for blob in blobs]
        return render_template('list.html', blobs=blob_names)
    except Exception as e:
        return f"Error listing files: {e}"

@app.route('/fileshare')
def file_share():
    try:
        # List files in Azure Files Share
        files = share_client.list_directories_and_files()
        file_names = [file.name for file in files]
        return render_template('list.html', blobs=file_names)
    except Exception as e:
        return f"Error accessing Azure Files: {e}"

if __name__ == "__main__":
    app.run(debug=True)
