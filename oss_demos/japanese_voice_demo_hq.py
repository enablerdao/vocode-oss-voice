#!/usr/bin/env python3
"""
高品質日本語音声会話デモ
- Google Speech Recognition: 日本語音声認識
- Edge TTS: 高品質日本語音声合成（Microsoft）
- OpenAI GPT-3.5: 日本語AI会話
"""

import asyncio
import signal
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from edge_tts_synthesizer import EdgeTTSSynthesizer, EdgeTTSSynthesizerConfig
from high_performance_oss_demo import OptimizedGoogleSRTranscriberConfig, OptimizedGoogleSRTranscriber
from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.logging import configure_pretty_logging
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.streaming_conversation import StreamingConversation

configure_pretty_logging()
load_dotenv()


async def list_voices():
    """利用可能な音声を表示"""
    await EdgeTTSSynthesizer.get_voices_list()


async def main():
    """メイン関数"""
    
    # OpenAI APIキーの確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OpenAI APIキーが設定されていません")
        return
    
    print("=" * 60)
    print("🎌 高品質日本語音声会話システム")
    print("=" * 60)
    print()
    print("🎤 音声認識: Google Speech Recognition")
    print("🔊 音声合成: Edge TTS (Microsoft Neural Voices)")
    print("🤖 AI: OpenAI GPT-3.5")
    print()
    print("利用可能な日本語音声:")
    print("- ja-JP-NanamiNeural (女性・標準)")
    print("- ja-JP-AoiNeural (女性・明るい)")
    print("- ja-JP-KeitaNeural (男性・標準)")
    print("- ja-JP-DaichiNeural (男性・明るい)")
    print()
    
    # 音声の選択
    voice_choice = input("音声を選択 (1-4, デフォルト: 1): ").strip() or "1"
    voices = {
        "1": "ja-JP-NanamiNeural",
        "2": "ja-JP-AoiNeural", 
        "3": "ja-JP-KeitaNeural",
        "4": "ja-JP-DaichiNeural"
    }
    selected_voice = voices.get(voice_choice, "ja-JP-NanamiNeural")
    
    print(f"\n選択された音声: {selected_voice}")
    print("-" * 60)
    
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
            initial_message=BaseMessage(text="こんにちは！私は高品質な音声でお話しできるAIアシスタントです。何かお聞きになりたいことはありますか？"),
            prompt_preamble="""あなたは親切で明るい日本語AIアシスタントです。
            ユーザーと楽しく会話してください。
            回答は自然で会話的なトーンを保ち、適度に感情を込めてください。
            相手の話をよく聞き、共感的に応答してください。
            時には「そうですね」「なるほど」などの相槌も使ってください。""",
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
                language="ja-JP",
                energy_threshold=300,
                pause_threshold=0.8,
                chunk_duration_seconds=0.5,
            ),
        ),
        agent=agent,
        synthesizer=EdgeTTSSynthesizer(
            EdgeTTSSynthesizerConfig.from_output_device(
                speaker_output,
                voice=selected_voice,
                rate="+5%",  # 少し速めで自然に
                volume="+0%",
                pitch="+0Hz",
            ),
        ),
    )
    
    await conversation.start()
    print("\n🎙️  高品質音声会話を開始しました！")
    print("💡 日本語で自然に話しかけてください")
    print("🛑 終了: Ctrl+C")
    print("-" * 60)
    
    # Ctrl+Cで終了
    signal.signal(signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate()))
    
    # 音声入力を処理
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


if __name__ == "__main__":
    print("\n🎌 高品質日本語音声会話システム（Edge TTS版）\n")
    
    # 音声リストを表示するかどうか
    if len(sys.argv) > 1 and sys.argv[1] == "--list-voices":
        asyncio.run(list_voices())
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n\n👋 ご利用ありがとうございました！")
        except EOFError:
            # 非対話モードの場合はデフォルト設定で実行
            print("非対話モードで実行します（デフォルト音声使用）")
            # asyncio.run(main_no_input())