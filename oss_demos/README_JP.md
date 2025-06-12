# 日本語音声会話システム

## 🎯 デモ一覧

### 1. **japanese_voice_demo.py** - Whisper.cpp完全統合版（推奨）
```bash
poetry run python japanese_voice_demo.py
```

**特徴：**
- ✅ **Whisper.cpp** - 完全ローカル音声認識（インターネット不要）
- ✅ **高精度日本語認識** - OpenAIのWhisperモデル使用
- ✅ **gTTS** - 日本語音声合成
- ✅ **GPT-3.5** - 日本語AI会話

**必要なもの：**
- Whisper.cppのインストール: `brew install whisper-cpp`
- Whisperモデル: `curl -L -o models/ggml-base.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin`

### 2. **japanese_voice_demo_simple.py** - Google Speech Recognition版
```bash
poetry run python japanese_voice_demo_simple.py
```

**特徴：**
- ✅ **Google Speech Recognition** - 無料日本語音声認識
- ✅ **簡単セットアップ** - 追加インストール不要
- ✅ **高速レスポンス** - クラウド処理
- ⚠️ インターネット接続必要

## 📊 比較表

| 機能 | Whisper.cpp版 | Google SR版 |
|------|--------------|-------------|
| 音声認識精度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| オフライン動作 | ✅ 可能 | ❌ 不可 |
| セットアップ | 📦 要モデルDL | 🚀 簡単 |
| 処理速度 | 🐢 やや遅い | 🐇 高速 |
| プライバシー | 🔒 完全ローカル | ☁️ クラウド |
| 無料枠 | ♾️ 無制限 | 🔢 50回/日 |

## 🚀 クイックスタート

### 基本セットアップ
```bash
# 依存関係インストール
poetry add gtts speechrecognition pyaudio

# 環境設定
echo "OPENAI_API_KEY=your_key" > .env
```

### Whisper.cpp版の追加セットアップ
```bash
# Whisper.cppインストール（Mac）
brew install whisper-cpp

# モデルダウンロード（選択）
mkdir -p models

# Tinyモデル（39MB、最速）
curl -L -o models/ggml-tiny.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin

# Baseモデル（142MB、推奨）
curl -L -o models/ggml-base.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

## 💡 使用例

### 基本的な会話
```
You: こんにちは
AI: こんにちは！今日はどのようなお手伝いができますか？

You: 今日の天気はどうですか？
AI: 申し訳ございません、リアルタイムの天気情報にはアクセスできません。
    お住まいの地域の天気予報サイトをご確認ください。

You: プログラミングについて教えて
AI: プログラミングについて何をお知りになりたいですか？
    言語の選び方、学習方法、特定の技術など、お聞きください。
```

## 🛠️ カスタマイズ

### 音声認識の調整
```python
# より敏感に
energy_threshold=200  # デフォルト: 300

# より長い無音を許容
pause_threshold=1.0  # デフォルト: 0.8
```

### AIの性格設定
```python
prompt_preamble="""
あなたは関西弁で話す親しみやすいAIアシスタントです。
冗談も交えながら楽しく会話してください。
"""
```

## 🔧 トラブルシューティング

### 音声が認識されない
1. マイクの音量を確認
2. 静かな環境で試す
3. `energy_threshold`を下げる

### Whisperが遅い
1. Tinyモデルを使用
2. `chunk_duration_seconds`を短くする
3. Google SR版を使用

### 日本語が文字化けする
1. ターミナルの文字コードをUTF-8に設定
2. フォントが日本語対応か確認

## 📈 パフォーマンス最適化

### Whisper.cpp版の高速化
- M1/M2 Macではメタル最適化が自動適用
- より小さいモデル（tiny）を使用
- チャンクサイズを調整

### メモリ使用量削減
- 不要なモデルを削除
- バッファサイズを調整
- 定期的にプロセスを再起動

## 🎉 完成！

これで日本語完全対応の音声会話システムが利用できます。
お好みの版を選んで、AIとの会話をお楽しみください！