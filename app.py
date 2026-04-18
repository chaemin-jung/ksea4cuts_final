from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import os
import requests
from utils.collage_generator import create_collage
from utils.lastest import get_latest_photo_folder
from utils.printer import print_image
from utils.prepare_image import prepare_image_for_print
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = 'ksea4cuts_final'


# ---------------- RESET ----------------
@app.before_request
def reset_if_new():
    if "initialized" not in session:
        session.clear()
        session["initialized"] = True


# ---------------- BASIC ----------------
@app.route('/')
def start():
    return render_template('start.html')


@app.route('/cam')
def cam():
    return render_template('cam.html')


# ---------------- FRAME / COPIES ----------------
@app.route('/select_frame', methods=['POST'])
def set_frame():
    session['selected_frame'] = request.json.get('frame')
    return '', 204

# ---------------- CAPTURE ----------------
@app.route('/start_capture')
def start_capture():
    session['shot'] = 0
    return '', 204


@app.route('/status')
def status():
    shot = session.get('shot', 0)
    countdown = session.get('countdown', 10)  # 카운트다운을 10초로 설정

    # 촬영 진행
    if shot < 4:
        if countdown > 0:
            session['countdown'] = countdown - 1  # 카운트다운 감소
        else:
            if shot < 4:  # 촬영되지 않은 경우에만 진행
                try:
                    # 촬영 후 shot 값을 증가시킴
                    requests.post('http://localhost:5052/capture', json={'index': shot+1})
                    session['shot'] = shot + 1
                    session['photo_folder'] = get_latest_photo_folder()
                    session['countdown'] = 10  # 카운트다운 리셋
                except Exception as e:
                    print("❌ camera error:", e)

    # 촬영 완료된 상태 (shot >= 4)에서 카운트다운 및 촬영 진행을 멈춤
    if shot >= 4:
        session['countdown'] = 0  # 카운트다운 중지

    return jsonify({
        "countdown": countdown,
        "shot": session.get('shot', 0),
        "done": session.get('shot', 0) >= 4,
        "session_id": get_latest_photo_folder().split('/')[-1]
    })

# ---------------- APPLY FRAME ----------------
@app.route('/apply_frame')
def apply_frame():

    if "photo_folder" not in session:
        return "❌ invalid session", 400

    photo_folder = session['photo_folder']
    selected_frame = session.get("selected_frame")

    if not os.path.exists(photo_folder):
        return "❌ 사진 없음", 400

    if not selected_frame:
        return "❌ 프레임 선택 안됨", 400

    frame_path = os.path.join("static", "frames", selected_frame)

    final_image = create_collage(photo_folder, frame_path)

    # 프린트용 변환
    flat_path = final_image.replace(".jpg", "_flat.jpg")
    prepare_image_for_print(final_image, flat_path)

    web_path = flat_path.replace("static/", "")

    return redirect(url_for('result', final_image=web_path))


# ---------------- RESULT ----------------
@app.route('/result')
def result():
    final_image = request.args.get("final_image")
    return render_template('result.html', final_image=final_image)


# ---------------- PRINT ----------------
@app.route('/print', methods=['POST'])
def print_result():
    if "photo_folder" not in session:
        return jsonify(success=False, error="invalid session"), 400

    data = request.get_json()
    image_path = data.get("path")

    full_path = os.path.join(os.getcwd(), "static", image_path)

    if not os.path.exists(full_path):
        return jsonify(success=False, error="file not found"), 404

    copies = session.get("copies", 2)
    real_prints = copies // 2   # 🔥 핵심 로직

    print(f"🖨️ printing {real_prints} copies")

    success = print_image(full_path, real_prints)

    return jsonify(success=success)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)