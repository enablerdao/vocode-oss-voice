"""
Edge TTS Synthesizer for Vocode
高品質な日本語音声合成（Microsoft Edge TTS使用）
"""

import asyncio
import io
import edge_tts
from typing import List, Optional
from pydub import AudioSegment

from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import SynthesizerConfig
from vocode.streaming.synthesizer.base_synthesizer import BaseSynthesizer, SynthesisResult


class EdgeTTSSynthesizerConfig(SynthesizerConfig, type="synthesizer_edge_tts"):
    """Edge TTS設定"""
    voice: str = "ja-JP-NanamiNeural"  # デフォルトは日本語女性音声
    rate: str = "+0%"  # 速度調整 (-50% to +100%)
    volume: str = "+0%"  # 音量調整 (-50% to +100%)
    pitch: str = "+0Hz"  # ピッチ調整 (-50Hz to +50Hz)
    
    @classmethod
    def get_available_voices(cls) -> List[str]:
        """利用可能な日本語音声のリスト"""
        return [
            "ja-JP-NanamiNeural",  # 女性（標準）
            "ja-JP-KeitaNeural",   # 男性（標準）
            "ja-JP-AoiNeural",     # 女性（明るい）
            "ja-JP-DaichiNeural",  # 男性（明るい）
            "ja-JP-MayuNeural",    # 女性（優しい）
            "ja-JP-NaokiNeural",   # 男性（ビジネス）
            "ja-JP-ShioriNeural",  # 女性（若い）
        ]


class EdgeTTSSynthesizer(BaseSynthesizer[EdgeTTSSynthesizerConfig]):
    """Edge TTSを使用した高品質音声合成"""
    
    def __init__(self, synthesizer_config: EdgeTTSSynthesizerConfig):
        super().__init__(synthesizer_config)
        self.voice = synthesizer_config.voice
        self.rate = synthesizer_config.rate
        self.volume = synthesizer_config.volume
        self.pitch = synthesizer_config.pitch
        
        print(f"🎤 Edge TTS initialized with voice: {self.voice}")
    
    async def create_speech(
        self,
        message: BaseMessage,
        chunk_size: int,
        is_first_text_chunk: bool = False,
        is_sole_text_chunk: bool = False,
    ) -> SynthesisResult:
        """テキストから音声を生成"""
        
        # Edge TTSコミュニケーターを作成
        communicate = edge_tts.Communicate(
            message.text,
            self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch
        )
        
        # 音声データを取得
        audio_data = io.BytesIO()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])
        
        # バイトストリームを巻き戻し
        audio_data.seek(0)
        
        # MP3からWAVに変換（VocodeはWAV形式を期待）
        audio_segment = AudioSegment.from_mp3(audio_data)
        
        # WAV形式でエクスポート
        wav_data = io.BytesIO()
        audio_segment.export(wav_data, format="wav")
        wav_data.seek(0)
        
        # 合成結果を作成
        result = self.create_synthesis_result_from_wav(
            synthesizer_config=self.synthesizer_config,
            file=wav_data,
            message=message,
            chunk_size=chunk_size,
        )
        
        return result
    
    @staticmethod
    async def get_voices_list():
        """利用可能な全音声のリストを取得"""
        voices = await edge_tts.list_voices()
        japanese_voices = [v for v in voices if v["Locale"].startswith("ja-JP")]
        
        print("\n利用可能な日本語音声:")
        for voice in japanese_voices:
            print(f"- {voice['ShortName']}: {voice['Gender']} ({voice.get('FriendlyName', 'N/A')})")
        
        return japanese_voices