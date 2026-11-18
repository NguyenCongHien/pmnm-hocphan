
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Regexp, Length


class CheckoutForm(FlaskForm):
    full_name = StringField(
        "Họ tên",
        validators=[
            DataRequired(message="Vui lòng nhập họ tên."),
            Length(max=150)
        ]
    )

    phone = StringField(
        "Số điện thoại",
        validators=[
            DataRequired(message="Vui lòng nhập số điện thoại."),
            Regexp(
                r"^0[0-9]{9}$",
                message="Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0."
            )
        ]
    )

    email = StringField(
        "Email",
        validators=[
            Optional(),
            Email(message="Email không đúng định dạng."),
            Length(max=150)
        ]
    )

    address = TextAreaField(
        "Địa chỉ giao hàng",
        validators=[DataRequired(message="Vui lòng nhập địa chỉ.")]
    )

    note = TextAreaField("Ghi chú")

    payment_method = SelectField(
        "Phương thức thanh toán",
        choices=[
            ("COD", "Tiền mặt khi nhận hàng"),
            ("BANK", "Chuyển khoản")
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Xác nhận đặt hàng")
