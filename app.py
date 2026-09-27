import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os
import random

# ==========================================
# 1. KẾT NỐI FIREBASE ĐÁM MÂY
# ==========================================
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        # Nếu chạy trên máy tính cá nhân, dùng file JSON
        if os.path.exists('firebase-key.json'):
            cred = credentials.Certificate('firebase-key.json')
        # Nếu chạy trên Streamlit Cloud, dùng Secrets (Sẽ cấu hình sau)
        # Nếu chạy trên Streamlit Cloud, dùng Secrets
        # Nếu chạy trên Streamlit Cloud, dùng Secrets
        else:
            import json
            key_dict = json.loads(st.secrets["text_json"])
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# ==========================================
# 2. HỆ THỐNG TÀI KHOẢN (ĐĂNG NHẬP)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

def login(user, pw):
    # DANG SÁCH TÀI KHOẢN (Bạn có thể tự thêm bớt ở đây)
    accounts = {
        "ducthang": "02102006",
        "honganh": "21062007",
        "hocsinh2": "123456"
    }
    if user in accounts and accounts[user] == pw:
        st.session_state.logged_in = True
        st.session_state.username = user
        st.rerun()
    else:
        st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.cards = [] 
    st.session_state.data_loaded = False
    st.rerun()

# --- GIAO DIỆN ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.set_page_config(page_title="Đăng nhập Flashcards", layout="centered")
    st.title("🔐Flashcards Thắng Anh")
    st.write("Vui lòng đăng nhập để vào không gian học tập của riêng bạn.")
    
    with st.container(border=True):
        user_input = st.text_input("Tên đăng nhập ")
        pw_input = st.text_input("Mật khẩu ", type="password")
        if st.button("Đăng nhập", type="primary", use_container_width=True):
            login(user_input, pw_input)
    st.stop() # Dừng chạy các code bên dưới nếu chưa đăng nhập thành công


# ==========================================
# 3. CÁC HÀM XỬ LÝ DỮ LIỆU TỪ FIREBASE
# ==========================================
def load_user_cards(username):
    """Tải thẻ của riêng người dùng đang đăng nhập"""
    cards_ref = db.collection("flashcards").where("owner", "==", username).stream()
    cards = []
    for doc in cards_ref:
        card = doc.to_dict()
        card["doc_id"] = doc.id # Lưu lại ID thực tế trên cơ sở dữ liệu
        cards.append(card)
    return cards

# Khởi tạo dữ liệu vào RAM khi vừa đăng nhập
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.session_state.cards = load_user_cards(st.session_state.username)
    st.session_state.current_index = 0
    st.session_state.flipped = False
    st.session_state.data_loaded = True

# --- ACTIONS LẬT THẺ & ĐIỂM SỐ ---
def flip_card(): st.session_state.flipped = not st.session_state.flipped
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

def update_score(field):
    card = st.session_state.cards[st.session_state.current_index]
    card[field] += 1
    # Cập nhật trực tiếp lên đám mây Firebase
    db.collection("flashcards").document(card["doc_id"]).update({field: card[field]})
    next_card()

def delete_current_card():
    if st.session_state.cards:
        doc_id = st.session_state.cards[st.session_state.current_index]["doc_id"]
        db.collection("flashcards").document(doc_id).delete() # Xóa trên Firebase
        
        st.session_state.cards.pop(st.session_state.current_index) # Xóa trên RAM
        if st.session_state.current_index >= len(st.session_state.cards):
            st.session_state.current_index = max(0, len(st.session_state.cards) - 1)
        st.session_state.flipped = False


# ==========================================
# 4. GIAO DIỆN CHÍNH CỦA ỨNG DỤNG
# ==========================================
st.set_page_config(page_title="Flashcards App", layout="centered")

col1, col2 = st.columns([4, 1])
with col1:
    st.title(f"📚Flashcards Thắng Anh ")
with col2:
    st.button("Đăng xuất", on_click=logout)

tab_learn, tab_quiz, tab_manage = st.tabs(["Lật Thẻ Học", "Trắc Nghiệm", "Quản Lý Thẻ"])

# --- TAB HỌC TẬP ---
with tab_learn:
    if not st.session_state.cards:
        st.info("Chưa có thẻ nào trong kho của bạn. Hãy sang tab 'Quản Lý Thẻ' để tạo nhé!")
    else:
        current_card = st.session_state.cards[st.session_state.current_index]
        
        col_stat, col_shuffle = st.columns([3, 1])
        with col_stat:
            st.write(f"**Tiến độ:** {st.session_state.current_index + 1} / {len(st.session_state.cards)} | "
                     f"✅ Nhớ: {current_card['remember']} | ❌ Quên: {current_card['forget']}")
        with col_shuffle:
            st.button("🔀 Trộn thẻ", on_click=shuffle_cards, use_container_width=True)

        # Khung hiển thị thẻ
        with st.container(border=True):
                if not st.session_state.flipped:
                    st.markdown("<p style='font-size: 15px; color: gray; margin-bottom: 0px;'>Mặt trước</p>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 45px; font-weight: bold; text-align: center; padding: 30px;'>{current_card['front']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='font-size: 15px; color: gray; margin-bottom: 0px;'>Mặt sau</p>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 45px; font-weight: bold; text-align: center; padding: 30px;'>{current_card['back']}</div>", unsafe_allow_html=True)
                
                # Nút Lật thẻ
                st.button("🔄 Lật thẻ", on_click=flip_card, use_container_width=True, type="primary")

            # Nút điều hướng (Chỉ giữ lại 1 bộ có chức năng vô hiệu hóa khi ở đầu/cuối)
        c_prev, c_next = st.columns(2)
        with c_prev:
            st.button("⬅️ Quay lại", on_click=prev_card, disabled=(st.session_state.current_index == 0), use_container_width=True)
        with c_next:
            st.button("Tiếp theo ➡️", on_click=next_card, disabled=(st.session_state.current_index == len(st.session_state.cards) - 1), use_container_width=True)

        st.divider()
        if st.session_state.flipped:
            st.write("**Bạn có nhớ đáp án này không?**")
            cf, cr = st.columns(2)
            with cf:
                st.button("❌ Quên", on_click=lambda: update_score("forget"), use_container_width=True)
            with cr:
                st.button("✅ Nhớ", on_click=lambda: update_score("remember"), use_container_width=True)
# --- TAB TRẮC NGHIỆM ---
with tab_quiz:
    st.header("📝 Bài Kiểm Tra Trắc Nghiệm")
    import random
    import time  
    
    if not st.session_state.cards or len(st.session_state.cards) < 4:
        st.warning("Bạn cần tạo ít nhất 4 thẻ trong 'Quản Lý Thẻ' để có đủ dữ liệu trộn 4 đáp án nhé!")
    else:
        # Nút tạo đề thi mới
        if st.button("🔄 Tạo đề trắc nghiệm mới", type="primary"):
            st.session_state.quiz_id = int(time.time())
            
            # --- ĐIỂM MỚI ---
            # Tạo một bản sao của danh sách thẻ và xáo trộn thứ tự các câu hỏi
            all_cards = list(st.session_state.cards)
            random.shuffle(all_cards)
            # ----------------
            
            quiz_data = []
            
            for card in all_cards:
                question = card.get('front', '')
                correct_answer = card.get('back', '')
                
                # Lấy ngẫu nhiên 3 đáp án sai từ TOÀN BỘ thẻ gốc (để đảm bảo tính đa dạng)
                wrong_answers = list(set([c.get('back', '') for c in st.session_state.cards if c.get('back', '') != correct_answer]))
                
                if len(wrong_answers) >= 3:
                    selected_wrongs = random.sample(wrong_answers, 3)
                else:
                    selected_wrongs = wrong_answers
                
                options = [correct_answer] + selected_wrongs
                random.shuffle(options)
                
                quiz_data.append({
                    'question': question,
                    'options': options,
                    'answer': correct_answer
                })
            
            st.session_state.quiz_data = quiz_data
            st.session_state.quiz_submitted = False

        # Hiển thị form bài thi
        if 'quiz_data' in st.session_state and st.session_state.quiz_data:
            st.write("---")
            quiz_id = st.session_state.get('quiz_id', 0)
            
            with st.form("quiz_form"):
                user_answers = {}
                for i, q in enumerate(st.session_state.quiz_data):
                    st.markdown(f"**Câu {i+1}: {q['question']}**")
                    
                    user_answers[i] = st.radio(
                        "Chọn đáp án:", 
                        q['options'], 
                        index=None, 
                        key=f"q_{quiz_id}_{i}", 
                        label_visibility="collapsed"
                    )
                    st.write("")
                
                submit_quiz = st.form_submit_button("Nộp bài")
                
                if submit_quiz:
                    st.session_state.quiz_submitted = True
                    
            # Chấm điểm và báo kết quả sau khi ấn Nộp bài
            if st.session_state.get('quiz_submitted'):
                score = 0
                total = len(st.session_state.quiz_data)
                unanswered = 0
                
                for i, q in enumerate(st.session_state.quiz_data):
                    if user_answers[i] == q['answer']:
                        score += 1
                    elif user_answers[i] is None:
                        unanswered += 1
                        
                st.success(f"🎉 **Bạn đã đúng {score} / {total} câu!**")
                
                if unanswered > 0:
                    st.warning(f"⚠️ Bạn đã bỏ trống {unanswered} câu chưa chọn đáp án.")
                
                with st.expander("📂 Xem chi tiết đáp án"):
                    for i, q in enumerate(st.session_state.quiz_data):
                        ans = user_answers[i] if user_answers[i] is not None else "Không chọn"
                        
                        if ans == q['answer']:
                            st.write(f"✅ **Câu {i+1}:** {q['question']} ➔ {ans}")
                        else:
                            st.write(f"❌ **Câu {i+1}:** {q['question']} ➔ Bạn chọn: *{ans}* | **Đúng là: {q['answer']}**")
#Tap Quản Lý
with tab_manage:
    st.subheader("Thêm thẻ mới")
    # Tạo một thanh bấm xổ xuống để xem toàn bộ thẻ
    with st.expander("📂 Xem toàn bộ thẻ đã lưu (Tùy chọn Xóa)"):
            if not st.session_state.cards:
                st.info("Hiện chưa có thẻ nào được lưu.")
            else:
                for i, card in enumerate(st.session_state.cards):
                    col1, col2, col3 = st.columns([4, 4, 2])
                    
                    with col1:
                        # Dùng .get() để lấy dữ liệu an toàn, không báo lỗi nếu thiếu
                        st.write(f"**Trước:** {card.get('front', '')}") 
                    with col2:
                        st.write(f"**Sau:** {card.get('back', '')}")
                    with col3:
                        # Lấy ID an toàn. Nếu thẻ không có ID, dùng số thứ tự i để web không sập
                        card_id = card.get('doc_id', f"loi_id_{i}")
                        
                        if st.button("❌ Xóa thẻ", key=f"del_all_{card_id}"):
                            if "loi_id" in card_id:
                                st.error("Lỗi: Không tìm thấy doc_id của thẻ này!")
                            else:
                                # 1. Xóa trên Firebase đám mây
                                db.collection('flashcards').document(card_id).delete()
                                
                                # 2. CẬP NHẬT NGAY LẬP TỨC TRÊN GIAO DIỆN WEB
                                st.session_state.cards = [c for c in st.session_state.cards if c.get('doc_id') != card_id]
                                
                                # 3. Đặt lại vị trí đang học (tránh lỗi out of index)
                                if st.session_state.current_index >= len(st.session_state.cards):
                                    st.session_state.current_index = max(0, len(st.session_state.cards) - 1)
                                    
                                st.success("Đã xóa thẻ!")
                                import time
                                time.sleep(0.5)
                                st.rerun()
    with st.form("add_form", clear_on_submit=True):
        new_front = st.text_area("Mặt trước (Câu hỏi / Toán học $$...$$)")
        new_back = st.text_area("Mặt sau (Đáp án / Công thức)")
        if st.form_submit_button("Thêm thẻ"):
            if new_front.strip() and new_back.strip():
                new_card_data = {
                    "front": new_front, "back": new_back,
                    "owner": st.session_state.username,
                    "remember": 0, "forget": 0
                }
                # Thêm vào Firebase
                doc_ref = db.collection("flashcards").add(new_card_data)
                
                # Cập nhật RAM để hiển thị ngay
                new_card_data["doc_id"] = doc_ref[1].id
                st.session_state.cards.append(new_card_data)
                st.success("Đã thêm thẻ thành công!")
                st.rerun()

    st.divider()
    
    if st.session_state.cards:
        st.subheader("Chỉnh sửa thẻ hiện tại")
        current_card = st.session_state.cards[st.session_state.current_index]
        edit_f = st.text_area("Sửa mặt trước", value=current_card['front'])
        edit_b = st.text_area("Sửa mặt sau", value=current_card['back'])
        
        c_save, c_del = st.columns(2)
        with c_save:
            if st.button("Lưu thay đổi", type="primary", use_container_width=True):
                # Cập nhật Firebase
                db.collection("flashcards").document(current_card['doc_id']).update({"front": edit_f, "back": edit_b})
                # Cập nhật RAM
                st.session_state.cards[st.session_state.current_index]['front'] = edit_f
                st.session_state.cards[st.session_state.current_index]['back'] = edit_b
                st.success("Đã cập nhật!")
        with c_del:
            if st.button("Xóa thẻ này", type="primary", on_click=delete_current_card, use_container_width=True):
                st.rerun()