import streamlit as st
import os
import time
from pathlib import Path
import wave
import numpy as np

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
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
import constants as ct

def record_audio(audio_input_file_path):
    """
    音声入力を受け取って音声ファイルを作成
    """
    
    # Streamlitのfile_uploaderを使用した音声アップロード
    uploaded_file = st.file_uploader(
        "音声ファイルをアップロードしてください",
        type=['wav', 'mp3', 'm4a', 'ogg'],
        help="録音した音声ファイルを選択してアップロードしてください"
    )
    
    if uploaded_file is not None:
        # アップロードされたファイルを保存
        with open(audio_input_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("音声ファイルがアップロードされました！")
    else:
        st.info("音声ファイルをアップロードしてください")
        st.stop()

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
    
    # 一定時間後にファイルクリーンアップ（バックグラウンドで実行される想定）

def create_chain(system_template):
    """
    LLMによる回答生成用のChain作成
    """

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_template),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}")
    ])
    chain = ConversationChain(
        llm=st.session_state.llm,
        memory=st.session_state.memory,
        prompt=prompt
    )

    return chain

def create_problem_and_play_audio():
    """
    問題生成と音声ファイルの再生
    Args:
        chain: 問題文生成用のChain
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
        openai_obj: OpenAIのオブジェクト
    """

    # 問題文を生成するChainを実行し、問題文を取得
    problem = st.session_state.chain_create_problem.predict(input="")

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
    play_wav(audio_output_file_path, st.session_state.speed)

    return problem, llm_response_audio

def create_evaluation():
    """
    ユーザー入力値の評価生成
    """

    llm_response_evaluation = st.session_state.chain_evaluation.predict(input="")

    return llm_response_evaluation