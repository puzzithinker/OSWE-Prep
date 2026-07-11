"""OSWE-LAB: MSSQL SQLi teaching front-end (product?id=)."""
import os
import time
from flask import Flask, request
import pymssql

app = Flask(__name__)
DB_HOST = os.getenv("DB_HOST", "mssql")
DB_USER = os.getenv("DB_USER", "sa")
DB_PASS = os.getenv("DB_PASS", "Your_strong_Password123")
DB_NAME = os.getenv("DB_NAME", "master")


def connect():
    return pymssql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME, login_timeout=5)


def init_db():
    for i in range(60):
        try:
            c = connect()
            cur = c.cursor()
            cur.execute(
                """
                IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'oswe')
                BEGIN
                  CREATE DATABASE oswe;
                END
                """
            )
            c.commit()
            c.close()
            c = pymssql.connect(DB_HOST, DB_USER, DB_PASS, "oswe", login_timeout=5)
            cur = c.cursor()
            cur.execute(
                """
                IF OBJECT_ID('products') IS NULL
                CREATE TABLE products (id INT PRIMARY KEY, name NVARCHAR(100));
                """
            )
            cur.execute("DELETE FROM products")
            cur.execute("INSERT INTO products (id, name) VALUES (1, 'Widget')")
            c.commit()
            c.close()
            print("mssql ready")
            return
        except Exception as e:
            print("wait mssql", e)
            time.sleep(3)


@app.get("/")
def index():
    return """
    <h1>OSWE-LAB · MSSQL SQLi</h1>
    <p>Endpoint: <code>/product.aspx?id=1</code> (alias <code>/product?id=</code>)</p>
    <p>SA-level connection — try stacked queries / WAITFOR / xp_cmdshell enable sequence.</p>
    <p>Note: SQL Server on Linux may limit xp_cmdshell; still excellent for blind SQLi + stacked practice.</p>
    """


@app.route("/product.aspx")
@app.route("/product")
def product():
    pid = request.args.get("id", "1")
    # VULNERABLE concat
    sql = f"SELECT id, name FROM products WHERE id = {pid}"
    try:
        c = pymssql.connect(DB_HOST, DB_USER, DB_PASS, "oswe", login_timeout=5, autocommit=True)
        cur = c.cursor()
        cur.execute(sql)
        rows = []
        try:
            rows = cur.fetchall()
        except Exception:
            pass
        c.close()
        return {"ok": True, "rows": rows, "sql": sql}
    except Exception as e:
        return {"ok": False, "error": str(e), "sql": sql}, 500


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
