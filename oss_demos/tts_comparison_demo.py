#!/usr/bin/env python3
"""
日本語TTS比較デモ
gTTS vs Edge TTS の音声品質を比較
"""

import asyncio
import edge_tts
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import tempfile
import os


async def play_gtts(text: str):
    """gTTSで音声再生"""
    print("\n🔊 gTTS (Google Text-to-Speech):")
    print("   特徴: シンプル、無料、機械的")
    
    tts = gTTS(text=text, lang='ja', slow=False)
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
        tts.save(tmp_file.name)
        audio = AudioSegment.from_mp3(tmp_file.name)
        play(audio)
        os.unlink(tmp_file.name)


async def play_edge_tts(text: str, voice: str = "ja-JP-NanamiNeural"):
    """Edge TTSで音声再生"""
    print(f"\n🎤 Edge TTS ({voice}):")
    print("   特徴: 自然、感情豊か、高品質")
    
    communicate = edge_tts.Communicate(text, voice, rate="+5%")
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
        await communicate.save(tmp_file.name)
        audio = AudioSegment.from_mp3(tmp_file.name)
        play(audio)
        os.unlink(tmp_file.name)


async def main():
    """メイン関数"""
    print("=" * 60)
    print("🎌 日本語TTS音声品質比較デモ")
    print("=" * 60)
    
    # テストテキスト
    test_texts = [
        "こんにちは！私はAIアシスタントです。",
        "今日はとても良い天気ですね。散歩に行きませんか？",
        "申し訳ございません。その質問にはお答えできません。",
        "わぁ！それは素晴らしいアイデアですね！ぜひやってみましょう！",
        "ええと、そうですね...少し考える時間をいただけますか？",
    ]
    
    print("\nテストする文章を選択してください:")
    for i, text in enumerate(test_texts, 1):
        print(f"{i}. {text}")
    print("0. カスタムテキストを入力")
    
    choice = input("\n選択 (0-5): ").strip()
    
    if choice == "0":
        text = input("テキストを入力: ")
    elif choice in ["1", "2", "3", "4", "5"]:
        text = test_texts[int(choice) - 1]
    else:
        text = test_texts[0]
    
    print(f"\n選択されたテキスト: {text}")
    print("-" * 60)
    
    # gTTSで再生
    await play_gtts(text)
    
    input("\nEnterキーを押してEdge TTSを聞く...")
    
    # Edge TTSで再生（複数の音声）
    voices = [
        ("ja-JP-NanamiNeural", "女性・標準"),
        ("ja-JP-AoiNeural", "女性・明るい"),
        ("ja-JP-KeitaNeural", "男性・標準"),
    ]
    
    for voice, description in voices:
        print(f"\n{description}の音声を再生します...")
        await play_edge_tts(text, voice)
        
        if voice != voices[-1][0]:
            input("\nEnterキーで次の音声...")
    
    print("\n" + "=" * 60)
    print("比較結果:")
    print("- gTTS: 機械的だが理解しやすい")
    print("- Edge TTS: 自然で感情豊か、人間に近い")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🔊 日本語音声合成比較ツール\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n終了しました")
    except Exception as e:
        print(f"エラー: {e}")
        print("\n必要なパッケージ:")
        print("poetry add gtts edge-tts pydub")