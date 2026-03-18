import streamlit as st

def get_custom_css():
    return """
<style>
    /* Import Dela Gothic One font */
    @import url('https://fonts.googleapis.com/css2?family=Dela+Gothic+One&display=swap');

    /* Force Light Mode Aesthetics */
    .stApp {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* Global layout - Align everything at the top with enough padding */
    .block-container {
        padding-top: 5rem !important;
        vertical-align: top !important;
    }

    /* Title Styling - Target the specific ID */
    h1[id="title"] {
        font-family: 'Dela Gothic One', cursive !important;
        color: #1a5d1a !important; /* Dark Green - Zundamon theme */
        font-size: 3rem !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
        border: none !important;
        padding: 0 !important;
    }

    /* Character image styling */
    .char-img {
        width: 100%;
        max-width: 240px;
        display: block;
        margin: 0 auto;
    }

    /* Chat Container */
    .chat-container {
        display: flex;
        flex-direction: column;
        padding: 0;
        margin: 0;
        justify-content: flex-start;
        align-items: stretch;
    }

    /* Modern Bubble styling */
    .bubble {
        padding: 14px 22px;
        border-radius: 20px;
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        line-height: 1.5;
        max-width: 80%;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        animation: slideUp 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        border: 1px solid #eee;
        position: relative;
        margin-bottom: 22px;
    }

    /* Left Character: Zundamon (Light Green) */
    .bubble.left {
        align-self: flex-start;
        background-color: #f0fdf4;
        color: #1a1a1a;
        border-bottom-left-radius: 4px;
        margin-right: auto;
    }

    /* Right Character: Ankomon-ready (Light Adzuki Color) */
    .bubble.right {
        align-self: flex-end;
        background-color: #fcf1f1;
        color: #4a2c2c;
        border: 1px solid #ecc9c9;
        border-bottom-right-radius: 4px;
        margin-left: auto;
    }

    @keyframes slideUp {
        0% { transform: translateY(15px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }

    /* Button Styling */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        padding: 0.8rem;
        background-color: #2D3436;
        color: white;
        border: none;
        font-weight: 600;
        margin-top: 10px;
    }

    /* Footer / License Box - Repositioned to top */
    .footer-box {
        margin-top: 0px;
        margin-bottom: 20px;
        padding: 8px 16px;
        border-radius: 8px;
        background-color: #f8f9fa;
        font-size: 0.8rem;
        color: #666;
        text-align: center;
        line-height: 1.4;
    }

    /* Force all Streamlit layout elements to top */
    div[data-testid="column"], div[data-testid="stVerticalBlock"] {
        vertical-align: top !important;
        justify-content: flex-start !important;
    }
</style>
"""
