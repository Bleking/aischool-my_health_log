from fastapi import FastAPI
from pydantic import BaseModel

import sqlite3
import datetime
import math

# DB 불러오기
conn = sqlite3.connect('healthcare.db')
cursor = conn.cursor()

app = FastAPI(title="마이 헬스 로그 API", version="1.0")

records = []  # 파일 저장

class RecordIn(BaseModel):
    date: str  # 측정일
    weight: float  # 몸무게 (kg)
    height: float  # 키 (cm)
    systolic: int  # 수축기 혈압
    diastolic: int  # 이완기 혈압
    blood_sugar: int  # 공복 혈당(mg/dL)
    steps: int = 0  # (선택 사항)
    sleep_hours: float = 0.0  # (선택 사항)
    memo: str = ""  # (선택 사항)

# BMI 계산
def calculate_bmi(height, weight):
    height_m = record.height / 100
    bmi = record.weight / (height_m**2)

    # Determine BMI classification
    if bmi >= 25:
        bmi_category = "비만"
    elif bmi >= 23:
        bmi_category = "과체중"
    elif bmi >= 18.5:
        bmi_category = "정상"
    else:
        bmi_category = "저체중"

    # 혈압
    if record.systolic >= 140 or record.diastolic >= 90:
        blood_pressure_warning = "고혈압"
    elif record.systolic >= 120 or record.diastolic >= 80:
        blood_pressure_warning = "주의"
    else:
        blood_pressure_warning = "정상"

    # 공복 혈당
    if record.blood_sugar >= 126:
        blood_sugar_warning = "당뇨 의심"
    elif record.blood_sugar >= 100:
        blood_sugar_warning = "공복혈당장애"
    else:
        blood_sugar_warning = "정상"
        
    return bmi_category, blood_pressure_warning, blood_sugar_warning


@app.get("/")
def read_root():
    print("Fast API 실행 완료")
    return {"message": "내 헬스 로그 API"}

# 건강 기록 추가. 저장 후 BMI·분류·경고를 계산해 응답
@app.post("/records")
def save_records(record: RecordIn):
    # Create a new connection and cursor for this thread/request
    local_conn = sqlite3.connect('healthcare.db')
    local_cursor = local_conn.cursor()

    date_obj = datetime.datetime.strptime(record.date, "%Y-%m-%d").date()
    
    try:
        # Insert data into the database using the local cursor
        local_cursor.execute(
            """INSERT INTO my_health (
                date, weight, height, systolic, diastolic, blood_sugar, steps, sleep_hours, memo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                date_obj,
                record.weight,
                record.height,
                record.systolic,
                record.diastolic,
                record.blood_sugar,
                record.steps,
                record.sleep_hours,
                record.memo,
            ),
        )
        local_conn.commit()

        # BMI 계산
        bmi_category, blood_pressure_warning, blood_sugar_warning = calculate_bmi(record.height, record.weight)
        
        return {
            "message": "건강 수치 저장 완료",
            "bmi": round(bmi, 2),
            "bmi_category": bmi_category,
            "blood_pressure_warning": blood_pressure_warning, 
            "blood_sugar_warning": blood_sugar_warning, 
        }
    finally:
        # Ensure the connection is closed
        local_conn.close()


# 전체 기록 조회 (개수 포함)
@app.get("/records")
async def get_all_records():
    cursor.execute("SELECT * FROM my_health")
    records = cursor.fetchall()
    
    col_names = [description[0] for description in cursor.description]
    
    formatted_records = []
    for record in records:
        formatted_records.append(dict(zip(col_names, record)))
    
    return {"total_count": len(formatted_records), "records": formatted_records}

# 기록 하나 조회. 없으면 404 반환
@app.get("/records/{record_id}")
def get_one_record(record_id):
    local_conn = sqlite3.connect('healthcare.db')
    local_cursor = local_conn.cursor()
    
    try:
        local_cursor.execute( """SELECT FROM my_health WHERE id = ?""", (record_id))
        local_conn.commit()
      
        return {"message": "회원 {record_id}에 대한 건강 기록 불러오기 완료"}
    finally:
        local_conn.close()


# 기록 수정
@app.put("/records/{record_id}")
def edit_records(record_id):
    return {"message": "회원 {record_id}에 대한 건강 기록 수정 완료"}


# 기록 삭제
@app.delete("/records/{record_id}")
def delete_records(record_id):
    local_conn = sqlite3.connect('healthcare.db')
    local_cursor = local_conn.cursor()
    
    try:
        local_cursor.execute("""DELETE FROM my_health WHERE id = ?""", (record_id))
        local_conn.commit()
        return {"message": f"회원 {record_id}에 대한 건강 기록 삭제 완료"}
    finally:
        local_conn.close()

# 날짜 범위로 검색
@app.get("/search")
def search_records():
    return

# 평균 체중 등 통계 반환
@app.get("/stats")
def load_stats():
    return
