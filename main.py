import streamlit as st

# ページ設定を最初に実行
st.set_page_config(
    page_title="🎓 AI英会話学習アプリ",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# スクロール改善のためのCSS
st.markdown("""
<style>
/* ページ全体のスクロールを改善 */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    overflow-y: auto;
}

/* iframe内のスクロールを有効化 */
iframe {
    overflow: auto !important;
}

/* ページ高さを確保 */
html, body {
    height: 100vh;
    overflow-y: auto;
}

/* Streamlit固有のスクロール問題を解決 */
.stApp {
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

import os
import time
from time import sleep
from pathlib import Path
from streamlit.components.v1 import html
from openai import OpenAI
from dotenv import load_dotenv
import functions as ft
import constants as ct

# 各種設定
load_dotenv()

# 必要なディレクトリを作成
os.makedirs(ct.AUDIO_INPUT_DIR, exist_ok=True)
os.makedirs(ct.AUDIO_OUTPUT_DIR, exist_ok=True)
os.makedirs("images", exist_ok=True)

# アバター画像のパスを取得する関数
def get_avatar_path(icon_path):
    """アイコンファイルが存在する場合はそのパス、存在しない場合はNoneを返す"""
    if os.path.exists(icon_path):
        return icon_path
    return None  # Streamlitのデフォルトアバターを使用

# 🎨 アプリヘッダー（コンパクト版）
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #FF6B6B 100%); 
            padding: 1rem; border-radius: 12px; margin-bottom: 1rem; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
    <div style="text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 2rem; font-weight: bold; 
                   text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
            🎓 AI英会話学習アプリ
        </h1>
        <p style="color: white; margin: 0.3rem 0 0 0; opacity: 0.95; 
                  font-size: 1rem; font-weight: 300;">
            OpenAI GPTを活用した次世代音声英会話練習プラットフォーム
        </p>
        <div style="margin-top: 0.5rem; padding: 0.3rem; background: rgba(255,255,255,0.2); 
                    border-radius: 10px; display: inline-block;">
            <span style="font-size: 0.8rem; color: white; opacity: 0.9;">
                🚀 3つの学習モード | 🎵 速度調整 | 🌏 日本語翻訳対応
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 初期処理
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.start_flg = False
    st.session_state.pre_mode = ""
    st.session_state.shadowing_flg = False
    st.session_state.shadowing_button_flg = False
    st.session_state.shadowing_count = 0
    st.session_state.shadowing_first_flg = True
    st.session_state.shadowing_audio_input_flg = False
    st.session_state.shadowing_evaluation_first_flg = True
    st.session_state.dictation_flg = False
    st.session_state.dictation_button_flg = False
    st.session_state.dictation_count = 0
    st.session_state.dictation_first_flg = True
    st.session_state.dictation_chat_message = ""
    st.session_state.dictation_evaluation_first_flg = True
    st.session_state.chat_open_flg = False
    st.session_state.problem = ""
    st.session_state.current_audio_file = ""
    
    st.session_state.openai_obj = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # シンプルなメッセージ履歴を使用（langchain不使用）
    st.session_state.conversation_history = []

    # OpenAI APIを直接使用（langchain不使用）

# 📊 サイドバー - 学習統計（改善版）
with st.sidebar:
    # サイドバーヘッダー
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 0.7rem; border-radius: 10px; margin-bottom: 1rem;">
        <h2 style="color: white; text-align: center; margin: 0; font-size: 1.2rem;">
            📊 学習ダッシュボード
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # 統計情報の計算
    user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
    ai_messages = [msg for msg in st.session_state.messages if msg["role"] == "assistant"]
    
    # 学習統計をカード風に表示（コンパクト）
    st.markdown("#### 📈 学習記録")
    
    stat_col1, stat_col2 = st.columns(2)
    with stat_col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4CAF50, #45a049); 
                    padding: 0.7rem; border-radius: 8px; text-align: center; 
                    color: white; margin-bottom: 0.3rem;">
            <div style="font-size: 1.2rem; font-weight: bold;">{len(user_messages)}</div>
            <div style="font-size: 0.7rem; opacity: 0.9;">💬 会話回数</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #2196F3, #1976D2); 
                    padding: 0.7rem; border-radius: 8px; text-align: center; 
                    color: white; margin-bottom: 0.3rem;">
            <div style="font-size: 1.2rem; font-weight: bold;">{len(ai_messages)}</div>
            <div style="font-size: 0.7rem; opacity: 0.9;">🤖 AI応答</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 学習効率の表示（コンパクト）
    if len(user_messages) > 0:
        efficiency = min(100, (len(user_messages) * 10))
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FF9800, #F57C00); 
                    padding: 0.7rem; border-radius: 8px; text-align: center; 
                    color: white; margin-bottom: 0.7rem;">
            <div style="font-size: 1rem; font-weight: bold;">{efficiency}%</div>
            <div style="font-size: 0.7rem; opacity: 0.9;">🎯 学習効率</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 現在の設定表示（改善版）
    st.markdown("#### ⚙️ 現在の設定")
    
    with st.container():
        if 'mode' in st.session_state:
            mode_color = "#4CAF50" if st.session_state.mode == ct.MODE_1 else "#FF9800" if st.session_state.mode == ct.MODE_2 else "#2196F3"
            st.markdown(f"""
            <div style="background: {mode_color}; padding: 0.5rem; border-radius: 8px; 
                        color: white; margin-bottom: 0.5rem; text-align: center;">
                📚 {st.session_state.mode}
            </div>
            """, unsafe_allow_html=True)
        
        if 'speed' in st.session_state:
            st.markdown(f"""
            <div style="background: #9C27B0; padding: 0.5rem; border-radius: 8px; 
                        color: white; margin-bottom: 0.5rem; text-align: center;">
                🎵 {st.session_state.speed}
            </div>
            """, unsafe_allow_html=True)
        
        if 'englv' in st.session_state:
            level_color = "#4CAF50" if "初級" in st.session_state.englv else "#FF9800" if "中級" in st.session_state.englv else "#F44336"
            st.markdown(f"""
            <div style="background: {level_color}; padding: 0.5rem; border-radius: 8px; 
                        color: white; margin-bottom: 1rem; text-align: center;">
                📊 {st.session_state.englv}
            </div>
            """, unsafe_allow_html=True)
    
    # 翻訳表示設定（改善版）
    st.markdown("#### 🌏 表示設定")
    if 'show_translation' not in st.session_state:
        st.session_state.show_translation = True
    
    st.session_state.show_translation = st.checkbox(
        "📖 日本語翻訳を表示", 
        value=st.session_state.show_translation,
        help="英語メッセージに日本語翻訳を追加表示します"
    )
    
    # 学習のヒント
    with st.expander("💡 学習のコツ", expanded=False):
        st.markdown("""
        **🎯 効果的な学習方法:**
        - 毎日少しずつでも継続する
        - 録音前に内容を整理する
        - AIの発音を真似して練習
        - 間違いを恐れずチャレンジ
        
        **🎤 録音のコツ:**
        - 静かな場所で録音
        - マイクに近づいて話す
        - ゆっくりはっきり発音
        """)
    
    # 💾 ダウンロード・アップロード機能
    st.markdown("---")
    st.markdown("#### 💾 データ管理")
    
    # 会話履歴のダウンロード
    if st.session_state.messages:
        # 会話履歴をJSON形式で保存
        import json
        from datetime import datetime
        
        conversation_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": st.session_state.get('mode', ''),
            "speed": st.session_state.get('speed', ''),
            "level": st.session_state.get('englv', ''),
            "total_messages": len(st.session_state.messages),
            "user_messages": len([msg for msg in st.session_state.messages if msg["role"] == "user"]),
            "ai_messages": len([msg for msg in st.session_state.messages if msg["role"] == "assistant"]),
            "conversation": st.session_state.messages
        }
        
        json_data = json.dumps(conversation_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="💾 会話履歴をダウンロード",
            data=json_data,
            file_name=f"english_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            help="今回の学習セッションをJSONファイルとして保存"
        )
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    padding: 1rem; border-radius: 10px; text-align: center; 
                    border: 2px dashed #dee2e6; margin: 0.5rem 0;">
            <div style="color: #6c757d; font-size: 0.9rem;">
                💾 会話開始後にダウンロード可能
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 会話履歴のアップロード
    st.markdown("<br>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "📁 会話履歴をアップロード",
        type=['json'],
        help="以前保存した会話履歴JSONファイルを読み込み"
    )
    
    if uploaded_file is not None:
        try:
            import json
            uploaded_data = json.load(uploaded_file)
            
            # データの妥当性チェック
            if "conversation" in uploaded_data and isinstance(uploaded_data["conversation"], list):
                # 確認ダイアログ
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); 
                            padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
                            border-left: 4px solid #2196F3;">
                    <strong>📂 アップロードファイル情報:</strong><br>
                    📅 保存日時: {uploaded_data.get('timestamp', '不明')}<br>
                    🎯 学習モード: {uploaded_data.get('mode', '不明')}<br>
                    💬 総メッセージ数: {uploaded_data.get('total_messages', 0)}
                </div>
                """, unsafe_allow_html=True)
                
                col_upload1, col_upload2 = st.columns(2)
                
                with col_upload1:
                    if st.button("📥 会話履歴を復元", use_container_width=True, type="primary"):
                        st.session_state.messages = uploaded_data["conversation"]
                        # その他の設定も復元（存在する場合）
                        if "mode" in uploaded_data:
                            st.session_state.mode = uploaded_data["mode"]
                        if "speed" in uploaded_data:
                            st.session_state.speed = uploaded_data["speed"]
                        if "level" in uploaded_data:
                            st.session_state.englv = uploaded_data["level"]
                        
                        st.success("✅ 会話履歴を復元しました！")
                        st.rerun()
                
                with col_upload2:
                    if st.button("❌ キャンセル", use_container_width=True, type="secondary"):
                        st.rerun()
            else:
                st.error("❌ 無効なファイル形式です")
                
        except Exception as e:
            st.error(f"❌ ファイル読み込みエラー: {e}")
    
    # リセットボタン（改善版）
    st.markdown("---")
    if st.button("🔄 会話履歴をリセット", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.start_flg = False
        st.session_state.shadowing_flg = False
        st.session_state.dictation_flg = False
        st.session_state.chat_open_flg = False
        st.rerun()

# 📱 メインコントロールパネル（コンパクト版）
st.markdown("""
<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
            padding: 1rem; border-radius: 12px; margin: 1rem 0; 
            border: 1px solid #dee2e6; box-shadow: 0 3px 10px rgba(0,0,0,0.1);">
    <h2 style="color: #495057; text-align: center; margin-bottom: 1rem; 
               font-size: 1.5rem; font-weight: bold;">
        🎯 学習設定コントロール
    </h2>
</div>
""", unsafe_allow_html=True)

# 設定エリアを美しくカード風に配置
with st.container():
    # 1行目：基本設定をカード風に
    st.markdown("#### 📚 基本学習設定")
    
    col1, col2, col3 = st.columns([1, 1, 1], gap="medium")
    
    with col1:
        with st.container():
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4CAF50, #45a049); 
                        padding: 0.7rem; border-radius: 10px; margin-bottom: 0.7rem;
                        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);">
                <h4 style="color: white; text-align: center; margin: 0; font-size: 1rem;">
                    📚 学習モード
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.mode = st.selectbox(
                label="学習モード選択", 
                options=[ct.MODE_1, ct.MODE_2, ct.MODE_3], 
                label_visibility="collapsed",
                help="🎯 日常英会話: 自由な会話練習\n🔄 シャドーイング: 音声復唱練習\n✍️ ディクテーション: 聞き取り練習"
            )
    
    with col2:
        with st.container():
            st.markdown("""
            <div style="background: linear-gradient(135deg, #2196F3, #1976D2); 
                        padding: 0.7rem; border-radius: 10px; margin-bottom: 0.7rem;
                        box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);">
                <h4 style="color: white; text-align: center; margin: 0; font-size: 1rem;">
                    🎵 再生速度
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.speed = st.selectbox(
                label="再生速度選択", 
                options=ct.PLAY_SPEED_OPTION, 
                index=3, 
                label_visibility="collapsed",
                help="🐌 ゆっくり: 初心者向け\n🚶 標準: 一般的な速度\n🏃 速め: 上級者向け"
            )
    
    with col3:
        with st.container():
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FF9800, #F57C00); 
                        padding: 0.7rem; border-radius: 10px; margin-bottom: 0.7rem;
                        box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);">
                <h4 style="color: white; text-align: center; margin: 0; font-size: 1rem;">
                    📊 英語レベル
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.englv = st.selectbox(
                label="英語レベル選択", 
                options=ct.ENGLISH_LEVEL_OPTION, 
                label_visibility="collapsed",
                help="🌱 初級: 基本的な英会話\n🌿 中級: 日常的な英会話\n🌳 上級: 複雑な英会話"
            )

    # 学習開始ボタンエリア
    st.markdown("---")    # 選択されたモードに応じた説明を表示
    mode_info = {
        ct.MODE_1: {
            "icon": "💬",
            "title": "日常英会話モード",
            "desc": "自由な英会話を楽しみながら学習できます",
            "color": "#4CAF50"
        },
        ct.MODE_2: {
            "icon": "🔄", 
            "title": "シャドーイングモード",
            "desc": "AIの音声を聞いて正確に復唱する練習です",
            "color": "#FF9800"
        },
        ct.MODE_3: {
            "icon": "✍️",
            "title": "ディクテーションモード", 
            "desc": "音声を聞いて正確に文字入力する練習です",
            "color": "#2196F3"
        }
    }
    
    current_mode = mode_info.get(st.session_state.mode, mode_info[ct.MODE_1])
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {current_mode['color']}, {current_mode['color']}dd); 
                padding: 1rem; border-radius: 12px; margin: 1rem 0; 
                color: white; text-align: center; box-shadow: 0 3px 10px rgba(0,0,0,0.15);">
        <h3 style="margin: 0; font-size: 1.3rem; font-weight: bold;">
            {current_mode['icon']} {current_mode['title']}
        </h3>
        <p style="margin: 0.7rem 0 0 0; opacity: 0.95; font-size: 1rem; line-height: 1.3;">
            {current_mode['desc']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 開始ボタン（改善版）
    col_start = st.columns([1, 2, 1])
    with col_start[1]:
        if st.session_state.start_flg:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4CAF50, #45a049); 
                        padding: 1.5rem; border-radius: 20px; text-align: center; 
                        color: white; margin: 1.5rem 0; box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);">
                <div style="font-size: 1.4rem; font-weight: bold;">
                    ⏳ 学習セッション実行中...
                </div>
                <div style="font-size: 1rem; opacity: 0.9; margin-top: 0.8rem;">
                    {current_mode['icon']} {current_mode['title']}で学習中
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # カスタムスタイルの開始ボタン
            button_clicked = st.button(
                f"🚀 {current_mode['title']}を開始", 
                use_container_width=True, 
                type="primary",
                help=f"{current_mode['desc']}を今すぐ始めましょう！"
            )
            if button_clicked:
                st.session_state.start_flg = True
                st.rerun()
    
    # モードを変更した際の処理
    if st.session_state.mode != st.session_state.pre_mode:
        # 自動でそのモードの処理が実行されないようにする
        st.session_state.start_flg = False
        # 「日常英会話」選択時の初期化処理
        if st.session_state.mode == ct.MODE_1:
            st.session_state.dictation_flg = False
            st.session_state.shadowing_flg = False
        # 「シャドーイング」選択時の初期化処理
        st.session_state.shadowing_count = 0
        if st.session_state.mode == ct.MODE_2:
            st.session_state.dictation_flg = False
        # 「ディクテーション」選択時の初期化処理
        st.session_state.dictation_count = 0
        if st.session_state.mode == ct.MODE_3:
            st.session_state.shadowing_flg = False
        # チャット入力欄を非表示にする
        st.session_state.chat_open_flg = False
    st.session_state.pre_mode = st.session_state.mode

# 📋 アプリ説明とガイド（改善版）
st.markdown("---")

st.markdown("""
<div style="background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%); 
            padding: 1.5rem; border-radius: 15px; margin: 1rem 0; 
            border-left: 5px solid #4CAF50;">
    <h3 style="color: #2E7D32; margin: 0 0 1rem 0; font-size: 1.5rem;">
        📖 アプリの使い方ガイド
    </h3>
    <p style="color: #388E3C; margin: 0; font-size: 1.1rem; font-weight: 500;">
        🎯 生成AIによる次世代音声英会話練習プラットフォーム<br>
        📈 継続的な練習で、あなたの英語力を確実にアップさせましょう！
    </p>
</div>
""", unsafe_allow_html=True)

# 使い方ガイドをタブ形式で整理
guide_tab1, guide_tab2, guide_tab3 = st.tabs(["🎯 学習モード解説", "🎤 録音方法", "💡 学習のコツ"])

with guide_tab1:
    mode_col1, mode_col2, mode_col3 = st.columns(3)
    
    with mode_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4CAF50, #45a049); 
                    padding: 1rem; border-radius: 15px; color: white; text-align: center; 
                    margin-bottom: 1rem;">
            <h4 style="margin: 0; font-size: 1.2rem;">💬 日常英会話</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **🎯 特徴:**
        - 自由な会話練習
        - リアルタイム AI応答
        - 自然な英会話体験
        
        **📝 使い方:**
        1. 音声で質問や話題を録音
        2. AIが自然に英語で応答
        3. 会話を続けて練習
        """)
    
    with mode_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FF9800, #F57C00); 
                    padding: 1rem; border-radius: 15px; color: white; text-align: center; 
                    margin-bottom: 1rem;">
            <h4 style="margin: 0; font-size: 1.2rem;">🔄 シャドーイング</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **🎯 特徴:**
        - 音声復唱練習
        - 発音・イントネーション向上
        - リスニング強化
        
        **📝 使い方:**
        1. AIが生成した英文を聞く
        2. 同じように音声で復唱
        3. 正確性をAIが評価
        """)
    
    with mode_col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2196F3, #1976D2); 
                    padding: 1rem; border-radius: 15px; color: white; text-align: center; 
                    margin-bottom: 1rem;">
            <h4 style="margin: 0; font-size: 1.2rem;">✍️ ディクテーション</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **🎯 特徴:**
        - 聞き取り練習
        - スペリング強化
        - 集中力向上
        
        **📝 使い方:**
        1. AIが英文を音声で読み上げ
        2. 聞こえた内容を文字入力
        3. 正確性をAIが評価
        """)

with guide_tab2:
    st.markdown("### 🎤 **音声録音方法**")
    
    recording_col1, recording_col2 = st.columns(2)
    
    with recording_col1:
        st.success("✅ **推奨方法**")
        st.markdown("""
        **📱 スマートフォン録音:**
        - ボイスメモアプリを使用
        - 静かな場所で録音
        - マイクに15-20cm近づく
        - ファイルアップロードで使用
        
        **💾 ファイル形式:**
        - MP3 (推奨)
        - WAV (高音質)
        - M4A (iPhone標準)
        """)
    
    with recording_col2:
        st.info("🌐 **ブラウザ録音**")
        st.markdown("""
        **🔧 ブラウザ直接録音:**
        - インストール不要
        - ワンクリックで録音
        - HTTPS環境推奨
        - マイク許可が必要
        
        **⚠️ 注意点:**
        - ブラウザによって品質が異なる
        - 環境によっては不安定
        - 代替手段として利用
        """)

with guide_tab3:
    st.markdown("### 💡 **効果的な学習のコツ**")
    
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.markdown("#### 🎯 **学習方法**")
        st.markdown("""
        **📅 継続のコツ:**
        - 毎日15分からスタート
        - 同じ時間帯に学習
        - 小さな目標を設定
        - 進歩を記録する
        
        **🗣️ 会話のコツ:**
        - 完璧を求めすぎない
        - 間違いを恐れない
        - 積極的に質問する
        - 感情を込めて話す
        """)
    
    with tips_col2:
        st.markdown("#### 🎤 **録音のコツ**")
        st.markdown("""
        **🎙️ 音質向上:**
        - 静かな室内で録音
        - マイクに適度に近づく
        - はっきりと発音
        - 一定の音量を保つ
        
        **📝 準備のコツ:**
        - 話す内容を軽く整理
        - 深呼吸してリラックス
        - 短いセンテンスで区切る
        - 録音後は必ず確認
        """)
    
    st.success("""
    🌟 **成功の秘訣**: 継続は力なり！毎日少しずつでも続けることで、
    確実に英語力が向上します。間違いを恐れず、積極的にチャレンジしましょう！
    """)

# 🎯 モード別アクションボタン
if st.session_state.shadowing_flg or st.session_state.dictation_flg:
    st.markdown("---")
    st.markdown("### 🎯 次のステップ")
    
    if st.session_state.shadowing_flg:
        col_shadow = st.columns([1, 2, 1])
        with col_shadow[1]:
            st.session_state.shadowing_button_flg = st.button(
                "🎤 シャドーイング開始", 
                use_container_width=True, 
                type="primary"
            )
    
    if st.session_state.dictation_flg:
        # ディクテーション継続ボタンセクション
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        ">
            <div style="color: white; margin-bottom: 15px;">
                <h4 style="margin: 0; font-size: 1.2em;">🎉 おつかれさまでした！</h4>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">次の問題に挑戦しますか？</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 1列レイアウトで見やすく表示
        st.session_state.dictation_button_flg = st.button(
            "✍️ 次の問題に挑戦", 
            use_container_width=True, 
            type="primary",
            help="新しいディクテーション問題を生成します"
        )

# ✍️ ディクテーションモード入力エリア
if st.session_state.chat_open_flg:
    st.markdown("---")
    
    # ディクテーション入力ヘッダー
    st.markdown("""
    <div class="gradient-header" style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    ">
        <h3 style="margin: 0; font-size: 1.3em;">
            ✍️ ディクテーション入力エリア
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 音声再生ボタン（問題が生成されている場合のみ表示）
    if st.session_state.get('problem'):
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px;
            border-radius: 12px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        ">
            <div style="color: white; margin-bottom: 10px;">
                <span style="font-size: 1.2em; font-weight: bold;">🎧 問題音声</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 音声コントロールボタン
        audio_col1, audio_col2, audio_col3 = st.columns([1, 1, 1])
        
        with audio_col1:
            if st.button("🔊 音声を再生", use_container_width=True, type="secondary", key="play_audio_dictation"):
                # デバッグ情報を表示
                current_file = st.session_state.get('current_audio_file', '')
                if current_file:
                    st.info(f"再生ファイル: {os.path.basename(current_file)}")
                    if os.path.exists(current_file):
                        ft.play_wav(current_file, ft.extract_speed_value(st.session_state.speed))
                    else:
                        st.error(f"音声ファイルが見つかりません: {current_file}")
                        # MP3ファイルを探す
                        mp3_file = current_file.replace('.wav', '.mp3')
                        if os.path.exists(mp3_file):
                            st.info("MP3版で再生します")
                            ft.play_wav(mp3_file, ft.extract_speed_value(st.session_state.speed))
                        else:
                            st.error("問題を再生成してください。")
                else:
                    st.error("音声ファイルが設定されていません。問題を再生成してください。")
        
        with audio_col3:
            # 音声ファイルダウンロードボタン
            current_file = st.session_state.get('current_audio_file', '')
            if current_file and os.path.exists(current_file):
                # ファイルを読み込んでダウンロードボタンを提供
                try:
                    with open(current_file, 'rb') as audio_file:
                        audio_data = audio_file.read()
                    
                    file_extension = os.path.splitext(current_file)[1]
                    mime_type = "audio/wav" if file_extension == ".wav" else "audio/mp3"
                    
                    st.download_button(
                        label="💾 音声DL",
                        data=audio_data,
                        file_name=f"dictation_audio_{int(time.time())}{file_extension}",
                        mime=mime_type,
                        use_container_width=True,
                        help="問題音声をダウンロード"
                    )
                except Exception as e:
                    st.error(f"音声ダウンロードエラー: {e}")
            else:
                st.markdown("""
                <div style="
                    background: #f8f9fa;
                    border: 2px dashed #dee2e6;
                    border-radius: 8px;
                    padding: 8px;
                    text-align: center;
                    color: #6c757d;
                    font-size: 0.8rem;
                ">
                    💾 音声生成後<br>DL可能
                </div>
                """, unsafe_allow_html=True)
    
    # ディクテーション説明カード
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-left: 5px solid #667eea;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 1.5em; margin-right: 10px;">🎧</span>
            <span style="font-weight: bold; color: #4a5568; font-size: 1.1em;">リスニング手順</span>
        </div>
        <ol style="margin: 0; padding-left: 20px; color: #2d3748;">
            <li style="margin: 8px 0;">上部の🔊ボタンを押して音声を再生</li>
            <li style="margin: 8px 0;">聞き取った英文を下の入力欄に正確に入力</li>
            <li style="margin: 8px 0;">Enterキーで送信して答え合わせ</li>
        </ol>
        <div style="
            background: rgba(102, 126, 234, 0.1);
            padding: 10px;
            border-radius: 6px;
            margin-top: 15px;
            border: 1px solid rgba(102, 126, 234, 0.2);
        ">
            <span style="color: #667eea; font-weight: bold;">💡 ヒント:</span>
            <span style="color: #4a5568;">何度でも音声を再生できます。正確な聞き取りを心がけましょう！</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# チャット入力フィールド
if st.session_state.mode == ct.MODE_3:
    # ディクテーションモード時の入力フィールド（1列レイアウト）
    if st.session_state.get('problem'):
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 1em;
            margin: 15px 0;
            box-shadow: 0 3px 10px rgba(72, 187, 120, 0.3);
            font-weight: 500;
        ">
            🎯 問題準備完了 - 下の入力欄に聞き取った英文を入力してください
        </div>
        """, unsafe_allow_html=True)
    
    st.session_state.dictation_chat_message = st.chat_input("✍️ 聞き取った英文を入力してください...")
else:
    # 他のモード時の無効化された入力フィールド
    st.session_state.dictation_chat_message = st.chat_input("📝 ディクテーションモード時のみ入力可能です", disabled=True)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
        border: 1px solid #fc8181;
        padding: 12px 16px;
        border-radius: 8px;
        text-align: center;
        margin: 10px 0;
        color: #c53030;
        font-weight: 500;
    ">
        ⚠️ ディクテーション入力は「ディクテーション」モード選択時のみ利用可能です
    </div>
    """, unsafe_allow_html=True)

if st.session_state.dictation_chat_message and not st.session_state.chat_open_flg:
    st.stop()

# 「英会話開始」ボタンが押された場合の処理
if st.session_state.start_flg:

    # モード：「ディクテーション」
    # 「ディクテーション」ボタン押下時か、「英会話開始」ボタン押下時か、チャット送信時
    if st.session_state.mode == ct.MODE_3 and (st.session_state.dictation_button_flg or st.session_state.dictation_count == 0 or st.session_state.dictation_chat_message):
        if st.session_state.dictation_first_flg:
            st.session_state.dictation_first_flg = False
        # チャット入力以外
        if not st.session_state.chat_open_flg:
            with st.spinner('🎯 ディクテーション問題を生成しています... しばらくお待ちください'):
                st.session_state.problem, llm_response_audio = ft.create_problem_and_play_audio()

            st.session_state.chat_open_flg = True
            st.session_state.dictation_flg = False
            st.rerun()
        # チャット入力時の処理
        else:
            # チャット欄から入力された場合にのみ評価処理が実行されるようにする
            if not st.session_state.dictation_chat_message:
                st.stop()
            
            # AIメッセージとユーザーメッセージの画面表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                if st.session_state.show_translation:
                    ft.display_english_with_translation(st.session_state.problem, True)
                else:
                    st.markdown(st.session_state.problem)
            with st.chat_message("user", avatar=ct.USER_ICON_PATH):
                if st.session_state.show_translation:
                    ft.display_english_with_translation(st.session_state.dictation_chat_message, True)
                else:
                    st.markdown(st.session_state.dictation_chat_message)

            # LLMが生成した問題文とチャット入力値をメッセージリストに追加
            st.session_state.messages.append({"role": "assistant", "content": st.session_state.problem})
            st.session_state.messages.append({"role": "user", "content": st.session_state.dictation_chat_message})
            
            with st.spinner('📝 あなたの答えを採点しています... 結果をお待ちください'):
                system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                    llm_text=st.session_state.problem,
                    user_text=st.session_state.dictation_chat_message
                )
                # 問題文と回答を比較し、評価結果の生成
                llm_response_evaluation = ft.generate_response(system_template, "")
            
            # 評価結果のメッセージリストへの追加と表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(llm_response_evaluation)
            st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
            st.session_state.messages.append({"role": "other"})
            
            # 各種フラグの更新
            st.session_state.dictation_flg = True
            st.session_state.dictation_chat_message = ""
            st.session_state.dictation_count += 1
            st.session_state.chat_open_flg = False

            st.rerun()

    
    # モード：「日常英会話」
    if st.session_state.mode == ct.MODE_1:
        st.write("### 🎤 音声入力")
        st.info("英語で話してAIと会話しましょう。リアルタイム録音またはファイルアップロードを選択できます。")
        
        # 音声入力を受け取って音声ファイルを作成
        audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        
        # 音声録音・アップロード処理
        if not ft.record_audio(audio_input_file_path):
            st.stop()  # 音声入力が完了していない場合は処理を停止

        # 音声入力ファイルから文字起こしテキストを取得
        with st.spinner('音声入力をテキストに変換中...'):
            transcript = ft.transcribe_audio(audio_input_file_path)
            audio_input_text = transcript.text

        # 音声入力テキストの画面表示
        with st.chat_message("user", avatar=ct.USER_ICON_PATH):
            st.markdown(audio_input_text)

        with st.spinner("回答の音声読み上げ準備中..."):
            # ユーザー入力値をLLMに渡して回答取得（OpenAI API直接使用）
            llm_response = ft.generate_response(
                ct.SYSTEM_TEMPLATE_BASIC_CONVERSATION, 
                audio_input_text,
                st.session_state.conversation_history
            )
            
            # 会話履歴に追加
            st.session_state.conversation_history.extend([
                {"role": "user", "content": audio_input_text},
                {"role": "assistant", "content": llm_response}
            ])
            
            # LLMからの回答を音声データに変換
            llm_response_audio = st.session_state.openai_obj.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=llm_response
            )

            # 一旦mp3形式で音声ファイル作成後、wav形式に変換
            audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
            ft.save_to_wav(llm_response_audio.content, audio_output_file_path)

        # 音声ファイルの読み上げ
        ft.play_wav(audio_output_file_path, speed=ft.extract_speed_value(st.session_state.speed))

        # AIメッセージの画面表示とリストへの追加
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            if st.session_state.show_translation:
                ft.display_english_with_translation(llm_response, True)
            else:
                st.markdown(llm_response)

        # ユーザー入力値とLLMからの回答をメッセージ一覧に追加
        st.session_state.messages.append({"role": "user", "content": audio_input_text})
        st.session_state.messages.append({"role": "assistant", "content": llm_response})


    # モード：「シャドーイング」
    # 「シャドーイング」ボタン押下時か、「英会話開始」ボタン押下時
    if st.session_state.mode == ct.MODE_2 and (st.session_state.shadowing_button_flg or st.session_state.shadowing_count == 0 or st.session_state.shadowing_audio_input_flg):
        if st.session_state.shadowing_first_flg:
            st.session_state.shadowing_first_flg = False
        
        if not st.session_state.shadowing_audio_input_flg:
            with st.spinner('🎯 新しいディクテーション問題を生成しています... しばらくお待ちください'):
                st.session_state.problem, llm_response_audio = ft.create_problem_and_play_audio()

        # 音声入力セクション
        st.write("### 🎤 音声入力")
        mode_text = "シャドーイング" if st.session_state.mode == ct.MODE_2 else "ディクテーション"
        st.info(f"{mode_text}練習：聞いた英語を正確に発音してください。")
        
        # 音声入力を受け取って音声ファイルを作成
        st.session_state.shadowing_audio_input_flg = True
        audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        
        # 音声録音・アップロード処理
        if not ft.record_audio(audio_input_file_path):
            st.session_state.shadowing_audio_input_flg = False
            st.stop()  # 音声入力が完了していない場合は処理を停止
            
        st.session_state.shadowing_audio_input_flg = False

        with st.spinner('音声入力をテキストに変換中...'):
            # 音声入力ファイルから文字起こしテキストを取得
            transcript = ft.transcribe_audio(audio_input_file_path)
            audio_input_text = transcript.text

        # AIメッセージとユーザーメッセージの画面表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            if st.session_state.show_translation:
                ft.display_english_with_translation(st.session_state.problem, True)
            else:
                st.markdown(st.session_state.problem)
        with st.chat_message("user", avatar=ct.USER_ICON_PATH):
            if st.session_state.show_translation:
                ft.display_english_with_translation(audio_input_text, True)
            else:
                st.markdown(audio_input_text)
        
        # LLMが生成した問題文と音声入力値をメッセージリストに追加
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.problem})
        st.session_state.messages.append({"role": "user", "content": audio_input_text})

        with st.spinner('評価結果の生成中...'):
            if st.session_state.shadowing_evaluation_first_flg:
                system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                    llm_text=st.session_state.problem,
                    user_text=audio_input_text
                )
                st.session_state.shadowing_evaluation_first_flg = False
            # 問題文と回答を比較し、評価結果の生成
            llm_response_evaluation = ft.generate_response(system_template, "")
        
        # 評価結果のメッセージリストへの追加と表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(llm_response_evaluation)
        st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
        st.session_state.messages.append({"role": "other"})
        
        # 各種フラグの更新
        st.session_state.shadowing_flg = True
        st.session_state.shadowing_count += 1

        # 「シャドーイング」ボタンを表示するために再描画
        st.rerun()

# 💬 会話履歴（改善版）
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("""
<div style="background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); 
            padding: 1rem; border-radius: 12px; margin: 1rem 0; 
            border-left: 5px solid #2196F3; box-shadow: 0 3px 10px rgba(33, 150, 243, 0.15);">
    <h3 style="color: #1976D2; margin: 0; font-size: 1.4rem; font-weight: bold;">
        💬 会話履歴 & 学習記録
    </h3>
    <p style="color: #424242; margin: 0.3rem 0 0 0; opacity: 0.8; font-size: 0.9rem;">
        あなたの学習の軌跡をここで確認できます
    </p>
</div>
""", unsafe_allow_html=True)

# メッセージが空の場合の表示
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; padding: 2rem 1rem; 
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                border-radius: 12px; border: 2px dashed #dee2e6; margin: 1rem 0;">
        <div style="font-size: 2.5rem; margin-bottom: 1rem;">🌟</div>
        <h3 style="color: #6c757d; margin-bottom: 1rem; font-size: 1.3rem;">学習を開始しましょう！</h3>
        <p style="color: #6c757d; margin: 0; font-size: 1rem; line-height: 1.4;">
            上の「🚀 学習開始」ボタンを押すと、ここに会話履歴が表示されます<br>
            <span style="opacity: 0.7;">選択したモードに応じた学習コンテンツが表示されます</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # メッセージ数のカウント表示（改善版）
    user_messages_count = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
    ai_messages_count = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
    
    # 学習統計を美しいカード風に表示
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #4CAF50, #45a049); 
                padding: 1rem; border-radius: 12px; color: white; 
                margin-bottom: 1rem; box-shadow: 0 3px 10px rgba(76, 175, 80, 0.2);">
        <h4 style="margin: 0 0 0.7rem 0; font-size: 1.1rem; text-align: center;">📊 今回の学習統計</h4>
        <div style="display: flex; justify-content: space-around; text-align: center;">
            <div style="flex: 1;">
                <div style="font-size: 1.6rem; font-weight: bold; margin-bottom: 0.3rem;">{user_messages_count}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">💬 あなたの発言</div>
            </div>
            <div style="flex: 1; border-left: 1px solid rgba(255,255,255,0.3); border-right: 1px solid rgba(255,255,255,0.3);">
                <div style="font-size: 1.6rem; font-weight: bold; margin-bottom: 0.3rem;">{ai_messages_count}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">🤖 AI応答</div>
            </div>
            <div style="flex: 1;">
                <div style="font-size: 1.6rem; font-weight: bold; margin-bottom: 0.3rem;">{user_messages_count + ai_messages_count}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">📝 総やり取り</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # メッセージリストの一覧表示
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message(message["role"], avatar=get_avatar_path(ct.AI_ICON_PATH)):
                if st.session_state.show_translation:
                    ft.display_english_with_translation(message["content"], True)
                else:
                    st.markdown(message["content"])
        elif message["role"] == "user":
            with st.chat_message(message["role"], avatar=get_avatar_path(ct.USER_ICON_PATH)):
                if st.session_state.show_translation:
                    ft.display_english_with_translation(message["content"], True)
                else:
                    st.markdown(message["content"])
        else:
            st.divider()