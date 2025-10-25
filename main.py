import streamlit as st

# ページ設定を最初に実行
st.set_page_config(
    page_title="英語学習アプリ"
)

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

# 🎨 アプリヘッダー
st.markdown("""
<div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
            padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
    <h1 style="color: white; text-align: center; margin: 0; font-size: 2.5rem;">
        🎓 AI英会話学習アプリ
    </h1>
    <p style="color: white; text-align: center; margin: 0.5rem 0 0 0; opacity: 0.9;">
        OpenAI GPTを活用した音声英会話練習プラットフォーム
    </p>
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
    
    st.session_state.openai_obj = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # シンプルなメッセージ履歴を使用（langchain不使用）
    st.session_state.conversation_history = []

    # OpenAI APIを直接使用（langchain不使用）

# 📊 サイドバー - 学習統計
with st.sidebar:
    st.markdown("### 📊 学習統計")
    
    # 統計情報の計算
    user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
    ai_messages = [msg for msg in st.session_state.messages if msg["role"] == "assistant"]
    
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("💬 会話回数", len(user_messages))
    with col_stat2:
        st.metric("🤖 AI応答", len(ai_messages))
    
    # 現在の設定表示
    st.markdown("### ⚙️ 現在の設定")
    if 'mode' in st.session_state:
        st.write(f"📚 **モード**: {st.session_state.mode}")
    if 'speed' in st.session_state:
        st.write(f"🎵 **速度**: {st.session_state.speed}")
    if 'englv' in st.session_state:
        st.write(f"📊 **レベル**: {st.session_state.englv}")
    
    # 翻訳表示設定
    st.markdown("### 🌏 翻訳設定")
    if 'show_translation' not in st.session_state:
        st.session_state.show_translation = True
    
    st.session_state.show_translation = st.checkbox(
        "📖 日本語翻訳を表示", 
        value=st.session_state.show_translation,
        help="英語メッセージに日本語翻訳を追加表示します"
    )
    
    # リセットボタン
    st.markdown("---")
    if st.button("🔄 会話履歴をリセット", use_container_width=True):
        st.session_state.messages = []
        st.session_state.start_flg = False
        st.session_state.shadowing_flg = False
        st.session_state.dictation_flg = False
        st.session_state.chat_open_flg = False
        st.rerun()

# 📱 メインコントロールパネル
st.markdown("### 🎯 学習設定")

# 設定エリアを2行に分けてスッキリと配置
with st.container():
    # 1行目：基本設定
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.session_state.mode = st.selectbox(
            label="📚 学習モード", 
            options=[ct.MODE_1, ct.MODE_2, ct.MODE_3], 
            label_visibility="visible",
            help="学習したいモードを選択してください"
        )
    with col2:
        st.session_state.speed = st.selectbox(
            label="🎵 再生速度", 
            options=ct.PLAY_SPEED_OPTION, 
            index=3, 
            label_visibility="visible",
            help="音声の再生速度を調整できます"
        )
    with col3:
        st.session_state.englv = st.selectbox(
            label="📊 英語レベル", 
            options=ct.ENGLISH_LEVEL_OPTION, 
            label_visibility="visible",
            help="あなたの英語レベルを選択してください"
        )
    
    # 2行目：開始ボタン
    st.markdown("---")
    col_start = st.columns([1, 2, 1])
    with col_start[1]:
        if st.session_state.start_flg:
            st.button("⏸️ 学習中...", use_container_width=True, type="secondary", disabled=True)
        else:
            st.session_state.start_flg = st.button("🚀 学習開始", use_container_width=True, type="primary")
    
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

# 📋 アプリ説明とガイド
st.markdown("---")
with st.expander("📖 アプリの使い方", expanded=False):
    st.markdown("**🎯 生成AIによる音声英会話練習アプリ**")
    st.markdown("何度も繰り返し練習して、英語力をアップさせましょう！")
    
    st.markdown("**【操作方法】**")
    col_help1, col_help2 = st.columns(2)
    with col_help1:
        st.info("""
        **📚 学習モード**
        - **日常英会話**：自由な会話練習
        - **シャドーイング**：音声を聞いて復唱
        - **ディクテーション**：聞き取り練習
        """)
    with col_help2:
        st.info("""
        **🎵 再生速度**
        - **ゆっくり (0.6x-0.8x)**：初心者向け
        - **標準 (1.0x)**：一般的な速度  
        - **速め (1.2x-2.0x)**：上級者向け
        """)
    
    st.warning("💡 **ヒント**: 音声入力後、5秒間沈黙すると自動的に処理が開始されます")

# 💬 会話履歴
st.markdown("### 💬 会話履歴")

# メッセージが空の場合の表示
if not st.session_state.messages:
    st.info("🌟 学習を開始すると、ここに会話履歴が表示されます")
else:
    # メッセージ数のカウント表示
    message_count = len([msg for msg in st.session_state.messages if msg["role"] in ["user", "assistant"]])
    st.caption(f"💭 会話数: {message_count // 2}回")

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
        col_dict = st.columns([1, 2, 1])
        with col_dict[1]:
            st.session_state.dictation_button_flg = st.button(
                "✍️ ディクテーション開始", 
                use_container_width=True, 
                type="primary"
            )

# ✍️ ディクテーションモード入力エリア
if st.session_state.chat_open_flg:
    st.markdown("---")
    st.markdown("### ✍️ ディクテーション入力")
    st.info("🎧 AIが読み上げた音声を、下のテキスト欄に正確に入力してください")

# チャット入力フィールド
if st.session_state.mode == ct.MODE_3:
    st.session_state.dictation_chat_message = st.chat_input("✍️ 聞き取った英文を入力してください...")
else:
    st.session_state.dictation_chat_message = st.chat_input("📝 ディクテーションモード時のみ入力可能です", disabled=True)

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
            with st.spinner('問題文生成中...'):
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
            
            with st.spinner('評価結果の生成中...'):
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
            with st.spinner('問題文生成中...'):
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