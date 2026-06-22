from pathlib import Path

import soundfile as sf
from voxcpm import VoxCPM


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SEGMENTS_FILE = ASSETS / "voxcpm_segments.txt"
OUT_DIR = ASSETS / "voxcpm-30s"

VOICE_CONTROL = "年轻女性，清晰自然，商务科技感，语速中等，像产品宣传片旁白"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2",
        load_denoiser=False,
        cache_dir=r"D:\tmp\hf-cache",
        optimize=False,
        device="cpu",
    )

    for index, line in enumerate(SEGMENTS_FILE.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        start, text = line.split("|", 1)
        final_text = f"({VOICE_CONTROL}){text.strip()}"
        wav = model.generate(
            text=final_text,
            cfg_value=2.0,
            inference_timesteps=4,
        )
        output = OUT_DIR / f"segment-{index:02d}.wav"
        sf.write(output, wav, model.tts_model.sample_rate)
        print(f"{start}s -> {output} ({text.strip()})")


if __name__ == "__main__":
    main()
