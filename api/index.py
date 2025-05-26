# File: my-vercel-flask-app/api/index.py

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from docx import Document
import io
import traceback
import logging

# Inisialisasi logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Atur level logging

# Variabel 'app' harus menjadi variabel global yang bisa diimpor oleh Vercel
app = Flask(__name__)

# --- KONFIGURASI CORS ---
# Izinkan permintaan dari origin frontend lokal Anda (SPCK Editor)
# Ganti port 7700 jika SPCK Editor Anda menggunakan port yang berbeda.
CORS(app, resources={
    r"/api/*": { # Terapkan CORS untuk semua rute di bawah /api/
        "origins": [
            "http://localhost:7700",
            "http://127.0.0.1:7700"
            # Jika nantinya Anda mendeploy frontend ke domain publik, tambahkan di sini
            # "https://nama-domain-frontend-anda.com"
        ]
    }
})

# Rute ini adalah untuk Vercel agar tahu ini aplikasi Flask
# dan untuk mengetes apakah dasar aplikasi berjalan.
# Vercel akan mengarahkan /api/ atau /api/index ke file ini.
@app.route('/api', methods=['GET']) # Menangani /api
@app.route('/api/index', methods=['GET']) # Menangani /api/index
def handle_root_api():
    logger.info("Endpoint dasar API (/api atau /api/index) dipanggil.")
    return jsonify(message="Python Flask Backend (TXT to DOCX) is running on Vercel!")

# Endpoint API utama Anda untuk konversi
@app.route('/api/convert-txt-to-docx', methods=['POST'])
def convert_txt_to_docx_route():
    logger.info("Menerima permintaan ke /api/convert-txt-to-docx")
    try:
        text_content = ""
        filename_base = "dokumen_hasil_konversi"

        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            logger.info(f"Menerima file: {file.filename}, mimetype: {file.mimetype}")
            if file.mimetype == 'text/plain' or file.filename.lower().endswith('.txt'):
                try:
                    text_content = file.read().decode('utf-8')
                    if '.' in file.filename:
                        filename_base = file.filename.rsplit('.', 1)[0]
                    else:
                        filename_base = file.filename
                except Exception as e:
                    logger.error(f"Error membaca file yang diunggah: {str(e)}")
                    return jsonify({"error": f"Gagal membaca file: {str(e)}"}), 500
            else:
                logger.warning(f"Format file tidak valid: {file.filename}")
                return jsonify({"error": "Format file tidak valid. Harap unggah file .txt"}), 400
        elif 'text_content' in request.form and request.form['text_content'].strip():
            text_content = request.form['text_content']
            logger.info("Menerima text_content dari form")
        else:
            logger.warning("Tidak ada input teks atau file yang valid.")
            return jsonify({"error": "Tidak ada input teks atau file yang valid."}), 400

        if not text_content.strip():
            logger.warning("Konten teks kosong setelah diproses.")
            return jsonify({"error": "Konten teks kosong."}), 400

        logger.info("Membuat dokumen DOCX...")
        document = Document()
        for line in text_content.splitlines():
            document.add_paragraph(line)

        file_stream = io.BytesIO()
        document.save(file_stream)
        file_stream.seek(0)
        output_filename = f"{filename_base}.docx"

        logger.info(f"Konversi sukses, mengirim file: {output_filename}")
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        logger.error(f"Error besar di /api/convert-txt-to-docx: {str(e)}")
        logger.error(traceback.format_exc()) # Cetak traceback lengkap ke log Vercel
        return jsonify({"error": "Terjadi kesalahan internal di server saat konversi."}), 500

# Bagian ini TIDAK akan dijalankan oleh Vercel, tapi berguna untuk tes lokal jika Anda mau.
# if __name__ == "__main__":
#     # Untuk tes lokal, pastikan Flask-CORS mengizinkan origin dari server tes frontend Anda
#     # misalnya, jika frontend tes lokal berjalan di port 8000:
#     # CORS(app, resources={r"/api/*": {"origins": "http://localhost:8000"}})
#     app.run(host='127.0.0.1', port=5001, debug=True)
