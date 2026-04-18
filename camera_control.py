from flask import Flask, request, jsonify
import os
from datetime import datetime
import subprocess
import threading
import time
from flask_cors import CORS
import cv2

app = Flask(__name__)
BASE_DIR = "static/photos"
CORS(app)

camera_port = None  # 카메라 포트 초기화
SESSION_FOLDER = None


# ✅ PTPCamera 프로세스 종료 (현재 코드에서는 필요 없으므로 삭제 가능)
def kill_ptpcamera():
    try:
        subprocess.run(["killall", "-9", "PTPCamera"], check=True)
        print("✅ PTPCamera 종료됨")
    except subprocess.CalledProcessError:
        print("❎ PTPCamera 프로세스 없음 (이미 종료됨)")


# ✅ 카메라 초기화 (cv2.VideoCapture 사용)
def initialize_camera():
    cap = cv2.VideoCapture(0)  # 기본 카메라 사용
    if not cap.isOpened():
        raise RuntimeError("❌ 카메라를 열 수 없습니다.")
    print("🎯 카메라 연결 성공")
    return cap


# 세션 폴더 생성
def update_last_folder(session_path):
    with open('static/last_folder.txt', 'w') as f:
        f.write(session_path)


def create_session_folder():
    global SESSION_FOLDER
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_path = os.path.join(BASE_DIR, timestamp)
    os.makedirs(session_path, exist_ok=True)
    os.chmod(session_path, 0o777)
    SESSION_FOLDER = session_path
    print(f"📂 세션 폴더 생성됨: {SESSION_FOLDER}")
    update_last_folder(SESSION_FOLDER)


# ✅ 카메라 연결 상태 확인
def check_camera_connection(cap):
    if not cap.isOpened():
        print("⚠️ 카메라가 연결되지 않았습니다.")
        return False
    return True


# ✅ 카메라 상태 유지 (USB keep-alive 대체)
def usb_keep_alive(cap):
    while True:
        if not check_camera_connection(cap):
            print("❌ 카메라 연결이 끊어졌습니다. 다시 연결해주세요.")
            break
        time.sleep(3)


# ✅ 촬영 함수
def capture_image(cap, photo_path):
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("❌ 사진 촬영 실패")

    # 사진 저장
    cv2.imwrite(photo_path, frame)
    print(f"📸 사진 저장 완료: {photo_path}")


# ✅ Flask route
@app.route('/capture', methods=['POST'])
def capture():
    try:
        global camera_port

        kill_ptpcamera()

        # 서버 시작 시 만들어둔 폴더 사용
        session_folder = SESSION_FOLDER

        index = request.json.get('index', 1)
        photo_path = os.path.join(session_folder, f"photo_{index}.jpg")

        print(f"📸 {index}번째 사진 저장 시도 → {photo_path}")

        # 촬영 시도
        capture_image(camera_port, photo_path)

        if not os.path.exists(photo_path):
            raise RuntimeError("❌ 사진 촬영 실패!")

        return jsonify(success=True, path=photo_path)

    except Exception as e:
        print(f"❌ 서버 오류 발생: {e}")
        return jsonify(success=False, error=str(e)), 500


# ✅ 메인 실행
if __name__ == '__main__':
    # 최초 세션 폴더 생성 (서버 실행 시 1회만)
    create_session_folder()

    # 카메라 초기화
    camera_port = initialize_camera()

    # USB Keep-Alive 스레드 시작
    keep_alive_thread = threading.Thread(target=usb_keep_alive, args=(camera_port,), daemon=True)
    keep_alive_thread.start()

    app.run(host='0.0.0.0', port=5052, debug=False)