from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PyPDF2 import PdfMerger
import tempfile, os, io

app = Flask(__name__)

# ✅ Omogući CORS samo za tvoju WordPress domenu

CORS(app, resources={r"/api/*": {"origins": ["https://www.quiconvert.com", "https://quiconvert.com"]}},
     supports_credentials=True)

@app.route('/api/pdf/merge', methods=['POST'])
def merge_pdfs():
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({"error": "No files uploaded"}), 400

        merger = PdfMerger()
        for file in files:
            merger.append(file)

        output = io.BytesIO()
        merger.write(output)
        output.seek(0)
        merger.close()

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='merged.pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # ⚙️ Pokreće Flask na svim mrežnim sučeljima (nužno za Render)
    app.run(host='0.0.0.0', port=5000)






