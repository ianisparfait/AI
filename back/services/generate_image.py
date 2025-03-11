import os
import uuid
import queue
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import Future

import torch
from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler
from PIL import Image

logger = logging.getLogger(__name__)

@dataclass
class ImageConfig:
    num_inference_steps: int = 50
    guidance_scale: float = 9.0
    height: int = 1024
    width: int = 1024
    output_dir: str = "output/generated_image"
    negative_prompt: str = """
    deformed hands, bad hands, extra hands, missing hands,
    deformed eyes, bad eyes, extra eyes, missing eyes,
    bad anatomy, deformed anatomy, mutated anatomy,
    blurry, low quality, worst quality, jpeg artifacts
    """

class ImageGenerator:
    def __init__(self, config: ImageConfig = ImageConfig()):
        self.config = config
        self._ensure_output_directory()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe: Optional[StableDiffusionXLPipeline] = None
        self._model_future: Optional[Future] = None
        self._request_queue = queue.Queue()
        self._processing_lock = threading.Lock()

        self._load_model_async()

    # Crée le répertoire de sortie s'il n'existe pas
    def _ensure_output_directory(self) -> None:
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    # Charge le modèle Stable Diffusion à la demande
    def _load_model_async(self):
        def _load_model():
            try:
                self.pipe = StableDiffusionXLPipeline.from_pretrained(
                    "stabilityai/stable-diffusion-xl-base-1.0",
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                )
                self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
                    self.pipe.scheduler.config
                )

                if self.device == "cuda":
                    self.pipe.enable_xformers_memory_efficient_attention()
                    self.pipe.enable_model_cpu_offload()
                else:
                    self.pipe.to(self.device)

            except Exception as e:
                logger.error(f"Error loading model : {e}")
                self._model_future.set_exception(e)
                raise

            self._model_future.set_result(None)

        self._model_future = Future()
        thread = threading.Thread(target=_load_model, daemon=True)
        thread.start()

    # Génère une image depuis un texte
    def generate_image_from_prompt(self, prompt: str) -> Tuple[str, Optional[Path]]:
        if self.pipe is None:
            if self._model_future is None:
                raise RuntimeError("Model is not loading.")

            if not self._model_future.done():
                self._request_queue.put(prompt)
                return "En attente", None

            try:
                self._model_future.result()
            except Exception as e:
                raise RuntimeError(f"Error loading model : {e}")

        try:
            with self._processing_lock:
                generator = torch.Generator(device=self.device)
                image = self.pipe(
                    prompt=prompt,
                    negative_prompt=self.config.negative_prompt,
                    num_inference_steps=self.config.num_inference_steps,
                    guidance_scale=self.config.guidance_scale,
                    width=self.config.width,
                    height=self.config.height,
                    generator=generator
                ).images[0]

                generation_id = str(uuid.uuid4())
                output_path = Path(self.config.output_dir) / f"{generation_id}.png"
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                image.save(output_path)

                logger.info(f"Image générée avec succès : {output_path}")

                while not self._request_queue.empty():
                    queued_prompt = self._request_queue.get()
                    pass

                return generation_id, output_path

        except Exception as e:
            logger.error(f"Error during image generation : {e}")
            raise RuntimeError(f"Image generation failure : {e}")

    # Nettoie les fichiers plus vieux que max_age_hours.
    def clean_old_files(self, max_age_hours: int = 24) -> None:
        try:
            current_time = time.time()
            for file_path in Path(self.config.output_dir).glob("*.png"):
                if (current_time - file_path.stat().st_mtime) > (max_age_hours * 3600):
                    file_path.unlink()
                    logger.info(f"File deleted : {file_path}")
        except Exception as e:
            logger.error(f"File cleanup error : {e}")
