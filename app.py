from flask import Flask, render_template, request, redirect, url_for, session
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for sessions

# Azure Storage account URL
account_url = "https://myflaskwebappstorage.blob.core.windows.net/"

# Authenticate using managed identity with DefaultAzureCredential
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)

# Set upload folder and allowed file extensions
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Simple authentication (replace with a real user database check)
        if username == 'admin' and password == 'password':
            session['user'] = username
            return redirect(url_for('index'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        return f"Name: {name}, Email: {email}"
    return render_template('data.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            # Upload to Azure Blob Storage using managed identity
            blob_client = blob_service_client.get_blob_client(container='uploads', blob=file.filename)
            blob_client.upload_blob(file, overwrite=True)  # Use overwrite=True to replace existing blobs

            return f"File {file.filename} uploaded successfully to Azure Blob Storage"
        return 'File not allowed'
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
