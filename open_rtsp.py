import cv2

cv2.namedWindow("RTSP View", cv2.WINDOW_NORMAL)
cap = cv2.VideoCapture(
    "rtsp://127.0.0.1:8554/video"
)  # or put "localhost" instead of "127.0.0.1"
while True:
    ret, frame = cap.read()
    if ret:
        cv2.imshow("RTSP View", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        print("Unable to open camera")
        break
cap.release()
cv2.destroyAllWindows()
