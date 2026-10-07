### 1. Kết quả flask --app sodiem routes , phải có 10
dòng (kể cả static )
Endpoint            Methods           Rule
------------------  ----------------  ------------------------------------
export_csv          GET               /students/<mssv>/export
home                GET               /
score_api           DELETE, GET, PUT  /api/students/<mssv>/scores/<course>
search              GET               /search
static              GET               /static/<path:filename>
student_api_detail  GET               /api/students/<mssv>
student_api_list    GET               /api/students
student_detail      GET               /students/<mssv>
student_list        GET               /students
student_shortcut    GET               /sv/<mssv>

### 2. Dòng trạng thái và body (hoặc header quan trọng)
của từng lệnh curl

Kết quả kiểm thử bằng curl

### 2.1. Redirect URL rút gọn

**Lệnh:**

```bash
curl.exe -i "$B/sv/23T1020001"
```

**Kết quả:**

```text
HTTP/1.1 301 MOVED PERMANENTLY
Content-Type: text/html; charset=utf-8
Location: /students/23T1020001
```

**Body:**

```html
<!doctype html>
<html lang=en>
<title>Redirecting...</title>
<h1>Redirecting...</h1>
<p>You should be redirected automatically to the target URL: <a href="/students/23T1020001">/students/23T1020001</a>. If not, click the link.
```

---

### 2.2. Xuất bảng điểm CSV

**Lệnh:**

```bash
curl.exe -i "$B/students/23T1020001/export"
```

**Kết quả:**

```text
HTTP/1.1 200 OK
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename=diem_23T1020001.csv
```

**Body:**

```text
hoc_phan,diem
PMMNM,8.5
CSDL,7.0
MMT,9.0
```

---

### 2.3. Lọc sinh viên theo lớp và điểm trung bình

**Lệnh:**

```bash
curl.exe "$B/api/students?lop=k47a&min_avg=7"
```

**Kết quả:**

```text
HTTP/1.1 200 OK
```

**Body:**

```json
[
  {
    "average": 8.17,
    "lop": "K47A",
    "mssv": "23T1020001",
    "name": "Nguyễn Văn An",
    "rank": "Khá",
    "scores": {
      "CSDL": 7.0,
      "MMT": 9.0,
      "PMMNM": 8.5
    }
  }
]
```

---

### 2.4. Tham số min_avg không hợp lệ

**Lệnh:**

```bash
curl.exe -i "$B/api/students?min_avg=abc"
```

**Kết quả:**

```text
HTTP/1.1 400 BAD REQUEST
Content-Type: application/json
```

**Body:**

```json
{
  "detail": "min_avg phải là một số.",
  "error": "Dữ liệu không hợp lệ"
}
```

---

### 2.5. Sinh viên không tồn tại

**Lệnh:**

```bash
curl.exe -i "$B/api/students/999"
```

**Kết quả:**

```text
HTTP/1.1 404 NOT FOUND
Content-Type: application/json
```

**Body:**

```json
{
  "detail": "Không có sinh viên với MSSV = 999.",
  "error": "Không tìm thấy"
}
```

---

### 2.6. Thêm điểm mới

**Lệnh:**

```bash
curl.exe -i -X PUT "$S/web?score=9"
```

**Kết quả:**

```text
HTTP/1.1 201 CREATED
Content-Type: application/json
Location: /api/students/23T1020005/scores/WEB
```

**Body:**

```json
{
  "average": 9.0,
  "course": "WEB",
  "mssv": "23T1020005",
  "score": 9.0
}
```

---

### 2.7. Cập nhật điểm

**Lệnh:**

```bash
curl.exe -X PUT "$S/WEB?score=7.5"
```

**Kết quả:**

```text
HTTP/1.1 200 OK
```

**Body:**

```json
{
  "average": 7.5,
  "course": "WEB",
  "mssv": "23T1020005",
  "score": 7.5
}
```

---

### 2.8. Điểm không hợp lệ

**Lệnh:**

```bash
curl.exe -i -X PUT "$S/WEB?score=11"
```

**Kết quả:**

```text
HTTP/1.1 400 BAD REQUEST
Content-Type: application/json
```

**Body:**

```json
{
  "detail": "score phải nằm trong khoảng từ 0 đến 10.",
  "error": "Dữ liệu không hợp lệ"
}
```

---

### 2.9. Xóa điểm

**Lệnh:**

```bash
curl.exe -i -X DELETE "$S/WEB"
```

**Kết quả:**

```text
HTTP/1.1 204 NO CONTENT
```

**Body:** Không có.

---

### 2.10. POST không được hỗ trợ trên API điểm

**Lệnh:**

```bash
curl.exe -i -X POST "$S/WEB"
```

**Kết quả:**

```text
HTTP/1.1 405 METHOD NOT ALLOWED
Content-Type: application/json
```

**Body:**

```json
{
  "detail": "The method is not allowed for the requested URL.",
  "error": "Phương thức không được hỗ trợ"
}
```

---

### 2.11. POST không được hỗ trợ trên trang web

**Lệnh:**

```bash
curl.exe -i -X POST "$B/students"
```

**Kết quả:**

```text
HTTP/1.1 405 METHOD NOT ALLOWED
Content-Type: text/html; charset=utf-8
```

**Body:**

```html
<!doctype html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Phương thức không được hỗ trợ - Sổ điểm</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 30px auto;
            padding: 0 20px;
            line-height: 1.6;
        }

        nav {
            margin-bottom: 25px;
            padding: 12px;
            background: #f2f2f2;
        }

        nav a {
            margin-right: 20px;
            text-decoration: none;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }

        th, td {
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
        }

        th {
            background: #eee;
        }

        .filter {
            margin: 15px 0;
        }
    </style>
</head>

<body>

<nav>
    <a href="/">Trang chủ</a>
    <a href="/students">Sinh viên</a>
    <a href="/search">Tìm kiếm sinh viên</a>
</nav>


    <h1>405 - Phương thức không được hỗ trợ</h1>

    <p>The method is not allowed for the requested URL.</p>


</body>
</html>
```
## 3. Trả lời ngắn

### Câu 1: Vì sao Câu 4 dùng 301 còn Câu 8 trả 201 kèm Location?

* **Câu 4 dùng HTTP 301** vì `/sv/<mssv>` chỉ là URL rút gọn và được chuyển hướng vĩnh viễn sang URL chính `/students/<mssv>`. Mã 301 cho biết tài nguyên đã được chuyển sang địa chỉ mới một cách lâu dài.
* **Câu 8 trả HTTP 201 Created** vì thao tác PUT đã tạo một điểm mới cho sinh viên. Header **Location** cho biết URL của tài nguyên điểm vừa được tạo: `/api/students/23T1020005/scores/WEB`.
* Nếu điểm đã tồn tại và chỉ được cập nhật thì API trả **200 OK**.

### Câu 2: Thêm điểm cho `23T1020005` rồi khởi động lại server, điểm đó còn không? Vì sao?

**Không còn.**

Dữ liệu sinh viên và điểm đang được lưu trong biến `STUDENTS` dưới dạng **dictionary trong bộ nhớ RAM của chương trình Python**. Khi khởi động lại Flask server, chương trình chạy lại từ đầu và `STUDENTS` được tạo lại theo dữ liệu ban đầu.

Ứng dụng chưa sử dụng cơ sở dữ liệu hoặc file để lưu dữ liệu lâu dài nên các điểm được thêm bằng API sẽ **mất sau khi server khởi động lại**.
