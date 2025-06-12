#!/usr/bin/env python3
"""
完全にOSSのみを使用したVocode会話デモ
- Whisper.cpp: ローカル音声認識
- gTTS: 無料の音声合成
- OpenAI: LLMエージェント
"""

import asyncio
import signal
import os
from pathlib import Path
from dotenv import load_dotenv

from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.logging import configure_pretty_logging
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import GTTSSynthesizerConfig
from vocode.streaming.models.transcriber import WhisperCPPTranscriberConfig
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.synthesizer.gtts_synthesizer import GTTSSynthesizer
from vocode.streaming.transcriber.whisper_cpp_transcriber import WhisperCPPTranscriber

configure_pretty_logging()
load_dotenv()


async def main():
    """OSSのみを使用した音声会話を実行"""
    
    # OpenAI APIキーの確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("エラー: OPENAI_API_KEY が .env ファイルに見つかりません")
        return
    
    # Whisperモデルファイルの確認
    model_path = Path("/Users/yuki/vocode-core/models/ggml-base.bin")
    if not model_path.exists():
        print(f"エラー: Whisperモデルファイルが見つかりません: {model_path}")
        print("モデルをダウンロードしてください:")
        print("curl -L -o models/ggml-base.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin")
        return
    
    # Whisper.cppライブラリの場所を探す
    possible_lib_paths = [
        "/opt/homebrew/lib/libwhisper.dylib",
        "/usr/local/lib/libwhisper.dylib",
        "/opt/homebrew/Cellar/whisper-cpp/1.7.5/lib/libwhisper.dylib",
    ]
    
    libwhisper_path = None
    for path in possible_lib_paths:
        if Path(path).exists():
            libwhisper_path = path
            break
    
    if not libwhisper_path:
        print("エラー: libwhisper.dylib が見つかりません")
        print("whisper-cpp がインストールされているか確認してください: brew install whisper-cpp")
        return
    
    print("OSSのみを使用したVocode音声会話デモを開始します...")
    print("- 音声認識: Whisper.cpp (ローカル)")
    print("- 音声合成: gTTS (Google Text-to-Speech、無料)")
    print("- AI: OpenAI GPT-3.5")
    print()
    
    # マイクとスピーカーの設定
    (
        microphone_input,
        speaker_output,
    ) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=True,
    )
    
    # 会話の設定
    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=WhisperCPPTranscriber(
            WhisperCPPTranscriberConfig.from_input_device(
                microphone_input,
                libname=libwhisper_path,
                fname_model=str(model_path),
                buffer_size_seconds=1.0,
            ),
        ),
        agent=ChatGPTAgent(
            ChatGPTAgentConfig(
                openai_api_key=openai_api_key,
                initial_message=BaseMessage(text="こんにちは！私はOSSを使用したAIアシスタントです。何でも聞いてください。"),
                prompt_preamble="あなたは親切で役立つAIアシスタントです。簡潔に回答してください。",
                model_name="gpt-3.5-turbo",
            )
        ),
        synthesizer=GTTSSynthesizer(
            GTTSSynthesizerConfig.from_output_device(
                speaker_output,
                lang="ja",  # 日本語
                tld="com",
            ),
        ),
    )
    
    await conversation.start()
    print("会話を開始しました！話しかけてください。")
    print("終了するには Ctrl+C を押してください。")
    
    # Ctrl+Cで終了
    signal.signal(signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate()))
    
    # 音声入力を処理
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


if __name__ == "__main__":
    asyncio.run(main())