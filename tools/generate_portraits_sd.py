#!/usr/bin/env python
"""Genera i ritratti anime e gli sfondi title/ending di AURIGA con SD-Turbo locale.

Uso:
    python tools/generate_portraits_sd.py kaira            # una sola immagine
    python tools/generate_portraits_sd.py kaira ilan ...   # piu' immagini in sequenza
    python tools/generate_portraits_sd.py --all            # tutte
    python tools/generate_portraits_sd.py kaira --seed 99  # override del seed

Il modello viene caricato SOLO da cache locale (local_files_only=True).
CPU, float32, 2 step, guidance 0.0. Ritratti 512x512 -> 320x320 LANCZOS.
Sfondi 768x432 -> 1280x720 LANCZOS.
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTRAITS_DIR = ROOT / "assets" / "portraits"
BACKGROUNDS_DIR = ROOT / "assets" / "backgrounds"

STYLE = ("anime portrait, cel shading, clean lineart, flat vivid colors, "
         "bust portrait, sci-fi ship crew, detailed eyes, soft rim light")
NEGATIVE = ("photorealistic, 3d render, blurry, text, watermark, nsfw, "
            "lowres, bad anatomy, extra fingers")

PORTRAITS = {
    "kaira": ("young woman around 30 years old, short wavy red hair, "
              "teal and orange captain jumpsuit, confident lopsided smile, " + STYLE, 101),
    "ilan": ("gentle man around 32 years old, olive skin, thin round glasses, "
             "dark hair tied back, cardigan over ship uniform, kind expression, " + STYLE, 202),
    "sette": ("elegant androgynous android, sleek white and blue face plates, "
              "glowing amber eyes, serene expression, " + STYLE, 303),
    "naia": ("cheerful young woman around 26 years old, warm dark brown skin, "
             "freckles on cheeks, teal green hair tied up in a bun, "
             "botanist jumpsuit decorated with small glowing bioluminescent flowers, "
             "sunny bright smile, " + STYLE, 404),
    "ada": ("mature female medic around 50 years old, grey hair in a bun, "
            "warm motherly gaze, medical uniform, " + STYLE, 505),
    "bruno": ("sturdy male technician, thick beard, bandana on head, "
              "friendly rugged face, work overalls, " + STYLE, 606),
    "luce": ("cute innocent little girl around 10 years old, pigtail braids, "
             "big curious sparkling eyes, happy wholesome smile, simple ship clothes, "
             "wholesome children book style, " + STYLE, 707),
    "custode": ("cold austere holographic face made of glowing blue geometric "
                "polygons, translucent digital hologram head, symmetric, dark background, " + STYLE, 808),
}

BACKGROUNDS = {
    "title": ("anime style space scene, giant generation ark ship drifting through "
              "teal and violet nebula, stars, cel shading, vibrant, cinematic", 1111),
    "ending": ("anime style space scene, golden sunrise dawn over a lush planet seen "
               "from space, warm hopeful light, stars, cel shading, vibrant, cinematic", 2222),
}


def load_pipe():
    import torch
    from diffusers import AutoPipelineForText2Image
    t0 = time.time()
    print("[load] carico stabilityai/sd-turbo (local_files_only=True)...", flush=True)
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sd-turbo",
        torch_dtype=torch.float32,
        local_files_only=True,
    )
    pipe = pipe.to("cpu")
    pipe.enable_attention_slicing()
    print(f"[load] pipeline pronta in {time.time() - t0:.1f}s", flush=True)
    return pipe


def generate(pipe, name, seed_override=None):
    import torch
    from PIL import Image

    if name in PORTRAITS:
        prompt, seed = PORTRAITS[name]
        w, h = 512, 512
        out_path = PORTRAITS_DIR / f"{name}.png"
        final_size = (320, 320)
    elif name in BACKGROUNDS:
        prompt, seed = BACKGROUNDS[name]
        w, h = 768, 432
        out_path = BACKGROUNDS_DIR / f"{name}.png"
        final_size = (1280, 720)
    else:
        raise SystemExit(f"nome sconosciuto: {name}")

    if seed_override is not None:
        seed = seed_override

    gen = torch.Generator("cpu").manual_seed(seed)
    t0 = time.time()
    print(f"[gen] {name}: {w}x{h}, seed={seed} ...", flush=True)
    img = pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE,
        num_inference_steps=2,
        guidance_scale=0.0,
        width=w,
        height=h,
        generator=gen,
    ).images[0]
    img = img.resize(final_size, Image.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"[gen] {name}: salvato {out_path} in {time.time() - t0:.1f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="nomi immagini da generare")
    ap.add_argument("--all", action="store_true", help="genera tutto")
    ap.add_argument("--seed", type=int, default=None, help="override del seed")
    args = ap.parse_args()

    names = list(PORTRAITS) + list(BACKGROUNDS) if args.all else args.names
    if not names:
        ap.error("indicare almeno un nome o --all")

    pipe = load_pipe()
    for name in names:
        generate(pipe, name, seed_override=args.seed)
    print("[done] tutte le immagini generate", flush=True)


if __name__ == "__main__":
    main()
