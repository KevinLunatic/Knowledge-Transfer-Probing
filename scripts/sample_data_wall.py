#!/usr/bin/env python3
"""Replace the existing photo-wall slots with reproducible training samples.

Requires Pillow. Source datasets are only read; all outputs stay in this site.
"""

import argparse
from collections import Counter
from hashlib import sha256
from html import escape
from io import BytesIO
import json
from pathlib import Path
import random
import re

from PIL import Image, ImageOps


SITE_ROOT = Path(__file__).resolve().parents[1]
TILE = re.compile(r'<li class="data-tile">.*?</li>', re.DOTALL)
TAG = re.compile(r'class="data-tag is-([a-z]+)"')


def attribute_value(category, info):
    if category == "spatial":
        arrow = " → " if info["stripe_orientation"] == "vertical" else " ↓ "
        return arrow.join(info["stripe_colors"])
    if category == "size":
        return f'{info["larger_country"]} > {info["smaller_country"]}'
    return str(info["title" if category == "text" else category])


def render_tile(sample):
    category = sample["category"]
    width, height = sample["asset_size"]
    return f'''<li class="data-tile">
            <img src="{escape(sample['asset'])}" width="{width}" height="{height}" alt="{escape(sample['alt'])}" loading="lazy">
            <span class="data-tag is-{category}">{category.title()}</span>
            <div class="data-tile-caption">
              <p class="data-prompt">{escape(sample['prompt'])}</p>
              <p class="data-value"><span>Value</span>{escape(sample['value'])}</p>
            </div>
          </li>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path,
                        default=SITE_ROOT.parent / "visgen_code_pipe" / "data")
    parser.add_argument("--seed", type=int, default=20261016)
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    page_path = SITE_ROOT / "index.html"
    page = page_path.read_text()
    categories = [TAG.search(tile.group()).group(1) for tile in TILE.finditer(page)]
    if not categories:
        raise ValueError("No photo-wall slots found in index.html")

    rng = random.Random(args.seed)
    selected = {}
    pool_counts = {}
    encoded_assets = {}
    for category, count in sorted(Counter(categories).items()):
        task = f"{category}_easy"
        task_root = data_root / task
        manifest = json.loads((task_root / "manifest.json").read_text())["instances"]
        specs = {s["instance_id"]: s for s in map(json.loads,
                 (task_root / "specs.jsonl").read_text().splitlines())}
        # These are the QC-passed, captioned images used by the T2I exporter.
        eligible = {
            ident: sorted(set(info.get("caption_images", []))
                          & set(info.get("qc_passed_images", [])))
            for ident, info in manifest.items() if ident in specs
        }
        eligible = {ident: indices for ident, indices in eligible.items() if indices}
        pool_counts[category] = {
            "entities": len(eligible),
            "images": sum(map(len, eligible.values())),
        }
        selected[category] = []
        # Sample distinct entities first, then one scene per entity.
        for ident in rng.sample(sorted(eligible), count):
            image_index = rng.choice(eligible[ident])
            instance = task_root / "instances" / ident
            stem = f"img_{image_index:02d}"
            caption = json.loads((instance / "captions" / f"{stem}.json").read_text())
            qc = json.loads((instance / "qc" / f"{stem}.json").read_text())
            if not caption.get("caption") or qc.get("pass") is not True:
                raise ValueError(f"Invalid training sample: {ident}/{stem}")
            source = instance / "images" / f"{stem}.png"
            source_bytes = source.read_bytes()
            # Some .png source files contain JPEG bytes; decode before exporting.
            with Image.open(BytesIO(source_bytes)) as original:
                source_format, source_size = original.format, original.size
                image = ImageOps.exif_transpose(original).convert("RGB")
                size = (round(image.width * 560 / image.height), 560)
                image = image.resize(size, Image.Resampling.LANCZOS)
                encoded = BytesIO()
                image.save(encoded, "JPEG", quality=88, optimize=True, progressive=True)
            asset = f"static/images/data/sampled/{ident}-{stem}.jpg"
            encoded_assets[asset] = encoded.getvalue()
            spec = specs[ident]
            prompt = spec["binding_name"]
            prompt = prompt[0].upper() + prompt[1:]
            value = attribute_value(category, spec["key_info"])
            selected[category].append({
                "category": category,
                "task": task,
                "instance_id": ident,
                "image_index": image_index,
                "split": spec["split"],
                "source": str(source.relative_to(data_root)),
                "source_format": source_format,
                "source_size": source_size,
                "source_sha256": sha256(source_bytes).hexdigest(),
                "asset": asset,
                "asset_size": size,
                "asset_sha256": sha256(encoded.getvalue()).hexdigest(),
                "prompt": prompt,
                "value": value,
                "alt": f"{prompt}; {category}: {value}.",
                "key_info": spec["key_info"],
            })

    queues = {category: iter(samples) for category, samples in selected.items()}
    samples = [dict(next(queues[category]), slot=slot)
               for slot, category in enumerate(categories, start=1)]
    replacements = iter(samples)
    page = TILE.sub(lambda _: render_tile(next(replacements)), page)
    page = re.sub(r'<!-- Row (\d+): .*? -->',
                  r'<!-- Row \1: sampled training examples; see static/images/data/samples.json. -->',
                  page)
    page = page.replace(
        "Miradel, Myravex, Arvenbrock, Nezara Wintermoss, Galiope, Zorin and Fyrnovan are all fictional names.",
        "All entity names in these examples are fictional.")
    provenance = {
        "seed": args.seed,
        "source_root": str(data_root),
        "method": "Per category: uniformly sample distinct entities without replacement, then one random QC-passed, captioned training image per entity.",
        "slots": len(samples),
        "counts": dict(sorted(Counter(categories).items())),
        "eligible_pool": pool_counts,
        "samples": samples,
    }
    # Write only after every selected source and its metadata have been validated.
    for asset, data in encoded_assets.items():
        path = SITE_ROOT / asset
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (SITE_ROOT / "static/images/data/samples.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    page_path.write_text(page)
    print(f"Updated {len(samples)} photo-wall slots with seed {args.seed}.")
    print(json.dumps(provenance["counts"]))
    print(f"Exported {sum(map(len, encoded_assets.values())) / 1024:.0f} KiB of JPEGs.")


if __name__ == "__main__":
    main()
