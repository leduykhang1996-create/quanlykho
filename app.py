from flask import Flask, request, redirect
import sqlite3

app = Flask(__name__)

def get_db():
    return sqlite3.connect("kho.db")

# 👉 convert nhập (1k -> 1000)
def convert_price(text):
    text = text.lower().replace(" ", "")
    if "k" in text:
        return int(float(text.replace("k", "")) * 1000)
    return int(text)

# 👉 convert hiển thị (10000 -> 10k)
def format_price(num):
    if not num:
        return ""
    num = int(num)
    if num >= 1000:
        val = num / 1000
        if val.is_integer():
            return f"{int(val)}k"
        return f"{val:.1f}k"
    return str(num)

@app.route("/")
def home():
    keyword = request.args.get("q", "")
    db = get_db()

    if keyword:
        data = db.execute(
            "SELECT * FROM phones WHERE name LIKE ? OR imei LIKE ?",
            (f"%{keyword}%", f"%{keyword}%")
        ).fetchall()
    else:
        data = db.execute("SELECT * FROM phones").fetchall()

    tong_von = sum(int(p[3]) for p in data if p[3])
    tong_loi = sum((int(p[4]) - int(p[3])) for p in data if p[4])

    html = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: Arial;
            background: #f4f6f8;
            padding: 10px;
        }}

        .top {{
            background: white;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}

        th, td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }}

        th {{
            background: #eee;
        }}

        .lai {{
            color: green;
            font-weight: bold;
        }}

        .lo {{
            color: red;
            font-weight: bold;
        }}

        .btn {{
            padding: 4px 8px;
            border-radius: 5px;
            text-decoration: none;
            color: white;
        }}

        .ban {{ background: green; }}
        .xoa {{ background: red; }}

        input {{
            padding: 5px;
            margin: 5px 0;
        }}
    </style>
    </head>

    <body>

    <div class="top">
        💰 Vốn: {format_price(tong_von)} |
        🔥 Lãi: {format_price(tong_loi)}
    </div>

    <div class="top">
        <form method="GET">
            🔍 <input name="q" value="{keyword}">
            <button>Tìm</button>
        </form>
    </div>

    <table>
        <tr>
            <th>Tên máy</th>
            <th>IMEI</th>
            <th>Giá nhập</th>
            <th>Giá bán</th>
            <th>Lãi</th>
            <th>Trạng thái</th>
            <th></th>
        </tr>
    """

    for p in data:
        lai = ""
        if p[4]:
            loi_val = int(p[4]) - int(p[3])
            color = "lai" if loi_val >= 0 else "lo"
            lai = f'<span class="{color}">{format_price(loi_val)}</span>'

        html += f"""
        <tr>
            <td>{p[1]}</td>
            <td>{p[2]}</td>
            <td>{format_price(p[3])}</td>
            <td>{format_price(p[4]) if p[4] else ""}</td>
            <td>{lai}</td>
            <td>{p[5]}</td>
            <td>
                <a class="btn ban" href="/ban/{p[0]}">Bán</a>
                <a class="btn xoa" href="/xoa/{p[0]}">Xoá</a>
            </td>
        </tr>
        """

    html += """
    </table>

    <div class="top">
        <h3>➕ Thêm máy</h3>
        <form method="POST" action="/add">
            Tên: <input name="name">
            IMEI: <input name="imei">
            Giá: <input name="price">
            <button>Thêm</button>
        </form>
    </div>

    </body>
    </html>
    """

    return html

@app.route("/add", methods=["POST"])
def add():
    db = get_db()
    db.execute(
        "INSERT INTO phones (name, imei, price_in, status) VALUES (?, ?, ?, 'còn')",
        (
            request.form["name"],
            request.form["imei"],
            convert_price(request.form["price"])
        )
    )
    db.commit()
    return redirect("/")

@app.route("/ban/<int:id>")
def ban(id):
    return f"""
    <div style="padding:20px;">
    <h2>Nhập giá bán</h2>
    <form method="POST" action="/luu_ban/{id}">
        <input name="price_out" placeholder="vd: 12k">
        <button>Bán</button>
    </form>
    </div>
    """

@app.route("/luu_ban/<int:id>", methods=["POST"])
def luu_ban(id):
    db = get_db()
    db.execute(
        "UPDATE phones SET price_out=?, status='đã bán' WHERE id=?",
        (
            convert_price(request.form["price_out"]),
            id
        )
    )
    db.commit()
    return redirect("/")

@app.route("/xoa/<int:id>")
def xoa(id):
    db = get_db()
    db.execute("DELETE FROM phones WHERE id=?", (id,))
    db.commit()
    return redirect("/")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
