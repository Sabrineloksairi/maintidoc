"""Pré-télécharge les modèles Hugging Face utilisés par MaintiDoc, avec reprise automatique.

Utile sur une connexion lente ou instable : chaque fichier reprend là où il s'était arrêté,
et le script réessaie jusqu'à 20 fois. On ne télécharge que les fichiers réellement utilisés
(par exemple sans les exports ONNX de BGE-M3, qui pèsent 2 Go de plus).

Usage : python scripts/telecharger_modeles.py            (tous les modèles, ~3,5 Go)
        python scripts/telecharger_modeles.py --texte    (BGE-M3 seulement)
Les modèles vont dans HF_HOME (défini dans .env, ex. D:\\hf_cache).
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402,F401  (charge .env : HF_HOME)

os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")     # 10 s par défaut : trop court
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from huggingface_hub import snapshot_download  # noqa: E402

SANS = ["*.onnx", "onnx/*", "openvino/*", "*.msgpack", "*.h5", "*.ot", "*tflite*", "imgs/*", "*.png", "*.jpg"]
MODELES = {
    "texte": [("BAAI/bge-m3", ["*.json", "*.txt", "*.model", "tokenizer*", "pytorch_model.bin", "1_Pooling/*"])],
    "clip-multilingue-st": [("sentence-transformers/clip-ViT-B-32-multilingual-v1", None),
                            ("sentence-transformers/clip-ViT-B-32", None)],
    "openclip-xlmr": [("laion/CLIP-ViT-B-32-xlm-roberta-base-laion5B-s13B-b90k", ["open_clip_*", "*.json"]),
                      ("xlm-roberta-base", ["*.json", "*.model", "tokenizer*"])],
}


def telecharger(depot: str, motifs: list[str] | None, essais: int = 20):
    for essai in range(1, essais + 1):
        try:
            t = time.perf_counter()
            chemin = snapshot_download(depot, allow_patterns=motifs, ignore_patterns=None if motifs else SANS)
            print(f"  OK {depot} ({time.perf_counter() - t:.0f} s) -> {chemin}")
            return
        except KeyboardInterrupt:
            raise
        except Exception as e:  # coupure réseau : on reprend
            print(f"  essai {essai}/{essais} interrompu ({e.__class__.__name__}) – reprise dans 15 s…")
            time.sleep(15)
    raise SystemExit(f"Échec du téléchargement de {depot} après {essais} essais.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texte", action="store_true", help="BGE-M3 uniquement")
    args = ap.parse_args()
    groupes = ["texte"] if args.texte else list(MODELES)
    print(f"Cache : {os.environ.get('HF_HOME', '(défaut Hugging Face)')}")
    for g in groupes:
        print(f"== {g}")
        for depot, motifs in MODELES[g]:
            telecharger(depot, motifs)
    print("Tous les modèles sont disponibles.")


if __name__ == "__main__":
    main()
