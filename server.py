from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        steps = extract_steps_from_pdf(file_path)
        return jsonify(steps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def extract_steps_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Match all numbered steps like 1.1, 2.5, 3.10, etc.
    step_pattern = re.compile(r'(\d+\.\d+)\s+(.*?)(?=\n\d+\.\d+|\Z)', re.DOTALL)

    steps = []
    for match in step_pattern.finditer(text):
        step_id = match.group(1)
        description = match.group(2).strip().replace('\n', ' ')
        title = description.split('.')[0][:60] + "..." if '.' in description else f"Step {step_id}"

        steps.append({
            "id": step_id,
            "title": title,
            "description": description,
            "targetObjectName": None  # Let Unity decide based on LLM or part matching
        })

    return {
        "totalSteps": len(steps),
        "fileName": os.path.basename(pdf_path),
        "steps": steps
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
