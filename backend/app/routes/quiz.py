import os
import csv
import random
from typing import List, Dict, Optional
from threading import Lock

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/quiz", tags=["quiz"])

# 環境変数またはデフォルトパス
CSV_PATH = os.environ.get("CSV_PATH", "data/csv/world_heritage.csv")
IMAGE_URL_PREFIX = "/images"
IMAGE_BASE_URL = os.environ.get("IMAGE_BASE_URL")

_dataset_cache: Optional[List[Dict[str, str]]] = None
# 追加: 再出現を避けるために残りプールを保持する
_remaining_answers: Optional[List[Dict[str, str]]] = None
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


# 追加: 残りプールを初期化 / リセットする
def _ensure_remaining_pool():
    global _remaining_answers
    if _remaining_answers is None or len(_remaining_answers) == 0:
        # _get_dataset() はグローバルキャッシュを返すので、
        # ここでは .copy() して独立したリストにする
        _remaining_answers = _get_dataset().copy()


@router.get("")
def get_quiz(request: Request):
    # ここで global宣言が必要です
    global _remaining_answers

    dataset = _get_dataset()
    if len(dataset) < 4:
        raise HTTPException(status_code=400, detail="Dataset must contain at least 4 entries")

    # answer の重複を避けるため、残りプールから選択する
    with _pool_lock:
        _ensure_remaining_pool()
        
        # 安全のためプールが空なら再初期化
        if not _remaining_answers:
            _ensure_remaining_pool()
        
        # プールからランダムに1つを選び、選ばれたらプールから削除する
        answer_entry = random.choice(_remaining_answers)
        
        # リストから削除（filenameが一致するものを除外して再構築）
        _remaining_answers = [e for e in _remaining_answers if e["filename"] != answer_entry["filename"]]

    # その他の選択肢はデータセット全体から answer を除外してランダムに選ぶ
    others_pool = [e for e in dataset if e is not answer_entry and e["name"] != answer_entry["name"]]
    
    # データが少なくて選択肢が作れない場合の安全策
    if len(others_pool) < 3:
         raise HTTPException(status_code=500, detail="Not enough unique entries to generate options")

    options_pool = random.sample(others_pool, 3)
    options: List[str] = [answer_entry["name"], *[e["name"] for e in options_pool]]
    random.shuffle(options)

    base = (IMAGE_BASE_URL or str(request.base_url)).rstrip("/")
    image_url = f"{base}{IMAGE_URL_PREFIX}/{answer_entry['filename']}"

    return {
        "question": f"この世界遺産は何でしょう？ (国名: {answer_entry['country_name']})",
        "image_url": image_url,
        "options": options,
        "answer": answer_entry["name"],
    }