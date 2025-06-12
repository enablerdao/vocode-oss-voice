#!/usr/bin/env python3
"""
日本語音声会話デモ（シンプル版）
Google Speech Recognition + gTTS使用
"""

import asyncio
import signal
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

sys.path.append(str(Path(__file__).parent.parent))
from high_performance_oss_demo import OptimizedGoogleSRTranscriberConfig, OptimizedGoogleSRTranscriber
from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.logging import configure_pretty_logging
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import GTTSSynthesizerConfig
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.synthesizer.gtts_synthesizer import GTTSSynthesizer

configure_pretty_logging()
load_dotenv()


async def main():
    """メイン関数"""
    
    # OpenAI APIキーの確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OpenAI APIキーが設定されていません")
        return
    
    print("=" * 60)
    print("🇯🇵 日本語音声会話デモ（シンプル版）")
    print("=" * 60)
    print()
    print("🎤 音声認識: Google Speech Recognition (日本語)")
    print("🔊 音声合成: gTTS (日本語)")
    print("🤖 AI: OpenAI GPT-3.5 (日本語)")
    print()
    
    # マイクとスピーカーの設定
    (
        microphone_input,
        speaker_output,
    ) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=True,
    )
    
    # 日本語AI設定
    agent = ChatGPTAgent(
        ChatGPTAgentConfig(
            openai_api_key=openai_api_key,
            initial_message=BaseMessage(text="こんにちは！何かお手伝いできることはありますか？"),
            prompt_preamble="""あなたは親切な日本語AIアシスタントです。
            簡潔で自然な日本語で応答してください。
            相手の質問に的確に答えてください。""",
            model_name="gpt-3.5-turbo",
            generate_responses=True,
        )
    )
    
    # 会話の設定
    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=OptimizedGoogleSRTranscriber(
            OptimizedGoogleSRTranscriberConfig.from_input_device(
                microphone_input,
                language="ja-JP",  # 日本語
                energy_threshold=300,
                pause_threshold=0.8,
                chunk_duration_seconds=0.5,
            ),
        ),
        agent=agent,
        synthesizer=GTTSSynthesizer(
            GTTSSynthesizerConfig.from_output_device(
                speaker_output,
                lang="ja",  # 日本語
                tld="com",
            ),
        ),
    )
    
    await conversation.start()
    print("🎙️  会話を開始しました！")
    print("💡 日本語で話しかけてください")
    print("🛑 終了: Ctrl+C")
    print("-" * 60)
    
    # Ctrl+Cで終了
    signal.signal(signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate()))
    
    # 音声入力を処理
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


if __name__ == "__main__":
    print("\n🇯🇵 日本語音声会話システム（シンプル版）\n")
    
    try:
        import speech_recognition as sr
        print("✅ 音声認識: 準備完了")
    except:
        print("❌ speech_recognitionがインストールされていません")
        exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 ありがとうございました！")