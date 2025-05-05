import sqlite3

def init_db():
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT,
            answer TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            is_correct INTEGER,
            score INTEGER DEFAULT 0,
            graded INTEGER DEFAULT 0,
            submission_date TEXT DEFAULT (datetime('now'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            full_name TEXT,
            school_email TEXT,
            username TEXT,
            password TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS assigned_quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quiz(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')

    conn.commit()
    conn.close()

    add_submission_date_column()

def add_submission_date_column():
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(quiz_scores)")
    columns = [col[1] for col in c.fetchall()]
    if 'submission_date' not in columns:
        c.execute("ALTER TABLE quiz_scores ADD COLUMN submission_date TEXT DEFAULT (datetime('now'))")
        conn.commit()
    conn.close()

def save_question(question_type, question_text, options, answer):
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO quiz (type, question, options, answer)
        VALUES (?, ?, ?, ?)
    ''', (question_type, question_text, options, answer))
    conn.commit()
    conn.close()

def save_student_answer(student_id, question_id, answer, is_correct, score, graded):
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO quiz_scores (student_id, question_id, answer, is_correct, score, graded)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (student_id, question_id, answer, is_correct, score, graded))
    conn.commit()
    conn.close()
