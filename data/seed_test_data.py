import datetime
import re
import sqlite3
from pathlib import Path


# main.py와 같은 프로젝트 루트에서 실행하는 것을 기준으로 함
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "healthcare.db"


def normalize_phone_no(phone_no: str) -> str:
    """전화번호에서 숫자만 남긴다."""
    return re.sub(r"\D", "", phone_no)


def calculate_health_result(
    weight: float,
    height: float,
    systolic: int,
    diastolic: int,
    measured_blood_sugar: int,
) -> tuple[float, str, str, str]:
    """BMI, BMI 분류, 혈압 분류, 혈당 분류를 계산한다."""

    height_m = height / 100
    bmi = weight / (height_m ** 2)

    if bmi >= 25:
        bmi_category = "비만"
    elif bmi >= 23:
        bmi_category = "과체중"
    elif bmi >= 18.5:
        bmi_category = "정상"
    else:
        bmi_category = "저체중"

    if systolic >= 140 or diastolic >= 90:
        blood_pressure_category = "고혈압"
    elif systolic >= 120 or diastolic >= 80:
        blood_pressure_category = "주의"
    else:
        blood_pressure_category = "정상"

    if measured_blood_sugar >= 126:
        blood_sugar_category = "당뇨 의심"
    elif measured_blood_sugar >= 100:
        blood_sugar_category = "공복혈당장애"
    else:
        blood_sugar_category = "정상"

    return (
        round(bmi, 2),
        bmi_category,
        blood_pressure_category,
        blood_sugar_category,
    )


def get_or_create_test_user(
    cursor: sqlite3.Cursor,
    name: str,
    phone_no: str,
) -> int:
    """전화번호로 사용자를 찾고, 없으면 신규 생성한다."""

    normalized_phone = normalize_phone_no(phone_no)

    cursor.execute(
        """
        SELECT
            user_id,
            name
        FROM users
        WHERE REPLACE(REPLACE(phone_no, '-', ''), ' ', '') = ?
        """,
        (normalized_phone,),
    )

    existing_user = cursor.fetchone()

    if existing_user is not None:
        user_id, existing_name = existing_user

        if existing_name.strip() != name:
            raise ValueError(
                f"해당 전화번호는 이미 '{existing_name}' 이름으로 "
                "등록되어 있습니다."
            )

        print(f"기존 회원 사용: user_id={user_id}, name={name}")
        return user_id

    cursor.execute(
        """
        INSERT INTO users (
            is_admin,
            name,
            phone_no
        )
        VALUES (?, ?, ?)
        """,
        (
            False,
            name,
            normalized_phone,
        ),
    )

    user_id = cursor.lastrowid

    print(f"신규 회원 생성: user_id={user_id}, name={name}")
    return user_id


def save_health_record(
    cursor: sqlite3.Cursor,
    user_id: int,
    record: dict,
) -> int:
    """
    같은 사용자의 같은 날짜 기록이 있으면 수정하고,
    없으면 신규 생성한다.
    """

    cursor.execute(
        """
        SELECT record_id
        FROM health_records
        WHERE user_id = ?
          AND date = ?
        """,
        (
            user_id,
            record["date"],
        ),
    )

    existing_record = cursor.fetchone()

    if existing_record is None:
        cursor.execute(
            """
            INSERT INTO health_records (
                date,
                user_id,
                weight,
                height,
                systolic,
                diastolic,
                blood_sugar,
                steps,
                sleep_hours,
                memo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["date"],
                user_id,
                record["weight"],
                record["height"],
                record["systolic"],
                record["diastolic"],
                record["blood_sugar"],
                record["steps"],
                record["sleep_hours"],
                record["memo"],
            ),
        )

        record_id = cursor.lastrowid
        action = "생성"

    else:
        record_id = existing_record[0]

        cursor.execute(
            """
            UPDATE health_records
            SET
                weight = ?,
                height = ?,
                systolic = ?,
                diastolic = ?,
                blood_sugar = ?,
                steps = ?,
                sleep_hours = ?,
                memo = ?
            WHERE record_id = ?
              AND user_id = ?
            """,
            (
                record["weight"],
                record["height"],
                record["systolic"],
                record["diastolic"],
                record["blood_sugar"],
                record["steps"],
                record["sleep_hours"],
                record["memo"],
                record_id,
                user_id,
            ),
        )

        action = "수정"

    (
        bmi_value,
        bmi_category,
        blood_pressure_category,
        blood_sugar_category,
    ) = calculate_health_result(
        weight=record["weight"],
        height=record["height"],
        systolic=record["systolic"],
        diastolic=record["diastolic"],
        measured_blood_sugar=record["blood_sugar"],
    )

    # 해당 건강 기록의 결과 행이 있는지 확인
    cursor.execute(
        """
        SELECT record_id
        FROM results
        WHERE record_id = ?
        """,
        (record_id,),
    )

    existing_result = cursor.fetchone()

    if existing_result is None:
        cursor.execute(
            """
            INSERT INTO results (
                user_id,
                record_id,
                bmi_value,
                bmi_category,
                blood_pressure,
                blood_sugar
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                record_id,
                bmi_value,
                bmi_category,
                blood_pressure_category,
                blood_sugar_category,
            ),
        )

    else:
        cursor.execute(
            """
            UPDATE results
            SET
                bmi_value = ?,
                bmi_category = ?,
                blood_pressure = ?,
                blood_sugar = ?
            WHERE record_id = ?
              AND user_id = ?
            """,
            (
                bmi_value,
                bmi_category,
                blood_pressure_category,
                blood_sugar_category,
                record_id,
                user_id,
            ),
        )

    print(
        f"[{action}] {record['date']} / "
        f"record_id={record_id} / "
        f"BMI={bmi_value}({bmi_category}) / "
        f"혈압={blood_pressure_category} / "
        f"혈당={blood_sugar_category}"
    )

    return record_id


def seed_test_data() -> None:
    today = datetime.date.today()

    # 몸무게와 키는 요청한 값으로 동일하게 유지
    # 혈압과 혈당을 날짜별로 변경하여 상태 비교가 가능하게 구성
    test_records = [
        {
            "date": (today - datetime.timedelta(days=2)).isoformat(),
            "weight": 68.0,
            "height": 173.0,
            "systolic": 116,
            "diastolic": 76,
            "blood_sugar": 92,
            "steps": 8500,
            "sleep_hours": 7.5,
            "memo": "정상 범위 테스트 데이터",
        },
        {
            "date": (today - datetime.timedelta(days=1)).isoformat(),
            "weight": 68.0,
            "height": 173.0,
            "systolic": 128,
            "diastolic": 82,
            "blood_sugar": 108,
            "steps": 5200,
            "sleep_hours": 6.0,
            "memo": "혈압 주의 및 공복혈당장애 테스트 데이터",
        },
        {
            "date": today.isoformat(),
            "weight": 68.0,
            "height": 173.0,
            "systolic": 142,
            "diastolic": 92,
            "blood_sugar": 131,
            "steps": 3100,
            "sleep_hours": 5.5,
            "memo": "고혈압 및 당뇨 의심 테스트 데이터",
        },
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        user_id = get_or_create_test_user(
            cursor=cursor,
            name="정승원",
            phone_no="010-1997-0927",
        )

        for record in test_records:
            save_health_record(
                cursor=cursor,
                user_id=user_id,
                record=record,
            )

        conn.commit()

        print()
        print("정승원 테스트 데이터 저장 완료")
        print(f"user_id: {user_id}")
        print(f"저장 건수: {len(test_records)}건")

    except Exception as error:
        conn.rollback()
        print(f"테스트 데이터 저장 실패: {error}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    seed_test_data()
