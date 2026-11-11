import csv                       # 파이썬 기본 CSV 읽기 도구 (빈칸을 nan 이 아니라 빈 글자 "" 로 줘요)
from pathlib import Path         # 파일 위치(경로)를 다루는 도구

# 이 파일(data.py)이 있는 폴더 → data → classes.csv (프로젝트 폴더 안에 있어야 서버에 같이 올라가요)
CSV_PATH = Path(__file__).resolve().parent / "data" / "classes.csv"


def to_number(text):             # 글자를 숫자로 바꾸는 함수
    text = text.strip()          # 앞뒤 공백을 지워요
    return float(text) if text else None   # 글자가 있으면 숫자로, 비어 있으면 None(값 없음)으로


def won(number):                 # 숫자를 '25,000원' 모양 글자로 바꾸는 함수
    return f"{number:,.0f}원"    # 세 자리마다 쉼표, 소수점 없이, 뒤에 '원'


def load_classes():              # CSV 를 읽어 클래스 목록을 만드는 함수
    classes = []                 # 결과를 담을 빈 목록
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:   # CSV 파일을 열어요 (한글 깨짐 방지)
        for row in csv.DictReader(f):   # 한 줄씩 꺼내요 (row["정가"] 처럼 제목으로 꺼낼 수 있어요)
            price = to_number(row["정가"])       # 정가 (비어 있으면 None)
            sale = to_number(row["할인가"])      # 할인가 (비어 있으면 None)
            rating = to_number(row["평점"])      # 평점 (비어 있으면 None)
            reviews = int(row["리뷰수"] or 0)    # 리뷰 수 (비어 있으면 0개)
            sell = sale if sale is not None else price   # 판매가: 할인가가 있으면 할인가, 없으면 정가
            on_sale = sale is not None and price is not None and sale < price   # 진짜 할인 중일 때만 True

            classes.append({
                "id": int(row["id"]),            # 클래스 번호 (상세 주소 /class/번호 에 써요)
                "category": row["카테고리"],     # 카테고리
                "region": row["지역"],           # 지역
                "name": row["클래스명"],         # 클래스명
                "price": price,                  # 정가 숫자 (없으면 None)
                "sale_price": sale,              # 할인가 숫자 (없으면 None)
                "sell_price": sell,              # 판매가 숫자 (정렬할 때 써요, 없으면 None)
                "rating": rating,                # 평점 숫자 (정렬할 때 써요, 없으면 None)
                "reviews": reviews,              # 리뷰 수
                "on_sale": on_sale,              # 할인 중인지 (True/False)
                "discount_pct": round((1 - sale / price) * 100) if on_sale else None,   # 할인율 % (할인 중이 아니면 None)
                "price_text": won(price) if price is not None else "",                # 취소선에 쓸 정가 글자
                "sell_text": won(sell) if sell is not None else "가격 문의",           # 화면에 보일 판매가 글자
                "rating_text": f"★ {rating:.1f} ({reviews})" if rating is not None else "아직 리뷰가 없어요",   # 화면에 보일 평점 글자
            })
    return classes               # 완성된 목록을 돌려줘요


def find_class(classes, class_id):   # 번호로 클래스 하나를 찾는 함수
    return next((c for c in classes if c["id"] == class_id), None)   # 처음 맞는 것을 돌려주고, 없으면 None


def to_api(c):                   # 클래스 하나를 JSON 으로 내보낼 모양으로 바꾸는 함수
    def whole(n):                # 가격은 원 단위라 25000.0 대신 25000 으로
        return int(n) if n is not None else None   # 값이 없으면 None 그대로 (JSON 에선 null)
    return {
        "id": c["id"],                       # 번호
        "category": c["category"],           # 카테고리
        "region": c["region"],               # 지역
        "name": c["name"],                   # 클래스명
        "price": whole(c["price"]),          # 정가 (없으면 null)
        "sale_price": whole(c["sale_price"]),   # 할인가 (없으면 null)
        "sell_price": whole(c["sell_price"]),   # 판매가 (없으면 null)
        "rating": c["rating"],               # 평점 (없으면 null)
        "reviews": c["reviews"],             # 리뷰 수
    }


def average(numbers):            # 평균을 구하는 함수 (None 은 빼고)
    values = [n for n in numbers if n is not None]   # 빈칸(None)을 빼요
    return sum(values) / len(values) if values else None   # 남은 게 있으면 평균, 하나도 없으면 None


def stats(classes):              # 통계를 만드는 함수
    sell_avg = average(c["sell_price"] for c in classes)   # 판매가 평균 (빈칸 빼고)
    rating_avg = average(c["rating"] for c in classes)     # 평점 평균 (빈칸 빼고)
    return {
        "total": len(classes),                                                   # 전체 개수
        "avg_sell_price": round(sell_avg) if sell_avg is not None else None,     # 평균 판매가 (원 단위로 반올림)
        "price_inquiry_count": sum(c["sell_price"] is None for c in classes),    # '가격 문의' 개수
        "avg_rating": round(rating_avg, 2) if rating_avg is not None else None,  # 평균 평점 (소수 둘째 자리)
        "no_review_count": sum(c["rating"] is None for c in classes),            # '리뷰 없음' 개수
        "by_category": {cat: sum(c["category"] == cat for c in classes) for cat in categories(classes)},   # 카테고리별 개수
    }


def categories(classes):         # 카테고리 이름 목록을 만드는 함수
    return sorted({c["category"] for c in classes})   # 겹치는 이름은 하나로 합치고 가나다순으로


def filter_and_sort(classes, category="", sort=""):   # 거르고 정렬하는 함수
    result = [c for c in classes if not category or c["category"] == category]   # 카테고리를 골랐으면 그것만 남겨요
    if sort == "price":          # 싼 순이면
        result.sort(key=lambda c: (c["sell_price"] is None, c["sell_price"] or 0))   # 가격 없는 건 맨 뒤, 나머지는 싼 것부터
    elif sort == "rating":       # 평점 순이면
        result.sort(key=lambda c: (c["rating"] is None, -(c["rating"] or 0)))      # 평점 없는 건 맨 뒤, 나머지는 높은 것부터
    return result                # 거르고 정렬한 목록을 돌려줘요


if __name__ == "__main__":       # python data.py 로 직접 실행하면 아래 점검을 해요
    rows = load_classes()        # CSV 를 읽어요
    texts = [c[k] for c in rows for k in ("sell_text", "price_text", "rating_text")]   # 화면에 보일 글자를 모두 모아요
    assert not any("nan" in t.lower() or "None" in t or t.startswith("0") for t in texts), "nan/None/0 이 보여요"
    by_price = filter_and_sort(rows, sort="price")               # 싼 순으로 정렬해서
    assert by_price[-1]["sell_text"] == "가격 문의"               # 맨 뒤가 '가격 문의' 인지
    assert all(c["category"] == "공예" for c in filter_and_sort(rows, "공예"))   # 공예만 남는지
    assert find_class(rows, 2)["name"] == "라탄 바구니" and find_class(rows, 999) is None   # 번호 찾기가 맞는지
    s = stats(rows)                                                   # 통계를 만들어서
    assert s["total"] == sum(s["by_category"].values())               # 카테고리별 합 = 전체 개수인지
    assert to_api(find_class(rows, 13))["sell_price"] is None         # 가격 빈칸이 None(JSON null) 인지
    print(f"점검 통과: {len(rows)}개, 카테고리 {categories(rows)}")
