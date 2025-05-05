from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file, make_response
import json
import sqlite3
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from quiz_db import init_db, save_question, save_student_answer

def get_db_connection():
    conn = sqlite3.connect('quiz.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_pdf(data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 50, "Quiz Score Report")

    pdf.setFont("Helvetica", 12)
    y = height - 80
    pdf.drawString(50, y, "Student ID")
    pdf.drawString(150, y, "Date")
    pdf.drawString(300, y, "Total Score")
    pdf.drawString(400, y, "Partial Score")
    y -= 20

    for row in data:
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(50, y, str(row[0]))
        pdf.drawString(150, y, str(row[1]))
        pdf.drawString(300, y, str(row[2]))
        pdf.drawString(400, y, str(row[3]))
        y -= 20

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='quiz_scores.pdf', mimetype='application/pdf')

def generate_csv(data):
    df = pd.DataFrame(data, columns=['Student ID', 'Date', 'Total Score', 'Partial Score'])
    response = make_response(df.to_csv(index=False))
    response.headers['Content-Disposition'] = 'attachment; filename=quiz_scores.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

app = Flask(__name__)
app.secret_key = 'secretkey'

init_db()

admin_users = {
    "alexakate": {
        "name": "Alexa Kate B. Mamato",
        "email": "alexa@example.com",
        "password": "yourpassword123"
    },
    "desserei": {
        "name": "Ma. Desserei C. Emaas",
        "email": "desserei@example.com",
        "password": "01234567"
    }
}

student_users = {}

@app.route('/')
def home():
    if 'admin_name' in session:
        return redirect(url_for('admin_home'))
    return render_template('select_role.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_id = request.form['admin_id']
        password = request.form['password']
        user = admin_users.get(admin_id)
        if user and user['password'] == password:
            session['admin_name'] = user['name']
            return redirect(url_for('admin_home'))
        flash("Invalid Admin ID or Password.")
    return render_template('admin_login.html')

@app.route('/admin/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    reset_stage = False
    admin_info = None
    if request.method == 'POST':
        if 'username' in request.form:
            username = request.form['username']
            if username in admin_users:
                session['reset_user'] = username
                admin_info = admin_users[username]
                reset_stage = True
            else:
                flash("No account found.")
        else:
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            if new_password != confirm_password:
                flash("Passwords do not match.")
                reset_stage = True
                admin_info = admin_users.get(session.get('reset_user'))
            else:
                admin_users[session['reset_user']]['password'] = new_password
                flash("Password reset.")
                session.pop('reset_user', None)
                return redirect(url_for('admin_login'))
    return render_template('admin_forgot_password.html', reset_stage=reset_stage, admin_info=admin_info)

@app.route('/admin/home')
def admin_home():
    return render_template('admin_home.html', admin_name=session.get('admin_name', 'Admin'))

@app.route('/attendance')
def attendance_page():
    return render_template('index.html', active_tab='attendance')

@app.route('/quiz')
def quiz_page():
    return render_template('quiz_page.html')

@app.route('/exam')
def exam_page():
    return render_template('index.html', active_tab='exam')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html', records=records)

records = []
student_number = 1

@app.route('/admin/add', methods=["POST"])
def add_student():
    global student_number
    student_id = f"{student_number:05d}"
    name = request.form['name']
    attendance = request.form['attendance']
    quiz_score = int(request.form['quiz_score'])
    exam_score = int(request.form['exam_score'])

    records.append({
        "id": student_id,
        "name": name,
        "attendance": attendance,
        "quiz_score": quiz_score,
        "exam_score": exam_score
    })
    student_number += 1
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<student_id>')
def delete(student_id):
    global records
    records = [r for r in records if r["id"] != student_id]
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<student_id>', methods=["GET", "POST"])
def edit(student_id):
    record = next((r for r in records if r["id"] == student_id), None)
    if request.method == "POST":
        if record:
            record["name"] = request.form["name"]
            record["attendance"] = request.form["attendance"]
            record["quiz_score"] = int(request.form["quiz_score"])
            record["exam_score"] = int(request.form["exam_score"])
        return redirect(url_for('admin_dashboard'))
    return render_template("edit.html", record=record)

@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match")
        else:
            admin_users[username] = {
                "full_name": full_name,
                "email": email,
                "username": username,
                "password": password
            }
            return redirect(url_for('admin_home'))
    return render_template('admin_signup.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        user = student_users.get(student_id)
        if user and user['password'] == password:
            session['student_name'] = user['full_name']
            session['student_id'] = student_id
            session['user_type'] = 'student'  
        return redirect(url_for('student_home'))
        flash('Invalid credentials')
    return render_template('student_login.html')

@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        school_email = request.form['school_email']
        student_id = request.form['student_id']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match")
        else:
            student_users[student_id] = {
                "full_name": full_name,
                "school_email": school_email,
                "username": username,
                "password": password
            }
            return redirect(url_for('student_login'))
    return render_template('student_signup.html')

@app.route('/student/home')
def student_home():
    return render_template('student_home.html', student_name=session.get('student_name', 'Student'))

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if request.method == 'POST':
        questions = request.form.getlist('questions[]')
        question_types = request.form.getlist('types[]')
        options_list = request.form.getlist('options[]')
        answers = request.form.getlist('answers[]')

        for i in range(len(questions)):
            q_type = question_types[i]
            q_text = questions[i]
            options = json.dumps(options_list[i].split(',')) if q_type == "mcq" else None
            answer = answers[i]
            save_question(q_type, q_text, options, answer)

        flash("Quiz successfully created!")
    return render_template('create_quiz.html')

@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    student_id = request.form['student_id']
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('SELECT * FROM quiz')
    questions = c.fetchall()

    for question in questions:
        q_id = question[0]
        q_type = question[1]
        correct_answer = question[4]
        submitted_answer = request.form.get(f'q_{q_id}', '')

        if q_type == 'mcq':
            is_correct = 1 if submitted_answer.strip().lower() == correct_answer.strip().lower() else 0
            score = 1 if is_correct else 0
            graded = 1
        else:
            is_correct = None
            score = 0
            graded = 0

        save_student_answer(student_id, q_id, submitted_answer, is_correct, score, graded)

    conn.close()
    flash("Answers submitted.")
    return redirect(url_for('home'))

@app.route('/view_records')
def view_records():
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''
        SELECT student_id, submission_date,
               SUM(CASE WHEN graded = 1 THEN score ELSE 0 END) as total_score,
               SUM(CASE WHEN is_correct = 1 THEN score ELSE 0 END) as partial_score
        FROM quiz_scores
        GROUP BY student_id, submission_date
    ''')
    data = c.fetchall()
    conn.close()

    records = [{"student_id": row[0], "submission_date": row[1], "total_score": row[2], "partial_score": row[3]} for row in data]
    return render_template('view_records.html', records=records)

@app.route('/grade_answer', methods=['POST'])
def grade_answer():
    score_id = request.form['score_id']
    new_score = request.form['score']

    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('UPDATE quiz_scores SET score = ?, graded = 1 WHERE id = ?', (new_score, score_id))
    conn.commit()
    conn.close()

    flash("Answer graded successfully!")
    return redirect(url_for('view_records'))

@app.route('/student_quiz')
def student_quiz():
    student_id = session.get('user_id')
    
    
   
    view = request.args.get('view')
    
    
    conn = get_db_connection()
    
   
    if student_id:
        quizzes = conn.execute(
            'SELECT q.id, q.question, q.options, q.correct_answer, sq.is_completed '
            'FROM quizzes q JOIN student_quizzes sq ON q.id = sq.quiz_id '
            'WHERE sq.student_id = ? AND sq.is_completed = 0',
            (student_id,)
        ).fetchall()
    else:
        quizzes = []
    
    conn.close()
    
    
    if not quizzes or view != 'assigned':
        return render_template('take_quiz.html', quizzes=quizzes, is_dashboard=True)
    else:
        
        return render_template('take_quiz.html', quizzes=quizzes, is_dashboard=False)

@app.route('/take_quiz/<int:quiz_id>')
def take_quiz(quiz_id):
    student_id = session.get('student_id')
    if not student_id:
        flash("Please log in to take quizzes.")
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    
    cursor.execute('''
        SELECT aq.id, q.id as quiz_id, q.question, q.options, q.type
        FROM assigned_quizzes aq
        JOIN quiz q ON aq.quiz_id = q.id
        WHERE aq.id = ?
    ''', (quiz_id,))
    
    quiz = cursor.fetchone()
    conn.close()
    
    if not quiz:
        flash("Quiz not found.")
        return redirect(url_for('student_quiz'))
    
    quizzes = [quiz]
    return render_template('take_quiz.html', quizzes=quizzes, is_dashboard=False)


@app.route('/student/view_records')
def student_view_records():
    student_id = session.get('student_id')
    if not student_id:
        flash("Please log in to view your records")
        return redirect(url_for('student_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT q.title as quiz_title, qs.submission_date as date_taken,
               qs.score as score
        FROM quiz_scores qs
        JOIN quizzes q ON qs.quiz_id = q.id
        WHERE qs.student_id = ?
        ORDER BY qs.submission_date DESC
    ''', (student_id,))
    
    records = [{'quiz_title': row[0], 'date_taken': row[1], 'score': row[2]} for row in cursor.fetchall()]
    conn.close()

    return render_template('student_view_records.html', records=records)


@app.route('/assigned_quizzes', methods=['GET', 'POST'])
def assign_quiz():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        quiz_id = request.form['quiz_id']
        student_id = request.form['student_id']
        cursor.execute('INSERT INTO assigned_quizzes (quiz_id, student_id) VALUES (?, ?)', (quiz_id, student_id))
        conn.commit()
        flash("Quiz assigned successfully!")
        return redirect(url_for('assign_quiz'))

    cursor.execute('SELECT id, question FROM quiz')
    quizzes = cursor.fetchall()

    
    students = list(student_users.keys())  

    
    cursor.execute('''
        SELECT aq.id, aq.student_id, q.question
        FROM assigned_quizzes aq
        JOIN quiz q ON aq.quiz_id = q.id
    ''')
    assigned = cursor.fetchall()

    conn.close()
    return render_template('assigned_quizzes.html', quizzes=quizzes, students=students, assigned=assigned)








@app.route('/student/export_student_quiz_csv')
def export_student_quiz_csv():
    student_id = session.get('student_id')
    if not student_id:
        flash("Please log in to export your records.")
        return redirect(url_for('student_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT q.question as quiz_title, qs.submission_date as date_taken,
               SUM(CASE WHEN qs.graded = 1 THEN qs.score ELSE 0 END) as score
        FROM quiz_scores qs
        JOIN quiz q ON qs.question_id = q.id
        WHERE qs.student_id = ?
        GROUP BY q.id, qs.submission_date
    ''', (student_id,))
    data = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(data, columns=['Quiz Title', 'Date Taken', 'Score'])
    response = make_response(df.to_csv(index=False))
    response.headers['Content-Disposition'] = 'attachment; filename=student_quiz_scores.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response



@app.route('/student/export_student_quiz_pdf')
def export_student_quiz_pdf():
    student_id = session.get('student_id')
    if not student_id:
        flash("Please log in to export your records.")
        return redirect(url_for('student_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT q.question as quiz_title, qs.submission_date as date_taken,
               SUM(CASE WHEN qs.graded = 1 THEN qs.score ELSE 0 END) as score
        FROM quiz_scores qs
        JOIN quiz q ON qs.question_id = q.id
        WHERE qs.student_id = ?
        GROUP BY q.id, qs.submission_date
    ''', (student_id,))
    data = cursor.fetchall()
    conn.close()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 50, "Student Quiz Report")

    pdf.setFont("Helvetica", 12)
    y = height - 80
    pdf.drawString(50, y, "Quiz Title")
    pdf.drawString(250, y, "Date Taken")
    pdf.drawString(450, y, "Score")
    y -= 20

    for row in data:
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(50, y, str(row[0]))
        pdf.drawString(250, y, str(row[1]))
        pdf.drawString(450, y, str(row[2]))
        y -= 20

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='student_quiz_scores.pdf', mimetype='application/pdf')


@app.route('/student_logout')
def student_logout():
    session.clear()
    flash("Student logged out.")
    return redirect(url_for('student_login'))

@app.route('/admin_logout')
def admin_logout():
    session.clear()
    flash("Admin logged out.")
    return redirect(url_for('admin_login'))

@app.route('/export_csv')
def export_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT student_id, submission_date,
               SUM(CASE WHEN graded = 1 THEN score ELSE 0 END) as total_score,
               SUM(CASE WHEN is_correct = 1 THEN score ELSE 0 END) as partial_score
        FROM quiz_scores
        GROUP BY student_id, submission_date
    ''')
    data = cursor.fetchall()
    conn.close()
    return generate_csv(data)

@app.route('/export_pdf')
def export_pdf():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT student_id, submission_date,
               SUM(CASE WHEN graded = 1 THEN score ELSE 0 END) as total_score,
               SUM(CASE WHEN is_correct = 1 THEN score ELSE 0 END) as partial_score
        FROM quiz_scores
        GROUP BY student_id, submission_date
    ''')
    data = cursor.fetchall()
    conn.close()
    return generate_pdf(data)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    student_id = session.get('student_id')
    if not student_id:
        flash("Please log in to take quizzes.")
        return redirect(url_for('student_login'))

    quiz_id = request.form['quiz_id']
    answer = request.form['answer']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT answer FROM quiz WHERE id = ?', (quiz_id,))
    correct_answer = cursor.fetchone()
    correct_answer = correct_answer[0] if correct_answer else ''

    is_correct = int(answer.strip().lower() == correct_answer.strip().lower())
    score = 1 if is_correct else 0

    cursor.execute('''
        INSERT INTO quiz_scores (student_id, question_id, answer, is_correct, score, graded)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (student_id, quiz_id, answer, is_correct, score, 1))

    conn.commit()
    conn.close()

    flash("Answer submitted successfully!")
    return redirect(url_for('student_quiz_page'))












if __name__ == '__main__':
    app.run(debug=True)
