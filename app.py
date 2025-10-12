from flask import Flask, request, send_file
from PyPDF2 import PdfMerger
import tempfile, os

app = Flask(__name__)

@app.route('/')
def home():
    return {"message": "QuiConvert API is running!"}

@app.route('/api/pdf/merge', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist("files")
    if not files:
        return {"error": "No files uploaded"}, 400

    merger = PdfMerger()
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    for f in files:
        merger.append(f)
    merger.write(temp_output)
    merger.close()
    temp_output.seek(0)

    return send_file(temp_output.name, as_attachment=True, download_name="merged.pdf")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
