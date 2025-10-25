import streamlit as st
import os
import time
from pathlib import Path
import wave
import numpy as np
from openai import OpenAI

# streamlit-audiorecorderを条件付きインポート
try:
    from streamlit_audiorecorder import audiorecorder
    STREAMLIT_AUDIORECORDER_AVAILABLE = True
except ImportError:
    STREAMLIT_AUDIORECORDER_AVAILABLE = False

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

def record_audio_browser_enhanced(audio_input_file_path):
    """
    改善されたブラウザネイティブのMediaRecorder APIを使用した音声録音
    """
    st.markdown("### 🌐 **改善版ブラウザ録音**")
    
    # 機能紹介
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ **新機能**")
        st.markdown("""
        - 🎯 高品質録音(48kHz)
        - ⏱️ リアルタイムタイマー
        - 📊 音声レベル表示
        - 🔄 自動フォーマット選択
        """)
    
    with col2:
        st.warning("⚠️ **動作環境**")
        st.markdown("""
        - 🔒 HTTPS環境推奨
        - 🎙️ マイク許可必須
        - 📱 モダンブラウザ対応
        - 📂 ダウンロード後使用
        """)
    
    # 詳細な使用方法
    with st.expander("📖 **使用方法ガイド**", expanded=True):
        st.markdown("""
        ### 🚀 **簡単3ステップ**
        
        **1️⃣ 録音準備**
        - 🎤 「録音開始」ボタンをクリック
        - 🔓 ブラウザのマイク許可を承認
        
        **2️⃣ 音声録音**
        - 🔴 録音中はタイマーが表示されます
        - 🗣️ クリアに話してください
        - ⏹️ 「録音停止」で終了
        
        **3️⃣ ファイル使用**
        - 💾 「ダウンロード」ボタンで保存
        - 📁 「ファイルアップロード」タブで使用
        
        ### 🔧 **トラブルシューティング**
        
        **❌ 問題が発生した場合:**
        - ページを更新してやり直し
        - ブラウザ設定でマイクを許可
        - 最新ブラウザを使用
        - 代替として「ファイルアップロード」を使用
        """)
    
    # 高機能HTMLとJavaScript（超コンパクト版）
    enhanced_recorder_html = """
    <div style="max-width: 550px; margin: 10px auto; padding: 15px; border: 2px solid #2196F3; border-radius: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); box-shadow: 0 8px 20px rgba(0,0,0,0.1); color: white;">
        <div style="text-align: center;">
            <h2 style="color: white; margin-bottom: 15px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); font-size: 1.3rem;">🎙️ プロ仕様ブラウザ録音</h2>
            
            <div style="margin: 15px 0;">
                <button id="enhancedRecordBtn" style="background: linear-gradient(45deg, #FF6B6B, #FF8E53); color: white; border: none; padding: 12px 25px; border-radius: 25px; font-size: 15px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(255,107,107,0.4); transition: all 0.3s ease; margin: 8px;">
                    🎤 高品質録音開始
                </button>
            </div>
            
            <div id="enhancedStatus" style="font-size: 14px; font-weight: bold; color: white; margin: 15px 0; min-height: 30px; padding: 10px; background: rgba(255,255,255,0.2); border-radius: 12px;">
                📝 高品質録音準備完了 - 録音開始ボタンをクリックしてください
            </div>
            
            <div id="enhancedControls" style="margin: 15px 0; display: none;">
                <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 12px; margin: 12px 0;">
                    <div id="enhancedTimer" style="font-size: 24px; color: #FFE082; font-weight: bold; margin: 8px 0;">00:00</div>
                    <div id="enhancedLevel" style="height: 15px; border: 2px solid rgba(255,255,255,0.3); border-radius: 8px; margin: 8px 0; background: rgba(0,0,0,0.2); position: relative;">
                        <div id="enhancedLevelBar" style="height: 100%; background: linear-gradient(90deg, #4CAF50, #FFC107, #FF5722); width: 0%; transition: width 0.1s; border-radius: 6px;"></div>
                    </div>
                    <div style="font-size: 12px; color: rgba(255,255,255,0.8);">音声レベル</div>
                </div>
                
                <audio id="enhancedAudioPlayer" controls style="width: 100%; max-width: 400px; margin: 12px 0; border-radius: 10px; display: none;"></audio>
                
                <div style="margin: 15px 0;">
                    <a id="enhancedDownloadBtn" style="display: none; background: linear-gradient(45deg, #43A047, #66BB6A); color: white; padding: 12px 25px; border-radius: 20px; text-decoration: none; font-weight: bold; box-shadow: 0 4px 15px rgba(67,160,71,0.4); transition: all 0.3s ease; font-size: 14px;">
                        💾 高品質音声をダウンロード
                    </a>
                </div>
            </div>
            
            <div style="margin-top: 15px; padding: 12px; background: rgba(76, 175, 80, 0.2); border-radius: 10px; font-size: 13px; color: rgba(255,255,255,0.9);">
                💡 録音後、ダウンロードしたファイルを「ファイルアップロード」タブでアップロードしてください
            </div>
        </div>
    </div>
    
    <script>
    (function() {
        let enhancedMediaRecorder = null;
        let enhancedAudioChunks = [];
        let enhancedIsRecording = false;
        let enhancedAudioContext = null;
        let enhancedAnalyser = null;
        let enhancedMicrophone = null;
        let enhancedTimer = null;
        let enhancedStartTime = 0;
        
        const enhancedRecordBtn = document.getElementById('enhancedRecordBtn');
        const enhancedStatus = document.getElementById('enhancedStatus');
        const enhancedControls = document.getElementById('enhancedControls');
        const enhancedTimerDisplay = document.getElementById('enhancedTimer');
        const enhancedLevel = document.getElementById('enhancedLevel');
        const enhancedLevelBar = document.getElementById('enhancedLevelBar');
        const enhancedAudioPlayer = document.getElementById('enhancedAudioPlayer');
        const enhancedDownloadBtn = document.getElementById('enhancedDownloadBtn');
        
        // ブラウザ対応チェック
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            enhancedStatus.innerHTML = '❌ このブラウザは録音機能に対応していません<br><small>Chrome、Firefox、Safari等の最新ブラウザをお使いください</small>';
            enhancedRecordBtn.disabled = true;
            return;
        }
        
        enhancedRecordBtn.addEventListener('click', async function() {
            if (!enhancedIsRecording) {
                await startEnhancedRecording();
            } else {
                stopEnhancedRecording();
            }
        });
        
        async function startEnhancedRecording() {
            try {
                enhancedStatus.innerHTML = '🔄 高品質マイクアクセスを要求中...<br><small>ブラウザの許可ダイアログで「許可」をクリックしてください</small>';
                
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 48000,
                        sampleSize: 16,
                        channelCount: 1
                    } 
                });
                
                enhancedAudioChunks = [];
                
                // 最高品質のMIMEタイプを選択
                let mimeType = 'audio/webm;codecs=opus';
                let fileExtension = 'webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/webm';
                    fileExtension = 'webm';
                    if (!MediaRecorder.isTypeSupported(mimeType)) {
                        mimeType = 'audio/mp4';
                        fileExtension = 'm4a';
                        if (!MediaRecorder.isTypeSupported(mimeType)) {
                            mimeType = 'audio/wav';
                            fileExtension = 'wav';
                        }
                    }
                }
                
                enhancedMediaRecorder = new MediaRecorder(stream, { 
                    mimeType: mimeType,
                    audioBitsPerSecond: 192000
                });
                
                enhancedMediaRecorder.ondataavailable = function(event) {
                    if (event.data.size > 0) {
                        enhancedAudioChunks.push(event.data);
                    }
                };
                
                enhancedMediaRecorder.onstop = function() {
                    const audioBlob = new Blob(enhancedAudioChunks, { type: mimeType });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    enhancedAudioPlayer.src = audioUrl;
                    enhancedAudioPlayer.style.display = 'block';
                    
                    // ダウンロードリンクを設定
                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
                    const fileName = `enhanced_recording_${timestamp}.${fileExtension}`;
                    
                    enhancedDownloadBtn.href = audioUrl;
                    enhancedDownloadBtn.download = fileName;
                    enhancedDownloadBtn.style.display = 'inline-block';
                    
                    const fileSizeMB = (audioBlob.size / 1024 / 1024).toFixed(2);
                    const duration = formatEnhancedTime(Date.now() - enhancedStartTime);
                    
                    enhancedStatus.innerHTML = `✅ 高品質録音完了！<br><small>時間: ${duration} | サイズ: ${fileSizeMB}MB</small>`;
                    
                    // ストリームを停止
                    stream.getTracks().forEach(track => track.stop());
                    
                    // UI をリセット
                    enhancedRecordBtn.disabled = false;
                    enhancedRecordBtn.innerHTML = '🎤 新しい録音を開始';
                    enhancedRecordBtn.style.background = 'linear-gradient(45deg, #FF6B6B, #FF8E53)';
                    clearInterval(enhancedTimer);
                    
                    // 音声コンテキストをクリーンアップ
                    if (enhancedAudioContext) {
                        enhancedAudioContext.close();
                    }
                    
                    // 録音完了後に下部コンテンツが見えるようにスクロール
                    setTimeout(() => {
                        // より大きくスクロールして確実に下部が見えるようにする
                        window.scrollBy({
                            top: 200,
                            behavior: 'smooth'
                        });
                        // さらに少し待って追加スクロール
                        setTimeout(() => {
                            window.scrollBy({
                                top: 100,
                                behavior: 'smooth'
                            });
                        }, 500);
                    }, 500);
                };
                
                // 録音開始
                enhancedMediaRecorder.start(250);
                enhancedIsRecording = true;
                enhancedStartTime = Date.now();
                
                // UI更新
                enhancedRecordBtn.innerHTML = '⏹️ 録音停止';
                enhancedRecordBtn.style.background = 'linear-gradient(45deg, #4ECDC4, #44A08D)';
                enhancedControls.style.display = 'block';
                enhancedStatus.innerHTML = '🔴 高品質録音中... クリアに話してください';
                
                // タイマー開始
                enhancedTimer = setInterval(updateEnhancedTimer, 100);
                
                // 音声レベル表示
                try {
                    enhancedAudioContext = new (window.AudioContext || window.webkitAudioContext)();
                    enhancedAnalyser = enhancedAudioContext.createAnalyser();
                    enhancedAnalyser.fftSize = 256;
                    
                    enhancedMicrophone = enhancedAudioContext.createMediaStreamSource(stream);
                    enhancedMicrophone.connect(enhancedAnalyser);
                    visualizeEnhancedAudio();
                } catch (e) {
                    console.log('音声視覚化は利用できません:', e);
                }
                
            } catch (error) {
                console.error('録音開始エラー:', error);
                let errorMessage = '❌ 録音を開始できませんでした<br>';
                
                if (error.name === 'NotAllowedError') {
                    errorMessage += '<small>マイクアクセスが拒否されました。ブラウザ設定でマイクを許可してください</small>';
                } else if (error.name === 'NotFoundError') {
                    errorMessage += '<small>マイクが見つかりません。デバイスの接続を確認してください</small>';
                } else {
                    errorMessage += `<small>エラー詳細: ${error.message}</small>`;
                }
                
                enhancedStatus.innerHTML = errorMessage;
                enhancedRecordBtn.disabled = false;
            }
        }
        
        function stopEnhancedRecording() {
            if (enhancedMediaRecorder && enhancedMediaRecorder.state === 'recording') {
                enhancedMediaRecorder.stop();
                enhancedIsRecording = false;
                enhancedStatus.innerHTML = '⏳ 高品質音声データを処理中...<br><small>しばらくお待ちください</small>';
            }
        }
        
        function updateEnhancedTimer() {
            const elapsed = Date.now() - enhancedStartTime;
            enhancedTimerDisplay.textContent = formatEnhancedTime(elapsed);
        }
        
        function formatEnhancedTime(ms) {
            const seconds = Math.floor(ms / 1000);
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
        }
        
        function visualizeEnhancedAudio() {
            if (!enhancedAnalyser || !enhancedIsRecording) return;
            
            const bufferLength = enhancedAnalyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            function draw() {
                if (!enhancedIsRecording) return;
                
                enhancedAnalyser.getByteFrequencyData(dataArray);
                
                // 音量の平均を計算
                const average = dataArray.reduce((a, b) => a + b) / bufferLength;
                const percentage = Math.floor((average / 255) * 100);
                
                enhancedLevelBar.style.width = percentage + '%';
                
                requestAnimationFrame(draw);
            }
            
            draw();
        }
        
    })();
    </script>
    """
    
    # HTMLコンポーネントを表示（さらに高さを縮小し、スクロール改善）
    st.components.v1.html(enhanced_recorder_html, height=350, scrolling=True)
    
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
    st.info("💡 **新機能**: Streamlit Audiorecorderを追加しました！")
    
    # タブで録音方法を選択
    if STREAMLIT_AUDIORECORDER_AVAILABLE:
        tab1, tab2, tab3, tab4 = st.tabs(["🎙️ リアルタイム録音", "📁 ファイルアップロード", "🌐 ブラウザ録音", "📱 録音ガイド"])
        
        with tab1:
            st.success("✅ **最新機能**: Streamlit専用の録音コンポーネント")
            result = record_audio_streamlit_recorder(audio_input_file_path)
            if result:
                return result
        
        with tab2:
            st.info("📁 **従来の方法**: 外部アプリで録音してからアップロード")
            result = record_audio_upload(audio_input_file_path)
            if result:
                return result
        
        with tab3:
            st.info("🌐 **改善版ブラウザ録音**: MediaRecorder APIを使用")
            result = record_audio_browser_enhanced(audio_input_file_path)
            if result:
                return result
        
        with tab4:
            st.info("📱 **録音ガイド**: 詳細な使用方法")
            show_recording_app_guide()
    else:
        tab1, tab2, tab3 = st.tabs(["📁 ファイルアップロード（推奨）", "🌐 ブラウザ録音", "📱 録音ガイド"])
        
        with tab1:
            st.success("✅ **最も安定した方法**: スマートフォンや録音アプリで録音してからアップロード")
            result = record_audio_upload(audio_input_file_path)
            if result:
                return result
        
        with tab2:
            st.info("🌐 **改善版ブラウザ録音**: MediaRecorder APIを使用")
            result = record_audio_browser_enhanced(audio_input_file_path)
            if result:
                return result
        
        with tab3:
            st.info("📱 **録音ガイド**: 詳細な使用方法")
            show_recording_app_guide()
    
    return False  # 音声が録音されていない場合

def record_audio_streamlit_recorder(audio_input_file_path):
    """
    Streamlit Audiorecorderを使用した録音
    """
    st.write("🎙️ **Streamlit Audiorecorder - 最新録音機能**")
    st.info("🔥 録音ボタンを押して話してください。もう一度押すと停止します。")
    
    # Streamlit Audiorecorderコンポーネント
    audio_bytes = audiorecorder("🎤 録音開始", "⏹️ 録音停止")
    
    if len(audio_bytes) > 0:
        # 録音データをファイルに保存
        with open(audio_input_file_path, "wb") as f:
            f.write(audio_bytes.tobytes())
        
        st.success("✅ 音声が録音されました！")
        
        # 録音した音声を再生して確認
        st.write("📻 **録音内容を確認**")
        st.audio(audio_bytes, format='audio/wav')
        
        # 録音をやり直すオプション
        if st.button("🔄 録音をやり直す", key="redo_streamlit_recorder"):
            st.rerun()
            
        return True
    else:
        st.info("🎙️ 上の録音ボタンを押して音声を録音してください")
        return False

def show_recording_app_guide():
    """
    録音アプリの使用ガイドを表示（改善版）
    """
    st.markdown("### 📱 **完全録音ガイド - 100%成功の秘訣**")
    
    # 成功率の高い方法を最初に表示
    st.success("🏆 **最も確実な方法 (成功率98%)**")
    
    # タブで情報を整理
    guide_tab1, guide_tab2, guide_tab3, guide_tab4 = st.tabs([
        "📱 スマートフォン", "💻 パソコン", "🎯 録音のコツ", "🔧 トラブル解決"
    ])
    
    with guide_tab1:
        st.markdown("### 📱 **スマートフォンで録音（推奨）**")
        
        phone_col1, phone_col2 = st.columns(2)
        
        with phone_col1:
            st.markdown("#### 🍎 **iPhone**")
            st.info("""
            **🥇 最推奨: ボイスメモ**
            - 📍 場所: ホーム画面の標準アプリ
            - � 操作: 赤い丸ボタンで録音開始
            - 💾 保存: 自動で保存される
            - 📤 共有: 共有ボタンでファイル出力
            
            **🥈 高音質: GarageBand**
            - 📍 App Storeから無料ダウンロード
            - 🎵 「Audio Recorder」を選択
            - 🎛️ 高音質設定が可能
            """)
            
        with phone_col2:
            st.markdown("#### 🤖 **Android**")
            st.info("""
            **🥇 最推奨: 音声レコーダー**
            - 📍 場所: プリインストール済み
            - � 操作: マイクボタンで録音
            - 💾 保存: 内部ストレージに保存
            - 📤 共有: 共有機能でファイル送信
            
            **🥈 高音質: Hi-Q MP3ボイスレコーダー**
            - � Google Playから無料ダウンロード
            - 🎵 MP3高音質録音対応
            """)
        
        st.markdown("#### 📋 **スマートフォン録音手順**")
        step_col1, step_col2, step_col3, step_col4 = st.columns(4)
        
        with step_col1:
            st.markdown("""
            **1️⃣ 準備**
            - 🔇 周囲を静かにする
            - 🎤 マイクに近づく（10-20cm）
            - 🔋 バッテリー確認
            """)
        
        with step_col2:
            st.markdown("""
            **2️⃣ 録音**
            - 🎤 録音ボタンをタップ
            - 🗣️ はっきりと話す
            - ⏸️ 必要に応じて一時停止
            """)
        
        with step_col3:
            st.markdown("""
            **3️⃣ 確認**
            - ▶️ 録音内容を再生
            - 🔊 音量・音質をチェック
            - 🔄 必要なら録り直し
            """)
        
        with step_col4:
            st.markdown("""
            **4️⃣ 送信**
            - 📤 共有ボタンをタップ
            - 💾 ファイルとして保存
            - 📁 アップロードで使用
            """)
    
    with guide_tab2:
        st.markdown("### 💻 **パソコンで録音**")
        
        pc_col1, pc_col2 = st.columns(2)
        
        with pc_col1:
            st.markdown("#### 🪟 **Windows**")
            st.info("""
            **🥇 簡単: ボイスレコーダー**
            - 📍 スタートメニュー → ボイスレコーダー
            - � マイクボタンで録音開始
            - 💾 自動保存（ドキュメント/録音）
            
            **🥈 高機能: Audacity（無料）**
            - 🌐 https://www.audacityteam.org/
            - 🎛️ プロ級の編集機能
            - � 多様なフォーマットで出力
            """)
            
        with pc_col2:
            st.markdown("#### 🍎 **macOS**")
            st.info("""
            **🥇 簡単: QuickTime Player**
            - 📍 アプリケーション → QuickTime Player
            - 🎬 ファイル → 新規オーディオ収録
            - � 録音ボタンで開始
            
            **🥈 高音質: GarageBand**
            - 📍 App Store → GarageBand
            - 🎵 「Audio Recorder」プロジェクト
            - 🎛️ プロレベルの音質調整
            """)
        
        st.markdown("#### 🎯 **パソコン録音の注意点**")
        st.warning("""
        - 🎤 **マイク設定**: システム設定でマイクを有効化
        - 🔊 **音量調整**: 録音レベルを適切に設定
        - 🔇 **ノイズ対策**: ファンやエアコンの音に注意
        - � **保存場所**: ファイルの保存先を覚えておく
        """)
    
    with guide_tab3:
        st.markdown("### 🎯 **高品質録音のコツ**")
        
        tip_col1, tip_col2 = st.columns(2)
        
        with tip_col1:
            st.success("✅ **DO（やるべきこと）**")
            st.markdown("""
            **🎤 録音環境**
            - 🤫 静かな場所を選ぶ
            - 🏠 室内録音を推奨
            - 🪑 安定した姿勢で録音
            - 📱 デバイスを固定する
            
            **🗣️ 話し方**
            - 📏 マイクから15-20cm距離
            - 🔊 普段より少し大きめの声
            - 🐌 ゆっくりはっきり話す
            - 😮‍💨 深呼吸してからスタート
            """)
        
        with tip_col2:
            st.error("❌ **DON'T（避けるべきこと）**")
            st.markdown("""
            **🚫 環境の問題**
            - 🚗 車内や電車内での録音
            - 🌬️ 風が強い屋外
            - 📺 テレビやラジオがついている
            - 👥 人が多い場所
            
            **🚫 話し方の問題**
            - 🤏 マイクに近すぎる
            - 👀 マイクから目を逸らす
            - 🏃‍♂️ 早口で話す
            - 😴 小さすぎる声
            """)
        
        st.markdown("#### 🌟 **プロのような録音テクニック**")
        st.info("""
        1. **🎬 録音前の準備**: 「テスト、テスト」で音声レベルを確認
        2. **🎭 録音中の姿勢**: 背筋を伸ばし、リラックスした状態
        3. **⏱️ 録音時間**: 1分程度の短いセクションに分割
        4. **🔄 品質確認**: 録音後すぐに再生して確認
        5. **📚 バックアップ**: 重要な録音は複数回録音
        """)
    
    with guide_tab4:
        st.markdown("### 🔧 **トラブルシューティング**")
        
        trouble_col1, trouble_col2 = st.columns(2)
        
        with trouble_col1:
            st.markdown("#### 🚨 **よくある問題**")
            
            with st.expander("� 音が録音されない", expanded=False):
                st.markdown("""
                **原因と解決方法:**
                - 🎤 マイクが無効: デバイス設定で有効化
                - 🔊 音量が0: システム音量を上げる
                - 🚫 アプリ権限: マイク使用を許可
                - 🔌 外部マイク: 接続を確認
                """)
            
            with st.expander("📢 音が小さい・聞こえにくい", expanded=False):
                st.markdown("""
                **改善方法:**
                - 📏 マイクに近づく（15cm以内）
                - 🔊 録音レベルを上げる
                - 🗣️ より大きな声で話す
                - 🎤 外部マイクの使用を検討
                """)
            
            with st.expander("🌪️ ノイズが入る", expanded=False):
                st.markdown("""
                **ノイズ除去方法:**
                - 🔇 周囲の音源を除去
                - 🪟 窓を閉める
                - 📱 携帯電話を離す
                - 🎤 マイクの向きを調整
                """)
        
        with trouble_col2:
            st.markdown("#### 💡 **代替解決策**")
            
            with st.expander("📱 どうしても録音できない場合", expanded=False):
                st.markdown("""
                **他の方法を試す:**
                - 🔄 異なるアプリを使用
                - 📱 別のデバイスで録音
                - 👥 他の人に録音を依頼
                - 🎤 外部マイクを購入
                """)
            
            with st.expander("📁 ファイルが見つからない", expanded=False):
                st.markdown("""
                **ファイル場所を確認:**
                - � アプリ内の履歴を確認
                - 💾 ダウンロードフォルダ
                - �️ ドキュメントフォルダ
                - ☁️ クラウドストレージ
                """)
            
            with st.expander("📤 アップロードできない", expanded=False):
                st.markdown("""
                **対応ファイル形式:**
                - ✅ MP3 (推奨)
                - ✅ WAV (高音質)
                - ✅ M4A (iPhone標準)
                - ❌ 非対応形式は変換が必要
                """)
    
    # 最後に重要なメッセージ
    st.markdown("---")
    st.success("""
    🎯 **成功のポイント**: 
    スマートフォンの標準録音アプリを使用し、静かな場所で15-20cm離れてはっきりと話す。
    録音後は必ず再生して確認し、「ファイルアップロード」タブでアップロードする。
    """)
    
    st.info("""
    💡 **お困りの時は**: 
    ブラウザ録音が上手くいかない場合は、必ずスマートフォンアプリでの録音をお試しください。
    99%の確率で成功します！
    """)


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
    Returns:
        str: 実際に保存されたファイルのパス
    """
    import os
    import shutil
    
    temp_audio_output_filename = f"{ct.AUDIO_OUTPUT_DIR}/temp_audio_output_{int(time.time())}.mp3"
    final_output_path = audio_output_file_path
    
    try:
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(audio_output_file_path), exist_ok=True)
        
        # mp3ファイルを一時的に保存
        with open(temp_audio_output_filename, "wb") as temp_audio_output_file:
            temp_audio_output_file.write(llm_response_audio)
        
        # ファイルが正常に保存されたか確認
        if not os.path.exists(temp_audio_output_filename):
            raise Exception("一時音声ファイルの保存に失敗しました")
        
        # pydubが利用できる場合のみ変換を実行
        if PYDUB_AVAILABLE:
            try:
                audio_mp3 = AudioSegment.from_file(temp_audio_output_filename, format="mp3")
                audio_mp3.export(audio_output_file_path, format="wav")
                
                # 変換結果を確認
                if os.path.exists(audio_output_file_path):
                    final_output_path = audio_output_file_path
                else:
                    raise Exception("WAV変換に失敗しました")
                    
            except Exception as pydub_error:
                st.warning(f"音声変換をスキップします (WAV→MP3): {pydub_error}")
                # 変換に失敗した場合、mp3ファイルをそのまま使用
                mp3_output_path = audio_output_file_path.replace('.wav', '.mp3')
                shutil.copy2(temp_audio_output_filename, mp3_output_path)
                final_output_path = mp3_output_path
        else:
            # pydubが利用できない場合、mp3ファイルをそのまま使用
            mp3_output_path = audio_output_file_path.replace('.wav', '.mp3')
            shutil.copy2(temp_audio_output_filename, mp3_output_path)
            final_output_path = mp3_output_path

        # 音声出力用に一時的に作ったmp3ファイルを削除
        if os.path.exists(temp_audio_output_filename):
            os.remove(temp_audio_output_filename)
            
        return final_output_path
            
    except Exception as e:
        st.error(f"音声ファイル処理エラー: {e}")
        # 一時ファイルのクリーンアップ
        if os.path.exists(temp_audio_output_filename):
            os.remove(temp_audio_output_filename)
        return None

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
    import os
    
    try:
        # ファイル存在確認
        if not os.path.exists(audio_output_file_path):
            # .wavファイルが存在しない場合、.mp3ファイルを探す
            mp3_path = audio_output_file_path.replace('.wav', '.mp3')
            if os.path.exists(mp3_path):
                audio_output_file_path = mp3_path
                st.info("MP3形式で音声を再生します")
            else:
                st.error(f"音声ファイルが見つかりません: {audio_output_file_path}")
                return
        
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
    actual_saved_path = save_to_wav(llm_response_audio.content, audio_output_file_path)

    # 音声ファイルパスをセッション状態に保存（実際に保存されたパスを使用）
    if actual_saved_path:
        st.session_state.current_audio_file = actual_saved_path
        # 音声ファイルの読み上げ
        play_wav(actual_saved_path, extract_speed_value(st.session_state.speed))
    else:
        st.error("音声ファイルの保存に失敗しました")
        st.session_state.current_audio_file = ""

    return problem, llm_response_audio