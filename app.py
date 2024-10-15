import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient
from azure.storage.fileshare import ShareClient
import msal

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Ensure SECRET_KEY is set in your environment

# Load environment variables
STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
BLOB_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME')
SHARE_NAME = os.getenv('AZURE_FILE_SHARE_NAME')

# Azure AD Config
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
TENANT_ID = os.getenv('AZURE_TENANT_ID')
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/getAToken"
SCOPE = ["https://storage.azure.com/user_impersonation"]
SESSION_TYPE = "filesystem"

# MSAL setup
msal_client = msal.ConfidentialClientApplication(
    CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
)

# Use Managed Identity to authenticate with Azure Storage
credential = ManagedIdentityCredential()

# Blob Storage client
blob_service_client = BlobServiceClient(
    f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net", credential=credential
)

# Azure File Share client
share_client = ShareClient(
    f"https://{STORAGE_ACCOUNT_NAME}.file.core.windows.net/{SHARE_NAME}", credential=credential
)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    # Upload to Azure Blob Storage
    try:
        blob_client = blob_service_client.get_blob_client(container=BLOB_CONTAINER_NAME, blob=file.filename)
        blob_client.upload_blob(file)
        flash(f"File {file.filename} uploaded to Blob Storage!")
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Failed to upload to Blob Storage: {e}")
        return redirect(request.url)

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

@app.route("/login")
def login():
    # Redirect to Azure AD for authentication
    auth_url = msal_client.get_authorization_request_url(SCOPE, redirect_uri=url_for("auth_response", _external=True))
    return redirect(auth_url)

@app.route(REDIRECT_PATH)
def auth_response():
    # Handle the redirect from Azure AD and acquire a token
    code = request.args.get('code')
    if code:
        token = msal_client.acquire_token_by_authorization_code(code, scopes=SCOPE, redirect_uri=url_for("auth_response", _external=True))
        if 'access_token' in token:
            session['user'] = token
            return redirect(url_for('index'))
        else:
            return "Login failed"
    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
