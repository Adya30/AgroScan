from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__, template_folder='.', static_folder='.')

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/style.css")
def style():
    return app.send_static_file("style.css")


@app.route("/predict", methods=["POST"])
def predict():
    tanaman    = request.form.get("tanaman", "")
    iklim      = request.form.get("iklim", "")
    suhu       = request.form.get("suhu", "")
    kelembaban = request.form.get("kelembaban", "")
    lokasi     = request.form.get("lokasi", "")

    file = request.files.get("gambar")
    if file and file.filename:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

    # --- Ganti bagian ini dengan model AI Anda ---
    hasil = {
        "tanaman":  tanaman,
        "penyakit": "Bercak Daun",
        "solusi":   "Gunakan fungisida dan kurangi kelembaban tinggi"
    }
    # ----------------------------------------------

    return jsonify(hasil)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)