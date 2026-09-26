import streamlit as st
import json
import random
import os
import uuid

# ==========================================
# CẤU HÌNH & QUẢN LÝ DỮ LIỆU
# ==========================================
DATA_FILE = 'flashcards.json'

def load_data():
    """Đọc dữ liệu từ file JSON. Nếu chưa có, tạo dữ liệu mẫu mặc định."""
    if not os.path.exists(DATA_FILE):
        # Dữ liệu mẫu kết hợp Toán học (THCS/THPT) và Tiếng Anh chuyên ngành
        default_cards = [
            {
                "id": str(uuid.uuid4()), 
                "front": "Định lý Pythagore (Tam giác vuông)", 
                "back": "Bình phương cạnh huyền bằng tổng bình phương hai cạnh góc vuông:\n\n$$a^2 + b^2 = c^2$$"
            },
            {
                "id": str(uuid.uuid4()), 
                "front": "Công thức nghiệm của phương trình bậc 2\n$$ax^2 + bx + c = 0$$", 
                "back": "$$x = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}$$ \nvới $$\\Delta = b^2 - 4ac$$"
            },
            {
                "id": str(uuid.uuid4()), 
                "front": "Yield Strength", 
                "back": "**Giới hạn chảy**\n\nỨng suất tại đó vật liệu bắt đầu biến dạng dẻo (không thể phục hồi hình dạng ban đầu)."
            }
        ]
        save_data(default_cards)
        return default_cards
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(cards):
    """Lưu danh sách thẻ vào file JSON."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(cards, f, ensure_ascii=False, indent=4)

# ==========================================
# KHỞI TẠO SESSION STATE (Trạng thái ứng dụng)
# ==========================================
if 'cards' not in st.session_state:
    st.session_state.cards = load_data()
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'flipped' not in st.session_state:
    st.session_state.flipped = False
if 'score' not in st.session_state:
    st.session_state.score = {"remember": 0, "forget": 0}

# ==========================================
# CÁC HÀM XỬ LÝ SỰ KIỆN (ACTIONS)
# ==========================================
def flip_card():
    st.session_state.flipped = not st.session_state.flipped

def next_card():
    if st.session_state.current_index < len(st.session_state.cards) - 1:
        st.session_state.current_index += 1
        st.session_state.flipped = False

def prev_card():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.session_state.flipped = False

def shuffle_cards():
    random.shuffle(st.session_state.cards)
    st.session_state.current_index = 0
    st.session_state.flipped = False

def mark_remember():
    st.session_state.score["remember"] += 1
    next_card()

def mark_forget():
    st.session_state.score["forget"] += 1
    next_card()

def delete_current_card():
    if st.session_state.cards:
        st.session_state.cards.pop(st.session_state.current_index)
        save_data(st.session_state.cards)
        # Điều chỉnh lại index nếu đang ở thẻ cuối cùng
        if st.session_state.current_index >= len(st.session_state.cards):
            st.session_state.current_index = max(0, len(st.session_state.cards) - 1)
        st.session_state.flipped = False

# ==========================================
# GIAO DIỆN NGƯỜI DÙNG (UI)
# ==========================================
st.set_page_config(page_title="Flashcards App", layout="centered")
st.title("📚 Ứng dụng Học tập Thắng Anh")

# --- Tabs chính của ứng dụng ---
tab_learn, tab_manage = st.tabs(["Lật Thẻ Học Tự Động", "Quản Lý Thẻ"])

# ------------------------------------------
# TAB 1: GIAO DIỆN HỌC TẬP
# ------------------------------------------
with tab_learn:
    if not st.session_state.cards:
        st.info("Chưa có thẻ nào. Hãy sang tab 'Quản Lý Thẻ' để thêm mới!")
    else:
        # Thống kê điểm số và nút trộn thẻ
        col_stat, col_shuffle = st.columns([3, 1])
        with col_stat:
            st.write(f"**Tiến độ:** Thẻ {st.session_state.current_index + 1} / {len(st.session_state.cards)} | "
                     f"✅ Nhớ: {st.session_state.score['remember']} | "
                     f"❌ Quên: {st.session_state.score['forget']}")
        with col_shuffle:
            st.button("🔀 Đảo ngẫu nhiên", on_click=shuffle_cards, use_container_width=True)

        st.divider()

        # Hiển thị thẻ hiện tại
        current_card = st.session_state.cards[st.session_state.current_index]
        
        # Tạo khung hiển thị thẻ bằng cách sử dụng container và Markdown
        card_container = st.container(border=True)
        with card_container:
            if not st.session_state.flipped:
                st.subheader("Mặt trước (Câu hỏi / Từ vựng)")
                st.markdown(current_card['front']) # Hỗ trợ render Toán học tự động nhờ Markdown
            else:
                st.subheader("Mặt sau (Đáp án / Công thức)")
                st.markdown(current_card['back'])
        
        st.button("🔄 Lật thẻ", on_click=flip_card, use_container_width=True, type="primary")

        # Nút điều hướng
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅️ Quay lại", on_click=prev_card, disabled=(st.session_state.current_index == 0), use_container_width=True)
        with col_next:
            st.button("Tiếp theo ➡️", on_click=next_card, disabled=(st.session_state.current_index == len(st.session_state.cards) - 1), use_container_width=True)

        st.divider()

        # Tự đánh giá sau khi lật
        if st.session_state.flipped:
            st.write("**Bạn có nhớ đáp án này không?**")
            col_forget, col_remember = st.columns(2)
            with col_forget:
                st.button("❌ Quên", on_click=mark_forget, use_container_width=True)
            with col_remember:
                st.button("✅ Nhớ", on_click=mark_remember, use_container_width=True)

# ------------------------------------------
# TAB 2: QUẢN LÝ THẺ (THÊM / SỬA / XÓA)
# ------------------------------------------
with tab_manage:
    st.subheader("Thêm thẻ mới")
    with st.form("add_form", clear_on_submit=True):
        new_front = st.text_area("Mặt trước (Có thể dùng cú pháp $$...$$ cho Toán học)")
        new_back = st.text_area("Mặt sau (Giải thích / Công thức)")
        submitted = st.form_submit_button("Thêm thẻ")
        
        if submitted and new_front.strip() and new_back.strip():
            st.session_state.cards.append({
                "id": str(uuid.uuid4()),
                "front": new_front,
                "back": new_back
            })
            save_data(st.session_state.cards)
            st.success("Đã thêm thẻ thành công!")
            st.rerun() # Refresh lại giao diện

    st.divider()
    
    st.subheader("Chỉnh sửa thẻ hiện tại")
    if st.session_state.cards:
        current_card = st.session_state.cards[st.session_state.current_index]
        edit_front = st.text_area("Sửa mặt trước", value=current_card['front'])
        edit_back = st.text_area("Sửa mặt sau", value=current_card['back'])
        
        col_save, col_del = st.columns(2)
        with col_save:
            if st.button("Lưu thay đổi", type="primary", use_container_width=True):
                st.session_state.cards[st.session_state.current_index]['front'] = edit_front
                st.session_state.cards[st.session_state.current_index]['back'] = edit_back
                save_data(st.session_state.cards)
                st.success("Đã cập nhật thẻ!")
        with col_del:
            if st.button("Xóa thẻ này", type="primary", on_click=delete_current_card, use_container_width=True):
                st.rerun()
