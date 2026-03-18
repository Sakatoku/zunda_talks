import streamlit as st
import time
import hashlib
import json
import requests
import base64
from pathlib import Path
import os
from google import genai
from google.genai import types

# Configuration from secrets
VOICEVOX_URL = st.secrets.get("VOICEVOX_ENGINE_URL", "https://voicevox-engine-cpu-latest-p0ga.onrender.com")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
# デバッグ用: secrets.toml に DEBUG_SKIP_VOICE = true を設定すると音声生成をスキップする
DEBUG_SKIP_VOICE: bool = st.secrets.get("DEBUG_SKIP_VOICE", False)

# google.genai は genai.Client() でクライアントを生成する方式に変わった
# APIキーが未設定の場合は None のまま保持し、呼び出し時にチェックする
gemini_client: genai.Client | None = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_PROMPT = """
あなたは、YouTubeの解説動画（ずんだもん解説）の台本を作成する優秀な構成作家です。
以下の二人のキャラクターによる対話形式の解説台本を生成してください。

【キャラクター設定】
1. ずんだもん (left): 
   - 語尾は「〜なのだ」「〜のだ」。
   - 一人称は「ずんだもん」もしくは「僕」。
   - 明るく、少し自信家で、好奇心旺盛な性格。
   - やや不幸属性が備わっており、ないがしろにされることもしばしば。
   - 視聴者に語りかけるような、親しみやすい解説。
   - 難しいことを分かりやすく説明するのが得意。
   - たまにボケる。
2. あんこもん (right):
   - 語尾は「〜だもん」「〜もん」。
   - 一人称は「あんこもん」。
   - 落ち着いたボイスだが、ずんだもんをライバル視している。「ずんだもん？そんなやつ、知らないもん」
   - ずんだもんの解説に相槌を打ったり、補足したりする。
   - 丁寧だが、少しドライな一面もあるかもしれない。
   - ずんだもんのボケに鋭いツッコミを入れる。

【出力フォーマット】
以下の形式のJSONリストのみを出力してください。他のテキストは一切含めないでください。
[["left", "ずんだもんのセリフ"], ["right", "あんこもんのセリフ"], ...]

【指示】
- 入力されたプロンプトの内容を分かりやすく、ステップバイステップで5〜8個のセリフで構成してください。
- 専門用語はなるべく噛み砕いて説明してください。
- ずんだもんとあんこもんの掛け合いを意識してください。
- ずんだもんとあんこもんには最初にユーザに向けた短い自己紹介をさせてください。
- 最後に小ボケとツッコミを入れるなど、ちょっとしたオチをつけるように意識してください。
"""

def get_cache_dir():
    """Determine cache directory (/tmp or ./tmp)"""
    tmp_path = Path("/tmp")
    if tmp_path.exists() and os.access(tmp_path, os.W_OK):
        cache_dir = tmp_path / "zunda_cache"
    else:
        cache_dir = Path("tmp") / "zunda_cache"
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def generate_dialogue(prompt: str):
    """
    Real dialogue generation using Gemini API with caching.
    """
    if not prompt:
        return []

    # Calculate hash for caching
    prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
    cache_file = get_cache_dir() / f"{prompt_hash}.json"

    # Check cache
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # API Call
    if not GEMINI_API_KEY:
        # st.error()はst.rerun()で消えてしまうため、セッションステートにエラーを保存する
        st.session_state.error_message = "GEMINI_API_KEY が secrets に設定されていません。"
        return [("left", "あわわ、APIキーが設定されていないのだ！設定を確認してほしいのだ。")]

    try:
        # google.genai SDK: client.models.generate_content() を使用
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{SYSTEM_PROMPT}\n\nプロンプト: {prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        dialogue = json.loads(response.text)
        
        # Validation: ensure list of lists
        if not isinstance(dialogue, list):
            raise ValueError("Invalid format: expected a list.")

        # Save to cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(dialogue, f, ensure_ascii=False, indent=2)

        return dialogue

    except Exception as e:
        # @st.fragment内でst.rerun()が呼ばれるとst.error()の内容がリセットされるため、
        # セッションステートに保存して再描画後に表示する
        st.session_state.error_message = f"Gemini API Error: {e}"
        return [("left", "なんだか調子が悪いのだ...。エラーが発生したみたいなのだ。")]

def generate_voice(text: str, speaker_id: int):
    """
    Real Voicevox API integration with file-based caching.
    """
    if not text:
        return ""

    # デバッグ中に音声生成を省略したい場合は secrets.toml に DEBUG_SKIP_VOICE = true を設定する
    if DEBUG_SKIP_VOICE:
        return ""

    # Calculate hash for caching (text + speaker_id)
    voice_hash = hashlib.md5(f"{text}_{speaker_id}".encode('utf-8')).hexdigest()
    cache_file = get_cache_dir() / f"voice_{voice_hash}.txt"

    # Check cache
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    try:
        # 1. Create Audio Query
        query_url = f"{VOICEVOX_URL}/audio_query"
        params = {"text": text, "speaker": speaker_id}
        query_response = requests.post(query_url, params=params, timeout=300)
        query_response.raise_for_status()
        query_data = query_response.json()

        # 2. Synthesis
        synthesis_url = f"{VOICEVOX_URL}/synthesis"
        synth_response = requests.post(
            synthesis_url,
            params={"speaker": speaker_id},
            json=query_data,
            timeout=600
        )
        synth_response.raise_for_status()

        # 3. Convert to Base64
        wav_data = synth_response.content
        b64_wav = base64.b64encode(wav_data).decode()
        audio_src = f"data:audio/wav;base64,{b64_wav}"

        # Save to cache
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(audio_src)

        return audio_src

    except Exception as e:
        # Fallback silently or with error log
        return ""
