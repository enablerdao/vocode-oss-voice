#!/usr/bin/env python3
"""
完全にOSS/無料サービスのみを使用したVocode音声会話デモ
- Google Speech Recognition: 無料の音声認識（APIキー不要）
- gTTS: 無料の音声合成（APIキー不要）
- OpenAI: LLMエージェント（APIキー必要）
"""

import asyncio
import signal
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# カスタムトランスクライバーをインポートパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from google_sr_transcriber import GoogleSRTranscriber, GoogleSRTranscriberConfig
from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.logging import configure_pretty_logging
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.agent.echo_agent import EchoAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig, EchoAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import GTTSSynthesizerConfig
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.synthesizer.gtts_synthesizer import GTTSSynthesizer

configure_pretty_logging()
load_dotenv()


async def main():
    """完全OSSベースの音声会話を実行"""
    
    # OpenAI APIキーの確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    use_openai = bool(openai_api_key)
    
    print("=" * 60)
    print("完全OSSベースのVocode音声会話デモ")
    print("=" * 60)
    print()
    print("🎤 音声認識: Google Speech Recognition (無料、APIキー不要)")
    print("🔊 音声合成: gTTS (Google Text-to-Speech、無料)")
    print(f"🤖 AI: {'OpenAI GPT-3.5' if use_openai else 'Echo Agent (APIキー不要)'}")
    print()
    print("使い方:")
    print("1. 話しかけてください")
    print("2. AIが応答します")
    print("3. 終了するには Ctrl+C を押してください")
    print()
    
    # マイクとスピーカーの設定
    (
        microphone_input,
        speaker_output,
    ) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=True,
    )
    
    # エージェントの選択
    if use_openai:
        agent = ChatGPTAgent(
            ChatGPTAgentConfig(
                openai_api_key=openai_api_key,
                initial_message=BaseMessage(text="Hello! I'm your AI assistant. How can I help you today?"),
                prompt_preamble="You are a helpful AI assistant. Keep responses brief and conversational.",
                model_name="gpt-3.5-turbo",
            )
        )
    else:
        agent = EchoAgent(
            EchoAgentConfig(
                initial_message=BaseMessage(text="Hello! I'm an echo agent. I'll repeat what you say!"),
            )
        )
    
    # 会話の設定
    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=GoogleSRTranscriber(
            GoogleSRTranscriberConfig.from_input_device(
                microphone_input,
                language="en-US",  # 英語認識（"ja-JP"で日本語も可能）
                energy_threshold=300,
                pause_threshold=0.8,
            ),
        ),
        agent=agent,
        synthesizer=GTTSSynthesizer(
            GTTSSynthesizerConfig.from_output_device(
                speaker_output,
                lang="en",  # 英語合成（"ja"で日本語も可能）
                tld="com",
            ),
        ),
    )
    
    await conversation.start()
    print("🎙️  会話を開始しました！話しかけてください...")
    print("    (音声認識には少し時間がかかる場合があります)")
    print()
    
    # Ctrl+Cで終了
    signal.signal(signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate()))
    
    # 音声入力を処理
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


def test_dependencies():
    """依存関係のテスト"""
    print("依存関係をチェック中...")
    
    try:
        import speech_recognition as sr
        print("✅ speech_recognition: インストール済み")
        
        # マイクのテスト
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("✅ マイク: 利用可能")
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
        
    try:
        from gtts import gTTS
        print("✅ gTTS: インストール済み")
    except:
        print("❌ gTTS: インストールされていません")
        return False
        
    return True


if __name__ == "__main__":
    if test_dependencies():
        print()
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n\n👋 終了しました。")
    else:
        print("\n依存関係に問題があります。以下を実行してください:")
        print("poetry add SpeechRecognition gtts")