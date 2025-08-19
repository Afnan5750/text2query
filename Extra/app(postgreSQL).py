import os
import psycopg2
import sqlparse
from flask import Flask, render_template, request, jsonify
from llama_cpp import Llama

app = Flask(__name__)

# --- Configuration ---
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'Lahore.01'
}

MODEL_CONFIG = {
    'model_path': os.path.abspath('model/sqlcoder-7b.Q4_K_M.gguf'),
    'n_ctx': 2048,
    'n_threads': 8,
    'n_gpu_layers': 0
}

PROMPT_TEMPLATE = """
### Task
Generate a SQL query to answer the following question:
\"\"\"{question}\"\"\"

### Database Schema
{schema_ddl}

### Answer
Given the database schema, here is the SQL query:
"""

# --- Utility Functions ---
def get_all_databases():
    conn = psycopg2.connect(dbname='postgres', **DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    dbs = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return dbs

def connect_postgres(dbname):
    return psycopg2.connect(dbname=dbname, **DB_CONFIG)

def get_schema(conn):
    ddl = []
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s;", (table,))
        columns = cursor.fetchall()
        column_defs = ", ".join([f"{col} {dtype}" for col, dtype in columns])
        ddl.append(f"CREATE TABLE {table} ({column_defs});")
    cursor.close()
    return "\n".join(ddl), tables

def generate_sql(prompt):
    llm = Llama(
        model_path=MODEL_CONFIG['model_path'],
        n_ctx=MODEL_CONFIG['n_ctx'],
        n_threads=MODEL_CONFIG['n_threads'],
        n_gpu_layers=MODEL_CONFIG['n_gpu_layers'],
        verbose=False
    )
    response = llm(prompt, max_tokens=256)
    sql_raw = response['choices'][0]['text'].strip()
    return sqlparse.format(sql_raw, reindent=False, keyword_case='upper')

def execute_query(conn, sql):
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        try:
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        except psycopg2.ProgrammingError:
            rows = []
            columns = []
        conn.commit()
        cursor.close()
        return {"rows": rows, "columns": columns}
    except Exception as e:
        cursor.close()
        return f"❌ Query failed: {e}"

def ensure_tables_exist(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS correct_queries (
            id SERIAL PRIMARY KEY,
            database_name TEXT,
            question TEXT,
            confirmed_sql TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id SERIAL PRIMARY KEY,
            database_name TEXT,
            question TEXT,
            generated_sql TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cursor.close()

def get_all_history():
    """Fetch history from all databases, newest first."""
    history_list = []
    for db in get_all_databases():
        try:
            conn = connect_postgres(db)
            ensure_tables_exist(conn)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, question, created_at
                FROM history
                ORDER BY created_at DESC;
            """)
            history_list.extend([(db, row[0], row[1], row[2]) for row in cursor.fetchall()])
            cursor.close()
            conn.close()
        except Exception:
            pass
    history_list.sort(key=lambda x: x[3], reverse=True)
    return [{"db": row[0], "id": row[1], "question": row[2]} for row in history_list]


@app.route('/delete_history/<db_name>/<int:history_id>', methods=['POST'])
def delete_history(db_name, history_id):
    try:
        conn = connect_postgres(db_name)
        ensure_tables_exist(conn)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history WHERE id = %s;", (history_id,))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "History item not found."}), 404
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def save_combine_query(conn, db_name, question, generated_sql):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (database_name, question, generated_sql)
        VALUES (%s, %s, %s);
    """, (db_name, question, generated_sql))
    conn.commit()
    cursor.close()

def save_correct_query(conn, db_name, question, confirmed_sql):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO correct_queries (database_name, question, confirmed_sql)
        VALUES (%s, %s, %s);
    """, (db_name, question, confirmed_sql))
    conn.commit()
    cursor.close()

# --- Flask Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    result = ''
    sql = ''
    question = ''
    selected_db = ''
    history_items = []
    databases = get_all_databases()

    if request.method == 'POST':
        question = request.form['question']
        selected_db = request.form['database']
        conn = connect_postgres(selected_db)

        ensure_tables_exist(conn)

        schema, _ = get_schema(conn)
        prompt = PROMPT_TEMPLATE.format(
            question=question,  # Directly use user's question
            schema_ddl=schema
        )
        sql = generate_sql(prompt)

        save_combine_query(conn, selected_db, question, sql)

        result = execute_query(conn, sql)

        history_items = get_all_history()

        conn.close()
    else:
        history_items = get_all_history()
        if databases:
            selected_db = databases[0]

    return render_template(
        'index.html',
        question=question,
        sql=sql,
        result=result,
        databases=databases,
        selected_db=selected_db,
        history_items=history_items
    )

@app.route('/history_item/<db_name>/<int:history_id>', methods=['GET'])
def get_history_item(db_name, history_id):
    try:
        conn = connect_postgres(db_name)
        ensure_tables_exist(conn)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question, generated_sql
            FROM history
            WHERE id = %s;
        """, (history_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({"status": "error", "message": "History item not found"}), 404
        
        question, generated_sql = row
        return jsonify({"status": "success", "question": question, "generated_sql": generated_sql})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/confirm', methods=['POST'])
def confirm():
    is_correct = request.form.get("is_correct")
    if is_correct != 'yes':
        return jsonify({"status": "ignored"})

    db_name = request.form.get("database")
    question = request.form.get("question")
    confirmed_sql = request.form.get("confirmed_sql")

    try:
        conn = connect_postgres(db_name)
        ensure_tables_exist(conn)
        save_correct_query(conn, db_name, question, confirmed_sql)
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
