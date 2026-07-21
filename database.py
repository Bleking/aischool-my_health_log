import sqlite3
import datetime

conn = sqlite3.connect('healthcare.db')
cursor = conn.cursor()

create_table_query = """
CREATE TABLE IF NOT EXISTS my_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATETIME NOT NULL,  -- 기록 날짜
    weight FLOAT NOT NULL,
    height FLOAT NOT NULL,
    systolic INT NOT NULL,
    diastolic INT NOT NULL,
    blood_sugar INT NOT NULL,
    steps INT,
    sleep_hours FLOAT,
    memo TEXT
);
"""

cursor.execute(create_table_query)
conn.commit()
