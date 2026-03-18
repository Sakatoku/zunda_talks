import streamlit as st
import zipfile
import io
from pathlib import Path
from styles import get_custom_css
from api_utils import get_cache_dir

# --- ページ設定 ---
st.set_page_config(
    page_title="キャッシュ取り込み | ずんだもん",
    page_icon="📦",
    layout="wide",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

# キャッシュとして受け入れる拡張子
ALLOWED_EXTENSIONS = {".json", ".txt"}


def import_single_file(filename: str, content: bytes, cache_dir: Path) -> tuple[bool, str]:
    """
    単体ファイルをキャッシュディレクトリへ保存する。
    既存ファイルは上書きしない（他環境からの意図しない上書きを防ぐため）。
    戻り値: (成功フラグ, メッセージ)
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return False, f"`{filename}` はサポート対象外の形式です（{suffix}）。スキップしました。"

    dest = cache_dir / filename
    if dest.exists():
        return False, f"`{filename}` はすでに存在します。スキップしました。"

    dest.write_bytes(content)
    return True, f"`{filename}` をインポートしました。"


def import_from_zip(zip_bytes: bytes, cache_dir: Path) -> dict[str, list[str]]:
    """
    ZIPアーカイブを展開し、許可された拡張子のファイルのみをキャッシュに取り込む。
    ディレクトリ構造は無視し、ファイル名のみを使用する。
    """
    results: dict[str, list[str]] = {"success": [], "skipped": [], "error": []}

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for entry in zf.infolist():
                # ディレクトリエントリはスキップ
                if entry.is_dir():
                    continue

                # ベース名のみ使用（サブディレクトリのパスを除去）
                filename = Path(entry.filename).name
                suffix = Path(filename).suffix.lower()

                if suffix not in ALLOWED_EXTENSIONS:
                    results["skipped"].append(f"`{filename}` （非対応形式）")
                    continue

                content = zf.read(entry.filename)
                ok, msg = import_single_file(filename, content, cache_dir)
                if ok:
                    results["success"].append(msg)
                else:
                    results["skipped"].append(msg)

    except zipfile.BadZipFile:
        results["error"].append("不正なZIPファイルです。")

    return results


# --- UI ---
st.title("📦 キャッシュ取り込み")
st.markdown("""
他の環境（別PC・クラウド等）で生成されたキャッシュファイルを現在の環境にインポートします。  
**単体ファイル**（`.json` / `.txt`）と **ZIPアーカイブ**（`.zip`）の両方に対応しており、自動で判別します。
""")

st.divider()

# --- 現在のキャッシュ状況 ---
cache_dir = get_cache_dir()
existing_files = list(cache_dir.glob("*"))
json_count = sum(1 for f in existing_files if f.suffix == ".json")
txt_count = sum(1 for f in existing_files if f.suffix == ".txt")

with st.expander(f"📁 現在のキャッシュ状況（合計 {len(existing_files)} 件）", expanded=False):
    col_a, col_b = st.columns(2)
    col_a.metric("対話キャッシュ (.json)", json_count)
    col_b.metric("音声キャッシュ (.txt)", txt_count)
    st.caption(f"保存先: `{cache_dir}`")

st.divider()

# --- ファイルアップロード ---
st.subheader("ファイルをアップロード")
uploaded_files = st.file_uploader(
    "キャッシュファイルまたはZIPアーカイブを選択（複数可）",
    type=["json", "txt", "zip"],
    accept_multiple_files=True,
    help="`.json`（対話キャッシュ）、`.txt`（音声キャッシュ）、`.zip`（複数ファイルをまとめた場合）に対応しています。",
)

if uploaded_files:
    if st.button("⬇️ インポート実行", use_container_width=True):
        all_success: list[str] = []
        all_skipped: list[str] = []
        all_error: list[str] = []

        with st.spinner("インポート中..."):
            for uploaded_file in uploaded_files:
                suffix = Path(uploaded_file.name).suffix.lower()
                raw_bytes = uploaded_file.read()

                if suffix == ".zip":
                    # ZIPを展開して一括インポート
                    results = import_from_zip(raw_bytes, cache_dir)
                    all_success.extend(results["success"])
                    all_skipped.extend(results["skipped"])
                    all_error.extend(results["error"])
                elif suffix in ALLOWED_EXTENSIONS:
                    # 単体ファイルをインポート
                    ok, msg = import_single_file(uploaded_file.name, raw_bytes, cache_dir)
                    if ok:
                        all_success.append(msg)
                    else:
                        all_skipped.append(msg)
                else:
                    all_skipped.append(f"`{uploaded_file.name}` はサポート対象外の形式です。スキップしました。")

        # --- 結果の表示 ---
        st.divider()
        st.subheader("インポート結果")

        col1, col2, col3 = st.columns(3)
        col1.metric("✅ 成功", len(all_success))
        col2.metric("⏭️ スキップ", len(all_skipped))
        col3.metric("❌ エラー", len(all_error))

        if all_success:
            with st.expander("✅ インポート成功", expanded=True):
                for msg in all_success:
                    st.success(msg, icon="✅")

        if all_skipped:
            with st.expander("⏭️ スキップされたファイル", expanded=True):
                for msg in all_skipped:
                    st.warning(msg, icon="⚠️")

        if all_error:
            with st.expander("❌ エラー", expanded=True):
                for msg in all_error:
                    st.error(msg, icon="🚨")

        if all_success:
            st.info("インポートが完了しました。解説ページに戻ると、次回から取り込んだキャッシュが利用されます。", icon="ℹ️")
