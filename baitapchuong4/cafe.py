
from flask import Flask, render_template, request, abort
from datetime import datetime
import math

app = Flask(__name__)

SHOP = {
    "name": "Cà phê Sông Hương",
    "address": "12 Lê Lợi, Huế",
    "phone": "0234 3888 999",
    "open": 7,
    "close": 22
}

PROMOTIONS = [
    "Giảm 10% cho sinh viên",
    "Mua 2 tặng 1 vào thứ Hai"
]

MENU = [
    {
        "id": 1,
        "name": "Cà phê đen",
        "price": 20000,
        "image": "ca-phe-den.jpg",
        "available": True
    },
    {
        "id": 2,
        "name": "Cà phê sữa",
        "price": 25000,
        "image": "ca-phe-sua.jpg",
        "available": True
    },
    {
        "id": 3,
        "name": "Bạc xỉu",
        "price": 30000,
        "image": "bac-xiu.jpg",
        "available": False
    },
    {
        "id": 4,
        "name": "Trà đào",
        "price": 35000,
        "image": "tra-dao.jpg",
        "available": True
    },
    {
        "id": 5,
        "name": "Trà sữa",
        "price": 30000,
        "image": "tra-sua.jpg",
        "available": True
    },
    {
        "id": 6,
        "name": "Nước cam",
        "price": 25000,
        "image": "nuoc-cam.jpg",
        "available": True
    },
    {
        "id": 7,
        "name": "Sinh tố bơ",
        "price": 40000,
        "image": "sinh-to-bo.jpg",
        "available": True
    }
]

PER_PAGE = 3


@app.template_filter("vnd")
def format_vnd(value):
    return f"{value:,.0f}".replace(",", ".") + " ₫"


def lay_du_lieu_chung():
    gio = request.args.get("gio", default=None, type=int)

    if gio is None:
        gio = datetime.now().hour

    if gio < 0 or gio > 23:
        return None

    dang_mo = SHOP["open"] <= gio < SHOP["close"]

    return {
        "shop": SHOP,
        "promotions": PROMOTIONS,
        "gio": gio,
        "dang_mo": dang_mo
    }


@app.route("/")
def home():
    du_lieu = lay_du_lieu_chung()

    if du_lieu is None:
        return "Giờ phải nằm trong khoảng từ 0 đến 23.", 400

    return render_template("index.html", **du_lieu)


@app.route("/menu")
def menu():
    du_lieu = lay_du_lieu_chung()

    if du_lieu is None:
        return "Giờ phải nằm trong khoảng từ 0 đến 23.", 400

    page = request.args.get("page", default=1, type=int)

    pages = math.ceil(len(MENU) / PER_PAGE)

    if page < 1 or page > pages:
        abort(404)

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE

    menu_trang = MENU[start:end]

    gia_trung_binh = (
        sum(item["price"] for item in MENU) / len(MENU)
        if MENU else 0
    )

    return render_template(
        "menu.html",
        **du_lieu,
        menu=menu_trang,
        page=page,
        pages=pages,
        gia_trung_binh=gia_trung_binh
    )


@app.route("/contact")
def contact():
    du_lieu = lay_du_lieu_chung()

    if du_lieu is None:
        return "Giờ phải nằm trong khoảng từ 0 đến 23.", 400

    return render_template("contact.html", **du_lieu)


@app.route("/khong-co")
def khong_co():
    abort(404)


@app.errorhandler(404)
def page_not_found(error):
    gio = request.args.get("gio", default=None, type=int)

    if gio is None or gio < 0 or gio > 23:
        gio = datetime.now().hour

    du_lieu = {
        "shop": SHOP,
        "promotions": PROMOTIONS,
        "gio": gio,
        "dang_mo": SHOP["open"] <= gio < SHOP["close"]
    }

    return render_template("404.html", **du_lieu), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
