import queue
import time

import cv2
import numpy as np
import supervision as sv


def create_box_annotator():
    try:
        return sv.BoundingBoxAnnotator(thickness=2)
    except AttributeError:
        return sv.BoxAnnotator(thickness=2)


def select_points_interactive(task_type, frame, window_name="Select Points"):
    points = []
    temp_frame = frame.copy()

    if task_type == "POLYGON":
        instruction = "Polygon: Chọn 4 điểm chính xác, nhấn Enter để lưu, chuột phải để xóa điểm cuối"
    else:
        instruction = "Line: Chọn 2 điểm chính xác, nhấn Enter để lưu, chuột phải để xóa điểm cuối"

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # Không cho phép chọn quá số điểm yêu cầu
            if task_type == "POLYGON" and len(points) >= 4:
                return
            if task_type == "LINE_CROSSING" and len(points) >= 2:
                return

            points.append([x, y])
            cv2.circle(temp_frame, (x, y), 5, (0, 0, 255), -1)
            
            if task_type == "POLYGON":
                if len(points) > 1:
                    cv2.line(temp_frame, tuple(points[-2]), tuple(points[-1]), (255, 0, 0), 2)
                # Đóng vòng polygon nếu đã đủ 4 điểm
                if len(points) == 4:
                    cv2.line(temp_frame, tuple(points[3]), tuple(points[0]), (255, 0, 0), 2)
            elif task_type == "LINE_CROSSING" and len(points) == 2:
                cv2.line(temp_frame, tuple(points[0]), tuple(points[1]), (255, 0, 0), 2)
            
            cv2.imshow(window_name, temp_frame)
            
        elif event == cv2.EVENT_RBUTTONDOWN:
            if points:
                points.pop()
                temp_frame[:] = frame.copy()
                cv2.putText(temp_frame, instruction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                for i, p in enumerate(points):
                    cv2.circle(temp_frame, tuple(p), 5, (0, 0, 255), -1)
                    if i > 0:
                        if task_type == "POLYGON" or (task_type == "LINE_CROSSING" and i == 1):
                            cv2.line(temp_frame, tuple(points[i-1]), tuple(p), (255, 0, 0), 2)
                cv2.imshow(window_name, temp_frame)

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)
        
    cv2.putText(temp_frame, instruction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow(window_name, temp_frame)

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter
            if task_type == "POLYGON" and len(points) == 4:
                break
            elif task_type == "LINE_CROSSING" and len(points) == 2:
                break
            else:
                print(f"[Warning] Không đủ điểm để xác định {task_type}")
        elif key == 27: # Esc
            break

    cv2.destroyWindow(window_name)
    return points


def create_zone(task_type, points):
    if not points:
        return None, None

    if task_type == "POLYGON":
        polygon = np.array(points)
        # trigger() → kiểm tra object có trong vùng không
        zone = sv.PolygonZone(polygon=polygon, triggering_anchors=[sv.Position.BOTTOM_CENTER])
        # vẽ polygon lên frame
        zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.WHITE)
        return zone, zone_annotator

    if task_type == "LINE_CROSSING":
        start = sv.Point(points[0][0], points[0][1])
        end = sv.Point(points[1][0], points[1][1])
        zone = sv.LineZone(start=start, end=end, triggering_anchors=[sv.Position.CENTER])
        zone_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)
        return zone, zone_annotator

    return None, None


def annotate_detections(task_type, zone, detections, annotated_frame, box_annotator, label_annotator):
    counts = {}
    # Điều kiện kích hoạt: Phải có đối tượng (len(detections) > 0) và đối tượng đó phải được định danh
    if len(detections) > 0 and detections.tracker_id is not None:
        if task_type == "POLYGON" and zone is not None:
            # Trả về một mảng Boolean (True/False) cho biết đối tượng nào đang nằm trong đa giác.
            mask = zone.trigger(detections=detections)
            # Lọc ra chỉ những đối tượng nằm trong vùng
            in_zone_detections = detections[mask]
            counts = {"count": len(in_zone_detections)}

            labels = [f"ID:{tid}" for tid in in_zone_detections.tracker_id]
            annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=in_zone_detections)
            annotated_frame = label_annotator.annotate(
                scene=annotated_frame,
                detections=in_zone_detections,
                labels=labels,
            )

        elif task_type == "LINE_CROSSING" and zone is not None:
            zone.trigger(detections=detections)
            counts = {"in": zone.in_count, "out": zone.out_count}

            labels = [f"ID:{tid}" for tid in detections.tracker_id]
            annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
            annotated_frame = label_annotator.annotate(
                scene=annotated_frame,
                detections=detections,
                labels=labels,
            )

    return annotated_frame, counts


def annotate_zone_frame(task_type, zone, zone_annotator, annotated_frame):
    if zone is None or zone_annotator is None:
        return annotated_frame

    if task_type == "LINE_CROSSING":
        return zone_annotator.annotate(frame=annotated_frame, line_counter=zone)

    return zone_annotator.annotate(scene=annotated_frame)


def update_fps_counter(fps_counter, fps_start_time, last_fps):
    current_time = time.time()
    fps_counter += 1

    fps_smooth = last_fps
    elapsed_fps_time = current_time - fps_start_time
    if elapsed_fps_time >= 1.0:
        fps_smooth = int(round(fps_counter / elapsed_fps_time))
        fps_counter = 0
        fps_start_time = current_time

    return current_time, fps_counter, fps_start_time, fps_smooth


def put_latest(queue_obj, item):
    if not queue_obj.full():
        queue_obj.put(item)
        return

    try:
        queue_obj.get_nowait()
        queue_obj.put(item)
    except queue.Empty:
        pass


def draw_fps(annotated_frame, fps_smooth):
    cv2.putText(
        annotated_frame,
        f"FPS: {fps_smooth}",
        (2400, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0, 255, 0),
        4,
    )
