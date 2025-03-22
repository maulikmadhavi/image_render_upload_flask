# Flask Image Summarizer

A web application for uploading, displaying, and managing images with detailed information about each image.

## Features

- **Multiple Image Upload Methods**:
  - File upload from local device
  - URL-based image import
  - Data URL support (base64 encoded images)

- **Image Information Display**:
  - Image dimensions (width and height)
  - Upload timestamp
  - Unique filename generation

- **User Interface**:
  - Clean, responsive design
  - Notification system for success/error messages
  - Tabular display of uploaded images

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/maulikmadhavi/image_render_upload_flask.git
   cd image_render_upload_flask
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Usage

### Uploading Images

1. **File Upload**:
   - Click the "Choose File" button
   - Select an image from your device
   - Click "Upload"

2. **URL Import**:
   - Enter an image URL in the "Image URL" field
   - Click "Upload"
   - Supported formats: JPG, JPEG, PNG, GIF, WebP

3. **Data URL Import**:
   - Paste a data URL (starting with "data:image/...") in the "Image URL" field
   - Click "Upload"

### Viewing Uploaded Images

All uploaded images are displayed in a table showing:
- Image preview
- Filename
- Dimensions (width × height)
- Upload time

## Technical Details

- **Backend**: Flask (Python)
- **Image Processing**: Pillow
- **Data Storage**: CSV files for image metadata
- **Session Management**: File-based session storage
- **Notification System**: File-based to avoid cookie size limitations

## Project Structure

```
flask_image_summarizer/
├── app.py                 # Main application file
├── utils.py               # Utility functions
├── static/                # Static files (CSS, JS, uploaded images)
│   ├── uploads/           # Directory for uploaded images
│   └── renames/           # Directory for renamed images
├── templates/             # HTML templates
│   └── upload_and_display.html  # Main template
└── requirements.txt       # Project dependencies
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
