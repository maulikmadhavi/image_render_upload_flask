from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
import shutil
import pandas as pd
from utils import VideoProcessor, LLM


# Initialize the Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads_video/'
app.secret_key = "secret_key"

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# # Ensure the rename folder exists
# RENAME_FOLDER = 'static/renames_video/'
# if not os.path.exists(RENAME_FOLDER):
#     os.makedirs(RENAME_FOLDER)

vp = VideoProcessor()
llm = LLM()
# Function to save video details to CSV
def save_video_details(filename, upload_time, summary, video_captions):
    data = {
        "filename": filename,
        "upload_time": upload_time,
        "summary": summary,
        "video_captions": video_captions
    }

    csv_file = os.path.join(app.config['UPLOAD_FOLDER'], '../video_data.csv')

    # Load existing data or create a new dataframe
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        df = df.append(data, ignore_index=True)
    else:
        df = pd.DataFrame([data])

    # Save the updated data to the CSV file
    df.to_csv(csv_file, index=False)

    return df

# Function to load existing video data from CSV
def load_existing_data():
    csv_file = os.path.join(app.config['UPLOAD_FOLDER'], '../video_data.csv')
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    else:
        return pd.DataFrame(columns=['filename',  'upload_time', 'summary', "video_captions"])

# Route for the upload form and displaying video details
@app.route('/', methods=['GET', 'POST'])
def video_upload_and_display():
    if request.method == 'POST':
        if 'delete' in request.form:
            filename = request.form.get('filename')
            csv_file = os.path.join(app.config['UPLOAD_FOLDER'], '../video_data.csv')

            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                df = df[df['filename'] != filename]
                df.to_csv(csv_file, index=False)

                # Also delete the video file from the renames folder
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

                flash(f'Video {filename} deleted successfully.')
            else:
                flash('No data file found.')

            return redirect(url_for('video_upload_and_display'))

        if 'video' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['video']

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

            # Save the uploaded file with the new filename in uploads folder
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)


            # Open the video to extract resolution
            try:
                _, video_captions = vp.get_caption(file_path)
                print(video_captions)
                # all_caps = [f"Frame {i}: {video_captions[i]}" for i in video_captions]
                # all_caps = '\n'.join(all_caps)
                num_frames = len(_)
                # video_captions = "Not implemented yet-video_captions"
            except Exception as e:
                flash(f"Could not process the video: {str(e)}")
                return redirect(request.url)
            llm_output = llm.run(str(num_frames-1), video_captions)
            # Save the details to CSV and return the updated data
            df = save_video_details(new_filename, upload_time, llm_output, video_captions)

            # Redirect to the display page to prevent form resubmission
            return redirect(url_for('video_upload_and_display'))

    # If it's a GET request, load existing data and render the form with table
    df = load_existing_data()
    return render_template('video_upload_and_display.html', table=df.to_dict('records') if not df.empty else None)

if __name__ == "__main__":
    app.run()
