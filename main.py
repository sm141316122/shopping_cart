from flask import Flask, request, render_template, redirect, abort, url_for, session, flash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from MySQLdb import IntegrityError
from form import LoginForm, RegisterForm
from functools import wraps


app = Flask(__name__)

app.config['SECRET_KEY'] = 'Flask-secret-key'

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "YOUR_PASSWORD"
app.config["MYSQL_DB"] = "shopping_cart"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL()
mysql.init_app(app)

Bootstrap(app)


def login_required(func):
    @wraps(func)
    def check_login(*args, **kwargs):
        if "login" not in session:
            return redirect(url_for("login"))

        return func(*args, **kwargs)
    return check_login


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        email = register_form.email.data
        password = register_form.password.data
        confirm_password = register_form.confirm_password.data

        with mysql.connect as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM user WHERE email = '{email}'")
            user_data = cur.fetchone()
            if user_data:
                flash("電子郵件已註冊，請前往登入")
                return redirect(url_for("register"))
            else:
                if password == confirm_password:
                    cur.execute(f"INSERT INTO user(email, password) VALUES('{email}', '{password}')")
                    conn.commit()

                    return redirect(url_for("login"))
                else:
                    flash("請確認密碼")
                    return redirect(url_for("register"))

    return render_template("register.html", form=register_form)


@app.route("/login", methods=["GET", "POST"])
def login():
    loginform = LoginForm()
    if loginform.validate_on_submit():
        email = loginform.email.data
        password = loginform.password.data

        with mysql.connect as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM user WHERE email = '{email}'")
            user_data = cur.fetchone()
            if user_data:
                if user_data["password"] == password:
                    session["login"] = True
                    session["user_id"] = user_data["user_id"]

                    return redirect(url_for("home"))
                else:
                    flash("密碼錯誤，請重新輸入")
                    return redirect(url_for("login"))
            else:
                flash("帳號錯誤，請重新輸入")
                return redirect(url_for("login"))

    return render_template("login.html", form=loginform)


@app.route("/logout")
@login_required
def logout():
    session.clear()

    return redirect(url_for("home"))


@app.route("/category/<int:category_id>")
def category(category_id):
    file = f"img/category_title_img/{category_id}.png"

    with mysql.connect as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM product WHERE category_id = {category_id}")
        data = cur.fetchall()

    return render_template("category.html", products=data, file=file)


@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product_page(product_id):
    if request.method == "POST":
        order_num = int(request.form["num"])

        with mysql.connect as conn:
            cur = conn.cursor()
            try:
                cur.execute(f"INSERT INTO cart(user_id, product_id, order_num) "
                            f"VALUES({session['user_id']}, {product_id}, {order_num})")
                if "cart_num" in session:
                    session["cart_num"] += 1
                else:
                    session["cart_num"] = 0
                    session["cart_num"] += 1
            except IntegrityError:
                cur.execute(f"UPDATE cart SET order_num = {order_num} "
                            f"WHERE user_id = {session['user_id']} AND product_id = {product_id}")
            finally:
                conn.commit()

            if "buy" in request.form:
                return redirect(url_for("cart_page"))
            else:
                return redirect(url_for("product_page", product_id=product_id))

    with mysql.connect as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM product WHERE product_id = {product_id}")
        data = cur.fetchone()

    return render_template("product_page.html", product=data)


@app.route("/cart")
@login_required
def cart_page():
    with mysql.connect as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT cart.product_id, product_name, order_num, product_price, product_stock "
                    f"FROM cart "
                    f"JOIN product "
                    f"ON cart.user_id = {session['user_id']} AND cart.product_id = product.product_id")
        data = cur.fetchall()
        total_price = 0
        for item in data:
            total_price += item["order_num"] * item["product_price"]

    return render_template("cart_page.html", cart_data=data, total_price=total_price)


@app.route("/delete_order/<int:product_id>")
@login_required
def delete_order(product_id):
    with mysql.connect as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM cart "
                    f"WHERE user_id = {session['user_id']} AND product_id = {product_id}")
        conn.commit()

        session["cart_num"] -= 1
        if session["cart_num"] == 0:
            session.pop("cart_num")

        return redirect(url_for("cart_page"))


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_text = request.form["search"]

        with mysql.connect as conn:
            cur = conn.cursor()
            if " " in search_text:
                search_text = search_text.split(" ")
                sql = ""
                for text in search_text:
                    if search_text[0] == text:
                        sql += f"(SELECT * FROM product WHERE product_name LIKE '%{text}%') as {text}"
                        continue
                    elif search_text[-1] == text:
                        sql = f"SELECT * FROM {sql} WHERE product_name LIKE '%{text}%'"
                    else:
                        sql = f"(SELECT * FROM {sql} WHERE product_name LIKE '%{text}%') as {text}"

                cur.execute(sql)
                data = cur.fetchall()
            else:
                cur.execute(f"SELECT * FROM product WHERE product_name LIKE '%{search_text}%'")
                data = cur.fetchall()

        return render_template("search_page.html", products=data)

    return abort(404)


if __name__ == "__main__":
    app.run(debug=True)
