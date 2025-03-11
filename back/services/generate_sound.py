import os
import queue
import threading
import time
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import Future

import torch
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.models import MAGNeT

logger = logging.getLogger(__name__)

@dataclass
class AudioConfig:
    sample_rate: int = 32000
    output_dir: str = "output/generated_music"
    model_name: str = "facebook/magnet-small-30secs"
    duration: int = 30

class MusicGenerator:
    def __init__(self, config: AudioConfig = AudioConfig()):
        self.config = config
        self._ensure_output_directory()
        self.model: Optional[MusicGen] = None
        self._model_future: Optional[Future] = None
        self._request_queue = queue.Queue()
        self._processing_lock = threading.Lock()
        self._load_model_async()

    def _ensure_output_directory(self) -> None:
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    def _load_model_async(self):
        def _load_model():
            try:
                logger.info("Loading the model...")
                self.model = MAGNeT.get_pretrained(self.config.model_name)
                logger.info("Successfully loaded model.")
                self._model_future.set_result(None)
                self._process_queue()
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                self._model_future.set_exception(e)

        self._model_future = Future()
        thread = threading.Thread(target=_load_model, daemon=True)
        thread.start()

    def generate_music(self, description: str) -> Tuple[str, Optional[Path]]:
        if self.model is None:
            if self._model_future is None:
                raise RuntimeError("Model is not loading.")

            if not self._model_future.done():
                logger.info("Model loading. Request queuing.")
                self._request_queue.put(description)
                return "Waiting", None

            try:
                self._model_future.result()
            except Exception as e:
                raise RuntimeError(f"Error loading model: {e}")

        return self._generate_audio(description)

    def _generate_audio(self, description: str) -> Tuple[str, Path]:
        try:
            with self._processing_lock:
                generation_id = str(uuid.uuid4())
                output_path = Path(self.config.output_dir) / f"{generation_id}.wav"

                with torch.no_grad():
                    logger.info(f"Music generation for description : {description}")
                    audio = self.model.generate([description])

                audio = audio.detach().cpu()

                if audio.dim() == 3:
                    audio = audio.squeeze(0)
                elif audio.dim() == 1:
                    audio = audio.unsqueeze(0)

                torchaudio.save(str(output_path), audio, self.config.sample_rate)
                logger.info(f"Successfully generated music : {output_path}")

                return generation_id, output_path

        except Exception as e:
            logger.error(f"Music generation error: {e}")
            raise RuntimeError(f"Music generation failure: {e}")

    def _process_queue(self):
        while not self._request_queue.empty():
            description = self._request_queue.get()
            try:
                self._generate_audio(description)
            except Exception as e:
                logger.error(f"Error processing a queued request: {e}")

    def clean_old_files(self, max_age_hours: int = 24) -> None:
        try:
            current_time = time.time()
            for file_path in Path(self.config.output_dir).glob("*.wav"):
                if (current_time - file_path.stat().st_mtime) > (max_age_hours * 3600):
                    file_path.unlink()
                    logger.info(f"File deleted: {file_path}")
        except Exception as e:
            logger.error(f"File cleanup error: {e}")
