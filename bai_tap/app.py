from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    ket_qua = None

    if request.method == "POST":
        so1 = int(request.form["so1"])
        so2 = int(request.form["so2"])
        phep_tinh = request.form["phep_tinh"]

        if phep_tinh == "tong":
            ket_qua = so1 + so2

        elif phep_tinh == "hieu":
            ket_qua = so1 - so2

        elif phep_tinh == "tich":
            ket_qua = so1 * so2

        elif phep_tinh == "thuong":
            if so2 != 0:
                ket_qua = so1 / so2
            else:
                ket_qua = "Không thể chia cho 0"

    return render_template("math.html", ket_qua=ket_qua)


if __name__ == "__main__":
    app.run(debug=True)