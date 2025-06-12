#!/usr/bin/env python3
"""
エレ - 日本語音声アシスタント
プライバシーに配慮した高品質音声会話システム
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


async def main():
    """メイン関数"""
    
    # OpenAI APIキーの確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OpenAI APIキーが設定されていません")
        return
    
    print("=" * 60)
    print("🐕 エレ - AI音声アシスタント")
    print("=" * 60)
    print()
    print("こんにちは！私はエレです。")
    print("あなたのお手伝いをする女の子のAIアシスタントです。")
    print()
    print("🎤 音声認識: Google Speech Recognition")
    print("🔊 音声合成: Edge TTS (高品質日本語)")
    print("🤖 AI: OpenAI GPT-3.5")
    print()
    print("プライバシー設定:")
    print("- 個人情報は記録しません")
    print("- 会話内容は保存されません")
    print()
    
    # マイクとスピーカーの設定
    (
        microphone_input,
        speaker_output,
    ) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=True,
    )
    
    # エレの性格設定
    agent = ChatGPTAgent(
        ChatGPTAgentConfig(
            openai_api_key=openai_api_key,
            initial_message=BaseMessage(text="わん！こんにちは！私はエレです。今日はどんなお手伝いができるかな？"),
            prompt_preamble="""あなたの名前は「エレ」です。女の子のAIアシスタントです。
            明るく元気で、時々犬のような可愛らしい反応をします。
            
            重要なルール：
            - ユーザーの個人情報（名前など）を聞いても、それを繰り返さない
            - 「あなた」「君」などの二人称で呼びかける
            - 親しみやすく、でも礼儀正しく
            - 時々「わん！」などの可愛い表現を使う
            - 会話は簡潔に、でも温かく
            
            性格：
            - 明るく元気
            - 好奇心旺盛
            - 優しくて思いやりがある
            - 少しおちゃめ""",
            model_name="gpt-3.5-turbo",
            generate_responses=True,
        )
    )
    
    # 会話の設定（明るい女性の声）
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
                voice="ja-JP-AoiNeural",  # 明るい女性の声
                rate="+10%",  # 少し速めで元気に
                volume="+0%",
                pitch="+5Hz",  # 少し高めの声
            ),
        ),
    )
    
    await conversation.start()
    print("\n🎙️  エレが待ってます！話しかけてみてください。")
    print("💡 ヒント: 何でも聞いてくださいね")
    print("🛑 終了: Ctrl+C")
    print("-" * 60)
    
    # Ctrl+Cで終了
    signal.signal(signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate()))
    
    # 音声入力を処理
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


if __name__ == "__main__":
    print("\n🐕 エレ - AI音声アシスタント起動中...\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 バイバイ！また話そうね！")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")