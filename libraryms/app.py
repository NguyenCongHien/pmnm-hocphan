from flask import Flask, request, render_template, url_for, jsonify, abort

app = Flask(__name__)


BOOKS = [
    {
        "id": 1,
        "title": "Lập trình Python",
        "author": "Nguyễn Văn A",
        "year": 2023,
        "category": "Lập trình",
        "available": True
    },
    {
        "id": 2,
        "title": "Flask cơ bản",
        "author": "Trần Văn B",
        "year": 2024,
        "category": "Lập trình",
        "available": True
    },
    {
        "id": 3,
        "title": "Cơ sở dữ liệu",
        "author": "Lê Văn C",
        "year": 2022,
        "category": "Cơ sở dữ liệu",
        "available": False
    },
    {
        "id": 4,
        "title": "HTML và CSS",
        "author": "Phạm Văn D",
        "year": 2021,
        "category": "Web",
        "available": True
    },
    {
        "id": 5,
        "title": "JavaScript cơ bản",
        "author": "Hoàng Văn E",
        "year": 2023,
        "category": "Web",
        "available": False
    },
    {
        "id": 6,
        "title": "Git và GitHub",
        "author": "Nguyễn Văn F",
        "year": 2024,
        "category": "Công cụ",
        "available": True
    }
]


@app.route("/")
def index():
    total_books = len(BOOKS)

    available_books = sum(
        1 for book in BOOKS
        if book["available"]
    )

    return render_template(
        "index.html",
        total_books=total_books,
        available_books=available_books
    )


@app.route("/books")
def books():
    category = request.args.get("category")

    if category:
        filtered_books = [
            book for book in BOOKS
            if book["category"] == category
        ]
    else:
        filtered_books = BOOKS

    categories = sorted(
        set(book["category"] for book in BOOKS)
    )

    return render_template(
        "books.html",
        books=filtered_books,
        categories=categories,
        current_category=category
    )


@app.route("/books/<int:book_id>")
def book_detail(book_id):
    book = next(
        (book for book in BOOKS if book["id"] == book_id),
        None
    )

    if book is None:
        abort(
            404,
            description=f"Không có sách với ID = {book_id}"
        )

    return render_template(
        "book_detail.html",
        book=book
    )


@app.route("/api/books")
def api_books():
    return jsonify(BOOKS)


@app.route("/api/books/<int:book_id>")
def api_book_detail(book_id):
    book = next(
        (book for book in BOOKS if book["id"] == book_id),
        None
    )

    if book is None:
        return jsonify({
            "error": f"Không có sách với ID = {book_id}"
        }), 404

    return jsonify(book)


@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        "404.html",
        error=error
    ), 404


if __name__ == "__main__":
    app.run(
        debug=True
    )