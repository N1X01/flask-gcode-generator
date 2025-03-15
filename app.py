from flask import Flask, request, send_file, render_template
import pandas as pd
import os
import zipfile
import re  # For cleaning names
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
GCODE_FOLDER = "gcode_files"
SVG_FOLDER = "svg_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GCODE_FOLDER, exist_ok=True)
os.makedirs(SVG_FOLDER, exist_ok=True)

def clean_name(name):
    """Keep the exact first name without filtering."""
    return str(name).strip()

def text_to_svg(name, filename):
    """Creates an SVG file with the name written in vector format."""
    svg_content = f"""
    <svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
        <text x="10" y="50" font-family="Arial" font-size="24" fill="black">{name}</text>
    </svg>
    """
    with open(filename, "w") as file:
        file.write(svg_content)
    return filename

def svg_to_gcode(svg_file):
    """Converts SVG text paths into G-code movements."""
    drawing = svg2rlg(svg_file)
    gcode_lines = [
        "G21 ; Set units to mm",
        "G90 ; Absolute positioning"
    ]

    start_x, start_y = 10, 50  # Set base position

    for shape in drawing.contents:
        if hasattr(shape, 'points'):
            for point in shape.points:
                x, y = point
                gcode_lines.append(f"G0 X{x + start_x} Y{y + start_y}")  # Move to start
                gcode_lines.append("G1 Z2")  # Pen down
                gcode_lines.append(f"G1 X{x + start_x} Y{y + start_y}")  # Draw segment
                gcode_lines.append("G1 Z0")  # Pen up

    gcode_lines.append("G0 X0 Y0")  # Return home
    return "\n".join(gcode_lines)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file and file.filename.endswith(".csv"):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            
            # Read CSV
            df = pd.read_csv(filepath)

            if "First Name" not in df.columns:
                return "Error: 'First Name' column not found in CSV file."

            # Extract and clean first names
            first_names = df["First Name"].dropna().apply(clean_name)

            # Create ZIP filename
            zip_filename = "generated_gcode.zip"
            zip_path = os.path.join(GCODE_FOLDER, zip_filename)

            # Delete old ZIP file if it exists
            if os.path.exists(zip_path):
                os.remove(zip_path)

            # Create new ZIP file
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for name in first_names:
                    if name != "Skipped":
                        svg_file = text_to_svg(name, os.path.join(SVG_FOLDER, f"{name}.svg"))
                        gcode_content = svg_to_gcode(svg_file)

                        gcode_filename = f"{name.strip()}.gcode"
                        gcode_path = os.path.join(GCODE_FOLDER, gcode_filename)

                        with open(gcode_path, "w") as gcode_file:
                            gcode_file.write(gcode_content)

                        zipf.write(gcode_path, gcode_filename)

            return send_file(zip_path, as_attachment=True)

    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
