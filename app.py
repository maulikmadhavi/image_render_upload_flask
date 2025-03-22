from flask import Flask, render_template, request, redirect, url_for, flash, session
from PIL import Image
import os
import re
import pandas as pd
from datetime import datetime
import shutil
import requests
from io import BytesIO
import uuid
import json
from flask_session import Session
from utils import Model


# Initialize the Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads/"  # Serve images from static folder
app.secret_key = "secret_key"

# Configure session to use filesystem instead of cookies
app.config["SESSION_TYPE"] = "filesystem"

# Define the folder for renamed images
RENAME_FOLDER = os.path.join(
    "static/renames/"  # Folder to store renamed images (save images with time stamp)
)
# Ensure the upload folder exists
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# Ensure the rename folder exists
if not os.path.exists(RENAME_FOLDER):
    os.makedirs(RENAME_FOLDER)

# Initialize Flask-Session
Session(app)

model = Model()

# Store notifications in a file instead of session
NOTIFICATION_FILE = os.path.join(os.getcwd(), "notifications.json")


# Function to save notification
def save_notification(message, message_type="info"):
    notifications = []
    if os.path.exists(NOTIFICATION_FILE):
        try:
            with open(NOTIFICATION_FILE, "r") as f:
                notifications = json.load(f)
        except:
            notifications = []

    # Add new notification
    notifications.append(
        {
            "message": message,
            "type": message_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )

    # Keep only the last 10 notifications
    notifications = notifications[-10:]

    # Save to file
    with open(NOTIFICATION_FILE, "w") as f:
        json.dump(notifications, f)


# Function to get notifications
def get_notifications():
    if os.path.exists(NOTIFICATION_FILE):
        try:
            with open(NOTIFICATION_FILE, "r") as f:
                notifications = json.load(f)
            # Clear the notifications after reading
            with open(NOTIFICATION_FILE, "w") as f:
                json.dump([], f)
            return notifications
        except:
            return []
    return []


# Function to save image details to CSV
def save_image_details(filename, width, height, upload_time, rename_filename):
    data = {
        "filename": filename,
        "width": width,
        "height": height,
        "upload_time": upload_time,
        "rename_filename": rename_filename,
    }

    csv_file = os.path.join(app.config["UPLOAD_FOLDER"], "../image_data.csv")

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
    csv_file = os.path.join(app.config["UPLOAD_FOLDER"], "../image_data.csv")
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        # Ensure width and height are integers
        if not df.empty:
            df["width"] = df["width"].astype(int)
            df["height"] = df["height"].astype(int)
        return df
    else:
        return pd.DataFrame(
            columns=["filename", "width", "height", "upload_time", "rename_filename"]
        )


@app.route("/", methods=["GET", "POST"])
def upload_and_display():
    if request.method == "POST":
        # Check if delete action is requested
        if "delete" in request.form and request.form["delete"] == "true":
            rename_filename = request.form["rename_filename"]
            # Delete the file
            try:
                # Get the original filename from the CSV
                df = load_existing_data()
                original_filename = df.loc[
                    df["rename_filename"] == rename_filename, "filename"
                ].values[0]

                # Delete the files
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], original_filename))
                os.remove(os.path.join(RENAME_FOLDER, rename_filename))

                # Update the CSV
                df = df[df["rename_filename"] != rename_filename]
                csv_file = os.path.join(
                    app.config["UPLOAD_FOLDER"], "../image_data.csv"
                )
                df.to_csv(csv_file, index=False)

                save_notification(
                    f"File {rename_filename} deleted successfully", "success"
                )
            except Exception as e:
                save_notification(f"Error deleting file: {str(e)}", "error")

            return redirect(url_for("upload_and_display"))

        # Generate a timestamp for the upload
        upload_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Check if image URL is provided
        image_url = request.form.get("image_url")

        if image_url and image_url.strip():
            try:
                # Check if it's a data URL
                if image_url.startswith("data:image/"):
                    # Parse the data URL
                    header, encoded = image_url.split(",", 1)
                    data_type = header.split(":")[1].split(";")[0]

                    # Get the encoding type (base64 or not)
                    is_base64 = ";base64" in header

                    # Decode the content
                    if is_base64:
                        import base64

                        content = base64.b64decode(encoded)
                    else:
                        from urllib.parse import unquote

                        content = unquote(encoded).encode("utf-8")

                    # Create a BytesIO object from the decoded content
                    image_content = BytesIO(content)

                    # Set a default filename for data URLs
                    url_filename = f"data_image_{uuid.uuid4().hex[:10]}.jpg"
                else:
                    # Regular URL - download the image
                    response = requests.get(image_url)
                    response.raise_for_status()  # Raise an exception for 4XX/5XX responses

                    # Create a BytesIO object from the response content
                    image_content = BytesIO(response.content)

                # For regular URLs, extract a filename from the URL
                if not image_url.startswith("data:image/"):
                    # Use first 25 characters of URL as filename base
                    url_base = image_url.split("?")[0]  # Remove query parameters
                    # Take the last part of the URL path or the domain if no path
                    url_parts = url_base.split("/")
                    url_last_part = url_parts[-1] if url_parts[-1] else url_parts[-2]
                    # Limit to 25 characters and remove invalid filename characters
                    url_filename_base = re.sub(r"[^\w\-\.]", "_", url_last_part[:25])

                    # If no valid filename could be extracted, create one with a UUID
                    if not url_filename_base or len(url_filename_base) < 3:
                        url_filename_base = f"url_image_{uuid.uuid4().hex[:10]}"

                    # Add jpg extension by default, will be updated with actual format later
                    url_filename = f"{url_filename_base}.jpg"
                # For data URLs, we already set url_filename above

                # Create a unique filename
                filename, ext = os.path.splitext(url_filename)

                # Load the image to validate it's a proper image
                try:
                    # image_content is already created above
                    image = Image.open(image_content)

                    # Get the actual format from the image if extension is missing or invalid
                    if not ext or ext.lower() not in [
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".webp",
                    ]:
                        ext = f".{image.format.lower()}" if image.format else ".jpg"

                    # Update filename with correct extension
                    new_filename = f"{filename}_{upload_time}{ext}"
                    rename_filename = f"{upload_time}{ext}"

                    # Save the image to the uploads folder
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
                    image.save(file_path)

                    # Save a copy to the renames folder
                    rename_file_path = os.path.join(RENAME_FOLDER, rename_filename)
                    image.save(rename_file_path)

                    # Get image dimensions
                    width, height = image.size
                    print(f"URL image dimensions: {width}x{height}")
                except Exception as img_error:
                    raise Exception(f"Invalid image format: {str(img_error)}")

                # Save the details to CSV
                df = save_image_details(
                    new_filename, width, height, upload_time, rename_filename
                )

                save_notification("Image successfully imported from URL", "success")
                return redirect(url_for("upload_and_display"))

            except Exception as e:
                save_notification(
                    f"Error downloading image from URL: {str(e)}", "error"
                )
                return redirect(request.url)

        # Check for file upload
        elif "image" in request.files:
            file = request.files["image"]

            if file.filename == "":
                save_notification("No file selected and no URL provided", "warning")
                return redirect(request.url)

            try:
                # Process the uploaded file
                original_filename = file.filename
                filename, ext = os.path.splitext(original_filename)

                # Load the file into memory to validate it's a proper image
                file_content = BytesIO(file.read())

                try:
                    # Try to open as an image to validate format
                    image = Image.open(file_content)

                    # Get the actual format from the image if extension is missing or invalid
                    if not ext or ext.lower() not in [
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".webp",
                    ]:
                        ext = f".{image.format.lower()}" if image.format else ".jpg"

                    # Update filename with correct extension
                    new_filename = f"{filename}_{upload_time}{ext}"
                    rename_filename = f"{upload_time}{ext}"

                    # Save the image to the uploads folder
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
                    image.save(file_path)

                    # Save a copy to the renames folder
                    rename_file_path = os.path.join(RENAME_FOLDER, rename_filename)
                    image.save(rename_file_path)

                    # Get image dimensions
                    width, height = image.size
                    print(f"File upload dimensions: {width}x{height}")
                except Exception as img_error:
                    raise Exception(f"Invalid image format: {str(img_error)}")
            except Exception as e:
                save_notification(f"Error processing uploaded file: {str(e)}", "error")
                return redirect(request.url)

            # Save the details to CSV and return the updated data
            df = save_image_details(
                new_filename, width, height, upload_time, rename_filename
            )

            save_notification("File successfully uploaded", "success")
            return redirect(url_for("upload_and_display"))

        else:
            save_notification("No file selected and no URL provided", "warning")
            return redirect(request.url)

    # If it's a GET request, load existing data and render the form with table
    df = load_existing_data()
    # Get any notifications
    notifications = get_notifications()

    # Debug: Print the dataframe to see what's being loaded
    print("Loaded dataframe:")
    if not df.empty:
        print(df)
        print("Data types:")
        print(df.dtypes)
    else:
        print("DataFrame is empty")

    # Convert to records and ensure all values are properly formatted
    table_data = None
    if not df.empty:
        table_data = df.to_dict("records")
        print("Table data being sent to template:")
        print(table_data)

    return render_template(
        "upload_and_display.html",
        table=table_data,
        notifications=notifications,
    )


if __name__ == "__main__":
    app.run()
