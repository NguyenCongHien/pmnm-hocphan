
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Text, Integer, Float, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.exc import IntegrityError


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)

app.config["SECRET_KEY"] = "secret-key-quan-ly-sach"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"

db.init_app(app)


class Category(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    books: Mapped[list["Book"]] = relationship(
        back_populates="category"
    )


class Book(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id"),
        nullable=False
    )

    category: Mapped["Category"] = relationship(
        back_populates="books"
    )


def seed_data():
    # Kiểm tra xem đã có dữ liệu danh mục chưa
    if db.session.scalar(db.select(Category.id).limit(1)) is not None:
        return

    # Tạo danh mục mẫu
    cong_nghe = Category(
        name="Công nghệ thông tin",
        description="Sách về lập trình và công nghệ"
    )

    kinh_te = Category(
        name="Kinh tế",
        description="Sách về kinh tế và kinh doanh"
    )

    van_hoc = Category(
        name="Văn học",
        description="Sách văn học trong và ngoài nước"
    )

    db.session.add_all([cong_nghe, kinh_te, van_hoc])
    db.session.flush()

    # Tạo sách mẫu
    books = [
        Book(
            title="Python cơ bản",
            author="Nguyễn Văn A",
            price=120000,
            quantity=10,
            category_id=cong_nghe.id
        ),
        Book(
            title="Java nâng cao",
            author="Trần Văn B",
            price=150000,
            quantity=8,
            category_id=cong_nghe.id
        ),
        Book(
            title="Kinh tế học đại cương",
            author="Lê Văn C",
            price=100000,
            quantity=15,
            category_id=kinh_te.id
        ),
        Book(
            title="Truyện Kiều",
            author="Nguyễn Du",
            price=80000,
            quantity=20,
            category_id=van_hoc.id
        )
    ]

    db.session.add_all(books)
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_data()


@app.route("/")
@app.route("/dashboard")
def dashboard():
    total_categories = db.session.scalar(
        db.select(func.count(Category.id))
    )

    total_books = db.session.scalar(
        db.select(func.count(Book.id))
    )

    total_quantity = db.session.scalar(
        db.select(func.sum(Book.quantity))
    ) or 0

    category_stats = db.session.execute(
        db.select(
            Category.name,
            func.count(Book.id)
        )
        .outerjoin(Book)
        .group_by(Category.id)
        .order_by(Category.name)
    ).all()

    latest_books = db.session.execute(
        db.select(Book)
        .order_by(Book.id.desc())
        .limit(5)
    ).scalars().all()

    return render_template(
        "dashboard.html",
        total_categories=total_categories,
        total_books=total_books,
        total_quantity=total_quantity,
        category_stats=category_stats,
        latest_books=latest_books
    )


@app.route("/categories")
def categories():
    category_list = db.session.execute(
        db.select(Category).order_by(Category.id.desc())
    ).scalars().all()

    return render_template(
        "categories/list.html",
        categories=category_list
    )


@app.route("/categories/add", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Vui lòng nhập tên danh mục.", "danger")
            return redirect(url_for("add_category"))

        category = Category(
            name=name,
            description=description
        )

        db.session.add(category)

        try:
            db.session.commit()
            flash("Thêm danh mục thành công.", "success")
            return redirect(url_for("categories"))
        except IntegrityError:
            db.session.rollback()
            flash("Tên danh mục đã tồn tại.", "danger")

    return render_template("categories/add.html")


@app.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    category = db.session.get(Category, category_id)

    if category is None:
        flash("Không tìm thấy danh mục.", "danger")
        return redirect(url_for("categories"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Vui lòng nhập tên danh mục.", "danger")
            return redirect(url_for("edit_category", category_id=category_id))

        category.name = name
        category.description = description

        try:
            db.session.commit()
            flash("Cập nhật danh mục thành công.", "success")
            return redirect(url_for("categories"))
        except IntegrityError:
            db.session.rollback()
            flash("Tên danh mục đã tồn tại.", "danger")

    return render_template(
        "categories/edit.html",
        category=category
    )


@app.route("/categories/delete/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    category = db.session.get(Category, category_id)

    if category is None:
        flash("Không tìm thấy danh mục.", "danger")
        return redirect(url_for("categories"))

    if category.books:
        flash(
            "Không thể xóa danh mục đang có sách. "
            "Hãy chuyển hoặc xóa sách trước.",
            "warning"
        )
        return redirect(url_for("categories"))

    db.session.delete(category)
    db.session.commit()

    flash("Xóa danh mục thành công.", "success")
    return redirect(url_for("categories"))


@app.route("/books")
def books():
    category_id = request.args.get("category_id", type=int)

    query = db.select(Book).order_by(Book.id.desc())

    selected_category = None

    if category_id is not None:
        selected_category = db.session.get(Category, category_id)

        if selected_category is None:
            flash("Danh mục không tồn tại.", "danger")
            return redirect(url_for("books"))

        query = query.where(Book.category_id == category_id)

    book_list = db.session.execute(query).scalars().all()

    category_list = db.session.execute(
        db.select(Category).order_by(Category.name)
    ).scalars().all()

    return render_template(
        "books/list.html",
        books=book_list,
        categories=category_list,
        selected_category=selected_category,
        selected_category_id=category_id
    )


@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    category_list = db.session.execute(
        db.select(Category).order_by(Category.name)
    ).scalars().all()

    if not category_list:
        flash("Hãy tạo danh mục trước khi thêm sách.", "warning")
        return redirect(url_for("categories"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        description = request.form.get("description", "").strip()

        try:
            price = float(request.form.get("price", "0"))
            quantity = int(request.form.get("quantity", "0"))
            category_id = int(request.form.get("category_id", "0"))
        except ValueError:
            flash("Giá, số lượng hoặc danh mục không hợp lệ.", "danger")
            return redirect(url_for("add_book"))

        category = db.session.get(Category, category_id)

        if not title or not author:
            flash("Vui lòng nhập tên sách và tác giả.", "danger")
            return redirect(url_for("add_book"))

        if price < 0 or quantity < 0 or category is None:
            flash("Thông tin sách không hợp lệ.", "danger")
            return redirect(url_for("add_book"))

        book = Book(
            title=title,
            author=author,
            price=price,
            quantity=quantity,
            description=description,
            category_id=category_id
        )

        db.session.add(book)
        db.session.commit()

        flash("Thêm sách thành công.", "success")
        return redirect(url_for("books"))

    return render_template(
        "books/add.html",
        categories=category_list
    )


@app.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    book = db.session.get(Book, book_id)

    if book is None:
        flash("Không tìm thấy sách.", "danger")
        return redirect(url_for("books"))

    category_list = db.session.execute(
        db.select(Category).order_by(Category.name)
    ).scalars().all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        description = request.form.get("description", "").strip()

        try:
            price = float(request.form.get("price", "0"))
            quantity = int(request.form.get("quantity", "0"))
            category_id = int(request.form.get("category_id", "0"))
        except ValueError:
            flash("Giá, số lượng hoặc danh mục không hợp lệ.", "danger")
            return redirect(url_for("edit_book", book_id=book_id))

        category = db.session.get(Category, category_id)

        if not title or not author:
            flash("Vui lòng nhập tên sách và tác giả.", "danger")
            return redirect(url_for("edit_book", book_id=book_id))

        if price < 0 or quantity < 0 or category is None:
            flash("Thông tin sách không hợp lệ.", "danger")
            return redirect(url_for("edit_book", book_id=book_id))

        book.title = title
        book.author = author
        book.price = price
        book.quantity = quantity
        book.description = description
        book.category_id = category_id

        db.session.commit()

        flash("Cập nhật sách thành công.", "success")
        return redirect(url_for("books"))

    return render_template(
        "books/edit.html",
        book=book,
        categories=category_list
    )


@app.route("/books/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    book = db.session.get(Book, book_id)

    if book is None:
        flash("Không tìm thấy sách.", "danger")
        return redirect(url_for("books"))

    db.session.delete(book)
    db.session.commit()

    flash("Xóa sách thành công.", "success")
    return redirect(url_for("books"))


if __name__ == "__main__":
    app.run(debug=True)
