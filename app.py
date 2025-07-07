from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'sirli_kalit'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ BAZANI INITSIALIZATSIYA QILISH
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            deadline TEXT,
            description TEXT,
            assigned_to TEXT,
            file_path TEXT,
            comment TEXT
        )
    ''')

    if not c.execute("SELECT * FROM users WHERE username='admin'").fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ('admin', 'admin123', 'admin'))

    conn.commit()
    conn.close()


# ✅ BOSH SAHIFA
@app.route('/')
def index():
    return redirect('/login')


# ✅ LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            session['role'] = user[3]
            return redirect('/admin' if user[3] == 'admin' else '/teacher')
        else:
            msg = "Login yoki parol noto‘g‘ri"
    return render_template('login.html', message=msg)


# ✅ LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ✅ ADMIN PANEL
@app.route('/admin')
def admin_dashboard():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')

    search = request.args.get('search')
    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    query = "SELECT * FROM tasks"
    params = []

    if search:
        query += " WHERE title LIKE ? OR description LIKE ? OR assigned_to LIKE ?"
        term = f"%{search}%"
        params = [term, term, term]

    count_query = f"SELECT COUNT(*) FROM ({query})"
    total = c.execute(count_query, params).fetchone()[0]

    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    tasks = c.execute(query, params).fetchall()

    c.execute("SELECT * FROM users WHERE role='teacher'")
    teachers = c.fetchall()

    conn.close()

    return render_template('dashboard_admin.html',
                           tasks=tasks,
                           teachers=teachers,
                           page=page,
                           total_pages=(total + per_page - 1) // per_page,
                           search=search)


# ✅ YANGI TOPSHIRIQ QO‘SHISH
@app.route('/add_task', methods=['POST'])
def add_task():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')
    title = request.form['title']
    deadline = request.form['deadline']
    description = request.form['description']
    assigned_to = request.form['assigned_to']
    file = request.files.get('file')
    filename = None

    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (title, deadline, description, assigned_to, file_path) VALUES (?, ?, ?, ?, ?)",
              (title, deadline, description, assigned_to, filename))
    conn.commit()
    conn.close()
    return redirect('/admin')


# ✅ TAHRIRLASH
@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        deadline = request.form['deadline']
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        c.execute("UPDATE tasks SET title=?, deadline=?, description=?, assigned_to=? WHERE id=?",
                  (title, deadline, description, assigned_to, task_id))
        conn.commit()
        conn.close()
        return redirect('/admin')

    c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    task = c.fetchone()
    c.execute("SELECT * FROM users WHERE role='teacher'")
    teachers = c.fetchall()
    conn.close()
    return render_template('edit_task.html', task=task, teachers=teachers)


# ✅ O‘CHIRISH
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return redirect('/admin')


# ✅ FAYL KO‘RISH
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ✅ O‘QITUVCHI PANEL
@app.route('/teacher')
def teacher_dashboard():
    if 'username' not in session or session['role'] != 'teacher':
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE assigned_to=?", (session['username'],))
    tasks = c.fetchall()
    conn.close()
    return render_template('teacher.html', tasks=tasks)
@app.route('/users')
def user_list():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return render_template('users.html', users=users)
@app.route('/users')
def users():
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE role='teacher'")
    teachers = cur.fetchall()
    return render_template("users.html", teachers=teachers)
from flask import jsonify
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')

    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            conn.commit()
            msg = 'Foydalanuvchi qo‘shildi!'
        except sqlite3.IntegrityError:
            msg = 'Bunday login allaqachon mavjud!'
        conn.close()

    return render_template('add_user.html', message=msg)

@app.route('/tasks_by_date')
def tasks_by_date():
    if 'username' not in session:
        return jsonify({'tasks': []})
    
    date = request.args.get('date')  # YYYY-MM-DD ko‘rinishida
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if session['role'] == 'admin':
        # Admin uchun barcha topshiriqlar
        c.execute("SELECT id, title, deadline, assigned_to FROM tasks WHERE deadline=?", (date,))
    else:
        # O‘qituvchi uchun faqat o‘z topshiriqlari
        c.execute("SELECT id, title, deadline, assigned_to FROM tasks WHERE deadline=? AND assigned_to=?", (date, session['username']))
    
    rows = c.fetchall()
    conn.close()
    
    # JSON formatga o‘tkazamiz
    tasks = [{'id': row[0], 'title': row[1], 'deadline': row[2], 'assigned_to': row[3]} for row in rows]
    return jsonify({'tasks': tasks})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
