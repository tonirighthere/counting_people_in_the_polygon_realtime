import queue
from ..threads.thread_capture import CaptureThread
from ..threads.thread_process import ProcessThread
from ..threads.thread_stream import StreamThread

class CameraController:
    def __init__(self, cam_id, src, task, model_path='resources/weights/yolov8n.pt'):
        self.cam_id = cam_id
        self.src = src
        self.task = task
        self.model_path = model_path
        
        self.capture_queue = queue.Queue(maxsize=2)
        self.process_queue = queue.Queue(maxsize=2)
        
        self.capture_thread = None
        self.process_thread = None
        self.stream_thread = None
        
        self.is_active = False

    def set_active(self, active):
        self.is_active = active
        if self.process_thread:
            self.process_thread.set_active(active)

    def start(self):
        self.capture_thread = CaptureThread(self.capture_queue, self.src)
        self.process_thread = ProcessThread(
            self.capture_queue, self.process_queue, 
            task_type=self.task, model_path=self.model_path
        )
        self.process_thread.set_active(self.is_active)
        self.stream_thread = StreamThread(self.cam_id, self.process_queue)

        self.capture_thread.start()
        self.process_thread.start()
        self.stream_thread.start()
        
    def stop(self):
        if self.capture_thread and self.capture_thread.isRunning():
            self.capture_thread.stop()
        if self.process_thread and self.process_thread.isRunning():
            self.process_thread.stop()
        if self.stream_thread and self.stream_thread.isRunning():
            self.stream_thread.stop()
        
        self.empty_queue(self.capture_queue)
        self.empty_queue(self.process_queue)

    def empty_queue(self, q):
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                break
