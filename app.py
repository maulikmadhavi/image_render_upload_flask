from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import os
import pandas as pd
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = "secret_key"

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to save image details to CSV
def save_image_details(filename, width, height, upload_time):
    data = {
        "filename": filename,
        "width": width,
        "height": height,
        "upload_time": upload_time
    }
    
    csv_file = os.path.join(app.config['UPLOAD_FOLDER'], 'image_data.csv')

    # Load existing data or create a new dataframe
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        df = df.append(data, ignore_index=True)
    else:
        df = pd.DataFrame([data])

    # Save the updated data to the CSV file
    df.to_csv(csv_file, index=False)

    return df

# Route for the upload form and displaying image details
@app.route('/', methods=['GET', 'POST'])
def upload_and_display():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['image']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file:
            # Save the uploaded file
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Open the image to extract width and height
            image = Image.open(file_path)
            width, height = image.size
            
            # Get the upload time
            upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Save the details to CSV and return the updated data
            df = save_image_details(filename, width, height, upload_time)
            
            # Render the same template but pass the image details
            return render_template('upload_and_display.html', table=df.to_dict('records'))

    # If it's a GET request, just render the form without any table
    return render_template('upload_and_display.html', table=None)

if __name__ == "__main__":
    app.run(debug=True)
