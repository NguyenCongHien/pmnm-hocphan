
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    a = ""
    b = ""
    op = "+"
    result = None

    error_a = ""
    error_b = ""
    error_op = ""

    if request.method == "POST":
        # Nhận dữ liệu từ form
        a = request.form.get("a", "").strip()
        b = request.form.get("b", "").strip()
        op = request.form.get("op", "+")

        # Kiểm tra và chuyển đổi số thứ nhất
        try:
            number_a = float(a.replace(",", "."))
        except ValueError:
            error_a = "Vui lòng nhập một số."

        # Kiểm tra và chuyển đổi số thứ hai
        try:
            number_b = float(b.replace(",", "."))
        except ValueError:
            error_b = "Vui lòng nhập một số."

        # Kiểm tra phép toán gửi lên server
        if op not in ["+", "-", "*", "/"]:
            error_op = "Phép toán không hợp lệ."

        # Chỉ thực hiện phép tính nếu các ô hợp lệ
        if not error_a and not error_b and not error_op:
            if op == "+":
                result = number_a + number_b
            elif op == "-":
                result = number_a - number_b
            elif op == "*":
                result = number_a * number_b
            elif op == "/":
                if number_b == 0:
                    error_b = "Không thể chia cho 0."
                else:
                    result = number_a / number_b

    return render_template(
        "calculator.html",
        a=a,
        b=b,
        op=op,
        result=result,
        error_a=error_a,
        error_b=error_b,
        error_op=error_op
    )

# Hàm kiểm tra điểm dùng chung cho cả 3 ô
def kiem_tra_diem(du_lieu):
    # Kiểm tra người dùng có để trống không
    if not du_lieu:
        return None, "Vui lòng nhập điểm."

    try:
        # Chấp nhận dấu phẩy thập phân, ví dụ 7,5
        diem = float(du_lieu.replace(",", "."))
    except ValueError:
        return None, "Vui lòng nhập một số."

    # Điểm phải nằm trong khoảng 0 đến 10
    if diem < 0 or diem > 10:
        return None, "Điểm phải từ 0 đến 10."

    return diem, ""


# Route tính điểm học phần
@app.route("/grade", methods=["GET", "POST"])
def grade():
    # Giá trị ban đầu của 3 ô điểm
    cc = ""
    gk = ""
    ck = ""

    # Thông báo lỗi riêng cho từng ô
    error_cc = ""
    error_gk = ""
    error_ck = ""

    # Kết quả ban đầu chưa có
    diem_hp = None
    diem_chu = None

    if request.method == "POST":
        # Lấy dữ liệu từ form
        cc = request.form.get("cc", "").strip()
        gk = request.form.get("gk", "").strip()
        ck = request.form.get("ck", "").strip()

        # Gọi cùng một hàm kiểm tra cho cả 3 ô
        diem_cc, error_cc = kiem_tra_diem(cc)
        diem_gk, error_gk = kiem_tra_diem(gk)
        diem_ck, error_ck = kiem_tra_diem(ck)

        # Chỉ tính điểm khi cả 3 ô đều hợp lệ
        if not error_cc and not error_gk and not error_ck:
            # Tính điểm học phần
            diem_hp = round(
                diem_cc * 0.1
                + diem_gk * 0.3
                + diem_ck * 0.6,
                1
            )

            # Cuối kỳ dưới 1 là điểm liệt
            if diem_ck < 1:
                diem_chu = "F"
            elif diem_hp >= 8.5:
                diem_chu = "A"
            elif diem_hp >= 7.0:
                diem_chu = "B"
            elif diem_hp >= 5.5:
                diem_chu = "C"
            elif diem_hp >= 4.0:
                diem_chu = "D"
            else:
                diem_chu = "F"

    return render_template(
        "grade.html",
        cc=cc,
        gk=gk,
        ck=ck,
        error_cc=error_cc,
        error_gk=error_gk,
        error_ck=error_ck,
        diem_hp=diem_hp,
        diem_chu=diem_chu
    )


# Hàm kiểm tra dữ liệu số dùng chung
def kiem_tra_khoang(du_lieu, ten_loai, gia_tri_min, gia_tri_max):
    # Kiểm tra dữ liệu rỗng
    if not du_lieu:
        return None, "Vui lòng nhập một số."

    try:
        # Chấp nhận dấu phẩy thập phân, ví dụ 65,5
        gia_tri = float(du_lieu.replace(",", "."))
    except ValueError:
        return None, "Vui lòng nhập một số."

    # Kiểm tra giá trị nằm trong khoảng cho phép
    if gia_tri < gia_tri_min or gia_tri > gia_tri_max:
        return None, f"Giá trị phải từ {gia_tri_min} đến {gia_tri_max}."

    return gia_tri, ""


# Route tính chỉ số BMI
@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    # Giá trị ban đầu
    chieu_cao = ""
    can_nang = ""

    # Lỗi riêng của từng ô
    error_chieu_cao = ""
    error_can_nang = ""

    # Kết quả ban đầu chưa có
    chi_so_bmi = None
    phan_loai = ""
    mau_ket_qua = ""
    can_nang_min = None
    can_nang_max = None

    if request.method == "POST":
        # Lấy dữ liệu từ form
        chieu_cao = request.form.get("chieu_cao", "").strip()
        can_nang = request.form.get("can_nang", "").strip()

        # Kiểm tra chiều cao: 50–250 cm
        cao, error_chieu_cao = kiem_tra_khoang(
            chieu_cao, "chiều cao", 50, 250
        )

        # Kiểm tra cân nặng: 10–300 kg
        nang, error_can_nang = kiem_tra_khoang(
            can_nang, "cân nặng", 10, 300
        )

        # Chỉ tính khi cả hai dữ liệu hợp lệ
        if not error_chieu_cao and not error_can_nang:
            # Đổi chiều cao từ cm sang mét
            chieu_cao_m = cao / 100

            # Tính BMI và làm tròn 1 chữ số
            chi_so_bmi = round(nang / (chieu_cao_m ** 2), 1)

            # Phân loại và chọn màu kết quả
            if chi_so_bmi < 18.5:
                phan_loai = "Thiếu cân"
                mau_ket_qua = "warning"
            elif chi_so_bmi < 23:
                phan_loai = "Bình thường"
                mau_ket_qua = "success"
            elif chi_so_bmi < 25:
                phan_loai = "Thừa cân"
                mau_ket_qua = "warning"
            else:
                phan_loai = "Béo phì"
                mau_ket_qua = "danger"

            # Tính khoảng cân nặng tương ứng BMI 18,5–22,9
            can_nang_min = round(18.5 * (chieu_cao_m ** 2), 1)
            can_nang_max = round(22.9 * (chieu_cao_m ** 2), 1)

    return render_template(
        "bmi.html",
        chieu_cao=chieu_cao,
        can_nang=can_nang,
        error_chieu_cao=error_chieu_cao,
        error_can_nang=error_can_nang,
        chi_so_bmi=chi_so_bmi,
        phan_loai=phan_loai,
        mau_ket_qua=mau_ket_qua,
        can_nang_min=can_nang_min,
        can_nang_max=can_nang_max
    )

if __name__ == "__main__":
    app.run(debug=True)
