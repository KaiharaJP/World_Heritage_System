import os
import csv
import random
from typing import List, Dict

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/quiz", tags=["quiz"])

CSV_PATH = os.environ.get("CSV_PATH", "data\csv\world_heritage.csv")
IMAGE_URL_PREFIX = "/images"
IMAGE_BASE_URL = os.environ.get("IMAGE_BASE_URL")

_dataset_cache: List[Dict[str, str]] | None = None


def _load_dataset() -> List[Dict[str, str]]:
	entries: List[Dict[str, str]] = []
	if not os.path.exists(CSV_PATH):
		raise FileNotFoundError(f"CSV not found: {CSV_PATH}")
	with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
		reader = csv.DictReader(f)
		for row in reader:
			name = (row.get("name") or "").strip()
			image_path_raw = (row.get("image_pass") or row.get("image_path") or "").strip()
			country_name = (row.get("country_name") or "").strip()
			if not name or not image_path_raw:
				continue
			# CSV が Windows 形式の区切りでも動くように正規化
			image_path_norm = image_path_raw.replace("\\", "/")
			filename = os.path.basename(image_path_norm)
			image_url = f"{IMAGE_URL_PREFIX}/{filename}"
			entries.append({
				"name": name,
				"image_url": image_url,
				"filename": filename,
				"country_name":country_name
			})
	return entries


def _get_dataset() -> List[Dict[str, str]]:
	global _dataset_cache
	if _dataset_cache is None:
		_dataset_cache = _load_dataset()
	return _dataset_cache


@router.get("")
def get_quiz(request: Request):
	dataset = _get_dataset()
	if len(dataset) < 4:
		raise HTTPException(status_code=400, detail="Dataset must contain at least 4 entries")
	answer_entry = random.choice(dataset)
	others_pool = [e for e in dataset if e is not answer_entry]
	options_pool = random.sample(others_pool, 3)
	options: List[str] = [answer_entry["name"], *[e["name"] for e in options_pool]]
	random.shuffle(options)
	base = (IMAGE_BASE_URL or str(request.base_url)).rstrip("/")
	image_url = f"{base}{IMAGE_URL_PREFIX}/{answer_entry['filename']}"
	return {
		"question": "この世界遺産は何でしょう？　国名:"+answer_entry["country_name"],
		"image_url": image_url,
		"options": options,
		"answer": answer_entry["name"],
	}
