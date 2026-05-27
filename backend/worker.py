"""Real inference engine wrapping NVIDIA's LocateAnything-3B.

Heavy deps (torch, transformers) are imported lazily inside the engine so that
mock mode, the test suite, and CI never need them. The generation call mirrors
the worker example from the model card.
"""

from __future__ import annotations

# Minimum CUDA compute capability we consider supported (Ampere = 8.0).
_MIN_COMPUTE_MAJOR = 8


def gpu_report() -> dict:
    """Best-effort GPU detection for the health endpoint. Never raises."""
    try:
        import torch
    except Exception:
        return {
            "device": None,
            "gpu_name": None,
            "vram_gb": None,
            "compatible": False,
            "note": "PyTorch not installed.",
        }

    if not torch.cuda.is_available():
        return {
            "device": "cpu",
            "gpu_name": None,
            "vram_gb": None,
            "compatible": False,
            "note": "No CUDA device detected.",
        }

    props = torch.cuda.get_device_properties(0)
    major = torch.cuda.get_device_capability(0)[0]
    compatible = major >= _MIN_COMPUTE_MAJOR
    vram_gb = round(props.total_memory / (1024**3), 1)
    note = None
    if not compatible:
        note = "GPU is older than Ampere (compute < 8.0) and is not supported."
    elif vram_gb < 12:
        note = f"Only {vram_gb} GB VRAM detected; 12 GB+ recommended."
    return {
        "device": "cuda",
        "gpu_name": props.name,
        "vram_gb": vram_gb,
        "compatible": compatible,
        "note": note,
    }


class RealEngine:
    """Loads the model once and serves grounding queries."""

    def __init__(self, model_path: str):
        import torch
        from transformers import AutoModel, AutoProcessor, AutoTokenizer

        self._torch = torch
        self.model_path = model_path
        self.device = "cuda"
        self.dtype = torch.bfloat16

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        # This model ships only a slow image processor; choose it explicitly to
        # silence the use_fast deprecation nudge (there is no fast version).
        self.processor = AutoProcessor.from_pretrained(
            model_path, trust_remote_code=True, use_fast=False
        )
        self.model = (
            AutoModel.from_pretrained(model_path, dtype=self.dtype, trust_remote_code=True)
            .to(self.device)
            .eval()
        )
        self.model_loaded = True

    def predict(
        self,
        image,  # noqa: ANN001 - PIL image
        prompt: str,
        generation_mode: str,
        output_type: str = "box",  # noqa: ARG002 - real model infers from prompt
    ) -> dict:
        torch = self._torch
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        text = self.processor.py_apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        images, videos = self.processor.process_vision_info(messages)
        inputs = self.processor(text=[text], images=images, videos=videos, return_tensors="pt").to(
            self.device
        )

        with torch.no_grad():
            response = self.model.generate(
                pixel_values=inputs["pixel_values"].to(self.dtype),
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                image_grid_hws=inputs.get("image_grid_hws"),
                tokenizer=self.tokenizer,
                max_new_tokens=8192,
                use_cache=True,
                generation_mode=generation_mode,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                verbose=False,
            )

        if isinstance(response, tuple):
            raw = response[0]
            stats = response[2] if len(response) >= 3 else None
        else:
            raw, stats = response, None
        return {"raw": raw, "stats": stats}

    def info(self) -> dict:
        report = gpu_report()
        report["model_loaded"] = self.model_loaded
        return report


def create_engine(settings):  # noqa: ANN001
    """Build the inference engine for the current settings."""
    if settings.mock:
        from mock_engine import MockEngine

        return MockEngine()
    return RealEngine(settings.model_path)
