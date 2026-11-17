"""쇼핑리스트 데이터 저장/CRUD 모듈 (UI 의존성 없음)."""
import json
import os
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "items.json"
MAX_NAME_LEN = 100
MAX_QUANTITY = 999

# 여러 세션(탭/기기)이 같은 프로세스에서 "읽기 → 수정 → 저장"을 동시에 하지 않도록 직렬화한다.
LOCK = threading.RLock()


def _to_quantity(value) -> int:
    """수량을 1~MAX_QUANTITY 정수로 보정한다. 숫자가 아니면 1."""
    try:
        return min(MAX_QUANTITY, max(1, int(value)))
    except (TypeError, ValueError):
        return 1


def load_items() -> list[dict]:
    """파일에서 목록을 읽는다. 없거나 비었으면 빈 리스트, 깨졌으면 백업해 두고 빈 리스트."""
    try:
        text = DATA_FILE.read_text(encoding="utf-8")
    except OSError:
        return []
    if not text.strip():
        return []
    try:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("목록 형식이 아님")
    except ValueError:
        # 다음 저장이 깨진 파일을 덮어쓰기 전에 원본을 보존한다
        try:
            os.replace(DATA_FILE, DATA_FILE.with_name("items.corrupt.json"))
        except OSError:
            pass
        return []
    items = []
    for i in data:
        if not isinstance(i, dict) or not i.get("id"):
            continue
        name = str(i.get("name", "")).strip()
        if not name:
            continue
        items.append({
            "id": str(i["id"]),
            "name": name,
            "quantity": _to_quantity(i.get("quantity", 1)),
            "checked": bool(i.get("checked", False)),
            "created_at": str(i.get("created_at", "")),
        })
    return items


def save_items(items: list[dict]) -> None:
    """임시 파일에 쓴 뒤 교체해서 파일 손상을 방지한다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def add_item(items: list[dict], name: str, quantity: int = 1) -> dict:
    """아이템을 추가하고 저장한다. 빈 이름은 ValueError."""
    name = (name or "").strip()[:MAX_NAME_LEN]
    if not name:
        raise ValueError("이름을 입력하세요.")
    item = {
        "id": str(uuid.uuid4()),
        "name": name,
        "quantity": _to_quantity(quantity),
        "checked": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    items.append(item)
    save_items(items)
    return item


def update_item(items: list[dict], item_id: str, name: str, quantity: int) -> bool:
    """이름/수량을 수정한다. 없는 id면 False, 빈 이름은 ValueError."""
    name = (name or "").strip()[:MAX_NAME_LEN]
    if not name:
        raise ValueError("이름을 입력하세요.")
    for item in items:
        if item["id"] == item_id:
            item["name"] = name
            item["quantity"] = _to_quantity(quantity)
            save_items(items)
            return True
    return False


def delete_item(items: list[dict], item_id: str) -> bool:
    """아이템을 삭제한다. 없는 id면 False."""
    for i, item in enumerate(items):
        if item["id"] == item_id:
            del items[i]
            save_items(items)
            return True
    return False


def toggle_item(items: list[dict], item_id: str) -> bool:
    """체크 상태를 뒤집는다. 없는 id면 False."""
    for item in items:
        if item["id"] == item_id:
            item["checked"] = not item.get("checked", False)
            save_items(items)
            return True
    return False


def set_checked(items: list[dict], item_id: str, checked: bool) -> bool:
    """체크 상태를 지정한 값으로 설정한다. 없는 id면 False."""
    for item in items:
        if item["id"] == item_id:
            item["checked"] = bool(checked)
            save_items(items)
            return True
    return False


def clear_checked(items: list[dict]) -> int:
    """체크된 아이템을 모두 삭제하고 삭제 개수를 반환한다."""
    remaining = [i for i in items if not i.get("checked")]
    removed = len(items) - len(remaining)
    if removed:
        items[:] = remaining
        save_items(items)
    return removed
