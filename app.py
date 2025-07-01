from flask import Flask, request, render_template_string
import boto3
import os
from datetime import datetime
from botocore.exceptions import NoCredentialsError, ClientError
import socket
from uuid import uuid4

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Max upload 10MB

# AWS configuration from environment
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Initialize S3 client
s3_client = boto3.client('s3', region_name=AWS_REGION)

@app.route('/')
def home():
    current_date = datetime.now().strftime("%Y-%m-%d")
    system_id = str(uuid4())
    private_ip = socket.gethostbyname(socket.gethostname())

    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Polypop Technologies</title>
        <style>
            body { font-family: Arial; padding: 20px; background-color: #f8f8f8; }
            .services { display: flex; gap: 20px; margin-top: 20px; }
            .service { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); width: 30%; }
            .nav-link { position: absolute; top: 20px; right: 20px; font-weight: bold; color: #4CAF50; text-decoration: none; }
            footer { margin-top: 50px; text-align: center; color: #777; }
        </style>
    </head>
    <body>
        <a href="/careers" class="nav-link">Careers</a>
        <h1>Welcome to Polypop Technologies!</h1>
        <p>We specialize in providing innovative solutions to make your business thrive.</p>

        <div class="services">
            <div class="service">
                <h3>Web Development</h3>
                <p>Building responsive and functional websites to meet your business needs.</p>
            </div>
            <div class="service">
                <h3>Cloud Solutions</h3>
                <p>Harnessing the power of cloud computing to drive scalability and efficiency.</p>
            </div>
            <div class="service">
                <h3>Mobile Apps</h3>
                <p>Creating user-friendly mobile apps for Android and iOS platforms.</p>
            </div>
        </div>

        <footer>From Polypop Technologies</footer>

        <div class="system-info">
            <p><strong>Current Date:</strong> {{ current_date }}</p>
            <p><strong>System ID:</strong> {{ system_id }}</p>
            <p><strong>Private IP:</strong> {{ private_ip }}</p>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_content, current_date=current_date, system_id=system_id, private_ip=private_ip)

@app.route('/careers', methods=['GET', 'POST'])
def careers():
    if request.method == 'POST':
        # Handle form submission
        name = request.form.get('name')
        phone = request.form.get('phone')
        experience = request.form.get('experience')
        position = request.form.get('position')
        salary = request.form.get('prefered salary')
        expected_salary = request.form.get('expected_ctc')

        #Handle file upload

        file = request.files.get('file')
        if not file or file.filename == '':
            return "No file selected", 400

        extension = os.path.splitext(file.filename)[1]
        date_folder = datetime.now().strftime('%d%m%Y')
        file_key = f"{date_folder}/{name.replace(' ', '_')}_resume{extension}"

        try:
            s3_client.upload_fileobj(file, S3_BUCKET_NAME, file_key)
            resume_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file_key}"

            return f"<h2>Thank you, {name}! Your application for {position} has been submitted successfully.</h2><p>Resume URL: <a href='{resume_url}' target='_blank'>{resume_url}</a></p><a href='/'>Return Home</a>"

        except NoCredentialsError:
            return "AWS credentials not available.", 500
        except ClientError as e:
            return f"AWS Error: {e}", 500
        except Exception as e:
            return f"An error occurred: {str(e)}", 500

    # GET: show form
    form_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Careers at Polypop</title>
        <style>
            body { font-family: Arial; padding: 30px; background: #f4f4f4; }
            form { background: #fff; padding: 20px; border-radius: 10px; max-width: 600px; margin: auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 15px; }
            label { display: block; font-weight: bold; margin-bottom: 5px; }
            input { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 5px; }
            button { background: #4CAF50; color: #fff; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            button:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <a href="/" style="color: #4CAF50;">← Back to Home</a>
        <h1>Join Our Team</h1>
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group"><label>Name:</label><input type="text" name="name" required></div>
            <div class="form-group"><label>Phone:</label><input type="tel" name="phone" required></div>
            <div class="form-group"><label>Experience (Years):</label><input type="number" name="experience" required></div>
            <div class="form-group"><label>Position:</label><input type="text" name="position" required></div>
            <div class="form-group"><label>Current Salary:</label><input type="number" name="salary" required></div>
            <div class="form-group"><label>Expected Salary:</label><input type="number" name="expected_salary" required></div>
            <div class="form-group"><label>Upload Resume:</label><input type="file" name="file" required></div>
            <button type="submit">Submit Application</button>
        </form>
    </body>
    </html>
    '''
    return render_template_string(form_html)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)