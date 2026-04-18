import cv2
import numpy as np
import os
import shutil

def create_collage_with_qr(photo_folder, frame_img_path):
    print(f"📂 [시작] 콜라주 생성 시작! Photo folder: {photo_folder}, Frame: {frame_img_path}")

    # 1. 프레임 로드
    frame = cv2.imread(frame_img_path, cv2.IMREAD_UNCHANGED)
    if frame is None or frame.shape[2] != 4:
        raise ValueError("❌ 프레임 이미지가 유효하지 않거나 알파 채널이 없습니다.")
    print("✅ 프레임 이미지 로드 성공")

    h_frame, w_frame = frame.shape[:2]

    # 2. 투명 영역 감지
    alpha = frame[:, :, 3]
    transparent_mask = (alpha < 128).astype(np.uint8) * 255
    contours, _ = cv2.findContours(transparent_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) < 8:
        raise ValueError("❌ 투명한 영역이 최소 8개 필요합니다.")
    print(f"✅ 투명 영역 {len(contours)}개 감지")

    bounding_boxes = sorted([cv2.boundingRect(c) for c in contours], key=lambda b: (b[1], b[0]))

    # 3. 사진 불러오기
    photos = []
    for i in range(1, 5):
        path = os.path.join(photo_folder, f"photo_{i}.jpg")
        photo = cv2.imread(path)
        if photo is None:
            raise ValueError(f"❌ {i}번째 사진이 없습니다: {path}")
        photos.append(photo)
    print("✅ 모든 사진 로드 성공")
    
    frame_rgb = frame[:, :, :3].copy()

    # 4. RGB 프레임 복사
    canvas = np.ones_like(frame_rgb) * 255  # 흰색 배경 (or 다른 배경)
    
    # Step 1: 오른쪽 (원본 flip)
    for i in range(4):
        right_idx = i * 2 + 1
        x_right, y_right, w_right, h_right = bounding_boxes[right_idx]
        resized = cv2.resize(photos[i], (w_right, h_right))
        flipped = cv2.flip(resized, 1)  # 👉 거울 모드 (좌우 반전)
        canvas[y_right:y_right+h_right, x_right:x_right+w_right] = flipped

    # Step 2: 왼쪽 (오른쪽 복사)
    for i in range(4):
        left_idx = i * 2
        right_idx = i * 2 + 1
        x_left, y_left, w_left, h_left = bounding_boxes[left_idx]
        x_right, y_right, w_right, h_right = bounding_boxes[right_idx]
        right_crop = canvas[y_right:y_right+h_right, x_right:x_right+w_right].copy()
        right_resized = cv2.resize(right_crop, (w_left, h_left))
        canvas[y_left:y_left+h_left, x_left:x_left+w_left] = right_resized

    print("✅ 오른쪽 (거울 모드) → 왼쪽 복사 완료")

    # 5. 각 영역에 사진 삽입
    for i in range(4):
        for j in range(2):
            x, y, w, h = bounding_boxes[i * 2 + j]
            resized = cv2.resize(photos[i], (w, h))
            canvas[y:y+h, x:x+w] = resized
    print("✅ 사진 삽입 완료")
    
    alpha = frame[:, :, 3] / 255.0
    for c in range(3):  # RGB
        canvas[:, :, c] = (alpha * frame[:, :, c] + (1 - alpha) * canvas[:, :, c]).astype(np.uint8)

    # 6. final.jpg 저장
    final_path = os.path.join(photo_folder, "final.jpg")   # ⭐ 이 줄 추가

    os.makedirs(photo_folder, exist_ok=True)

    if not cv2.imwrite(final_path, canvas):
        raise IOError(f"❌ final.jpg 저장 실패: {final_path}")

    print(f"✅ final.jpg 저장 완료: {final_path}")

    return final_path   # ⭐ 이것도 추가 (app.py 때문에 중요)