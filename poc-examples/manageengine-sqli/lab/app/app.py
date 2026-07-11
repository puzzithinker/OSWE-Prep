"""OSWE-LAB: ManageEngine-style Postgres SQLi teaching app."""
import os
import time
from flask import Flask, request, send_from_directory
import psycopg2

app = Flask(__name__)
DB = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "oswe"),
    "user": os.getenv("DB_USER", "oswe"),
    "password": os.getenv("DB_PASS", "oswe"),
}
STATIC = "/app/static"


def conn():
    return psycopg2.connect(**DB)


def init_db():
    for _ in range(30):
        try:
            c = conn()
            c.autocommit = True
            cur = c.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS resources (id INT PRIMARY KEY, name TEXT)"
            )
            cur.execute("DELETE FROM resources")
            cur.execute("INSERT INTO resources (id, name) VALUES (1, 'default')")
            # Lab role is superuser (POSTGRES_USER) — enables COPY to /export
            cur.close()
            c.close()
            return
        except Exception as e:
            print("db wait", e)
            time.sleep(2)


@app.get("/")
def index():
    return """
    <h1>OSWE-LAB · Postgres SQLi (ManageEngine-style)</h1>
    <p>Endpoint: <code>/servlet/AMUserResourcesSyncServlet?ForMasRange=</code></p>
    <p>Stacked queries + time-based <code>pg_sleep</code>. Write webshell under <code>/static/</code>.</p>
    <p>Static files: <a href="/static/flag.txt">/static/flag.txt</a></p>
    """


@app.get("/servlet/AMUserResourcesSyncServlet")
def sync():
    # VULNERABLE: string concat into SQL
    rng = request.args.get("ForMasRange", "1")
    sql = f"SELECT id, name FROM resources WHERE id = {rng}"
    try:
        c = conn()
        c.autocommit = True
        cur = c.cursor()
        # allow multiple statements
        cur.execute(sql)
        try:
            rows = cur.fetchall()
        except Exception:
            rows = []
        cur.close()
        c.close()
        return {"ok": True, "rows": rows, "sql": sql}
    except Exception as e:
        return {"ok": False, "error": str(e), "sql": sql}, 500


@app.get("/static/<path:path>")
def static_files(path):
    return send_from_directory(STATIC, path)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    init_db()
    try:
        open(os.path.join(STATIC, "flag.txt"), "w").write("OSWE{pg_sqli_lab_flag}\n")  # static flag
    except Exception as e:
        print("flag write", e)
    app.run(host="0.0.0.0", port=8080)
