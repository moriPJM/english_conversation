import streamlit as st
import os
import time
from pathlib import Path
import wave
import numpy as np
from openai import OpenAI

# カスタム音声録音機能（ブラウザネイティブAPIを使用）
def record_audio_browser_native(audio_input_file_path):
    """
    ブラウザネイティブのMediaRecorder APIを使用した音声録音（改善版）
    """
    st.write("🎤 **ブラウザネイティブ音声録音**")
    st.warning("⚠️ この機能は実験的です。安定した動作には「ファイルアップロード」タブをご利用ください。")
    
    # 簡単な説明
    with st.expander("📖 ブラウザ録音について", expanded=False):
        st.markdown("""
        **🌐 ブラウザ録音の特徴:**
        - ✅ インストール不要で直接録音可能
        - ⚠️ ブラウザやデバイスによって動作が異なる場合があります
        - 🔒 HTTPSまたはlocalhost環境が必要
        - 🎙️ マイクアクセス許可が必要
        
        **💡 推奨:** より確実な動作のため、スマートフォンアプリでの録音をお勧めします
        """)
    
    # 改善されたHTMLとJavaScript
    audio_recorder_html = """
    <div style="text-align: center; padding: 20px; border: 2px solid #4CAF50; border-radius: 15px; margin: 20px 0; background: linear-gradient(145deg, #f0f8ff, #e6f3ff);">
        <h3 style="color: #2E7D32;">🎙️ ワンクリック録音</h3>
        <div style="margin: 20px 0;">
            <button id="recordBtn" style="background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white; border: none; padding: 15px 30px; border-radius: 25px; margin: 10px; font-size: 18px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                🎤 録音開始
            </button>
        </div>
        <div id="status" style="font-size: 16px; font-weight: bold; color: #1976D2; margin: 15px 0;">
            📝 録音準備完了 - 上のボタンをクリックしてください
        </div>
        <div id="audioContainer" style="margin: 20px 0; display: none;">
            <audio id="audioPlayer" controls style="width: 100%; max-width: 400px; margin: 10px 0;"></audio>
            <br>
            <a id="downloadBtn" style="background: linear-gradient(45deg, #4CAF50, #45a049); color: white; padding: 12px 24px; border-radius: 20px; text-decoration: none; margin: 10px; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                💾 音声ファイルをダウンロード
            </a>
        </div>
        <div id="instructions" style="font-size: 14px; color: #666; margin-top: 20px;">
            � 録音後、ダウンロードしたファイルを「ファイルアップロード」タブでアップロードしてください
        </div>
    </div>
    
    <script>
    (function() {
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        
        const recordBtn = document.getElementById('recordBtn');
        const status = document.getElementById('status');
        const audioContainer = document.getElementById('audioContainer');
        const audioPlayer = document.getElementById('audioPlayer');
        const downloadBtn = document.getElementById('downloadBtn');
        
        // ブラウザ対応チェック
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            status.innerHTML = '❌ このブラウザは録音機能に対応していません';
            recordBtn.disabled = true;
            return;
        }
        
        recordBtn.addEventListener('click', async function() {
            if (!isRecording) {
                await startRecording();
            } else {
                stopRecording();
            }
        });
        
        async function startRecording() {
            try {
                status.innerHTML = '🔄 マイクアクセスを要求中...';
                
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 44100
                    } 
                });
                
                audioChunks = [];
                
                // ブラウザに応じてMIMEタイプを選択
                let mimeType = 'audio/webm';
                if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                    mimeType = 'audio/webm;codecs=opus';
                } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                    mimeType = 'audio/mp4';
                } else if (MediaRecorder.isTypeSupported('audio/wav')) {
                    mimeType = 'audio/wav';
                }
                
                mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
                
                mediaRecorder.ondataavailable = function(event) {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = function() {
                    const audioBlob = new Blob(audioChunks, { type: mimeType });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    audioPlayer.src = audioUrl;
                    audioContainer.style.display = 'block';
                    
                    // ファイル名にタイムスタンプを追加
                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                    const fileName = `recorded_audio_${timestamp}.webm`;
                    
                    downloadBtn.href = audioUrl;
                    downloadBtn.download = fileName;
                    
                    status.innerHTML = '✅ 録音完了！再生・ダウンロードできます';
                    
                    // マイクストリームを停止
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.onerror = function(event) {
                    status.innerHTML = '❌ 録音エラーが発生しました';
                    console.error('MediaRecorder error:', event);
                };
                
                mediaRecorder.start(1000); // 1秒ごとにデータを収集
                isRecording = true;
                
                recordBtn.innerHTML = '⏹️ 録音停止';
                recordBtn.style.background = 'linear-gradient(45deg, #f44336, #d32f2f)';
                status.innerHTML = '🔴 録音中... もう一度クリックで停止';
                
            } catch (error) {
                console.error('録音開始エラー:', error);
                if (error.name === 'NotAllowedError') {
                    status.innerHTML = '❌ マイクアクセスが拒否されました。ブラウザ設定を確認してください';
                } else if (error.name === 'NotFoundError') {
                    status.innerHTML = '❌ マイクが見つかりません';
                } else {
                    status.innerHTML = '❌ 録音を開始できませんでした';
                }
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                isRecording = false;
                
                recordBtn.innerHTML = '🎤 録音開始';
                recordBtn.style.background = 'linear-gradient(45deg, #ff6b6b, #ee5a24)';
                status.innerHTML = '⏳ 録音データを処理中...';
            }
        }
    })();
    </script>
    """
    
    # HTMLコンポーネントを表示
    st.components.v1.html(audio_recorder_html, height=400)
    
    return False  # この機能は録音データを直接返さない

# pydubを条件付きインポート
try:
    from pydub import AudioSegment
    from pydub.utils import which
    PYDUB_AVAILABLE = True
    
    # ffmpegの可用性をチェック
    if not which("ffmpeg"):
        st.warning("ffmpegが見つかりません。一部の音声機能が制限される可能性があります。")
except ImportError:
    st.warning("pydubが利用できません。音声変換機能が制限されます。")
    PYDUB_AVAILABLE = False
# Streamlit and core libraries only - no langchain
import constants as ct

def record_audio(audio_input_file_path):
    """
    音声入力を受け取って音声ファイルを作成（録音機能付き）
    """
    
    # 録音方法を選択
    audio_input_method = st.radio(
        "音声入力方法を選択してください：",
        ["📱 リアルタイム録音", "📁 ファイルアップロード"],
        horizontal=True
    )
    
    if audio_input_method == "📱 リアルタイム録音":
        return record_audio_realtime(audio_input_file_path)
    else:
        return record_audio_upload(audio_input_file_path)

def record_audio_realtime(audio_input_file_path):
    """
    複数の音声録音方法を提供（フォールバック機能付き）
    """
    st.write("🎤 **音声入力方法を選択**")
    st.info("💡 **推奨**: 最も確実な「ファイルアップロード」方式をお試しください")
    
    # タブで録音方法を選択
    tab1, tab2, tab3 = st.tabs(["📁 ファイルアップロード（推奨）", "🎙️ ブラウザ録音（実験的）", "📱 録音アプリガイド"])
    
    with tab1:
        st.success("✅ **最も安定した方法**: スマートフォンや録音アプリで録音してからアップロード")
        return record_audio_upload(audio_input_file_path)
    
    with tab2:
        return record_audio_browser_native(audio_input_file_path)
    
    with tab3:
        show_recording_app_guide()
        return False

def show_recording_app_guide():
    """
    録音アプリの使用ガイドを表示
    """
    st.write("📱 **おすすめ録音アプリ・方法**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📱 **スマートフォン**
        
        **iPhone の場合:**
        - 🎤 **ボイスメモ** (標準アプリ)
        - 🎵 **GarageBand** (高音質)
        - 📱 **録音 - PCM録音** (高品質)
        
        **Android の場合:**
        - 🎤 **音声レコーダー** (標準)
        - 🎵 **Hi-Q MP3ボイスレコーダー**
        - 📱 **Smart Recorder**
        """)
    
    with col2:
        st.markdown("""
        ### 💻 **パソコン**
        
        **Windows の場合:**
        - 🎤 **ボイスレコーダー** (標準アプリ)
        - 🎵 **Audacity** (無料・高機能)
        - 📱 **Windows Media Player**
        
        **Mac の場合:**
        - 🎤 **QuickTime Player**
        - 🎵 **GarageBand**
        - 📱 **Voice Memos**
        """)
    
    st.markdown("---")
    
    # 録音手順ガイド
    with st.expander("📖 詳細録音手順", expanded=True):
        step_col1, step_col2, step_col3 = st.columns(3)
        
        with step_col1:
            st.markdown("""
            **ステップ 1: 録音**
            1. 📱 録音アプリを開く
            2. 🎤 録音ボタンを押す
            3. 🗣️ 明確に話す
            4. ⏹️ 録音を停止
            """)
        
        with step_col2:
            st.markdown("""
            **ステップ 2: 保存**
            1. 💾 ファイルを保存
            2. 📂 保存場所を確認
            3. 🏷️ 分かりやすい名前をつける
            4. ✅ 形式を確認 (WAV/MP3推奨)
            """)
        
        with step_col3:
            st.markdown("""
            **ステップ 3: アップロード**
            1. 🔄 このアプリに戻る
            2. 📁 「ファイルアップロード」タブ
            3. 🎤 録音ファイルを選択
            4. 🚀 アップロード実行
            """)
    
    # 音質向上のコツ
    with st.expander("🎯 高品質録音のコツ", expanded=False):
        tip_col1, tip_col2 = st.columns(2)
        
        with tip_col1:
            st.markdown("""
            **📍 環境設定:**
            - 🔇 静かな場所で録音
            - 🎤 マイクに近づく（10-15cm）
            - 🚫 風切り音を避ける
            - 💡 エアコン等の騒音を止める
            """)
        
        with tip_col2:
            st.markdown("""
            **🗣️ 話し方:**
            - 📢 はっきりと発音
            - 🐌 ゆっくりと話す
            - 📏 一定の音量を保つ
            - ⏸️ 文の間に少し間を入れる
            """)
    
    st.success("💡 **重要**: 録音後は「ファイルアップロード」タブでファイルをアップロードしてください！")

def record_audio_upload(audio_input_file_path):
    """
    改善された音声ファイルアップロード機能
    """
    st.write("📁 **音声ファイルアップロード**")
    
    # 使い方ガイド
    with st.expander("📖 録音方法ガイド", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📱 スマートフォンの場合:**
            1. 「ボイスメモ」や「録音」アプリを開く
            2. 録音ボタンを押して話す
            3. 録音を停止して保存
            4. ファイルを選択してアップロード
            """)
        with col2:
            st.markdown("""
            **💻 パソコンの場合:**
            1. Windows「ボイスレコーダー」を開く
            2. 録音ボタンを押して話す
            3. 録音を停止して保存
            4. ファイルを選択してアップロード
            """)
    
    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "🎙️ 音声ファイルを選択してアップロード",
        type=['wav', 'mp3', 'm4a', 'aac', 'ogg', 'flac', 'webm', 'mp4'],
        help="録音アプリで作成した音声ファイルをアップロードしてください",
        key="audio_upload_main"
    )
    
    if uploaded_file is not None:
        # ファイル情報を表示
        file_size = len(uploaded_file.getvalue()) / 1024 / 1024  # MB
        st.info(f"📄 ファイル名: {uploaded_file.name} | サイズ: {file_size:.2f} MB")
        
        # アップロードされたファイルを保存
        with open(audio_input_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success("✅ 音声ファイルがアップロードされました！")
        
        # アップロードした音声を再生して確認
        st.write("📻 **アップロード内容を確認**")
        st.audio(audio_input_file_path)
        
        # アップロードをやり直すオプション
        if st.button("🔄 別のファイルをアップロード", key="redo_upload"):
            st.rerun()
        
        return True
    else:
        st.info("🎙️ 音声ファイルを選択してアップロードしてください")
        return False

def transcribe_audio(audio_input_file_path):
    """
    音声入力ファイルから文字起こしテキストを取得
    Args:
        audio_input_file_path: 音声入力ファイルのパス
    """

    with open(audio_input_file_path, 'rb') as audio_input_file:
        transcript = st.session_state.openai_obj.audio.transcriptions.create(
            model="whisper-1",
            file=audio_input_file,
            language="en"
        )
    
    # 音声入力ファイルを削除
    os.remove(audio_input_file_path)

    return transcript

def save_to_wav(llm_response_audio, audio_output_file_path):
    """
    一旦mp3形式で音声ファイル作成後、wav形式に変換
    Args:
        llm_response_audio: LLMからの回答の音声データ
        audio_output_file_path: 出力先のファイルパス
    """

    temp_audio_output_filename = f"{ct.AUDIO_OUTPUT_DIR}/temp_audio_output_{int(time.time())}.mp3"
    
    try:
        # mp3ファイルを一時的に保存
        with open(temp_audio_output_filename, "wb") as temp_audio_output_file:
            temp_audio_output_file.write(llm_response_audio)
        
        # pydubが利用できる場合のみ変換を実行
        if PYDUB_AVAILABLE:
            try:
                audio_mp3 = AudioSegment.from_file(temp_audio_output_filename, format="mp3")
                audio_mp3.export(audio_output_file_path, format="wav")
            except Exception as pydub_error:
                st.warning(f"音声変換をスキップします (pydub利用不可): {pydub_error}")
                # 変換に失敗した場合、mp3ファイルをそのまま使用
                import shutil
                mp3_output_path = audio_output_file_path.replace('.wav', '.mp3')
                shutil.copy2(temp_audio_output_filename, mp3_output_path)
                audio_output_file_path = mp3_output_path
        else:
            # pydubが利用できない場合、mp3ファイルをそのまま使用
            import shutil
            mp3_output_path = audio_output_file_path.replace('.wav', '.mp3')
            shutil.copy2(temp_audio_output_filename, mp3_output_path)
            audio_output_file_path = mp3_output_path

        # 音声出力用に一時的に作ったmp3ファイルを削除
        if os.path.exists(temp_audio_output_filename):
            os.remove(temp_audio_output_filename)
            
    except Exception as e:
        st.error(f"音声ファイル処理エラー: {e}")
        # 一時ファイルのクリーンアップ
        if os.path.exists(temp_audio_output_filename):
            os.remove(temp_audio_output_filename)

def extract_speed_value(speed_string):
    """
    再生速度文字列から数値を抽出
    Args:
        speed_string: "1.0x (標準)" のような形式の文字列
    Returns:
        float: 速度の数値（例: 1.0）
    """
    try:
        # "1.0x" の部分を抽出
        speed_part = speed_string.split('x')[0]
        return float(speed_part)
    except (ValueError, IndexError):
        # エラーの場合は標準速度を返す
        return 1.0

def play_wav(audio_output_file_path, speed=1.0):
    """
    音声ファイルの読み上げ
    Args:
        audio_output_file_path: 音声ファイルのパス
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
    """

    try:
        if PYDUB_AVAILABLE:
            # 音声ファイルの形式を判定
            if audio_output_file_path.endswith('.wav'):
                audio = AudioSegment.from_wav(audio_output_file_path)
                audio_format = 'audio/wav'
            elif audio_output_file_path.endswith('.mp3'):
                audio = AudioSegment.from_mp3(audio_output_file_path)
                audio_format = 'audio/mp3'
            else:
                st.error("サポートされていない音声形式です")
                return
            
            # 速度を変更
            if speed != 1.0:
                # frame_rateを変更することで速度を調整
                modified_audio = audio._spawn(
                    audio.raw_data, 
                    overrides={"frame_rate": int(audio.frame_rate * speed)}
                )
                # 元のframe_rateに戻すことで正常再生させる（ピッチを保持したまま速度だけ変更）
                modified_audio = modified_audio.set_frame_rate(audio.frame_rate)

                # 一時ファイルとして保存
                temp_path = audio_output_file_path.replace('.wav', '_temp.wav').replace('.mp3', '_temp.wav')
                modified_audio.export(temp_path, format="wav")
                audio_output_file_path = temp_path
                audio_format = 'audio/wav'

        else:
            # pydubが利用できない場合は速度変更なしで再生
            if speed != 1.0:
                st.warning("pydubが利用できないため、速度変更はスキップされます")
            audio_format = 'audio/wav' if audio_output_file_path.endswith('.wav') else 'audio/mp3'

        # Streamlitの音声プレーヤーで再生
        st.audio(audio_output_file_path, format=audio_format)
        
    except Exception as e:
        st.error(f"音声再生エラー: {e}")
        # フォールバック: 元のファイルをそのまま再生
        try:
            format_type = 'audio/wav' if audio_output_file_path.endswith('.wav') else 'audio/mp3'
            st.audio(audio_output_file_path, format=format_type)
        except Exception as fallback_error:
            st.error(f"音声再生に失敗しました: {fallback_error}")

def translate_to_japanese(english_text):
    """
    英語テキストを日本語に翻訳
    Args:
        english_text: 翻訳する英語テキスト
    Returns:
        str: 日本語翻訳テキスト
    """
    try:
        # OpenAI APIのクライアントを初期化
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは優秀な英日翻訳者です。英語を自然で分かりやすい日本語に翻訳してください。翻訳結果のみを返してください。"},
                {"role": "user", "content": f"以下の英語を日本語に翻訳してください:\n{english_text}"}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        st.error(f"翻訳エラー: {e}")
        return "翻訳に失敗しました"

def display_english_with_translation(english_text, show_translation=True):
    """
    英語テキストと日本語訳を表示
    Args:
        english_text: 英語テキスト
        show_translation: 翻訳を表示するかどうか
    """
    # 英語テキストを表示
    st.markdown(f"**🇺🇸 English**: {english_text}")
    
    if show_translation:
        # 翻訳を取得して表示
        with st.spinner("翻訳中..."):
            japanese_text = translate_to_japanese(english_text)
        st.markdown(f"**🇯🇵 日本語**: {japanese_text}")
        st.markdown("---")
    
    # 一定時間後にファイルクリーンアップ（バックグラウンドで実行される想定）

def generate_response(system_template, user_input, conversation_history=None):
    """
    OpenAI APIを直接使用してレスポンスを生成（langchain不使用）
    """
    try:
        messages = [{"role": "system", "content": system_template}]
        
        # 会話履歴があれば追加
        if conversation_history:
            messages.extend(conversation_history[-10:])  # 最新10件のみ保持
            
        messages.append({"role": "user", "content": user_input})
        
        response = st.session_state.openai_obj.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API エラー: {e}")
        return "申し訳ございません。エラーが発生しました。"

def create_problem_and_play_audio():
    """
    問題生成と音声ファイルの再生（OpenAI API直接使用）
    """

    # 問題文を生成
    problem = generate_response(ct.SYSTEM_TEMPLATE_CREATE_PROBLEM, "")

    # LLMからの回答を音声データに変換
    llm_response_audio = st.session_state.openai_obj.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=problem
    )

    # 音声ファイルの作成
    audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
    save_to_wav(llm_response_audio.content, audio_output_file_path)

    # 音声ファイルの読み上げ
    play_wav(audio_output_file_path, extract_speed_value(st.session_state.speed))

    return problem, llm_response_audio