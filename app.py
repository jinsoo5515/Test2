import streamlit as st

import storage

st.set_page_config(page_title="쇼핑리스트", page_icon="🛒", layout="centered")

st.session_state.setdefault("editing_id", None)
st.session_state.setdefault("add_error", "")
st.session_state.setdefault("edit_error", "")

# 목록은 세션에 캐시하지 않고 매 실행/콜백마다 파일에서 읽는다.
# (캐시하면 탭/기기 여러 곳에서 쓸 때 서로의 변경을 덮어쓴다)
# 주의: session_state의 "items" 키/속성은 dict 메서드와 충돌하므로 쓰지 않는다.
items: list[dict] = storage.load_items()


# ---------- 콜백 ----------
# 모든 변경은 LOCK 안에서 파일의 최신 목록을 읽어 수정·저장한다.
def on_add():
    name = st.session_state.get("add_name", "")
    qty = st.session_state.get("add_qty", 1)
    with storage.LOCK:
        try:
            storage.add_item(storage.load_items(), name, qty)
        except ValueError:
            st.session_state["add_error"] = "아이템 이름을 입력해 주세요."
            return
    st.session_state["add_error"] = ""


def on_toggle(item_id: str):
    checked = st.session_state.get(f"chk_{item_id}", False)
    open(r"C:/Users/User/AppData/Local/Temp/claude/15af9671870f89f0/1d35de09-9eff-4e80-a6e7-265cd4c5f6d4/scratchpad/toggle.log", "a", encoding="utf-8").write(f"{item_id[:6]} {checked}" + chr(10))  # TEMP-DEBUG
    with storage.LOCK:
        storage.set_checked(storage.load_items(), item_id, checked)


def on_delete(item_id: str):
    with storage.LOCK:
        storage.delete_item(storage.load_items(), item_id)
    if st.session_state["editing_id"] == item_id:
        st.session_state["editing_id"] = None


def on_start_edit(item_id: str):
    item = next((i for i in storage.load_items() if i["id"] == item_id), None)
    if item is None:
        return
    st.session_state["editing_id"] = item_id
    st.session_state["edit_error"] = ""
    st.session_state[f"edit_name_{item_id}"] = item["name"]
    st.session_state[f"edit_qty_{item_id}"] = item["quantity"]


def on_save_edit(item_id: str):
    name = st.session_state.get(f"edit_name_{item_id}", "")
    qty = st.session_state.get(f"edit_qty_{item_id}", 1)
    with storage.LOCK:
        try:
            storage.update_item(storage.load_items(), item_id, name, qty)
        except ValueError:
            st.session_state["edit_error"] = "아이템 이름을 입력해 주세요."
            return
    st.session_state["editing_id"] = None
    st.session_state["edit_error"] = ""


def on_cancel_edit():
    st.session_state["editing_id"] = None
    st.session_state["edit_error"] = ""


def on_clear_checked():
    with storage.LOCK:
        storage.clear_checked(storage.load_items())
    st.session_state["editing_id"] = None


# ---------- 스타일 ----------
# 이 Streamlit 버전은 테마 색을 CSS 변수로 노출하지 않으므로, 카드 배경은 글자색(currentColor) 기준
# color-mix로 만들어 라이트/다크 모두 자동 대응한다. 실제 색은 .streamlit/config.toml에서 정한다.
# data-testid(stHorizontalBlock, stColumn, stCheckbox, stForm)는 Streamlit 버전에 민감하므로
# 버전을 올린 뒤에는 화면을 꼭 다시 확인할 것. 우리 쪽 요소는 key(st-key-*) 클래스로 지정한다.
CSS = """
<style>
.block-container { max-width: 640px; padding-top: 2.2rem; padding-bottom: 3rem; }
h1 { font-size: 1.9rem !important; padding-bottom: .2rem !important; }

/* 진행 상황 카드 */
.st-key-progress_card {
    background: color-mix(in srgb, currentColor 7%, transparent);
    border-radius: 16px; padding: .9rem 1.1rem .7rem; gap: .35rem;
}
.progress-big { font-size: 1.5rem; font-weight: 700; line-height: 1.2; }
.progress-big small { font-size: .9rem; font-weight: 500; opacity: .65; margin-left: .35rem; }
.st-key-progress_card [data-testid="stProgress"] { margin-top: .1rem; }

/* 추가 폼 */
[data-testid="stForm"] {
    border: none; border-radius: 16px;
    background: color-mix(in srgb, currentColor 7%, transparent); padding: .8rem;
}

/* 좁은 화면에서도 가로 한 줄 유지 (Streamlit 기본은 모바일에서 세로로 쌓임) */
.st-key-add_card [data-testid="stHorizontalBlock"],
[class*="st-key-item"] [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important; align-items: center; gap: .4rem !important;
}
.st-key-add_card [data-testid="stColumn"],
[class*="st-key-item"] [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; }
.st-key-add_card [data-testid="stColumn"]:nth-child(1) { flex: 1 1 0 !important; }
.st-key-add_card [data-testid="stColumn"]:nth-child(2) { flex: 0 0 6.2rem !important; }
.st-key-add_card [data-testid="stColumn"]:nth-child(3) { flex: 0 0 auto !important; }

/* 아이템 카드 */
[class*="st-key-item"] {
    background: color-mix(in srgb, currentColor 7%, transparent);
    border-radius: 14px; padding: .3rem .7rem; gap: 0;
}
[class*="st-key-item"] [data-testid="stColumn"]:nth-child(1) { flex: 0 0 1.8rem !important; }
[class*="st-key-item"] [data-testid="stColumn"]:nth-child(2) { flex: 1 1 0 !important; }
[class*="st-key-item"] [data-testid="stColumn"]:nth-child(n+3) { flex: 0 0 2.3rem !important; }
/* 이름은 st.text(서식 해석 없음)로 그린다. 마크다운으로 그리면 URL 자동 링크 등이 입력값을 왜곡한다. */
[class*="st-key-item"] [data-testid="stText"] {
    font-family: inherit; font-size: 1.05rem; line-height: 1.4;
    white-space: normal; overflow-wrap: anywhere; margin: 0;
}
[class*="st-key-itemdone_"] [data-testid="stText"] { opacity: .5; text-decoration: line-through; }

/* 수정 카드 */
[class*="st-key-editcard_"] [data-testid="stForm"] { padding: .6rem; }

/* 아이콘 버튼 */
[class*="st-key-item"] button { padding: 0; min-height: 2.3rem; width: 2.3rem; }
.st-key-clear_checked button { width: 100%; }

/* 완료 영역 */
[data-testid="stExpander"] { border: none; }
[data-testid="stExpander"] summary { font-weight: 600; }

/* 빈 목록 */
.empty-box { text-align: center; padding: 2.2rem 1rem; opacity: .85; }
.empty-box .emoji { font-size: 3rem; line-height: 1.2; }
.empty-box .msg { font-size: 1.05rem; margin-top: .4rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------- UI ----------
def render_row(item: dict):
    iid = item["id"]
    if st.session_state["editing_id"] == iid:
        with st.container(key=f"editcard_{iid}"):
            with st.form(f"edit_form_{iid}"):
                c1, c2 = st.columns([3, 1.2])
                c1.text_input("이름", key=f"edit_name_{iid}", max_chars=storage.MAX_NAME_LEN)
                c2.number_input("수량", min_value=1, max_value=storage.MAX_QUANTITY, step=1,
                                key=f"edit_qty_{iid}")
                b1, b2 = st.columns(2)
                b1.form_submit_button("저장", on_click=on_save_edit, args=(iid,),
                                      type="primary", icon=":material/check:", use_container_width=True)
                b2.form_submit_button("취소", on_click=on_cancel_edit,
                                      icon=":material/close:", use_container_width=True)
            if st.session_state["edit_error"]:
                st.warning(st.session_state["edit_error"])
        return

    prefix = "itemdone" if item["checked"] else "item"
    with st.container(key=f"{prefix}_{iid}"):
        c_chk, c_name, c_edit, c_del = st.columns(4, vertical_alignment="center")
        st.session_state[f"chk_{iid}"] = item["checked"]  # 다른 탭의 변경과 어긋나지 않게 동기화
        c_chk.checkbox(
            "체크", key=f"chk_{iid}",
            on_change=on_toggle, args=(iid,), label_visibility="collapsed",
        )
        c_name.text(f"{item['name']} ×{item['quantity']}")
        c_edit.button(" ", key=f"edit_{iid}", on_click=on_start_edit, args=(iid,),
                      help="수정", icon=":material/edit:", type="tertiary")
        c_del.button(" ", key=f"del_{iid}", on_click=on_delete, args=(iid,),
                     help="삭제", icon=":material/delete:", type="tertiary")


st.title("🛒 쇼핑리스트")

total = len(items)
done = sum(1 for i in items if i["checked"])
with st.container(key="progress_card"):
    st.markdown(
        f'<div class="progress-big">{done} / {total}<small>완료</small></div>',
        unsafe_allow_html=True,
    )
    st.progress(done / total if total else 0.0)

with st.container(key="add_card"):
    with st.form("add_form", clear_on_submit=True, border=False):
        c1, c2, c3 = st.columns([4, 1.5, 1.5], vertical_alignment="center")
        c1.text_input("아이템", key="add_name", placeholder="무엇을 살까요?",
                      max_chars=storage.MAX_NAME_LEN, label_visibility="collapsed")
        c2.number_input("수량", min_value=1, max_value=storage.MAX_QUANTITY, value=1, step=1,
                        key="add_qty", label_visibility="collapsed")
        c3.form_submit_button("추가", on_click=on_add, type="primary", icon=":material/add:")
if st.session_state["add_error"]:
    st.warning(st.session_state["add_error"])

if not items:
    st.markdown(
        '<div class="empty-box"><div class="emoji">🧺</div>'
        '<div class="msg">장바구니가 비었어요.<br>살 물건을 위에서 추가해 보세요!</div></div>',
        unsafe_allow_html=True,
    )
else:
    for item in [i for i in items if not i["checked"]]:
        render_row(item)

    checked_items = [i for i in items if i["checked"]]
    if checked_items:
        with st.expander(f"완료 ({len(checked_items)})", expanded=True):
            for item in checked_items:
                render_row(item)
            st.button("완료 항목 모두 삭제", key="clear_checked", on_click=on_clear_checked,
                      icon=":material/delete_sweep:")
