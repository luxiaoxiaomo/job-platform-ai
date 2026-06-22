from pathlib import Path

import soundfile as sf
from voxcpm import VoxCPM


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SEGMENTS_FILE = ASSETS / "voxcpm_segments.txt"
OUT_DIR = ASSETS / "voxcpm-30s-cloned"
REFERENCE = ASSETS / "voxcpm_reference_voice.wav"

REFERENCE_TEXT = "你好，我来简单介绍一下这个招聘平台。我们会尽量说得清楚一点，节奏放松一点。"
REFERENCE_VOICE = "年轻女性，自然清晰，声音温和但不甜腻，像真实产品经理在演示产品，语速中等偏慢，有轻微停顿"
SEGMENT_CONTROL = "保持参考音色，自然口播，不要播音腔，语速中等偏慢，句尾自然收住"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2",
        load_denoiser=False,
        cache_dir=r"D:\tmp\hf-cache",
        optimize=False,
        device="cpu",
    )

    reference_wav = model.generate(
        text=f"({REFERENCE_VOICE}){REFERENCE_TEXT}",
        cfg_value=2.0,
        inference_timesteps=4,
        normalize=False,
    )
    sf.write(REFERENCE, reference_wav, model.tts_model.sample_rate)
    print(f"reference -> {REFERENCE}")

    for index, line in enumerate(SEGMENTS_FILE.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        start, text = line.split("|", 1)
        wav = model.generate(
            text=f"({SEGMENT_CONTROL}){text.strip()}",
            reference_wav_path=str(REFERENCE),
            cfg_value=2.4,
            inference_timesteps=6,
            normalize=False,
        )
        output = OUT_DIR / f"segment-{index:02d}.wav"
        sf.write(output, wav, model.tts_model.sample_rate)
        print(f"{start}s -> {output} ({text.strip()})")


if __name__ == "__main__":
    main()
