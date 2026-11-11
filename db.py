import sqlite3                   # 파이썬 기본 SQLite 도구 (따로 설치할 필요 없어요)
from contextlib import closing   # 다 쓰면 연결을 꼭 닫아 주는 도구
from pathlib import Path         # 파일 위치(경로)를 다루는 도구

DB_PATH = Path(__file__).resolve().parent / "reviews.db"   # 이 파일(db.py) 옆에 reviews.db 를 만들어요


def connect():                   # DB 에 연결하는 함수
    conn = sqlite3.connect(DB_PATH)   # reviews.db 파일을 열어요 (없으면 새로 만들어요)
    conn.row_factory = sqlite3.Row    # 꺼낸 줄을 row["nickname"] 처럼 칸 이름으로 읽게 해요
    return conn                  # 연결을 돌려줘요


def init_db():                   # 표를 만드는 함수 (이미 있으면 그냥 넘어가요)
    with closing(connect()) as conn:   # 연결하고, 끝나면 자동으로 닫아요
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,              -- 후기 번호 (자동으로 1, 2, 3 …)
                class_id   INTEGER NOT NULL,                               -- 어느 클래스의 후기인지 (꼭 있어야 해요)
                nickname   TEXT    NOT NULL,                               -- 닉네임 (꼭 있어야 해요)
                rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),-- 별점 (1~5 만 들어가요)
                content    TEXT    NOT NULL,                               -- 후기 내용 (꼭 있어야 해요)
                created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))   -- 저장 시각 (안 넣으면 지금 한국 시각)
            )
        """)
        conn.commit()            # 바꾼 내용을 파일에 확정해요


def add_review(class_id, nickname, rating, content):   # 후기 하나를 넣는 함수
    with closing(connect()) as conn:   # 연결하고, 끝나면 자동으로 닫아요
        conn.execute(
            "INSERT INTO reviews (class_id, nickname, rating, content) VALUES (?, ?, ?, ?)",   # ? 자리에 값이 하나씩 들어가요 (값을 SQL 글자에 직접 붙이지 않아서 안전해요)
            (class_id, nickname, rating, content),   # ? 자리에 순서대로 들어갈 값들
        )
        conn.commit()            # 바꾼 내용을 파일에 확정해요


def get_reviews(class_id):       # 그 클래스의 후기를 최신 순으로 꺼내는 함수
    with closing(connect()) as conn:   # 연결하고, 끝나면 자동으로 닫아요
        rows = conn.execute(
            "SELECT * FROM reviews WHERE class_id = ? ORDER BY id DESC",   # 이 클래스 것만, 번호가 큰(나중에 쓴) 것부터
            (class_id,),         # ? 자리에 들어갈 값 (값이 하나여도 끝에 쉼표가 있어야 '묶음'이 돼요)
        ).fetchall()             # 결과를 모두 가져와요
    return [dict(r) for r in rows]   # 한 줄씩 딕셔너리로 바꿔 돌려줘요 (템플릿에서 r.nickname 으로 써요)


if __name__ == "__main__":       # python db.py 로 직접 실행하면 아래 점검을 해요
    import tempfile              # 진짜 reviews.db 를 건드리지 않게 임시 폴더를 써요
    with tempfile.TemporaryDirectory() as tmp:
        DB_PATH = Path(tmp) / "test.db"   # 점검할 때만 임시 DB 를 써요
        init_db()                         # 표를 만들고
        init_db()                         # 두 번 불러도 에러가 안 나는지
        add_review(2, "민지", 4, "재밌어요")      # 2번 클래스에 후기 둘,
        add_review(2, "준호", 5, "또 갈래요")
        add_review(3, "다른반", 3, "보통")        # 3번 클래스에 후기 하나를 넣어요
        rows = get_reviews(2)
        assert [r["nickname"] for r in rows] == ["준호", "민지"]   # 2번 것만, 최신 순인지
        assert rows[0]["created_at"][:2] == "20"                   # 저장 시각이 자동으로 들어갔는지
        try:
            add_review(2, "x", 7, "별점 7점")                      # 별점 7점은
            raise AssertionError("7점이 들어갔어요")
        except sqlite3.IntegrityError:                             # 표가 막아야 해요
            pass
        print("점검 통과")
