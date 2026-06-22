from pathlib import Path

import soundfile as sf
from voxcpm import VoxCPM


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "voxcpm_voiceover_30s_single.wav"

VOICE_CONTROL = "年轻女性，清晰自然，商务科技感，语速中等偏慢，像产品宣传片旁白，音色稳定"
NARRATION = (
    "空岗发布，真正难的是找到合适的人。"
    "平台把企业端、求职端和管理端，放进同一个小程序。"
    "AI 代写岗位，整理职责、亮点和技能关键词。"
    "再把岗位画像和人才标签连接起来，给出高匹配候选人。"
    "认证、隐私和审核流程，形成可信闭环。"
    "让招聘，更快走向下一次有效对话。"
)


def main() -> None:
    model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2",
        load_denoiser=False,
        cache_dir=r"D:\tmp\hf-cache",
        optimize=False,
        device="cpu",
    )

    wav = model.generate(
        text=f"({VOICE_CONTROL}){NARRATION}",
        cfg_value=2.0,
        inference_timesteps=4,
        normalize=False,
    )
    sf.write(OUTPUT, wav, model.tts_model.sample_rate)
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
