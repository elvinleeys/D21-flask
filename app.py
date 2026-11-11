import os                        # 컴퓨터 환경 변수(SECRET_KEY)를 읽는 도구
from dotenv import load_dotenv   # .env 파일을 읽어 환경 변수로 넣어 주는 도구 (python-dotenv)
from flask import Flask, render_template, request, abort, jsonify, redirect, url_for, flash, session   # Flask 도구, 템플릿 그리는 도구, '주소 뒤 ?조건'·폼 값 읽는 도구, '여기서 멈추고 에러 보내기' 도구, JSON 으로 바꿔 보내는 도구, '다른 주소로 가세요(302)' 도구, 함수 이름으로 주소 만드는 도구, '다음 화면에 한 번만 보일 안내' 도구, '이 브라우저만의 보관함(세션)' 도구
from data import load_classes, categories, filter_and_sort, find_class, to_api, stats   # data.py 에서 만든 함수들을 가져와요
from db import init_db, add_review, get_reviews   # db.py 에서 표 만들기·후기 넣기·후기 꺼내기 함수를 가져와요

load_dotenv()                    # .env 파일의 SECRET_KEY·FLASK_DEBUG 를 읽어요 (서버에 이미 같은 이름의 값이 있으면 그걸 그대로 써요)

app = Flask(__name__)            # 내 웹 서비스(앱)를 하나 만들어요
app.json.ensure_ascii = False    # JSON 에서 한글을 \uXXXX 로 바꾸지 말고 그대로 보내요
app.json.sort_keys = False       # 항목을 가나다·abc 순으로 섞지 말고 코드에 쓴 순서대로 보내요
secret_key = os.environ.get("SECRET_KEY")   # .env(또는 서버 설정)에서 비밀 열쇠를 꺼내요
if not secret_key:               # 열쇠가 없으면
    raise RuntimeError("SECRET_KEY 가 없어요. .env.example 을 보고 .env 를 만들어 주세요")   # 서버를 켜지 않고 이유를 알려줘요 (열쇠 없이 몰래 켜지는 것보다 안전해요)
app.secret_key = secret_key      # flash 안내·찜 목록(세션)은 브라우저 쿠키에 담겨요. 남이 위조하지 못하게 서명하는 열쇠예요

init_db()                        # 서버를 켤 때 reviews 표가 없으면 만들어요 (있으면 그대로 둬요)


@app.route("/")                  # 주소 / 로 요청이 오면
def home():                      # 이 함수가 실행돼요
    classes = load_classes()     # CSV 에서 클래스 목록을 읽어요
    return render_template("index.html", total=len(classes), categories=categories(classes))   # 전체 개수와 카테고리 목록을 넘겨 홈 화면을 그려요


@app.route("/about")             # 주소 /about 로 요청이 오면
def about():                     # 이 함수가 실행돼요
    return render_template("about.html")   # templates/about.html 화면을 돌려줘요


@app.route("/hello/<name>")      # 주소 /hello/ 뒤에 쓴 글자를 name 이라는 이름으로 받아요
def hello(name):                 # 받은 name 을 이 함수에 넘겨줘요
    return render_template("hello.html", name=name)   # hello.html 에 name 을 넘겨 화면을 그려요 (템플릿이 알아서 안전하게 바꿔줘요)


@app.route("/classes")           # 주소 /classes 로 요청이 오면
def class_list():                # 이 함수가 실행돼요
    category = request.args.get("category", "")   # 주소의 ?category=공예 를 읽어요 (없으면 빈 글자)
    sort = request.args.get("sort", "")           # 주소의 ?sort=price 를 읽어요 (없으면 빈 글자)
    classes = load_classes()                      # CSV 에서 클래스 목록을 읽어요
    result = filter_and_sort(classes, category, sort)   # 조건대로 거르고 정렬해요
    return render_template(
        "classes.html",                           # templates/classes.html 화면에
        classes=result,                           # 걸러진 클래스 목록
        categories=categories(classes),           # 고르는 상자에 넣을 카테고리 목록
        category=category,                        # 지금 고른 카테고리 (상자에 그대로 보이게)
        sort=sort,                                # 지금 고른 정렬 (상자에 그대로 보이게)
    )


@app.route("/class/<int:class_id>", methods=["GET", "POST"])   # 주소 /class/3 처럼 뒤에 '숫자'가 오면 class_id 로 받아요. 보기(GET)와 후기 저장(POST)을 둘 다 받아요
def class_detail(class_id):      # 받은 번호를 이 함수에 넘겨줘요
    c = find_class(load_classes(), class_id)   # 번호에 맞는 클래스를 찾아요
    if c is None:                # 그런 번호가 없으면
        abort(404)               # 여기서 멈추고 '404 없음'을 보내요 (아래 not_found 함수가 화면을 그려요)

    if request.method == "POST":   # 저장 버튼을 눌러 봉투(POST)가 왔으면
        nickname = request.form.get("nickname", "").strip()   # 봉투에서 닉네임을 꺼내요 (앞뒤 공백은 지워요)
        rating = request.form.get("rating", "")               # 봉투에서 별점을 꺼내요 (글자 "1"~"5")
        content = request.form.get("content", "").strip()     # 봉투에서 후기 내용을 꺼내요
        if not nickname or len(nickname) > 20:                 # 닉네임이 비었거나 20자보다 길면
            abort(400)                                         # '400 잘못된 요청'을 보내요
        if rating not in ("1", "2", "3", "4", "5"):            # 별점이 1~5 가 아니면 (주소창 등으로 이상한 값을 보낸 경우)
            abort(400)                                         # '400 잘못된 요청'을 보내요
        if not content or len(content) > 500:                  # 내용이 비었거나 500자보다 길면
            abort(400)                                         # '400 잘못된 요청'을 보내요
        add_review(class_id, nickname, int(rating), content)   # 확인을 통과했으면 DB 에 후기 하나를 넣어요 (별점은 글자 "4" → 숫자 4)
        flash("후기가 저장됐어요")                             # 다음 화면에 딱 한 번 보일 안내를 맡겨 둬요
        return redirect(url_for("class_detail", class_id=class_id))   # PRG: POST 를 처리한 뒤 302 로 같은 주소를 GET 으로 다시 열게 해요 (새로고침해도 GET 만 다시 가서 두 번 저장 안 돼요)

    return render_template("detail.html", c=c, reviews=get_reviews(class_id))   # DB 에서 이 클래스 후기를 최신 순으로 꺼내 상세 화면과 함께 그려요


@app.route("/class/<int:class_id>/wish", methods=["POST"])   # 찜하기·찜 취소는 값을 바꾸는 일이라 POST 로만 받아요
def toggle_wish(class_id):       # 받은 번호를 이 함수에 넘겨줘요
    if find_class(load_classes(), class_id) is None:   # 그런 번호의 클래스가 없으면
        abort(404)               # 찜하지 못하게 404 를 보내요
    wishlist = session.get("wishlist", [])   # 세션에서 내 찜 목록을 꺼내요 (처음이면 빈 목록)
    if class_id in wishlist:     # 이미 찜한 클래스면
        wishlist.remove(class_id)   # 목록에서 빼요 (찜 취소)
    else:                        # 아직 안 찜했으면
        wishlist.append(class_id)   # 목록에 넣어요 (찜하기)
    session["wishlist"] = wishlist   # 바뀐 목록을 세션에 다시 넣어요 (다시 넣어야 Flask 가 '바뀌었구나' 하고 저장해요)
    return redirect(url_for("class_detail", class_id=class_id))   # PRG: 302 로 상세 화면을 GET 으로 다시 열어요


@app.route("/wishlist")          # 주소 /wishlist 로 요청이 오면
def wishlist():                  # 이 함수가 실행돼요
    ids = session.get("wishlist", [])   # 세션에서 내 찜 번호 목록을 꺼내요
    classes = load_classes()            # CSV 에서 클래스 목록을 읽어요
    wished = []                         # 찾은 클래스를 담을 빈 목록
    for class_id in ids:                # 찜한 순서대로 번호를 하나씩 꺼내서
        c = find_class(classes, class_id)   # 그 번호의 클래스를 찾아요
        if c is not None:               # 찾았으면 (CSV 에서 사라진 번호는 건너뛰어요)
            wished.append(c)            # 목록에 넣어요
    return render_template("wishlist.html", classes=wished)   # 찜 목록 화면을 그려요


@app.route("/api/classes")       # 주소 /api/classes 로 요청이 오면
def api_classes():               # 이 함수가 실행돼요
    category = request.args.get("category", "")   # 주소의 ?category=공예 를 읽어요 (없으면 빈 글자 = 전체)
    result = filter_and_sort(load_classes(), category)   # 카테고리로 걸러요
    return jsonify(count=len(result), classes=[to_api(c) for c in result])   # 개수와 목록을 JSON 으로 보내요


@app.route("/api/classes/<int:class_id>")   # 주소 /api/classes/3 처럼 뒤에 숫자가 오면
def api_class(class_id):         # 받은 번호를 이 함수에 넘겨줘요
    c = find_class(load_classes(), class_id)   # 번호에 맞는 클래스를 찾아요
    if c is None:                # 그런 번호가 없으면
        abort(404)               # 404 를 보내요 (아래 not_found 가 /api 주소라서 JSON 에러로 답해요)
    return jsonify(to_api(c))    # 찾았으면 그 클래스 하나를 JSON 으로 보내요


@app.route("/api/stats")         # 주소 /api/stats 로 요청이 오면
def api_stats():                 # 이 함수가 실행돼요
    return jsonify(stats(load_classes()))   # 통계를 JSON 으로 보내요


@app.errorhandler(404)           # 어디서든 404(없는 페이지)가 생기면
def not_found(error):            # 이 함수가 실행돼요
    if request.path.startswith("/api/"):   # /api 로 시작하는 주소면 (프로그램이 읽는 주소)
        return jsonify(error="찾는 클래스가 없어요"), 404   # JSON 에러 메시지 + 상태 코드 404
    return render_template("404.html"), 404   # 그 밖의 주소면 '찾는 페이지가 없어요' 화면 + 진짜 상태 코드 404 를 함께 보내요


@app.errorhandler(500)           # 코드에서 예상 못 한 에러가 나면 (debug 가 켜진 내 컴퓨터에선 대신 자세한 에러 화면이 떠요)
def server_error(error):         # 이 함수가 실행돼요
    if request.path.startswith("/api/"):   # /api 로 시작하는 주소면
        return jsonify(error="잠시 문제가 생겼어요"), 500   # JSON 에러 메시지 + 상태 코드 500
    return render_template("500.html"), 500   # 그 밖의 주소면 친절한 안내 화면 + 상태 코드 500 (에러 내용은 숨겨요)


if __name__ == "__main__":       # python app.py 로 직접 켤 때만 아래 줄이 실행돼요 (서버의 gunicorn 은 이 줄을 실행하지 않아요)
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")   # .env 에 FLASK_DEBUG=1 이 있는 내 컴퓨터에서만 debug 를 켜요
