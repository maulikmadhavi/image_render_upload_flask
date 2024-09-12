from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import os
import pandas as pd
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # Serve images from static folder
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
    
    csv_file = os.path.join(app.config['UPLOAD_FOLDER'], '../image_data.csv')

    # Load existing data or create a new dataframe
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        df = df.append(data, ignore_index=True)
    else:
        df = pd.DataFrame([data])

    # Save the updated data to the CSV file
    df.to_csv(csv_file, index=False)

    return df

# Function to load existing image data from CSV
def load_existing_data():
    csv_file = os.path.join(app.config['UPLOAD_FOLDER'], '../image_data.csv')
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    else:
        return pd.DataFrame(columns=['filename', 'width', 'height', 'upload_time'])

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
            # Get the upload time
            upload_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            
            # Add a unique timestamp to the filename
            original_filename = file.filename
            filename, ext = os.path.splitext(original_filename)
            new_filename = f"{filename}_{upload_time}{ext}"

            # Save the uploaded file with the new filename in static/uploads/
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)

            # Open the image to extract width and height
            image = Image.open(file_path)
            width, height = image.size
            
            # Save the details to CSV and return the updated data
            df = save_image_details(new_filename, width, height, upload_time)
            
            # Redirect to the display page to prevent form resubmission
            return redirect(url_for('upload_and_display'))

    # If it's a GET request, load existing data and render the form with table
    df = load_existing_data()
    return render_template('upload_and_display.html', table=None if df.empty else df.to_dict('records'))


if __name__ == "__main__":
    app.run(debug=True)
