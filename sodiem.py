from flask import Flask, request, redirect, url_for, abort, make_response, jsonify
from markupsafe import escape

app = Flask(__name__)
app.json.ensure_ascii = False
STUDENTS = {
    "23T1020001": {
        "name": "Nguyễn Văn An",
        "lop": "K47A",
        "scores": {
            "PMMNM": 8.5,
            "CSDL": 7.0,
            "MMT": 9.0
        }
    },
    "23T1020002": {
        "name": "Trần Thị Bình",
        "lop": "K47A",
        "scores": {
            "PMMNM": 6.0,
            "CSDL": 5.5,
            "MMT": 7.0
        }
    },
    "23T1020003": {
        "name": "Lê Hoàng Cường",
        "lop": "K47B",
        "scores": {
            "PMMNM": 9.5,
            "CSDL": 9.0
        }
    },
    "23T1020004": {
        "name": "Phạm Minh Dũng",
        "lop": "K47B",
        "scores": {
            "PMMNM": 4.0,
            "CSDL": 3.5,
            "MMT": 5.0
        }
    },
    "23T1020005": {
        "name": "Hoàng Thu Hà",
        "lop": "K47A",
        "scores": {}
    },
    "23T1020006": {
        "name": "Võ Quốc Khánh",
        "lop": "K47C",
        "scores": {
            "PMMNM": 7.5,
            "MMT": 8.0
        }
    }
}

def average(scores):
    """
    Tính điểm trung bình cộng.

    - Nếu scores rỗng -> None
    - Nếu có điểm -> trung bình, làm tròn 2 chữ số
    """
    if not scores:
        return None

    return round(sum(scores.values()) / len(scores), 2)

def rank(avg):
    """
    Xếp loại dựa trên điểm trung bình.
    """
    if avg is None:
        return "Chưa có điểm"

    if avg >= 8.5:
        return "Giỏi"

    if avg >= 7.0:
        return "Khá"

    if avg >= 5.0:
        return "Trung bình"

    return "Yếu"
def student_summary(mssv):
    """
    Tạo dictionary thông tin tổng hợp của một sinh viên.
    """
    student = STUDENTS[mssv]

    avg = average(student["scores"])

    return {
        "mssv": mssv,
        "name": student["name"],
        "lop": student["lop"],
        "scores": student["scores"],
        "average": avg,
        "rank": rank(avg)
    }
def layout(title, body):
    """
    Tạo một trang HTML hoàn chỉnh.

    title được escape() vì title là dữ liệu được chèn vào HTML.

    body được chèn nguyên văn theo yêu cầu đề bài.
    """

    safe_title = escape(title)

    return f"""<!doctype html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>{safe_title} - Sổ điểm</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 30px auto;
            padding: 0 20px;
            line-height: 1.6;
        }}

        nav {{
            margin-bottom: 25px;
            padding: 12px;
            background: #f2f2f2;
        }}

        nav a {{
            margin-right: 20px;
            text-decoration: none;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }}

        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
        }}

        th {{
            background: #eee;
        }}

        .filter {{
            margin: 15px 0;
        }}
    </style>
</head>

<body>

<nav>
    <a href="{url_for('home')}">Trang chủ</a>
    <a href="{url_for('student_list')}">Sinh viên</a>
    <a href="{url_for('search')}">Tìm kiếm sinh viên</a>
</nav>

{body}

</body>
</html>"""
@app.route("/")
def home():
    return layout(
        "Trang chủ",
        "<h1>Sổ điểm</h1><p>Đang xây dựng...</p>"
    )
@app.route("/students")
def student_list():
    return layout(
        "Danh sách sinh viên",
        "<h1>Danh sách sinh viên</h1><p>Đang xây dựng...</p>"
    )
@app.route("/search")
def search():
    return layout(
        "Tìm kiếm sinh viên",
        "<h1>Tìm kiếm sinh viên</h1><p>Đang xây dựng...</p>"
    )
if __name__ == "__main__":
    app.run(debug=True, port=8000)