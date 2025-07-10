import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
from PIL import Image
import io
import socket

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Serve a simple HTML form for file upload
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"""
            <html>
            <head>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #1c1c1c; /* Updated dark grey background */
                    }
                    .container {
                        text-align: center;
                        border: 1px solid #ccc;
                        padding: 68px; /* Increased padding */
                        background-color: #fff;
                        border-radius: 18px; /* Increased border-radius */
                        box-shadow: 0 9px 18px rgba(0, 0, 0, 0.15); /* Increased shadow */
                        width: 80%; /* Adjust width */
                        max-width: 800px; /* Set a maximum width */
                        box-sizing: border-box; /* Include padding and border in total width and height */
                    }
                    h2 {
                        margin: 0 0 45px 0; /* Margin for spacing */
                        font-size: 54px; /* Increased font size */
                    }
                    form {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }
                    input[type="file"] {
                        margin-bottom: 45px; /* Margin to space out from the upload button */
                        font-size: 36px; /* Larger font size for the file input */
                        padding: 20px 30px; /* Adjusted padding for a better fit */
                        height: 80px; /* Increased height */
                        width: 100%; /* Full width */
                        max-width: 600px; /* Maximum width */
                        box-sizing: border-box; /* Include padding and border in total width and height */
                        text-align: center; /* Center text */
                        display: block; /* Ensure it takes full width */
                    }
                    input[type="submit"] {
                        font-size: 36px; /* Larger font size */
                        padding: 30px 45px; /* Increased padding */
                        width: 100%; /* Full width */
                        max-width: 600px; /* Maximum width */
                        background-color: #d80d0d; /* Upload button color */
                        color: white; /* Text color */
                        border: none; /* Remove border */
                        border-radius: 9px; /* Rounded corners */
                        cursor: pointer; /* Pointer cursor on hover */
                        box-sizing: border-box; /* Include padding and border in total width and height */
                    }
                    input[type="submit"]:hover {
                        background-color: #c20a0a; /* Darker shade on hover */
                    }
                    input[type="file"]::-webkit-file-upload-button {
                        font-size: 36px; /* Match font size */
                        padding: 30px 45px; /* Match padding */
                        cursor: pointer; /* Pointer cursor */
                        border: none; /* Remove border */
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Upload image files</h2>
                    <form enctype="multipart/form-data" method="post">
                        <input type="file" name="file" multiple>
                        <input type="submit" value="Upload">
                    </form>
                </div>
            </body>
            </html>
        """)

    def do_POST(self):
        # Handle file upload using cgi.FieldStorage for better compatibility
        content_type = self.headers.get('Content-Type')
        if not content_type or not content_type.startswith('multipart/form-data'):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Bad Request: Expected multipart/form-data")
            return

        # Parse form data
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type,
            }
        )

        # Directory to save files - use relative path for portability
        upload_dir = os.path.join(os.path.expanduser("~"), "Desktop", "UploadedImages")
        os.makedirs(upload_dir, exist_ok=True)

        # Support both single and multiple file uploads
        files = form['file']
        if not isinstance(files, list):
            files = [files]

        success_count = 0
        for i, file_field in enumerate(files):
            if not file_field.filename:
                continue  # Skip empty fields
            try:
                # Read file data
                file_data = file_field.file.read()
                # Try to open as image
                image = Image.open(io.BytesIO(file_data))
                png_image = image.convert('RGBA')
                # Use original filename if possible, else fallback
                base_name = os.path.splitext(os.path.basename(file_field.filename))[0] or f"uploaded_image_{i+1}"
                file_name = f"{base_name}.png"
                png_filename = os.path.join(upload_dir, file_name)
                png_image.save(png_filename, 'PNG')
                success_count += 1
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Failed to convert file '{getattr(file_field, 'filename', 'unknown')}' to PNG: {str(e)}".encode())
                return

        self.send_response(200)
        self.end_headers()
        if success_count:
            self.wfile.write(f"{success_count} file(s) uploaded and converted to PNG successfully!".encode())
        else:
            self.wfile.write(b"No valid files uploaded.")

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    try:
        server_address = ('0.0.0.0', port)  # Bind to all interfaces (accessible on the local network)
        httpd = server_class(server_address, handler_class)
        
        # Get local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Get upload directory for display
        upload_dir = os.path.join(os.path.expanduser("~"), "Desktop", "UploadedImages")
        
        print("=" * 60)
        print("FILE UPLOAD SERVER STARTED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Server running on port {port}")
        print(f"Local access: http://localhost:{port}")
        print(f"Network access: http://{local_ip}:{port}")
        print("=" * 60)
        print("Instructions:")
        print("1. Open a web browser")
        print("2. Go to one of the URLs above")
        print("3. Upload your image files")
        print(f"4. Files will be saved to: {upload_dir}")
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        httpd.serve_forever()
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"ERROR: Port {port} is already in use!")
            print("Please close other applications using this port or restart your computer.")
        else:
            print(f"ERROR: Could not start server: {e}")
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
    finally:
        print("\nPress Enter to close this window...")
        input()

if __name__ == "__main__":
    run()
