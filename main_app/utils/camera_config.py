import os

import json
import yaml


UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(UTILS_DIR))
CONFIG_DIR = os.path.join(ROOT_DIR, "resources", "config")
CAMERAS_YAML_PATH = os.path.join(CONFIG_DIR, "cameras.yaml")
LEGACY_CAMERAS_JSON_PATH = os.path.join(CONFIG_DIR, "cameras.json")

# Backward-compatible alias for old imports
CAMERAS_JSON_PATH = CAMERAS_YAML_PATH

def ensure_config_dir():
	os.makedirs(CONFIG_DIR, exist_ok=True)


def _is_valid_camera_config(camera_cfg):
	if not isinstance(camera_cfg, dict):
		return False

	return all(
		key in camera_cfg and isinstance(camera_cfg[key], str) and camera_cfg[key].strip()
		for key in ("url", "task", "name")
	)


def _normalize_cameras(raw_data):
	if not isinstance(raw_data, dict):
		return {}

	normalized = {}
	for cam_id, cam_cfg in raw_data.items():
		if isinstance(cam_id, str) and _is_valid_camera_config(cam_cfg):
			normalized[cam_id] = {
				"url": cam_cfg["url"].strip(),
				"task": cam_cfg["task"].strip(),
				"name": cam_cfg["name"].strip(),
			}

	return normalized


def _write_cameras(cameras_dict):
	with open(CAMERAS_YAML_PATH, "w", encoding="utf-8") as file_handle:
		yaml.safe_dump(cameras_dict, file_handle, allow_unicode=True, sort_keys=False)


def load_cameras():
	ensure_config_dir()

	if os.path.exists(CAMERAS_YAML_PATH):
		try:
			with open(CAMERAS_YAML_PATH, "r", encoding="utf-8") as file_handle:
				return _normalize_cameras(yaml.safe_load(file_handle))
		except Exception as error:
			print(f"[ConfigManager] Lỗi tải cameras.yaml: {error}")

	if os.path.exists(LEGACY_CAMERAS_JSON_PATH):
		try:
			with open(LEGACY_CAMERAS_JSON_PATH, "r", encoding="utf-8") as file_handle:
				migrated_cameras = _normalize_cameras(json.load(file_handle))
			_write_cameras(migrated_cameras)
			print("[ConfigManager] Đã migrate cameras.json -> cameras.yaml")
			return migrated_cameras
		except Exception as error:
			print(f"[ConfigManager] Lỗi migrate từ cameras.json: {error}")

	cameras = {}
	try:
		_write_cameras(cameras)
	except Exception as error:
		print(f"[ConfigManager] Lỗi ghi cameras.yaml mặc định: {error}")

	return cameras


def save_cameras(cameras_dict):
	"""Lưu cấu hình camera hiện tại vào file cameras.yaml"""
	ensure_config_dir()
	try:
		normalized = _normalize_cameras(cameras_dict)
		_write_cameras(normalized)
		print(f"[ConfigManager] Đã lưu {len(normalized)} camera vào file cấu hình.")
	except Exception as error:
		print(f"[ConfigManager] Lỗi lưu cameras.yaml: {error}")


CAMERAS = load_cameras()
