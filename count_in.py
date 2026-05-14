import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

from core.app_count_in import CountInApp
from core.config import RTSP_URL_CAM1, MODEL_PATH

def main():
    app = CountInApp(rtsp_url=RTSP_URL_CAM1, model_path=MODEL_PATH)
    app.run()

if __name__ == "__main__":
    main()
