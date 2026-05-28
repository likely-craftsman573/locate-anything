"""Real inference engine wrapping NVIDIA's LocateAnything-3B.

Heavy deps (torch, transformers) are imported lazily inside the engine so that
mock mode, the test suite, and CI never need them. The generation call mirrors
the worker example from the model card.
"""

import threading

# Minimum CUDA compute capability we consider supported (Ampere = 8.0).
_MIN_COMPUTE_MAJOR = 8
# Approx free VRAM (GB) needed to host the 3B model + headroom before a switch.
_MIN_FREE_VRAM_GB = 7.0


def _reset_rope_cache(model) -> int:  # noqa: ANN001 - torch nn.Module
    """Invalidate lazily-cached RoPE frequencies after a device move.

    The model's ``Rope2DPosEmb`` stores ``freqs_cis`` as a plain attribute (not a
    registered buffer) computed once on the device of the first forward pass, so
    ``model.to(device)`` neither moves nor clears it. Clearing it forces a
    recompute on the model's new device on the next forward; otherwise inference
    after a device switch fails with a cuda:0/cuda:N tensor-device mismatch.
    """
    count = 0
    for module in model.modules():
        if getattr(module, "freqs_cis", None) is not None:
            module.freqs_cis = None
            count += 1
    return count


def enumerate_devices() -> list[dict]:
    """List visible CUDA GPUs with VRAM + compatibility. Never raises."""
    try:
        import torch
    except Exception:
        return []
    if not torch.cuda.is_available():
        return []

    devices = []
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        major = torch.cuda.get_device_capability(i)[0]
        try:
            free, _ = torch.cuda.mem_get_info(i)
            free_gb = round(free / (1024**3), 1)
        except Exception:
            free_gb = None
        devices.append(
            {
                "index": i,
                "name": props.name,
                "vram_gb": round(props.total_memory / (1024**3), 1),
                "vram_free_gb": free_gb,
                "compatible": major >= _MIN_COMPUTE_MAJOR,
            }
        )
    return devices


def gpu_report(index: int = 0) -> dict:
    """Best-effort detail for one GPU, for the health endpoint. Never raises."""
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

    props = torch.cuda.get_device_properties(index)
    major = torch.cuda.get_device_capability(index)[0]
    compatible = major >= _MIN_COMPUTE_MAJOR
    vram_gb = round(props.total_memory / (1024**3), 1)
    note = None
    if not compatible:
        note = "GPU is older than Ampere (compute < 8.0) and is not supported."
    elif vram_gb < 12:
        note = f"Only {vram_gb} GB VRAM detected; 12 GB+ recommended."
    return {
        "device": f"cuda:{index}",
        "gpu_name": props.name,
        "vram_gb": vram_gb,
        "compatible": compatible,
        "note": note,
    }


class RealEngine:
    """Loads the model once and serves grounding queries."""

    def __init__(self, model_path: str, device_index: int = 0):
        import torch
        from transformers import AutoModel, AutoProcessor, AutoTokenizer

        self._torch = torch
        self.model_path = model_path
        self.device_index = device_index
        self.device = f"cuda:{device_index}"
        self.dtype = torch.bfloat16
        # Serializes inference vs. device switches so we never move the model
        # mid-generation.
        self._lock = threading.Lock()

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

        with self._lock:
            inputs = self.processor(
                text=[text], images=images, videos=videos, return_tensors="pt"
            ).to(self.device)

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

    def list_devices(self) -> dict:
        return {"current": self.device_index, "devices": enumerate_devices()}

    def switch_device(self, index: int) -> dict:
        """Move the model to GPU `index`. Guards VRAM and rolls back on failure."""
        by_index = {d["index"]: d for d in enumerate_devices()}
        target = by_index.get(index)
        if target is None:
            raise ValueError(f"No such GPU index: {index}")
        if not target["compatible"]:
            raise ValueError(f"GPU {index} is not supported (needs Ampere or newer).")
        if index == self.device_index:
            return self.list_devices()
        free = target["vram_free_gb"]
        if free is not None and free < _MIN_FREE_VRAM_GB:
            raise MemoryError(f"GPU {index} has only {free} GB free; need ~{_MIN_FREE_VRAM_GB} GB.")

        torch = self._torch
        prev = self.device_index
        with self._lock:
            try:
                self.model.to(f"cuda:{index}")
                _reset_rope_cache(self.model)
                self.device_index = index
                self.device = f"cuda:{index}"
            except Exception:
                self.model.to(f"cuda:{prev}")
                self.device_index = prev
                self.device = f"cuda:{prev}"
                raise
            finally:
                torch.cuda.empty_cache()
        return self.list_devices()

    def info(self) -> dict:
        report = gpu_report(self.device_index)
        report["model_loaded"] = self.model_loaded
        report["device_index"] = self.device_index
        return report
