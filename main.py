from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sqlite3
import datetime
import math
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"

DATA_DIR.mkdir(parents=True, exist_ok=True)  # 데이터 경로가 없으면 경로 생성
DB_PATH = DATA_DIR / "healthcare.db"

# DB 불러오기
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

app = FastAPI(title="마이 헬스 로그 API", version="1.0")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

records = []  # 파일 저장

# 
class UserIn(BaseModel):
    name: str
    phone_no: str

class RecordIn(BaseModel):
    user_id: int
    date: str
    weight: float
    height: float
    systolic: int
    diastolic: int
    blood_sugar: int
    steps: int = 0
    sleep_hours: float = 0.0
    memo: str = ""

class ResultIn(BaseModel):
    user_id: int  # 회원 정보
    record_id: int
    bmi_value: int
    bmi_category: str
    blood_pressure: str
    blood_sugar: str

# BMI 계산
def calculate_bmi(record: RecordIn):
    height_m = record.height / 100
    bmi = record.weight / (height_m**2)

    # BMI 수치별 분류
    if bmi >= 25:
        bmi_category = "비만"
    elif bmi >= 23:
        bmi_category = "과체중"
    elif bmi >= 18.5:
        bmi_category = "정상"
    else:
        bmi_category = "저체중"

    # 혈압 수치별 분류
    if record.systolic >= 140 or record.diastolic >= 90:
        blood_pressure_warning = "고혈압"
    elif record.systolic >= 120 or record.diastolic >= 80:
        blood_pressure_warning = "주의"
    else:
        blood_pressure_warning = "정상"

    # 공복 혈당 수치별 분류
    if record.blood_sugar >= 126:
        blood_sugar_warning = "당뇨 의심"
    elif record.blood_sugar >= 100:
        blood_sugar_warning = "공복혈당장애"
    else:
        blood_sugar_warning = "정상"
    
    return bmi, bmi_category, blood_pressure_warning, blood_sugar_warning

# 전화번호에서 숫자 이외의 문자 제거 (-)
def normalize_phone_no(number: str):
    return re.sub(r"\D", "", number)

# 관리자 확인
def verify_admin(admin_user_id: int):
    local_conn = sqlite3.connect(DB_PATH)
    local_conn.row_factory = sqlite3.Row
    local_cursor = local_conn.cursor()
    
    try:
        local_cursor.execute(
            """SELECT user_id, is_admin 
            FROM users 
            WHERE user_id = ?
            """, 
            (admin_user_id,),
        )
        
        admin_user = local_cursor.fetchone()
        
        if admin_user is None:
            raise HTTPException(status_code=401, detail="로그인 정보가 존재하지 않습니다.")
        
        is_admin = bool(admin_user["is_admin"])
        
        if not is_admin:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    finally:
        local_conn.close()


@app.get("/")
def read_root():
    print("Fast API 실행 완료")
    return FileResponse(FRONTEND_DIR / "index.html")

# 회원 가입
@app.post("/auth")
def authenticate_user(login: UserIn):
    name = login.name.strip()
    phone_no = normalize_phone_no(login.phone_no)

    if not name:
        raise HTTPException(
            status_code=400,
            detail="이름을 입력해주세요.",
        )

    if len(phone_no) not in (10, 11):
        raise HTTPException(
            status_code=400,
            detail="올바른 전화번호를 입력해주세요.",
        )

    local_conn = sqlite3.connect(DB_PATH)
    local_conn.row_factory = sqlite3.Row
    local_cursor = local_conn.cursor()

    try:
        # 기존에 하이픈을 포함해 저장된 데이터도 함께 검색
        local_cursor.execute(
            """
            SELECT user_id, name, phone_no, is_admin
            FROM users
            WHERE REPLACE(REPLACE(phone_no, '-', ''), ' ', '') = ?
            """,
            (phone_no,),
        )

        existing_user = local_cursor.fetchone()

        # 1. 전화번호가 없으면 신규 회원 등록
        if existing_user is None:
            local_cursor.execute(
                """
                INSERT INTO users (is_admin, name, phone_no)
                VALUES (?, ?, ?)
                """,
                (False, name, phone_no),
            )

            local_conn.commit()
            user_id = local_cursor.lastrowid

            return {
                "status": "signup",
                "message": "회원가입이 완료되었습니다.",
                "user_id": user_id,
                "name": name,
                "is_admin": False,
            }

        # 2. 전화번호는 있지만 이름이 다르면 로그인 거부
        if existing_user["name"].strip() != name:
            raise HTTPException(
                status_code=409,
                detail="이미 존재하는 회원입니다.",
            )

        # 3. 전화번호와 이름이 모두 일치하면 로그인 성공
        return {
            "status": "login",
            "message": "로그인에 성공했습니다.",
            "user_id": existing_user["user_id"],
            "name": existing_user["name"],
            "is_admin": bool(existing_user["is_admin"]),
        }

    finally:
        local_conn.close()

@app.get("/survey", include_in_schema=False)
def serve_survey_page():
    return FileResponse(FRONTEND_DIR / "survey.html")

@app.get("/result", include_in_schema=False)
def serve_result_page():
    return FileResponse(FRONTEND_DIR / "result.html")

@app.get("/admin", include_in_schema=False)
def serve_admin_page():
    return FileResponse(FRONTEND_DIR / "admin.html")

# 건강 기록 추가. 저장 후 BMI·분류·경고를 계산해 응답
@app.post("/records/{user_id}")
def save_records(user_id: int, record: RecordIn):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()

    date_obj = datetime.datetime.strptime(record.date, "%Y-%m-%d").date()

    try:
        # 건강 기록 입력하는 회원 정보
        local_cursor.execute(
            """INSERT INTO health_records (
                date, user_id, weight, height, systolic, diastolic, blood_sugar, steps, sleep_hours, memo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                date_obj,
                record.user_id,
                record.weight, record.height,
                record.systolic, record.diastolic, record.blood_sugar,
                record.steps, record.sleep_hours, record.memo,
            ),
        )
        local_conn.commit()

        # BMI 계산
        bmi, bmi_category, blood_pressure_warning, blood_sugar_warning = calculate_bmi(record)

        return {
            "message": f"회원 {record.user_id} 건강 수치 저장 완료",
            "bmi": round(bmi, 2),
            "bmi_category": bmi_category,
            "blood_pressure_warning": blood_pressure_warning,
            "blood_sugar_warning": blood_sugar_warning,
        }
    finally:
        local_conn.close()


# 전체 기록 조회 (모든 회원에 대한)
@app.get("/records")
async def get_all_records():
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()
    
    try:
        local_cursor.execute("SELECT * FROM health_records")
        records = local_cursor.fetchall()

        # Get column names
        col_names = [description[0] for description in local_cursor.description]

        # Format records into a list of dictionaries
        formatted_records = []
        for record_data in records:
            formatted_records.append(dict(zip(col_names, record_data)))

        return {"total_count": len(formatted_records), "records": formatted_records}
    finally:
        local_conn.close()

# 회원 한 명에 대한 기록 조회. 없으면 404 반환
@app.get("/records/{user_id}")
def get_one_record(user_id):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute( """SELECT * FROM health_records WHERE user_id = ?""", (user_id,))
        local_conn.commit()

        return {"message": f"회원 {user_id}에 대한 건강 기록 불러오기 완료"}
    finally:
        local_conn.close()

## 관리자 기능
# 관리자 페이지
@app.get("/admin/users")
def get_admin_users(
    admin_user_id: int,
    name: str = "",
):
    verify_admin(admin_user_id)

    keyword = name.strip()
    name_pattern = f"{keyword}%"

    local_conn = sqlite3.connect(DB_PATH)
    local_conn.row_factory = sqlite3.Row
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute("""
            SELECT
                u.user_id, u.name, u.phone_no,

                hr.record_id, hr.date,
                hr.weight, hr.height,
                hr.systolic, hr.diastolic, hr.blood_sugar,
                hr.steps, hr.sleep_hours, hr.memo,

                result.bmi_value, result.bmi_category, result.blood_pressure_category, result.blood_sugar_category

            FROM users AS u

            LEFT JOIN health_records AS hr
                ON hr.record_id = (
                    SELECT hr2.record_id
                    FROM health_records AS hr2
                    WHERE hr2.user_id = u.user_id
                    ORDER BY
                        hr2.date DESC,
                        hr2.record_id DESC
                    LIMIT 1
                )

            LEFT JOIN health_results AS result
                ON result.record_id = hr.record_id

            WHERE
                u.is_admin = 0  # FALSE
                AND (
                    ? = ''
                    OR u.name LIKE ?
                )

            ORDER BY
                u.name ASC,
                u.user_id ASC
            """,
            (
                keyword,
                name_pattern,
            ),
        )

        rows = local_cursor.fetchall()

        users = []

        for row in rows:
            user_data = {
                "user_id": row["user_id"], "name": row["name"], "phone_no": row["phone_no"],
                "record_id": row["record_id"], "date": row["date"],
                "weight": row["weight"], "height": row["height"],
                "systolic": row["systolic"], "diastolic": row["diastolic"], "blood_sugar": row["blood_sugar"],
                "bmi": row["bmi_value"], "bmi_category": row["bmi_category"],
                "blood_pressure_category": row["blood_pressure_category"],
                "blood_sugar_category": row["blood_sugar_category"],
                "steps": row["steps"], "sleep_hours": row["sleep_hours"], "memo": row["memo"],
            }
        
            users.append(user_data)

        return {
            "total_count": len(users),
            "keyword": keyword,
            "users": users,
        }

    finally:
        local_conn.close()

# 기록 수정 (한 회원의 기록 한개 수정)
@app.put("/records/{user_id}/{record_id}")
def edit_records(user_id: int, record_id: int, record: RecordIn):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()
    
    try:
        record.user_id = user_id
        
        local_cursor.execute(
            """UPDATE health_records SET
                date = ?, weight = ?, height = ?, systolic = ?, diastolic = ?,
                blood_sugar = ?, steps = ?, sleep_hours = ?, memo = ?
            WHERE record_id = ? AND user_id = ?""",
            (
                datetime.datetime.strptime(record.date, "%Y-%m-%d").date(),
                record.weight, record.height,
                record.systolic, record.diastolic, record.blood_sugar,
                record.steps, record.sleep_hours, record.memo,
                record_id, user_id
            ),
        )
        local_conn.commit()

        # Recalculate BMI and warnings for the updated record
        bmi, bmi_category, blood_pressure_warning, blood_sugar_warning = calculate_bmi(record)

        return {
            "message": f"회원 {user_id}의 기록 {record_id} 수정 완료",
            "bmi": round(bmi, 2),
            "bmi_category": bmi_category,
            "blood_pressure_warning": blood_pressure_warning,
            "blood_sugar_warning": blood_sugar_warning,
        }
    finally:
        local_conn.close()


# 기록 삭제 (한 회원의 기록 한개 삭제)
@app.delete("/records/{user_id}/{record_id}")
def delete_records(user_id: int, record_id: int):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute("""DELETE FROM health_records WHERE record_id = ? AND user_id = ?""", (record_id, user_id))
        local_conn.commit()
        return {"message": f"회원 {user_id}의 기록 {record_id} 삭제 완료"}
    finally:
        local_conn.close()

# (회원, 관리자) 날짜 범위로 검색 (회원은 본인의 정보만 조회 가능)
@app.get("/search/{user_id}")
def search_by_dates(user_id: int, start_date: str, end_date: str):  # YYYY-MM-DD
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()

    try:
        # 날짜 문자열을 datetime 객체로 변환
        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        local_cursor.execute(
            """SELECT * FROM health_records WHERE user_id = ? AND date BETWEEN ? AND ? ORDER BY date ASC""",
            (user_id, start_date_obj, end_date_obj)
        )
        records = local_cursor.fetchall()

        # Get column names
        col_names = [description[0] for description in local_cursor.description]

        # Format records into a list of dictionaries
        formatted_records = []
        for record_data in records:
            formatted_records.append(dict(zip(col_names, record_data)))

        return {"total_count": len(formatted_records), "records": formatted_records}
    finally:
        local_conn.close()

# (관리자용) 날짜 범위로 검색 (관리자는 모든 회원의 정보 조회 가능)
@app.get("/search")
def search_by_dates(start_date: str, end_date: str):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()

    try:
        # 날짜 문자열을 datetime 객체로 변환
        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        local_cursor.execute(
            """SELECT * FROM health_records WHERE date BETWEEN ? AND ? ORDER BY date ASC""",
            (start_date_obj, end_date_obj)
        )
        records = local_cursor.fetchall()

        # Get column names
        col_names = [description[0] for description in local_cursor.description]

        # Format records into a list of dictionaries
        formatted_records = []
        for record_data in records:
            formatted_records.append(dict(zip(col_names, record_data)))

        return {"total_count": len(formatted_records), "records": formatted_records}
    finally:
        local_conn.close()


# 특정 회원의 평균 통계 반환
@app.get("/stats/{user_id}")
def get_stats(user_id: int):
    local_conn = sqlite3.connect(DB_PATH)
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute("""
        SELECT 
            AVG(weight), AVG(height), AVG(systolic), AVG(diastolic), AVG(blood_sugar), 
            AVG(steps), AVG(sleep_hours)  
        FROM health_records WHERE user_id = ?
        """, (user_id,))
        stats = local_conn.commit()
        
        return {"message": f"회원 {user_id}에 대한 건강 기록 평균"}
    finally:
        local_conn.close()
