from flask import Flask, request, send_file, render_template
import pandas as pd
import os
import zipfile

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
GCODE_FOLDER = "gcode_files"
os.makedirs(UPLOAD_FOLDER,exist_ok=True)
os.makedirs(GCODE_FOLDER, exist_ok=True)

def generate_gcode(name):
    return f"""(
G21 ; Set units to mm
G90 ; Absolute positioning
M3 S100 ; Pen down
G0 X10 Y10 ; Move to start position
G1 X20 Y10 ; Write name: {name}
M5 ; Pen up
G0 X0 Y0 ; Return to home
)"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file and file.filename.endswith(".csv"):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            df = pd.read_csv(filepath)
            
            if "First Name" not in df.columns:
                return "Error: 'First Name' column not found in CSV file.", 400
            
            first_names = df["First Name"].dropna().unique()
            
            zip_filename = "generated_gcode.zip"
            zip_path = os.path.join(GCODE_FOLDER, zip_filename)
            
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for name in first_names:
                    gcode_content = generate_gcode(name)
                    gcode_filename = f"{name}.gcode"
                    gcode_path = os.path.join(GCODE_FOLDER, gcode_filename)
                    with open(gcode_path, "w") as gcode_file:
                        gcode_file.write(gcode_content)
                    zipf.write(gcode_path, gcode_filename)
            
            return send_file(zip_path, as_attachment=True)
    
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
