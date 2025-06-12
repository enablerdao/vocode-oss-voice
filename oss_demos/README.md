# Vocode OSS デモガイド

このリポジトリには、APIキーなし（またはOpenAIのみ）で動作するOSSベースのVocodeデモが含まれています。

## 🚀 デモ一覧

### 1. **oss_conversation_simple.py** - gTTS音声合成デモ
- ✅ **gTTS**（Google Text-to-Speech）- 無料、APIキー不要
- ✅ **OpenAI GPT-3.5** - AIエージェント
- ❌ 音声認識はDeepgram APIキーが必要

```bash
poetry run python oss_conversation_simple.py
```

**動作内容**: 初期メッセージを音声で再生します。

### 2. **full_oss_demo.py** - 完全OSSストリーミング会話（実験的）
- ✅ **Google Speech Recognition** - 無料音声認識
- ✅ **gTTS** - 無料音声合成
- ✅ **OpenAI GPT-3.5** - AIエージェント

```bash
poetry run python full_oss_demo.py
```

**注意**: カスタムトランスクライバーを使用する実験的な実装です。

### 3. **oss_turn_based_demo.py** - ターンベース会話（推奨）
- ✅ **Google Speech Recognition** - 無料音声認識
- ✅ **gTTS** - 無料音声合成
- ✅ **OpenAI GPT-3.5** - AIエージェント

```bash
poetry run python oss_turn_based_demo.py
```

**使い方**:
1. Enterキーを押して録音開始
2. 話し終わったら少し待つ（自動的に認識されます）
3. AIが音声で応答します
4. "goodbye"と言うと終了

## 📋 必要な環境

### 必須
- Python 3.8+
- マイク（音声入力用）
- スピーカー（音声出力用）

### インストール
```bash
# 依存関係のインストール
poetry install
poetry add gtts speechrecognition pyaudio

# .envファイルの作成（OpenAI使用時）
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

## 🎯 動作確認済みの機能

1. **音声合成（TTS）**
   - gTTS: Google Text-to-Speechを使用（無料、制限なし）
   - 多言語対応（日本語: lang="ja"）

2. **音声認識（STT）**
   - Google Web Speech API（無料、1日50リクエストまで）
   - リアルタイム認識

3. **AIエージェント**
   - OpenAI GPT-3.5（APIキー必要）
   - Echo Agent（APIキー不要、テスト用）

## 🛠️ トラブルシューティング

### 音声が認識されない場合
- マイクの権限を確認
- 環境ノイズを減らす
- より大きな声で話す
- `energy_threshold`を調整（デフォルト: 300）

### 音声が再生されない場合
- スピーカーの音量を確認
- デフォルトの出力デバイスを確認

### Google Speech Recognition エラー
- インターネット接続を確認
- 1日の無料リクエスト制限（50回）に注意

## 🔮 今後の改善案

1. **Whisper.cpp統合**
   - 完全オフライン音声認識
   - より高精度な認識

2. **Coqui TTS**
   - ローカル音声合成
   - カスタム音声の作成

3. **ストリーミング会話の改善**
   - より自然な会話フロー
   - 割り込み機能の実装