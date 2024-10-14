from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Ensure this is set in your environment

# Set the directory for the Azure Files share (this should match the mounted drive)
AZURE_FILES_PATH = '/mnt/myfiles'  # Adjust this path based on your mounting

# Set upload folder and allowed file extensions
app.config['UPLOAD_FOLDER'] = AZURE_FILES_PATH
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf'}

# Home page route
@app.route('/')
def index():
    return render_template('index.html')

# Check if a file is allowed (based on extension)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# File upload route
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    error_message = None  # Initialize an error message variable
    if request.method == 'POST':
        file = request.files.get('file')  # Use .get() for safer access
        if not file:
            error_message = 'No file selected for upload.'
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Check for file existence and handle duplicates
            if os.path.exists(file_path):
                error_message = f'File {filename} already exists. Please rename it and try again.'
            else:
                file.save(file_path)  # Save to Azure Files share
                return f"File {filename} uploaded successfully to Azure Files share"
        else:
            error_message = 'File type not allowed.'
    
    return render_template('upload.html', error=error_message)  # Pass error message to the template

# List all files in Azure Files share
@app.route('/list')
def list_files():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])  # List files in the mounted share
        return render_template('list.html', files=files)
    except Exception as e:
        return f"Failed to list files: {e}"

# Download a file from Azure Files share
@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Error downloading file: {e}"

# Data submission form route (optional)
@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        return f"Name: {name}, Email: {email}"
    return render_template('data.html')

if __name__ == '__main__':
    app.run(debug=True)
