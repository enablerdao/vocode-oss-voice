#!/usr/bin/env python3
"""
完全OSSターンベース会話デモ
- Google Speech Recognition (無料)
- gTTS (無料)
- OpenAI GPT-3.5
"""

import os
from dotenv import load_dotenv
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import tempfile

from vocode.turn_based.agent.chat_gpt_agent import ChatGPTAgent
from vocode.logging import configure_pretty_logging

configure_pretty_logging()
load_dotenv()


def record_audio(recognizer, microphone, timeout=5):
    """マイクから音声を録音し、テキストに変換"""
    print("🎤 聞いています... (話し終わったら少し待ってください)")
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            print("🔄 音声を認識中...")
            
            try:
                text = recognizer.recognize_google(audio, language="en-US")
                print(f"📝 認識結果: {text}")
                return text
            except sr.UnknownValueError:
                print("❌ 音声を認識できませんでした")
                return None
            except sr.RequestError as e:
                print(f"❌ Google Speech Recognition エラー: {e}")
                return None
                
        except sr.WaitTimeoutError:
            print("⏱️  タイムアウト: 音声が検出されませんでした")
            return None


def speak_text(text, lang="en"):
    """テキストを音声に変換して再生"""
    print(f"🔊 AI: {text}")
    
    # gTTSで音声合成
    tts = gTTS(text=text, lang=lang, slow=False)
    
    # 一時ファイルに保存
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
        tts.save(tmp_file.name)
        
        # pydubで再生
        audio = AudioSegment.from_mp3(tmp_file.name)
        play(audio)
        
        # 一時ファイルを削除
        os.unlink(tmp_file.name)


def main():
    """メイン関数"""
    print("=" * 60)
    print("OSS ターンベース音声会話デモ")
    print("=" * 60)
    print()
    print("🎤 音声認識: Google Speech Recognition (無料)")
    print("🔊 音声合成: gTTS (無料)")
    print("🤖 AI: OpenAI GPT-3.5")
    print()
    
    # OpenAI APIキーの確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        print("Echo モードで起動します（話した内容を繰り返します）")
        use_ai = False
    else:
        use_ai = True
        agent = ChatGPTAgent(
            system_prompt="You are a helpful AI assistant. Keep responses brief and conversational.",
            initial_message="Hello! I'm ready to chat.",
            api_key=openai_api_key,
        )
    
    # 音声認識の初期化
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # 初期メッセージ
    initial_message = "Hello! I'm ready to chat. Say 'goodbye' to exit."
    speak_text(initial_message)
    
    print("\n使い方:")
    print("1. Enterキーを押して録音開始")
    print("2. 話し終わったら少し待つ")
    print("3. 'goodbye' と言うと終了")
    print("-" * 60)
    
    while True:
        # Enterキーを待つ
        input("\n⏎ Enterキーを押して話してください...")
        
        # 音声を録音
        user_text = record_audio(recognizer, microphone)
        
        if user_text:
            # 終了チェック
            if "goodbye" in user_text.lower() or "bye" in user_text.lower():
                speak_text("Goodbye! It was nice talking with you.")
                break
            
            # AIの応答を生成
            if use_ai:
                response = agent.respond(user_text)
            else:
                # Echo モード
                response = f"You said: {user_text}"
            
            # 応答を音声で再生
            speak_text(response)
        else:
            print("もう一度お試しください")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 終了しました")