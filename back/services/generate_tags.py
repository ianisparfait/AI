from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import threading
from concurrent.futures import Future
from typing import List, Optional

class TagsGenerator:
    def __init__(self, model_name="google/flan-t5-base"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        self.tokenizer: Optional[T5Tokenizer] = None
        self.model: Optional[T5ForConditionalGeneration] = None
        self._model_future: Optional[Future] = None
        self._load_model_async()

    def _load_model_async(self):
        def _load_model():
            try:
                self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
                self.model = T5ForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
                self._model_future.set_result(None)
            except Exception as e:
                self._model_future.set_exception(e)
                raise

        self._model_future = Future()
        thread = threading.Thread(target=_load_model, daemon=True)
        thread.start()

    def _wait_for_model(self):
        if self._model_future is None:
            raise RuntimeError("The model has not been initialized correctly.")

        if not self._model_future.done():
            print("⌛ Loading...")
            self._model_future.result()

        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not available after loading.")

    def generate_tags(self, image_prompt: str, music_prompt: str, max_tags: int = 10) -> List[str]:
        self._wait_for_model()

        combined_prompt = (
            "Generate a list of relevant tags for a video based on the following descriptions.\n\n"
            f"Image: {image_prompt}\n"
            f"Music: {music_prompt}\n\n"
            "Provide only the tags as a comma-separated list. Do not include any other text."
        )

        inputs = self.tokenizer(
            combined_prompt, return_tensors="pt", padding=True, truncation=True
        ).to(self.device)

        try:
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=64,
                num_beams=5,
                temperature=0.8,
                no_repeat_ngram_size=2,
                num_return_sequences=1
            )

            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

            tags = [tag.strip().lower() for tag in generated_text.split(',')]
            tags = [tag for tag in tags if 2 < len(tag) <= 30]
            
            return tags[:max_tags]

        except Exception as e:
            print(f"❌ Error during tag generation : {e}")
            return []

    def format(self, tags: List[str]) -> str:
        return ', '.join([f"#{tag.replace(' ', '')}" for tag in tags])
