from flask import Flask, render_template, request, jsonify
import os
import base64
import anthropic

app = Flask(__name__, template_folder='.', static_folder='static')

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Inisialisasi Anthropic client
# Simpan API key di environment variable: ANTHROPIC_API_KEY
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


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
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

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

    # Prompt ke Claude
    prompt = f"""Kamu adalah pakar pertanian dan penyakit tanaman.
Analisis foto tanaman berikut dan berikan diagnosis penyakit secara akurat.

Data lingkungan:
- Jenis tanaman : {tanaman}
- Iklim         : {iklim}
- Suhu          : {suhu}°C
- Kelembaban    : {kelembaban}%
- Lokasi        : {lokasi}

Berikan respons HANYA dalam format JSON berikut, tanpa teks tambahan apapun:
{{
  "penyakit": "nama penyakit yang terdeteksi (atau 'Sehat' jika tidak ada penyakit)",
  "solusi": "langkah penanganan yang disarankan secara singkat dan jelas"
}}"""

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        # Parse JSON dari respons Claude
        import json
        raw = message.content[0].text.strip()
        # Bersihkan jika ada markdown code block
        raw = raw.replace("```json", "").replace("```", "").strip()
        hasil_ai = json.loads(raw)

        hasil = {
            "tanaman":  tanaman,
            "penyakit": hasil_ai.get("penyakit", "Tidak terdeteksi"),
            "solusi":   hasil_ai.get("solusi",   "Tidak ada saran tersedia"),
        }

    except json.JSONDecodeError:
        # Jika Claude tidak mengembalikan JSON murni, tampilkan teks biasa
        hasil = {
            "tanaman":  tanaman,
            "penyakit": "Lihat detail di bawah",
            "solusi":   message.content[0].text.strip(),
        }
    except Exception as e:
        return jsonify({"error": f"Gagal menganalisis: {str(e)}"}), 500

    return jsonify(hasil)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)