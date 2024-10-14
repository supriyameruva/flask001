from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
import os
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Set secret key from environment variable

# Azure Blob Storage connection string and container name from .env file
connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
container_name = os.getenv('STORAGE_CONTAINER_NAME')

# Initialize BlobServiceClient with connection string
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Set upload folder and allowed file extensions
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf'}

# Home page route
@app.route('/')
def index():
    return render_template('index.html')

# User login route
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

# Check if a file is allowed (based on extension)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# File upload route
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Upload file to Azure Blob Storage
            blob_client = container_client.get_blob_client(filename)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data)

            os.remove(file_path)  # Optionally remove the local copy after upload
            return f"File {filename} uploaded successfully to Azure Blob Storage"
        return 'File not allowed'
    return render_template('upload.html')

# List all blobs (files) in the Azure Blob Storage container
@app.route('/list')
def list_blobs():
    try:
        blobs = container_client.list_blobs()
        return render_template('list.html', blobs=blobs)
    except Exception as e:
        return f"Failed to list blobs: {e}"

# Download a file from Azure Blob Storage
@app.route('/download/<filename>')
def download_file(filename):
    try:
        blob_client = container_client.get_blob_client(filename)
        blob_data = blob_client.download_blob()
        stream = io.BytesIO(blob_data.readall())
        return send_file(stream, as_attachment=True, download_name=filename)
    except Exception as e:
        return f"Error downloading file: {e}"

# Data submission form route (optional, can modify)
@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        return f"Name: {name}, Email: {email}"
    return render_template('data.html')

if __name__ == '__main__':
    app.run(debug=True)
