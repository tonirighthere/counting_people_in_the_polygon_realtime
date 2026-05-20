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


def create_zone(task_type, frame_shape):
    h, w = frame_shape[:2]

    if task_type == "POLYGON":
        polygon = np.array([
            [int(w * 0.50), int(h * 0.40)],
            [int(w * 0.70), int(h * 0.30)],
            [int(w * 0.85), int(h * 0.40)],
            [int(w * 0.60), int(h * 0.60)],
        ])
        zone = sv.PolygonZone(polygon=polygon, triggering_anchors=[sv.Position.BOTTOM_CENTER])
        zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.WHITE)
        return zone, zone_annotator

    if task_type == "LINE_CROSSING":
        start = sv.Point(int(w * 0.38), int(h * 0.32))
        end = sv.Point(int(w * 0.51), int(h * 0.32))
        zone = sv.LineZone(start=start, end=end, triggering_anchors=[sv.Position.CENTER])
        zone_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)
        return zone, zone_annotator

    return None, None


def annotate_detections(task_type, zone, detections, annotated_frame, box_annotator, label_annotator):
    counts = {}

    if len(detections) > 0 and detections.tracker_id is not None:
        if task_type == "POLYGON" and zone is not None:
            mask = zone.trigger(detections=detections)
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
