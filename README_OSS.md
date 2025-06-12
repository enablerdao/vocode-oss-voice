# Vocode OSS Voice - 完全無料の音声会話システム

このリポジトリは、[Vocode](https://github.com/vocodedev/vocode-core)をベースに、完全に無料/OSSのサービスのみを使用した音声会話システムの実装例です。

## 🌟 特徴

- **完全無料** - クラウドAPIキー不要（OpenAI除く）
- **高性能音声認識** - Google Speech Recognition使用
- **自然な音声合成** - gTTS (Google Text-to-Speech)使用
- **リアルタイム処理** - 低遅延の音声会話を実現

## 🚀 デモ

### 高性能音声会話（推奨）
```bash
cd oss_demos
poetry run python high_performance_oss_demo.py
```

最適化されたリアルタイム音声認識と自然な会話フローを実現。

### その他のデモ
- `oss_conversation_simple.py` - シンプルな音声合成デモ
- `oss_turn_based_demo.py` - ターンベース会話
- `full_oss_demo.py` - 実験的なストリーミング実装

## 📦 インストール

```bash
# リポジトリのクローン
git clone https://github.com/enablerdao/vocode-oss-voice.git
cd vocode-oss-voice

# 依存関係のインストール
poetry install
poetry add gtts speechrecognition pyaudio

# 環境設定（OpenAI使用時のみ）
echo "OPENAI_API_KEY=your_key_here" > .env
```

## 🎯 使い方

1. マイクとスピーカーが正しく設定されていることを確認
2. デモスクリプトを実行
3. マイクに向かって話す
4. AIの応答を聞く
5. Ctrl+Cで終了

## 🛠️ 技術スタック

- **音声認識**: Google Speech Recognition (無料、1日50リクエストまで)
- **音声合成**: gTTS (無料、制限なし)
- **AIエージェント**: OpenAI GPT-3.5 (APIキー必要) または Echo Agent (無料)
- **フレームワーク**: Vocode Core

## 📚 ドキュメント

詳細は[oss_demos/README.md](oss_demos/README.md)を参照してください。

## 🔮 今後の計画

- [ ] Whisper.cpp統合（完全オフライン音声認識）
- [ ] Coqui TTS統合（ローカル音声合成）
- [ ] 日本語対応の強化
- [ ] WebRTCインターフェース
- [ ] 音声の割り込み機能改善

## 📄 ライセンス

このプロジェクトは[MIT License](LICENSE)の下で公開されています。

## 🤝 貢献

プルリクエストを歓迎します！改善案がある場合は、Issueを作成してください。

---

Created by [EnablerDAO](https://github.com/enablerdao) with ❤️