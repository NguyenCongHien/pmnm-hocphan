
from decimal import Decimal

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
)
from sqlalchemy import select, or_

from extensions import db, migrate, csrf
from models import (
    Category,
    Book,
    Customer,
    Order,
    OrderItem,
    OrderStatusHistory,
)
from forms import CheckoutForm
from sqlalchemy import select, or_, func
from datetime import datetime
import os
import uuid

from decimal import Decimal, InvalidOperation
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy import select, or_, func
app = Flask(__name__)

app.config["SECRET_KEY"] = "nha-sach-song-huong-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nha_sach.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)


@app.template_filter("vnd")
def vnd(value):
    if value is None:
        value = 0

    return f"{value:,.0f}".replace(",", ".") + " đ"


@app.context_processor
def inject_cart_count():
    cart = session.get("cart", {})

    cart_count = sum(
        int(quantity)
        for quantity in cart.values()
        if str(quantity).isdigit()
    )

    pending_orders = db.session.scalar(
        select(func.count(Order.id)).where(Order.status == "Chờ xác nhận")
    ) or 0
    return {"cart_count": cart_count, "pending_orders": pending_orders}


@app.route("/")
def index():
    return redirect(url_for("books"))


# =========================
# DANH SÁCH SÁCH
# =========================

@app.route("/books")
def books():
    keyword = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()

    query = select(Book)

    # Tìm kiếm theo tên sách hoặc tên tác giả
    if keyword:
        search_keyword = f"%{keyword}%"

        query = query.where(
            or_(
                Book.title.ilike(search_keyword),
                Book.author.ilike(search_keyword),
            )
        )

    # Lọc theo thể loại
    if selected_category:
        try:
            category_id = int(selected_category)
            query = query.where(Book.category_id == category_id)
        except ValueError:
            selected_category = ""

    # Lấy danh sách sách mới nhất
    query = query.order_by(Book.id.desc())

    books_list = db.session.scalars(query).all()

    # Lấy tất cả thể loại trực tiếp từ database
    categories = db.session.scalars(
        select(Category).order_by(Category.name)
    ).all()

    return render_template(
        "store/books.html",
        books=books_list,
        categories=categories,
        keyword=keyword,
        selected_category=selected_category,
    )


# =========================
# CHI TIẾT SÁCH
# =========================

@app.route("/books/<int:book_id>")
def book_detail(book_id):
    book = db.get_or_404(Book, book_id)

    return render_template(
        "store/book_detail.html",
        book=book,
    )


# =========================
# THÊM VÀO GIỎ HÀNG
# =========================

@app.route("/cart/add/<int:book_id>", methods=["POST"])
def add_to_cart(book_id):
    book = db.get_or_404(Book, book_id)

    try:
        quantity = int(request.form.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        flash("Số lượng sách không hợp lệ.", "danger")
        return redirect(url_for("book_detail", book_id=book_id))

    if book.quantity <= 0:
        flash("Sách hiện đã hết hàng.", "danger")
        return redirect(url_for("book_detail", book_id=book_id))

    cart = session.get("cart", {})
    book_key = str(book_id)

    current_quantity = int(cart.get(book_key, 0))

    if current_quantity + quantity > book.quantity:
        flash(
            f"Không đủ hàng. Sách chỉ còn {book.quantity} cuốn.",
            "warning",
        )
        return redirect(url_for("book_detail", book_id=book_id))

    cart[book_key] = current_quantity + quantity

    session["cart"] = cart
    session.modified = True

    flash(f"Đã thêm {book.title} vào giỏ hàng.", "success")

    return redirect(
        request.referrer or url_for("books")
    )


# =========================
# GIỎ HÀNG
# =========================


@app.route("/cart")
def cart():
    cart_data = session.get("cart", {})

    items = []
    subtotal = Decimal("0")

    for book_id, quantity in list(cart_data.items()):
        try:
            book = db.session.get(Book, int(book_id))
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if book is None or quantity <= 0:
            continue

        line_total = book.price * quantity
        subtotal += line_total

        items.append({
            "book": book,
            "quantity": quantity,
            "line_total": line_total,
        })

    total = subtotal

    return render_template(
        "store/cart.html",
        items=items,
        cart_items=items,
        subtotal=subtotal,
        total=total,
    )



@app.route("/cart/update/<int:book_id>", methods=["POST"])
def cart_update(book_id):
    cart_data = session.get("cart", {})
    book_key = str(book_id)

    if book_key not in cart_data:
        flash("Sách không có trong giỏ hàng.", "warning")
        return redirect(url_for("cart"))

    book = db.session.get(Book, book_id)

    if book is None:
        cart_data.pop(book_key, None)
        session["cart"] = cart_data
        session.modified = True

        flash("Sách không còn tồn tại.", "warning")
        return redirect(url_for("cart"))

    action = request.form.get("action", "")

    current_quantity = int(cart_data.get(book_key, 0))

    if action == "increase":
        if current_quantity + 1 > book.quantity:
            flash("Số lượng trong kho không đủ.", "warning")
        else:
            cart_data[book_key] = current_quantity + 1

    elif action == "decrease":
        new_quantity = current_quantity - 1

        if new_quantity <= 0:
            cart_data.pop(book_key, None)
        else:
            cart_data[book_key] = new_quantity

    else:
        try:
            new_quantity = int(request.form.get("quantity", current_quantity))

            if new_quantity <= 0:
                cart_data.pop(book_key, None)
            elif new_quantity > book.quantity:
                flash("Số lượng vượt quá số sách trong kho.", "warning")
            else:
                cart_data[book_key] = new_quantity

        except (TypeError, ValueError):
            flash("Số lượng không hợp lệ.", "danger")

    session["cart"] = cart_data
    session.modified = True

    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:book_id>", methods=["POST"])
def cart_remove(book_id):
    cart_data = session.get("cart", {})

    cart_data.pop(str(book_id), None)

    session["cart"] = cart_data
    session.modified = True

    flash("Đã xóa sách khỏi giỏ hàng.", "success")

    return redirect(url_for("cart"))


@app.route("/cart/clear", methods=["POST"])
def cart_clear():
    session["cart"] = {}
    session.modified = True

    flash("Đã xóa toàn bộ giỏ hàng.", "success")

    return redirect(url_for("cart"))


# =========================
# THANH TOÁN
# =========================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart_data = session.get("cart", {})

    if not cart_data:
        flash("Giỏ hàng đang trống, vui lòng chọn sách trước.", "warning")
        return redirect(url_for("cart"))

    items = []
    subtotal = Decimal("0")

    for book_id, quantity in list(cart_data.items()):
        try:
            book = db.session.get(Book, int(book_id))
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if book is None or quantity <= 0:
            continue

        line_total = book.price * quantity
        subtotal += line_total

        items.append({
            "book": book,
            "quantity": quantity,
            "line_total": line_total,
        })

    if not items:
        session["cart"] = {}
        session.modified = True

        flash("Không có sách hợp lệ trong giỏ hàng.", "warning")
        return redirect(url_for("cart"))

    shipping_fee = (
        Decimal("0")
        if subtotal >= Decimal("200000")
        else Decimal("20000")
    )

    total = subtotal + shipping_fee

    form = CheckoutForm()

    if form.validate_on_submit():

        # Kiểm tra lại tồn kho trước khi tạo đơn hàng
        insufficient_books = []

        for item in items:
            book = item["book"]
            quantity = item["quantity"]

            if book.quantity < quantity:
                insufficient_books.append(
                    f"{book.title} (còn {book.quantity} cuốn)"
                )

        if insufficient_books:
            flash(
                "Không đủ hàng trong kho: "
                + ", ".join(insufficient_books),
                "danger",
            )
            return redirect(url_for("cart"))

        try:
            customer = Customer(
                full_name=form.full_name.data.strip(),
                phone=form.phone.data.strip(),
                email=(form.email.data or "").strip() or None,
                address=form.address.data.strip(),
            )

            db.session.add(customer)
            db.session.flush()

            order = Order(
                customer_id=customer.id,
                status="Chờ xác nhận",
                note=(form.note.data or "").strip() or None,
                payment_method=form.payment_method.data,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total=total,
            )

            db.session.add(order)
            db.session.flush()

            for item in items:
                book = item["book"]
                quantity = item["quantity"]

                order_item = OrderItem(
                    order_id=order.id,
                    book_id=book.id,
                    quantity=quantity,
                    unit_price=book.price,
                )

                db.session.add(order_item)

                book.quantity -= quantity

            history = OrderStatusHistory(
                order_id=order.id,
                status="Chờ xác nhận",
            )

            db.session.add(history)

            db.session.commit()

            order_id = order.id

            session["cart"] = {}
            session.modified = True

            flash("Đặt hàng thành công!", "success")

            return redirect(
                url_for("order_success", order_id=order_id)
            )

        except Exception:
            db.session.rollback()

            flash(
                "Có lỗi xảy ra khi đặt hàng. Vui lòng thử lại.",
                "danger",
            )

            return redirect(url_for("checkout"))

    return render_template(
        "store/checkout.html",
        form=form,
        items=items,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total=total,
    )


# =========================
# ĐẶT HÀNG THÀNH CÔNG
# =========================

@app.route("/orders/<int:order_id>")
def order_success(order_id):
    order = db.get_or_404(Order, order_id)

    return render_template(
        "store/order_success.html",
        order=order,
    )


# =========================
# TRANG QUẢN TRỊ - TỔNG QUAN
# =========================

@app.route("/admin")
def admin_dashboard():
    now = datetime.now()

    month_start = now.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if now.month == 12:
        next_month = month_start.replace(
            year=now.year + 1,
            month=1,
        )
    else:
        next_month = month_start.replace(
            month=now.month + 1,
        )

    # Tổng số sách
    book_count = db.session.scalar(
        select(func.count(Book.id))
    ) or 0

    # Số đơn đang chờ xác nhận
    pending_orders = db.session.scalar(
        select(func.count(Order.id)).where(
            Order.status == "Chờ xác nhận"
        )
    ) or 0

    # Doanh thu tháng: chỉ tính đơn đã hoàn tất
    monthly_revenue = db.session.scalar(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.status == "Hoàn tất",
            Order.created_at >= month_start,
            Order.created_at < next_month,
        )
    ) or Decimal("0")

    # Số sách sắp hết hàng: tồn kho từ 0 đến 5
    low_stock_count = db.session.scalar(
        select(func.count(Book.id)).where(
            Book.quantity <= 5
        )
    ) or 0

    # 5 đơn hàng mới nhất
    latest_orders = db.session.scalars(
        select(Order)
        .order_by(Order.created_at.desc())
        .limit(5)
    ).all()

    # Danh sách sách sắp hết hàng
    low_stock_books = db.session.scalars(
        select(Book)
        .where(Book.quantity <= 5)
        .order_by(Book.quantity.asc(), Book.title.asc())
        .limit(10)
    ).all()

    return render_template(
        "admin/dashboard.html",
        book_count=book_count,
        pending_orders=pending_orders,
        monthly_revenue=monthly_revenue,
        low_stock_count=low_stock_count,
        latest_orders=latest_orders,
        low_stock_books=low_stock_books,
        month_label=now.month,
    )

# =========================
# QUẢN LÝ SÁCH - DANH SÁCH
# =========================

@app.route("/admin/books")
def admin_books():
    keyword = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()
    stock_filter = request.args.get("stock", "").strip()

    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            page = 1
    except (TypeError, ValueError):
        page = 1

    query = select(Book)

    # Tìm kiếm tên sách hoặc tác giả
    if keyword:
        search_keyword = f"%{keyword}%"

        query = query.where(
            or_(
                Book.title.ilike(search_keyword),
                Book.author.ilike(search_keyword),
            )
        )

    # Lọc theo thể loại
    if selected_category:
        try:
            category_id = int(selected_category)
            query = query.where(Book.category_id == category_id)
        except ValueError:
            selected_category = ""

    # Lọc theo tồn kho
    if stock_filter == "in_stock":
        query = query.where(Book.quantity > 5)

    elif stock_filter == "low":
        query = query.where(
            Book.quantity >= 1,
            Book.quantity <= 5,
        )

    elif stock_filter == "out":
        query = query.where(Book.quantity == 0)

    # Sách mới nhất hiển thị trước
    query = query.order_by(Book.id.desc())

    # Phân trang: 5 sách mỗi trang
    pagination = db.paginate(
        query,
        page=page,
        per_page=5,
        error_out=False,
    )

    categories = db.session.scalars(
        select(Category).order_by(Category.name)
    ).all()

    return render_template(
        "admin/books.html",
        books=pagination.items,
        pagination=pagination,
        categories=categories,
        keyword=keyword,
        selected_category=selected_category,
        stock_filter=stock_filter,
    )


# =========================
# XÓA SÁCH
# =========================

@app.route("/admin/books/<int:book_id>/delete", methods=["POST"])
def admin_book_delete(book_id):
    book = db.get_or_404(Book, book_id)

    # Không cho xóa sách đã có trong đơn hàng
    if book.order_items:
        flash(
            f"Không thể xóa sách '{book.title}' vì sách đã có trong đơn hàng.",
            "danger",
        )
        return redirect(url_for("admin_books"))

    try:
        db.session.delete(book)
        db.session.commit()

        flash(
            f"Đã xóa sách '{book.title}' thành công.",
            "success",
        )

    except Exception:
        db.session.rollback()
        flash("Không thể xóa sách. Vui lòng thử lại.", "danger")

    return redirect(url_for("admin_books"))

# =========================
# HÀM HỖ TRỢ FORM SÁCH
# =========================

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024


def render_book_form(book=None, form_data=None):
    categories = db.session.scalars(
        select(Category).order_by(Category.name)
    ).all()

    return render_template(
        "admin/book_form.html",
        book=book,
        categories=categories,
        form_data=form_data or {},
    )


# =========================
# THÊM SÁCH
# =========================

@app.route("/admin/books/new", methods=["GET", "POST"])
def admin_book_create():
    if request.method == "GET":
        return render_book_form()

    form_data = request.form.to_dict()

    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    publisher = request.form.get("publisher", "").strip()
    published_year_text = request.form.get("published_year", "").strip()
    price_text = request.form.get("price", "").strip()
    quantity_text = request.form.get("quantity", "").strip()
    description = request.form.get("description", "").strip()
    category_id_text = request.form.get("category_id", "").strip()

    errors = []

    if not title:
        errors.append("Vui lòng nhập tên sách.")

    if not author:
        errors.append("Vui lòng nhập tên tác giả.")

    # Kiểm tra tên sách không trùng
    if title:
        existing_book = db.session.scalar(
            select(Book).where(func.lower(Book.title) == title.lower())
        )

        if existing_book:
            errors.append("Tên sách này đã tồn tại.")

    # Kiểm tra năm xuất bản
    published_year = None

    if published_year_text:
        try:
            published_year = int(published_year_text)
            if published_year < 1900 or published_year > datetime.now().year:
                errors.append(
                    f"Năm xuất bản phải từ 1900 đến {datetime.now().year}."
                )
        except ValueError:
            errors.append("Năm xuất bản không hợp lệ.")
    else:
        published_year = None

    # Kiểm tra giá
    price = None

    try:
        price = Decimal(price_text)

        if not price.is_finite() or price < Decimal("1000"):
            errors.append("Giá sách phải từ 1.000 đồng trở lên.")
    except (InvalidOperation, ValueError):
        errors.append("Giá sách không hợp lệ.")

    # Kiểm tra số lượng
    quantity = None

    try:
        quantity = int(quantity_text)

        if quantity < 0:
            errors.append("Số lượng sách không được âm.")
    except ValueError:
        errors.append("Số lượng sách không hợp lệ.")

    # Kiểm tra thể loại
    category = None

    try:
        category_id = int(category_id_text)
        category = db.session.get(Category, category_id)
    except (ValueError, TypeError):
        category = None

    if category is None:
        errors.append("Vui lòng chọn thể loại hợp lệ.")

    # Kiểm tra ảnh bìa
    image = request.files.get("cover_image")
    image_extension = None

    if image and image.filename:
        extension = image.filename.rsplit(".", 1)[-1].lower()

        if "." not in image.filename or extension not in ALLOWED_IMAGE_EXTENSIONS:
            errors.append("Ảnh phải có định dạng JPG, JPEG, PNG hoặc WEBP.")
        else:
            image_extension = extension

            image_data = image.read(MAX_IMAGE_SIZE + 1)
            image.seek(0)

            if len(image_data) > MAX_IMAGE_SIZE:
                errors.append("Dung lượng ảnh không được vượt quá 2MB.")

    if errors:
        for error in errors:
            flash(error, "danger")

        return render_book_form(form_data=form_data)

    # Lưu ảnh
    cover_image = None

    if image_extension:
        upload_folder = os.path.join(
            app.root_path, "static", "uploads"
        )
        os.makedirs(upload_folder, exist_ok=True)

        filename = f"{uuid.uuid4().hex}.{image_extension}"
        image.save(os.path.join(upload_folder, filename))
        cover_image = filename

    book = Book(
        title=title,
        author=author,
        publisher=publisher or None,
        published_year=published_year,
        price=price,
        quantity=quantity,
        description=description or None,
        category_id=category.id,
        cover_image=cover_image,
    )

    try:
        db.session.add(book)
        db.session.commit()

        flash("Thêm sách thành công.", "success")
        return redirect(url_for("admin_books"))

    except Exception:
        db.session.rollback()

        if cover_image:
            image_path = os.path.join(
                app.root_path, "static", "uploads", cover_image
            )
            if os.path.isfile(image_path):
                os.remove(image_path)

        flash("Không thể thêm sách. Vui lòng thử lại.", "danger")
        return render_book_form(form_data=form_data)


# =========================
# SỬA SÁCH
# =========================

@app.route("/admin/books/<int:book_id>/edit", methods=["GET", "POST"])
def admin_book_edit(book_id):
    book = db.get_or_404(Book, book_id)

    if request.method == "GET":
        form_data = {
            "title": book.title,
            "author": book.author,
            "publisher": book.publisher or "",
            "published_year": book.published_year,
            "price": book.price,
            "quantity": book.quantity,
            "description": book.description or "",
            "category_id": book.category_id,
        }

        return render_book_form(book, form_data)

    form_data = request.form.to_dict()

    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    publisher = request.form.get("publisher", "").strip()
    published_year_text = request.form.get("published_year", "").strip()
    price_text = request.form.get("price", "").strip()
    quantity_text = request.form.get("quantity", "").strip()
    description = request.form.get("description", "").strip()
    category_id_text = request.form.get("category_id", "").strip()

    errors = []

    if not title:
        errors.append("Vui lòng nhập tên sách.")

    if not author:
        errors.append("Vui lòng nhập tên tác giả.")

    # Kiểm tra tên sách trùng với sách khác
    if title:
        existing_book = db.session.scalar(
            select(Book).where(
                func.lower(Book.title) == title.lower(),
                Book.id != book.id,
            )
        )

        if existing_book:
            errors.append("Tên sách này đã tồn tại.")

    # Kiểm tra năm xuất bản
    published_year = None

    if published_year_text:
        try:
            published_year = int(published_year_text)
            if published_year < 1900 or published_year > datetime.now().year:
                errors.append(
                    f"Năm xuất bản phải từ 1900 đến {datetime.now().year}."
                )
        except ValueError:
            errors.append("Năm xuất bản không hợp lệ.")
    else:
        published_year = None

    # Kiểm tra giá
    price = None

    try:
        price = Decimal(price_text)

        if not price.is_finite() or price < Decimal("1000"):
            errors.append("Giá sách phải từ 1.000 đồng trở lên.")
    except (InvalidOperation, ValueError):
        errors.append("Giá sách không hợp lệ.")

    # Kiểm tra số lượng
    quantity = None

    try:
        quantity = int(quantity_text)

        if quantity < 0:
            errors.append("Số lượng sách không được âm.")
    except ValueError:
        errors.append("Số lượng sách không hợp lệ.")

    # Kiểm tra thể loại
    category = None

    try:
        category_id = int(category_id_text)
        category = db.session.get(Category, category_id)
    except (ValueError, TypeError):
        category = None

    if category is None:
        errors.append("Vui lòng chọn thể loại hợp lệ.")

    # Kiểm tra ảnh mới nếu có
    image = request.files.get("cover_image")
    image_extension = None

    if image and image.filename:
        extension = image.filename.rsplit(".", 1)[-1].lower()

        if "." not in image.filename or extension not in ALLOWED_IMAGE_EXTENSIONS:
            errors.append("Ảnh phải có định dạng JPG, JPEG, PNG hoặc WEBP.")
        else:
            image_extension = extension

            image_data = image.read(MAX_IMAGE_SIZE + 1)
            image.seek(0)

            if len(image_data) > MAX_IMAGE_SIZE:
                errors.append("Dung lượng ảnh không được vượt quá 2MB.")

    if errors:
        for error in errors:
            flash(error, "danger")

        return render_book_form(book, form_data)

    old_cover_image = book.cover_image
    new_cover_image = old_cover_image

    # Nếu chọn ảnh mới thì lưu ảnh mới
    if image_extension:
        upload_folder = os.path.join(
            app.root_path, "static", "uploads"
        )
        os.makedirs(upload_folder, exist_ok=True)

        filename = f"{uuid.uuid4().hex}.{image_extension}"
        image.save(os.path.join(upload_folder, filename))
        new_cover_image = filename

    book.title = title
    book.author = author
    book.publisher = publisher or None
    book.published_year = published_year
    book.price = price
    book.quantity = quantity
    book.description = description or None
    book.category_id = category.id
    book.cover_image = new_cover_image

    try:
        db.session.commit()

        # Xóa ảnh cũ sau khi cập nhật thành công
        if image_extension and old_cover_image:
            old_filename = os.path.basename(old_cover_image)
            old_path = os.path.join(
                app.root_path, "static", "uploads", old_filename
            )

            if os.path.isfile(old_path):
                os.remove(old_path)

        flash("Cập nhật sách thành công.", "success")
        return redirect(url_for("admin_books"))

    except Exception:
        db.session.rollback()

        if image_extension and new_cover_image:
            new_path = os.path.join(
                app.root_path, "static", "uploads", new_cover_image
            )

            if os.path.isfile(new_path):
                os.remove(new_path)

        flash("Không thể cập nhật sách. Vui lòng thử lại.", "danger")
        return render_book_form(book, form_data)

# =========================
# QUẢN LÝ DANH MỤC
# =========================

@app.route("/admin/categories", methods=["GET", "POST"])
def admin_categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Vui lòng nhập tên danh mục.", "danger")
            return redirect(url_for("admin_categories"))

        existing = db.session.scalar(
            select(Category).where(func.lower(Category.name) == name.lower())
        )
        if existing:
            flash("Tên danh mục đã tồn tại.", "danger")
            return redirect(url_for("admin_categories"))

        db.session.add(Category(name=name, description=description or None))
        db.session.commit()
        flash("Thêm danh mục thành công.", "success")
        return redirect(url_for("admin_categories"))

    categories = db.session.scalars(select(Category).order_by(Category.id.desc())).all()
    count_rows = db.session.execute(
        select(Category.id, func.count(Book.id))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id)
    ).all()
    category_counts = {category_id: count for category_id, count in count_rows}
    return render_template(
        "admin/categories.html", categories=categories,
        category_counts=category_counts, editing_category=None,
    )


@app.route("/admin/categories/<int:category_id>/edit", methods=["GET", "POST"])
def admin_category_edit(category_id):
    category = db.get_or_404(Category, category_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        if not name:
            flash("Vui lòng nhập tên danh mục.", "danger")
        else:
            existing = db.session.scalar(
                select(Category).where(
                    func.lower(Category.name) == name.lower(),
                    Category.id != category.id,
                )
            )
            if existing:
                flash("Tên danh mục đã tồn tại.", "danger")
            else:
                category.name = name
                category.description = description or None
                db.session.commit()
                flash("Cập nhật danh mục thành công.", "success")
                return redirect(url_for("admin_categories"))

    categories = db.session.scalars(select(Category).order_by(Category.id.desc())).all()
    count_rows = db.session.execute(
        select(Category.id, func.count(Book.id))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id)
    ).all()
    category_counts = {category_id: count for category_id, count in count_rows}
    return render_template(
        "admin/categories.html", categories=categories,
        category_counts=category_counts, editing_category=category,
    )


@app.route("/admin/categories/<int:category_id>/delete", methods=["POST"])
def admin_category_delete(category_id):
    category = db.get_or_404(Category, category_id)
    book_count = db.session.scalar(
        select(func.count(Book.id)).where(Book.category_id == category.id)
    ) or 0
    if book_count:
        flash(
            f'Không thể xóa "{category.name}": còn {book_count} sách.',
            "danger",
        )
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Xóa danh mục thành công.", "success")
    return redirect(url_for("admin_categories"))

# =========================
# QUẢN LÝ ĐƠN HÀNG
# =========================

@app.route("/admin/orders")
def admin_orders():
    keyword = request.args.get("q", "").strip()
    selected_status = request.args.get("status", "").strip()

    valid_statuses = [
        "Chờ xác nhận",
        "Đang giao",
        "Hoàn tất",
        "Đã huỷ",
    ]

    if selected_status not in valid_statuses:
        selected_status = ""

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1

    # Các điều kiện lọc
    conditions = []

    if keyword:
        search_keyword = f"%{keyword}%"
        search_conditions = [
            Customer.full_name.ilike(search_keyword),
            Customer.phone.ilike(search_keyword),
        ]

        if keyword.isdigit():
            search_conditions.append(Order.id == int(keyword))

        conditions.append(or_(*search_conditions))

    if selected_status:
        conditions.append(Order.status == selected_status)

    # Truy vấn đơn hàng
    query = (
        select(Order)
        .join(Order.customer)
        .where(*conditions)
        .order_by(Order.created_at.desc())
    )

    pagination = db.paginate(
        query,
        page=page,
        per_page=10,
        error_out=False,
    )

    # Đếm số đơn theo từng trạng thái
    status_counts = {
        status: 0 for status in valid_statuses
    }

    count_rows = db.session.execute(
        select(Order.status, func.count(Order.id))
        .group_by(Order.status)
    ).all()

    for status, count in count_rows:
        if status in status_counts:
            status_counts[status] = count

    # Tổng tiền của các đơn đang được lọc
    total_amount = db.session.scalar(
        select(func.coalesce(func.sum(Order.total), 0))
        .select_from(Order)
        .join(Order.customer)
        .where(*conditions)
    )

    return render_template(
        "admin/orders.html",
        orders=pagination.items,
        pagination=pagination,
        keyword=keyword,
        selected_status=selected_status,
        valid_statuses=valid_statuses,
        status_counts=status_counts,
        total_orders=pagination.total,
        total_amount=total_amount,
    )

# =========================
# CHI TIẾT ĐƠN HÀNG
# =========================

@app.route("/admin/orders/<int:order_id>")
def admin_order_detail(order_id):
    order = db.get_or_404(Order, order_id)

    return render_template(
        "admin/order_detail.html",
        order=order,
    )


# =========================
# CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG
# =========================

@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
def admin_order_update_status(order_id):
    order = db.get_or_404(Order, order_id)

    new_status = request.form.get("status", "").strip()

    allowed_transitions = {
        "Chờ xác nhận": ["Đang giao", "Đã huỷ"],
        "Đang giao": ["Hoàn tất", "Đã huỷ"],
        "Hoàn tất": [],
        "Đã huỷ": [],
    }

    current_status = order.status

    if new_status not in allowed_transitions.get(current_status, []):
        flash("Không thể chuyển sang trạng thái này.", "danger")
        return redirect(
            url_for("admin_order_detail", order_id=order.id)
        )

    try:
        # Nếu hủy đơn, hoàn trả sách vào kho
        if new_status == "Đã huỷ":
            for item in order.items:
                item.book.quantity += item.quantity

        # Cập nhật trạng thái
        order.status = new_status

        # Lưu lịch sử thay đổi
        history = OrderStatusHistory(
            order_id=order.id,
            status=new_status,
            changed_at=datetime.now(),
        )

        db.session.add(history)
        db.session.commit()

        flash("Cập nhật trạng thái đơn hàng thành công.", "success")

    except Exception:
        db.session.rollback()
        flash("Có lỗi xảy ra khi cập nhật đơn hàng.", "danger")

    return redirect(
        url_for("admin_order_detail", order_id=order.id)
    )

# =========================
# TRANG 404
# =========================

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
