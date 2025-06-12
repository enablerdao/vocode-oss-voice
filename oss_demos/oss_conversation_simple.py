#!/usr/bin/env python3
"""
OSSのみを使用したシンプルなVocode会話デモ
- gTTS: 無料の音声合成
- OpenAI: LLMエージェント
- Echo Agent: APIキー不要のシンプルなエージェント（オプション）
"""

import asyncio
import signal
import os
from dotenv import load_dotenv

from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.logging import configure_pretty_logging
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.agent.echo_agent import EchoAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig, EchoAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import GTTSSynthesizerConfig, StreamElementsSynthesizerConfig
from vocode.streaming.models.transcriber import DeepgramTranscriberConfig, PunctuationEndpointingConfig
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.synthesizer.gtts_synthesizer import GTTSSynthesizer
from vocode.streaming.synthesizer.stream_elements_synthesizer import StreamElementsSynthesizer
from vocode.streaming.transcriber.deepgram_transcriber import DeepgramTranscriber

configure_pretty_logging()
load_dotenv()


async def main():
    """OSSを使用した音声会話を実行"""
    
    # OpenAI APIキーの確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    use_openai = bool(openai_api_key)
    
    print("=" * 60)
    print("OSSベースのVocode音声会話デモ")
    print("=" * 60)
    print()
    print("音声合成: gTTS (Google Text-to-Speech、無料)")
    print(f"AI: {'OpenAI GPT-3.5' if use_openai else 'Echo Agent (APIキー不要)'}")
    print()
    print("注意: 音声認識にはDeepgram APIキーが必要です。")
    print("      現在はダミーキーを使用しているため、音声認識は動作しません。")
    print("      デモとして音声合成のみ動作します。")
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
                initial_message=BaseMessage(text="Hello! I'm an AI assistant using free text to speech. How can I help you today?"),
                prompt_preamble="You are a helpful AI assistant. Keep responses brief and friendly.",
                model_name="gpt-3.5-turbo",
            )
        )
    else:
        agent = EchoAgent(
            EchoAgentConfig(
                initial_message=BaseMessage(text="Hello! I'm an echo agent. I'll repeat everything you say!"),
            )
        )
    
    # 会話の設定
    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=DeepgramTranscriber(
            DeepgramTranscriberConfig.from_input_device(
                microphone_input,
                endpointing_config=PunctuationEndpointingConfig(),
                api_key="dummy_key",  # 実際の音声認識にはAPIキーが必要
            ),
        ),
        agent=agent,
        synthesizer=GTTSSynthesizer(
            GTTSSynthesizerConfig.from_output_device(
                speaker_output,
                lang="en",  # 英語
                tld="com",
            ),
        ),
    )
    
    await conversation.start()
    print("会話を開始しました！")
    print("（音声認識は動作しないため、初期メッセージのみ再生されます）")
    print("終了するには Ctrl+C を押してください。")
    
    # Ctrl+Cで終了
    signal.signal(signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate()))
    
    # 音声入力を処理
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n終了しました。")