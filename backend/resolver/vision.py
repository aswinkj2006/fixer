"""
fixer.ai — Vision Module
Analyzes uploaded images and produces short structured defect descriptions.

In LLM_STUB_MODE: returns realistic stub defect summaries per machine type.
In production: sends image to Gemma 3 4B (or Qwen3-VL) via Ollama.

Design note from spec: Vision model output is a SHORT, STRUCTURED defect summary,
NOT a raw image forwarded downstream. This keeps the fusion reasoning model's
context short and improves output quality on small local models.
"""
import base64
from typing import Optional

from backend.config import LLM_STUB_MODE, OLLAMA_BASE_URL, VISION_MODEL

# Prompt designed for short, structured output from a 3-4B vision model
_VISION_SYSTEM_PROMPT = """You are an industrial fault inspection assistant.
Analyze the provided image and output a SHORT, STRUCTURED defect description.
Format your response EXACTLY as:
COMPONENT: [what component is visible]
OBSERVED_DEFECT: [specific visual finding in ≤ 2 sentences]
SEVERITY_ESTIMATE: [none | minor | moderate | severe]
MAINTENANCE_INDICATORS: [any wear, leakage, corrosion, damage indicators visible]

Be precise and factual. Do not speculate beyond what is visually evident."""

_VISION_USER_PROMPT = "Analyze this industrial equipment image and provide a structured defect description."


async def analyze_image(
    image_bytes: bytes,
    filename: str = "image.jpg",
    machine_id: Optional[str] = None,
) -> dict:
    """
    Analyze an uploaded equipment image and return a structured defect summary.

    Returns:
        dict with keys:
            - component: str
            - observed_defect: str
            - severity_estimate: str  (none/minor/moderate/severe)
            - maintenance_indicators: str
            - raw_description: str    (full model output)
            - stub_mode: bool
    """
    if LLM_STUB_MODE or not image_bytes:
        return _stub_analyze(machine_id, bool(image_bytes))

    try:
        return await _ollama_analyze(image_bytes, filename)
    except Exception as e:
        print(f"[vision] Analysis failed: {e}. Falling back to stub.")
        return _stub_analyze(machine_id, True)


def _stub_analyze(machine_id: Optional[str], has_image: bool) -> dict:
    """
    # LLM-STUB: Deterministic mock vision analysis per machine type.
    Replace with real Ollama vision call on capable hardware.
    """
    if not has_image:
        return {
            "component": "N/A",
            "observed_defect": "No image provided.",
            "severity_estimate": "none",
            "maintenance_indicators": "None visible — no image uploaded.",
            "raw_description": "No image provided.",
            "stub_mode": True,
        }

    stubs = {
        "M-01": {
            "component": "J2 harmonic drive reducer housing and output flange",
            "observed_defect": (
                "Visible grease discoloration and metallic residue on the J2 reducer output flange. "
                "Grease shows silver-grey metallic particulate contamination consistent with gear mesh wear."
            ),
            "severity_estimate": "moderate",
            "maintenance_indicators": (
                "Grease extrusion from seal gap, metallic sheen in discharged grease, "
                "slight surface scoring on flange mating face."
            ),
            "raw_description": (
                "COMPONENT: J2 harmonic drive reducer housing and output flange\n"
                "OBSERVED_DEFECT: Visible grease discoloration and metallic residue on the J2 reducer output flange. "
                "Grease shows silver-grey metallic particulate contamination consistent with gear mesh wear.\n"
                "SEVERITY_ESTIMATE: moderate\n"
                "MAINTENANCE_INDICATORS: Grease extrusion from seal gap, metallic sheen in discharged grease, "
                "slight surface scoring on flange mating face."
            ),
            "stub_mode": True,
        },
        "M-02": {
            "component": "Spindle nose and tool holder taper interface",
            "observed_defect": (
                "Fretting corrosion marks visible on spindle taper mating surface. "
                "Tool holder shows micro-pitting and abrasion marks on the 40-taper contact zone."
            ),
            "severity_estimate": "moderate",
            "maintenance_indicators": (
                "Brown-red fretting debris on taper bore, polished wear marks at retention knob seat, "
                "light surface rust on exposed taper surfaces."
            ),
            "raw_description": (
                "COMPONENT: Spindle nose and tool holder taper interface\n"
                "OBSERVED_DEFECT: Fretting corrosion marks visible on spindle taper mating surface.\n"
                "SEVERITY_ESTIMATE: moderate\n"
                "MAINTENANCE_INDICATORS: Brown-red fretting debris, polished wear marks at retention knob seat."
            ),
            "stub_mode": True,
        },
        "M-03": {
            "component": "Drive motor end bell and bearing housing (Drive-End)",
            "observed_defect": (
                "Thermal discoloration on drive-end bearing housing, indicating sustained overtemperature. "
                "Grease purge residue visible at bearing seal, darkened and oxidised."
            ),
            "severity_estimate": "severe",
            "maintenance_indicators": (
                "Dark brown / black grease discharge at seal lip, heat-induced paint blistering on housing, "
                "visible separation in bearing seal lip."
            ),
            "raw_description": (
                "COMPONENT: Drive motor end bell and bearing housing (Drive-End)\n"
                "OBSERVED_DEFECT: Thermal discoloration on drive-end bearing housing indicating sustained overtemperature.\n"
                "SEVERITY_ESTIMATE: severe\n"
                "MAINTENANCE_INDICATORS: Dark oxidised grease at seal lip, heat blistering on paint, separated seal."
            ),
            "stub_mode": True,
        },
        "M-04": {
            "component": "Torque transducer mounting flange and cable connector",
            "observed_defect": (
                "Transducer cable connector shows slight green oxidation on pin contacts. "
                "Mounting flange bolts show minor corrosion — possible micro-movement under cyclic loading."
            ),
            "severity_estimate": "minor",
            "maintenance_indicators": (
                "Pin contact oxidation on 8-pin connector, surface rust on mounting bolts, "
                "slight fretting marks on alignment dowel pins."
            ),
            "raw_description": (
                "COMPONENT: Torque transducer mounting flange and cable connector\n"
                "OBSERVED_DEFECT: Cable connector pin oxidation and mounting bolt corrosion.\n"
                "SEVERITY_ESTIMATE: minor\n"
                "MAINTENANCE_INDICATORS: Pin contact oxidation, surface rust on bolts, fretting on dowel pins."
            ),
            "stub_mode": True,
        },
    }
    result = stubs.get(machine_id or "", stubs["M-01"]).copy()
    result["stub_mode"] = True
    return result


async def _ollama_analyze(image_bytes: bytes, filename: str) -> dict:
    """
    # Production: Call Gemma 3 4B (or Qwen3-VL) via Ollama for vision analysis.
    Requires: Ollama running locally with `ollama pull gemma3:4b` done.
    """
    import httpx

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": _VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _VISION_USER_PROMPT,
                "images": [image_b64],
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 256,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        resp.raise_for_status()
        raw = resp.json()["message"]["content"].strip()

    return _parse_vision_output(raw)


def _parse_vision_output(raw: str) -> dict:
    """Parse structured KEY: value output from the vision model."""
    result = {
        "component": "",
        "observed_defect": "",
        "severity_estimate": "none",
        "maintenance_indicators": "",
        "raw_description": raw,
        "stub_mode": False,
    }
    key_map = {
        "COMPONENT": "component",
        "OBSERVED_DEFECT": "observed_defect",
        "SEVERITY_ESTIMATE": "severity_estimate",
        "MAINTENANCE_INDICATORS": "maintenance_indicators",
    }
    current_key = None
    current_lines = []
    for line in raw.splitlines():
        matched = False
        for prefix, field in key_map.items():
            if line.startswith(f"{prefix}:"):
                if current_key:
                    result[current_key] = " ".join(current_lines).strip()
                current_key = field
                current_lines = [line[len(prefix) + 1:].strip()]
                matched = True
                break
        if not matched and current_key:
            current_lines.append(line.strip())
    if current_key:
        result[current_key] = " ".join(current_lines).strip()
    return result
