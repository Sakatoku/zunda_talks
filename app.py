import streamlit as st
import base64
from pathlib import Path
from styles import get_custom_css
from api_utils import generate_dialogue, generate_voice

# --- Page Configuration ---
st.set_page_config(
    page_title="何かを解説するずんだもんなのだ",
    page_icon="🎬",
    layout="wide",
)

# --- Apply Custom CSS ---
st.markdown(get_custom_css(), unsafe_allow_html=True)

# --- Helper: Image to Base64 ---
def get_image_as_base64(path):
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- Assets ---
assets_dir = Path("assets")
zundamon_base64 = get_image_as_base64(assets_dir / "zundamon.png")
ankomon_base64 = get_image_as_base64(assets_dir / "ankomon.png")

# --- Title Header ---
st.title("何かを解説するずんだもんなのだ", anchor="title")

# --- Footer / License (Top) ---
st.markdown("""
<div class="footer-box">
    VOICEVOX:ずんだもん / VOICEVOX:あんこもん / キャラクター立ち絵:坂本アヒル様
</div>
""", unsafe_allow_html=True)

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.counter = 0
    st.session_state.current_dialogue = []
    st.session_state.last_prompt = ""
    st.session_state.play_audio = False
    # st.rerun()後もエラーを表示できるようセッションステートで管理する
    st.session_state.error_message = ""

# --- Logic ---
def proceed_explanation(prompt_input):
    # If prompt changed, reset everything
    if prompt_input != st.session_state.last_prompt:
        st.session_state.current_dialogue = []
        st.session_state.messages = []
        st.session_state.counter = 0
        st.session_state.last_prompt = prompt_input

    # Generate dialogue if not exists
    if not st.session_state.current_dialogue:
        if prompt_input:
            with st.spinner("思考中..."):
                st.session_state.current_dialogue = generate_dialogue(prompt_input)
        
    # Standard linear progression
    if st.session_state.counter < len(st.session_state.current_dialogue):
        msg = st.session_state.current_dialogue[st.session_state.counter]
        st.session_state.messages.append(msg)
        st.session_state.counter += 1
        if len(st.session_state.messages) > 5:
            st.session_state.messages.pop(0)
        st.session_state.play_audio = True

# --- Main Columns Layout ---
col1, col2, col3 = st.columns([1, 2, 1], gap="large")

with col1:
    # Only show character if dialogue has started
    if st.session_state.messages and zundamon_base64:
        st.write("") # Placeholder for spacing if needed
        st.markdown(f'<img class="char-img" src="data:image/png;base64,{zundamon_base64}">', unsafe_allow_html=True)

with col3:
    # Only show character if dialogue has started
    if st.session_state.messages and ankomon_base64:
        st.write("") 
        st.markdown(f'<img class="char-img" src="data:image/png;base64,{ankomon_base64}">', unsafe_allow_html=True)

with col2:
    @st.fragment
    def main_interaction_area():
        # 1. Prompt Input Area
        prompt_input = st.text_area(
            "解説させたい内容",
            value="Streamlitの使い方について3ステップで教えて",
            placeholder="例: Streamlitの使い方について3ステップで教えて",
            height=100,
            label_visibility="collapsed"
        )

        # 2. Action Button with dynamic label
        btn_label = "解説を開始" if not st.session_state.messages else "解説を進める"
        if st.button(btn_label, key="next_btn", use_container_width=True):
            proceed_explanation(prompt_input)
            st.rerun()

        # api_utils側でセッションステートに保存されたエラーをここで表示する
        # (st.rerun()後も消えないよう、表示後にクリアする)
        if st.session_state.get("error_message"):
            st.error(st.session_state.error_message)
            st.session_state.error_message = ""

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. Chat Messages Area
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for side, text in st.session_state.messages:
            st.markdown(f'<div class="bubble {side}">{text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 4. Audio Playback (Voicevox Integration)
        if st.session_state.play_audio:
            if st.session_state.messages:
                side, text = st.session_state.messages[-1]
                # speaker_id: 3 (ずんだもん), 113 (あんこもん)
                # Note: Adjust speaker IDs based on your Voicevox Engine setup
                speaker_id = 3 if side == "left" else 113
                
                with st.spinner("音声を生成中..."):
                    audio_src = generate_voice(text, speaker_id)
                    st.markdown(f'<audio src="{audio_src}" autoplay style="display:none;"></audio>', unsafe_allow_html=True)
            st.session_state.play_audio = False

    main_interaction_area()
