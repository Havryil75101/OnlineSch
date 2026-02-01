import sqlite3

DB_PATH = "database.db"

class Database:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.db.cursor()
        self.create_tables()
        self.add_classes()
        self.generate_schedule()  # создаём готовое расписание
        self.cursor.execute(
            "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
            (5578984865,) 
        )
        self.db.commit()

    # ===== Создание таблиц =====
    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            name TEXT PRIMARY KEY
        )""")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            class TEXT REFERENCES classes(name)
        )""")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            class TEXT,
            day TEXT,
            lesson_num INTEGER,
            lesson TEXT,
            PRIMARY KEY (class, day, lesson_num)
        )""")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )""")
        self.db.commit()

    # ===== Добавление классов 1–10 A/B =====
    def add_classes(self):
        classes = [f"{i}{letter}" for i in range(1, 11) for letter in ["A","B"]]
        for cls in classes:
            self.cursor.execute("INSERT OR IGNORE INTO classes (name) VALUES (?)", (cls,))
        self.db.commit()

    # ===== Генерация готового расписания =====
    def generate_schedule(self):
        subjects = [
            "Математика","Русский язык","Литература","История","Биология","География",
            "Физика","Химия","Английский","ИЗО","Музыка","Физкультура","Технология"
        ]
        days = ["mon","tue","wed","thu","fri"]

        for i in range(1, 11):
            for letter in ["A","B"]:
                cls = f"{i}{letter}"
                for d_index, day in enumerate(days):
                    used_subjects = set()
                    for lesson_num in range(1,7):  # 6 уроков в день
                        subj_index = (lesson_num + d_index + i + (0 if letter=="A" else 1)) % len(subjects)
                        lesson = subjects[subj_index]
                        # проверка, чтобы урок не повторялся в этот день
                        while lesson in used_subjects:
                            subj_index = (subj_index + 1) % len(subjects)
                            lesson = subjects[subj_index]
                        used_subjects.add(lesson)
                        self.cursor.execute("""
                            INSERT OR IGNORE INTO schedule (class, day, lesson_num, lesson) VALUES (?,?,?,?)
                        """, (cls, day, lesson_num, lesson))
        self.db.commit()

    # ===== Админ =====
    def is_admin(self, user_id):
        self.cursor.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
        return self.cursor.fetchone() is not None

    # ===== Работа с пользователем =====
    def set_user_class(self, user_id, cls):
        self.cursor.execute("INSERT OR REPLACE INTO users (user_id, class) VALUES (?,?)", (user_id, cls))
        self.db.commit()

    def get_user_class(self, user_id):
        self.cursor.execute("SELECT class FROM users WHERE user_id=?", (user_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    # ===== Работа с расписанием =====
    def get_schedule(self, cls, day):
        self.cursor.execute(
            "SELECT lesson_num, lesson FROM schedule WHERE class=? AND day=? ORDER BY lesson_num",
            (cls, day)
        )
        return self.cursor.fetchall()

    def add_lesson(self, cls, day, num, lesson):
        self.cursor.execute(
            "INSERT OR REPLACE INTO schedule (class, day, lesson_num, lesson) VALUES (?,?,?,?)",
            (cls, day, num, lesson)
        )
        self.db.commit()
