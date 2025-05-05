# exam_db.py
import sqlite3

def init_db():
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS exam (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT,
            answer TEXT
        )
    ''')
    conn.commit()
    conn.close()
    create_score_table()
    add_submission_date_column()

def save_question(question_type, question_text, options, answer):
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO exam (type, question, options, answer)
        VALUES (?, ?, ?, ?)
    ''', (question_type, question_text, options, answer))
    conn.commit()
    conn.close()

def create_score_table():
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS exam_scores (
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
    conn.commit()
    conn.close()

def add_submission_date_column():
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    # Check if column exists before trying to add it
    c.execute("PRAGMA table_info(exam_scores)")
    columns = [col[1] for col in c.fetchall()]
    if 'submission_date' not in columns:
        c.execute("ALTER TABLE exam_scores ADD COLUMN submission_date TEXT DEFAULT (datetime('now'))")
        conn.commit()
    conn.close()

def save_student_answer(student_id, question_id, answer, is_correct, score, graded):
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO exam_scores (student_id, question_id, answer, is_correct, score, graded)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (student_id, question_id, answer, is_correct, score, graded))
    conn.commit()
    conn.close()