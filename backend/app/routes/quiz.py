import os
import csv
import random
from typing import List, Dict, Optional, Set
from threading import Lock

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/quiz", tags=["quiz"])

# 環境変数またはデフォルトパス
CSV_PATH = os.environ.get("CSV_PATH", "data/csv/world_heritage.csv")
IMAGE_URL_PREFIX = "/images"
IMAGE_BASE_URL = os.environ.get("IMAGE_BASE_URL")

_dataset_cache: Optional[List[Dict[str, str]]] = None

# exclude が渡らない場合でも重複出題しないためのプール（1プロセス内）
_remaining_filenames: Optional[List[str]] = None
_pool_lock = Lock()


def _load_dataset() -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    # パスのセパレータをOSに合わせて修正などが必要な場合は適宜調整
    # ここでは単純に存在確認
    if not os.path.exists(CSV_PATH):
        # コンテナ環境などでパスが異なる場合のエラーハンドリング
        print(f"File not found: {os.path.abspath(CSV_PATH)}")
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
                "country_name": country_name
            })
    return entries


def _get_dataset() -> List[Dict[str, str]]:
    global _dataset_cache
    if _dataset_cache is None:
        _dataset_cache = _load_dataset()
    return _dataset_cache


def _ensure_remaining_filenames(dataset: List[Dict[str, str]]):
    global _remaining_filenames
    if _remaining_filenames is None or len(_remaining_filenames) == 0:
        filenames = [e.get("filename") for e in dataset if e.get("filename")]
        random.shuffle(filenames)
        _remaining_filenames = filenames


@router.get("")
def get_quiz(
    request: Request,
    exclude: Optional[str] = Query(
        default=None,
        description="既出問題の除外ID（カンマ区切り。idはレスポンスのid=filename）",
    ),
):
    dataset = _get_dataset()
    if len(dataset) < 4:
        raise HTTPException(status_code=400, detail="Dataset must contain at least 4 entries")

    exclude_set: Set[str] = set()
    if exclude:
        exclude_set = {part.strip() for part in exclude.split(",") if part.strip()}

    by_filename = {e.get("filename"): e for e in dataset if e.get("filename")}

    if exclude_set:
        # 既出(exclude)を除外して answer を選ぶ（除外しすぎて空なら除外を無視して選ぶ）
        available_answers = [e for e in dataset if e.get("filename") not in exclude_set]
        if not available_answers:
            available_answers = dataset
        answer_entry = random.choice(available_answers)
    else:
        # exclude が無い場合はサーバ側プールで重複なし
        with _pool_lock:
            _ensure_remaining_filenames(dataset)
            if not _remaining_filenames:
                _ensure_remaining_filenames(dataset)
            chosen_filename = _remaining_filenames.pop()
        answer_entry = by_filename.get(chosen_filename) or random.choice(dataset)

    # その他の選択肢はデータセット全体から answer を除外してランダムに選ぶ
    others_pool = [e for e in dataset if e.get("filename") != answer_entry.get("filename")]

    # name 重複に備えて、選択肢は name 単位でユニークにサンプリング
    other_names = sorted({e.get("name") for e in others_pool if e.get("name") and e.get("name") != answer_entry.get("name")})
    if len(other_names) < 3:
        raise HTTPException(status_code=500, detail="Not enough unique entries to generate options")

    distractors = random.sample(other_names, 3)
    options: List[str] = [answer_entry["name"], *distractors]
    random.shuffle(options)

    base = (IMAGE_BASE_URL or str(request.base_url)).rstrip("/")
    image_url = f"{base}{IMAGE_URL_PREFIX}/{answer_entry['filename']}"

    return {
        "id": answer_entry["filename"],
        "question": f"この世界遺産は何でしょう？ (国名: {answer_entry['country_name']})",
        "image_url": image_url,
        "options": options,
        "answer": answer_entry["name"],
    }