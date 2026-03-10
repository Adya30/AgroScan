from flask import Flask, render_template, request, jsonify
import os
import base64
import json
import requests

app = Flask(__name__, template_folder='.', static_folder='static')

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Simpan API key di environment variable: GEMINI_API_KEY
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCX00bvIMfybkZwrxZjRFA0kHw2ygNFX_U")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    tanaman    = request.form.get("tanaman", "")
    iklim      = request.form.get("iklim", "")
    suhu       = request.form.get("suhu", "")
    kelembaban = request.form.get("kelembaban", "")
    lokasi     = request.form.get("lokasi", "")

    file = request.files.get("gambar")

    if not file or not file.filename:
        return jsonify({"error": "Foto tanaman wajib diupload."}), 400

    # Simpan file
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Baca gambar dan encode ke base64
    with open(filepath, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Deteksi media type
    ext = file.filename.rsplit(".", 1)[-1].lower()
    media_type_map = {
        "jpg":  "image/jpeg",
        "jpeg": "image/jpeg",
        "png":  "image/png",
        "webp": "image/webp",
        "gif":  "image/gif",
    }
    media_type = media_type_map.get(ext, "image/jpeg")

    # Prompt ke Gemini
    prompt = f"""Kamu adalah pakar pertanian dan penyakit tanaman.
Analisis foto tanaman berikut dan berikan diagnosis penyakit secara akurat.

Data lingkungan:
- Jenis tanaman : {tanaman}
- Iklim         : {iklim}
- Suhu          : {suhu}°C
- Kelembaban    : {kelembaban}%
- Lokasi        : {lokasi}

Berikan respons HANYA dalam format JSON berikut, tanpa teks tambahan, tanpa markdown:
{{
  "penyakit": "nama penyakit yang terdeteksi (atau 'Sehat' jika tidak ada penyakit)",
  "solusi": "langkah penanganan yang disarankan secara singkat dan jelas"
}}"""

    # Request ke Gemini API
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 512
        }
    }

    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=30)
        response.raise_for_status()

        result    = response.json()
        raw_text  = result["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Bersihkan jika ada markdown code block
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        hasil_ai = json.loads(raw_text)

        hasil = {
            "tanaman":  tanaman,
            "penyakit": hasil_ai.get("penyakit", "Tidak terdeteksi"),
            "solusi":   hasil_ai.get("solusi",   "Tidak ada saran tersedia"),
        }

    except json.JSONDecodeError:
        # Jika tidak JSON murni, tampilkan teks langsung
        hasil = {
            "tanaman":  tanaman,
            "penyakit": "Lihat detail",
            "solusi":   raw_text,
        }
    except Exception as e:
        return jsonify({"error": f"Gagal menganalisis: {str(e)}"}), 500

    return jsonify(hasil)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)