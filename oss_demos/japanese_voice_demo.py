#!/usr/bin/env python3
"""
日本語完全対応音声会話デモ
- Whisper.cpp: ローカル日本語音声認識（高精度）
- gTTS: 日本語音声合成（無料）
- OpenAI GPT-3.5: 日本語AI会話
"""

import asyncio
import signal
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))

from whisper_cpp_transcriber import WhisperCPPTranscriber, VocodeWhisperCPPTranscriberConfig
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


def check_whisper_model():
    """Whisperモデルの存在確認とダウンロード指示"""
    model_paths = [
        "/Users/yuki/vocode-core/models/ggml-base.bin",
        "models/ggml-base.bin",
    ]
    
    for path in model_paths:
        if Path(path).exists():
            return path
    
    print("❌ Whisperモデルが見つかりません")
    print("\n以下のコマンドでダウンロードしてください：")
    print("mkdir -p models")
    print("curl -L -o models/ggml-base.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin")
    print("\nまたは日本語特化モデル：")
    print("curl -L -o models/ggml-medium.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin")
    return None


async def main():
    """メイン関数"""
    
    # Whisperモデルの確認
    model_path = check_whisper_model()
    if not model_path:
        return
    
    # OpenAI APIキーの確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OpenAI APIキーが設定されていません")
        print("echo 'OPENAI_API_KEY=your_key' > .env")
        return
    
    print("=" * 60)
    print("🇯🇵 日本語完全対応音声会話システム")
    print("=" * 60)
    print()
    print("🎤 音声認識: Whisper.cpp (ローカル、高精度)")
    print("🔊 音声合成: gTTS (日本語対応)")
    print("🤖 AI: OpenAI GPT-3.5 (日本語会話)")
    print()
    print("特徴:")
    print("- 完全ローカル音声認識（インターネット不要）")
    print("- 高精度な日本語認識")
    print("- 自然な日本語会話")
    print()
    
    # マイクとスピーカーの設定
    (
        microphone_input,
        speaker_output,
    ) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=True,
    )
    
    # 日本語対応エージェント
    agent = ChatGPTAgent(
        ChatGPTAgentConfig(
            openai_api_key=openai_api_key,
            initial_message=BaseMessage(text="こんにちは！私は日本語で会話できるAIアシスタントです。何でもお聞きください。"),
            prompt_preamble="""あなたは親切で丁寧な日本語AIアシスタントです。
            ユーザーと自然な会話をしてください。
            回答は簡潔にし、会話的なトーンを保ってください。
            相手の話をよく聞き、適切に応答してください。""",
            model_name="gpt-3.5-turbo",
            generate_responses=True,
        )
    )
    
    # 会話の設定
    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=WhisperCPPTranscriber(
            VocodeWhisperCPPTranscriberConfig.from_input_device(
                microphone_input,
                language="ja",  # 日本語
                model_path=model_path,
                chunk_duration_seconds=2.0,  # 2秒ごとに処理
                silence_threshold=500,
                min_chunk_duration=0.5,
            ),
        ),
        agent=agent,
        synthesizer=GTTSSynthesizer(
            GTTSSynthesizerConfig.from_output_device(
                speaker_output,
                lang="ja",  # 日本語
                tld="com",
                slow=False,  # 通常速度
            ),
        ),
    )
    
    await conversation.start()
    print("🎙️  会話を開始しました！日本語で話しかけてください。")
    print("💡 ヒント: はっきりと話してください。少し間を置くと認識されます。")
    print("🛑 終了: Ctrl+C")
    print("-" * 60)
    
    # Ctrl+Cで終了
    signal.signal(signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate()))
    
    # 音声入力を処理
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


def test_system():
    """システムテスト"""
    print("🔧 システムチェック中...")
    
    # Whisper.cppの確認
    whisper_path = "/opt/homebrew/bin/whisper-cpp"
    if Path(whisper_path).exists():
        print("✅ Whisper.cpp: インストール済み")
    else:
        print("❌ Whisper.cpp: 未インストール")
        print("   brew install whisper-cpp")
        return False
    
    # モデルの確認
    if check_whisper_model():
        print("✅ Whisperモデル: 準備完了")
    else:
        return False
    
    # マイクの確認
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print("✅ オーディオデバイス: 利用可能")
    except:
        print("❌ オーディオデバイス: エラー")
        return False
    
    return True


if __name__ == "__main__":
    print("\n🇯🇵 日本語音声会話システムを起動します...\n")
    
    if test_system():
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n\n👋 ご利用ありがとうございました！")
    else:
        print("\nシステム要件を満たしていません。上記の指示に従ってください。")