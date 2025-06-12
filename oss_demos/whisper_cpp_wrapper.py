"""
Whisper.cpp wrapper for Python
Provides simple interface to whisper-cpp command line tool
"""

import subprocess
import tempfile
import wave
import os
import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor


class WhisperCPPWrapper:
    """Wrapper for whisper-cpp command line tool"""
    
    def __init__(
        self,
        model_path: str = None,
        whisper_cpp_path: str = "/opt/homebrew/bin/whisper-cpp",
        language: str = "ja",  # Japanese by default
        translate: bool = False,
        n_threads: int = 4,
    ):
        self.whisper_cpp_path = whisper_cpp_path
        self.language = language
        self.translate = translate
        self.n_threads = n_threads
        
        # モデルパスの設定
        if model_path:
            self.model_path = model_path
        else:
            # デフォルトモデルパスを探す
            possible_paths = [
                "/Users/yuki/vocode-core/models/ggml-base.bin",
                "models/ggml-base.bin",
                "../models/ggml-base.bin",
            ]
            for path in possible_paths:
                if Path(path).exists():
                    self.model_path = path
                    break
            else:
                raise FileNotFoundError(
                    "Whisper model not found. Please download: "
                    "curl -L -o models/ggml-base.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
                )
        
        # whisper-cppの存在確認
        if not Path(self.whisper_cpp_path).exists():
            raise FileNotFoundError(f"whisper-cpp not found at {self.whisper_cpp_path}")
            
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def transcribe_file(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio file using whisper-cpp"""
        
        # コマンドライン引数の構築
        cmd = [
            self.whisper_cpp_path,
            "-m", self.model_path,
            "-f", audio_file_path,
            "-l", self.language,
            "-t", str(self.n_threads),
            "--no-timestamps",
            "-oj",  # JSON output
        ]
        
        if self.translate:
            cmd.append("--translate")
        
        try:
            # whisper-cppを実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # JSON出力をパース
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line.strip().startswith('{'):
                    try:
                        json_result = json.loads(line)
                        return json_result
                    except json.JSONDecodeError:
                        pass
            
            # JSONが見つからない場合はテキストを返す
            return {
                "text": result.stdout.strip(),
                "language": self.language
            }
            
        except subprocess.CalledProcessError as e:
            print(f"Whisper-cpp error: {e.stderr}")
            return {"text": "", "error": str(e)}
    
    async def transcribe_audio_data(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcribe raw audio data asynchronously"""
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # WAVファイルとして保存
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            
            # 非同期で転写
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self.transcribe_file,
                tmp_file.name
            )
            
            # 一時ファイルを削除
            os.unlink(tmp_file.name)
            
            return result.get("text", "")
    
    def close(self):
        """Clean up resources"""
        self.executor.shutdown(wait=False)


class WhisperCPPTranscriberConfig:
    """Configuration for Whisper.cpp transcriber"""
    sampling_rate: int = 16000
    audio_encoding: str = "LINEAR16"
    chunk_size: float = 1.0
    language: str = "ja"
    model_path: Optional[str] = None
    whisper_cpp_path: str = "/opt/homebrew/bin/whisper-cpp"
    translate: bool = False
    
    @classmethod
    def from_input_device(cls, input_device, **kwargs):
        return cls(
            sampling_rate=input_device.sampling_rate,
            audio_encoding=input_device.audio_encoding,
            **kwargs
        )