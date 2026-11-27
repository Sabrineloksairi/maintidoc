"""Encodeurs d'embeddings.

- Texte : BGE-M3 (BAAI/bge-m3, MIT), vecteurs denses 1024 dimensions, multilingue.
- Texte-image (compatible CLIP, multilingue) : deux options comparées par benchmark
    * clip-multilingue-st : sentence-transformers/clip-ViT-B-32-multilingual-v1 (texte)
                            + clip-ViT-B-32 (image), 512 dimensions, Apache 2.0
    * openclip-xlmr       : OpenCLIP xlm-roberta-base-ViT-B-32 (laion5b_s13b_b90k), 512 dim., MIT
- Factices : vecteurs déterministes sans modèle (tests automatiques, CI) — MAINTIDOC_EMBEDDINGS_FACTICES=1.

Les modèles sont téléchargés depuis Hugging Face au premier lancement puis mis en cache.
"""
from __future__ import annotations

import hashlib
import re
from functools import lru_cache

import numpy as np
from PIL import Image

from src import config


def _normaliser(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.clip(n, 1e-9, None)


# ---------------------------------------------------------------------- texte
class EncodeurTexte:
    nom = "BAAI/bge-m3"
    dim = 1024

    def __init__(self, modele: str | None = None):
        from sentence_transformers import SentenceTransformer
        self.nom = modele or config.MODELE_TEXTE
        self._m = SentenceTransformer(self.nom, device="cpu")
        self._m.max_seq_length = 512            # nos passages font ~250 tokens
        self.dim = self._m.get_sentence_embedding_dimension()

    def encoder(self, textes: list[str], batch: int = 8) -> np.ndarray:
        return self._m.encode(textes, batch_size=batch, normalize_embeddings=True,
                              show_progress_bar=len(textes) > 20)


# ---------------------------------------------------------------- texte-image
class EncodeurImageST:
    """Option A : CLIP multilingue (sentence-transformers)."""
    nom = "clip-multilingue-st"
    dim = 512
    licence = "Apache 2.0"
    versions = "sentence-transformers/clip-ViT-B-32-multilingual-v1 + sentence-transformers/clip-ViT-B-32"

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self._texte = SentenceTransformer("sentence-transformers/clip-ViT-B-32-multilingual-v1", device="cpu")
        self._image = SentenceTransformer("sentence-transformers/clip-ViT-B-32", device="cpu")

    def encoder_textes(self, textes: list[str]) -> np.ndarray:
        return _normaliser(self._texte.encode(textes, batch_size=16))

    def encoder_images(self, images: list[Image.Image]) -> np.ndarray:
        return _normaliser(self._image.encode([i.convert("RGB") for i in images], batch_size=8))


class EncodeurImageOpenCLIP:
    """Option B : OpenCLIP avec encodeur de texte XLM-RoBERTa (multilingue)."""
    nom = "openclip-xlmr"
    dim = 512
    licence = "MIT (open_clip, poids LAION)"
    versions = "open_clip xlm-roberta-base-ViT-B-32 / laion5b_s13b_b90k"

    def __init__(self):
        import open_clip
        import torch
        self._torch = torch
        self._m, _, self._pre = open_clip.create_model_and_transforms(
            "xlm-roberta-base-ViT-B-32", pretrained="laion5b_s13b_b90k", device="cpu")
        self._m.eval()
        self._tok = open_clip.get_tokenizer("xlm-roberta-base-ViT-B-32")

    def encoder_textes(self, textes):
        with self._torch.no_grad():
            return _normaliser(self._m.encode_text(self._tok(textes)).numpy())

    def encoder_images(self, images):
        with self._torch.no_grad():
            x = self._torch.stack([self._pre(i.convert("RGB")) for i in images])
            return _normaliser(self._m.encode_image(x).numpy())


# ------------------------------------------------------------------- factices
class EncodeurTexteFactice:
    """Sac de mots haché (256 dim.) : pas de sens sémantique, mais déterministe et instantané."""
    nom = "factice-texte"
    dim = 256

    def encoder(self, textes, batch: int = 8):
        out = np.zeros((len(textes), self.dim), dtype=np.float32)
        for i, t in enumerate(textes):
            for mot in re.findall(r"\w+", t.lower()):
                h = int(hashlib.md5(mot.encode()).hexdigest(), 16)
                out[i, h % self.dim] += 1.0
        return _normaliser(out + 1e-6)


class EncodeurImageFactice:
    nom = "factice-image"
    dim = 256
    licence = "—"
    versions = "aucun modèle"

    def encoder_textes(self, textes):
        return EncodeurTexteFactice().encoder(textes)

    def encoder_images(self, images):
        return _normaliser(np.stack([np.asarray(i.convert("L").resize((16, 16)), dtype=np.float32).ravel()
                                     for i in images]) + 1e-6)


ENCODEURS_IMAGE = {"clip-multilingue-st": EncodeurImageST, "openclip-xlmr": EncodeurImageOpenCLIP}


@lru_cache(maxsize=2)
def encodeur_texte():
    return EncodeurTexteFactice() if config.EMBEDDINGS_FACTICES else EncodeurTexte()


@lru_cache(maxsize=3)
def encodeur_image(nom: str | None = None):
    if config.EMBEDDINGS_FACTICES:
        return EncodeurImageFactice()
    nom = nom or config.ENCODEUR_IMAGE
    if nom not in ENCODEURS_IMAGE:
        raise ValueError(f"Encodeur texte-image inconnu : {nom} (choix : {', '.join(ENCODEURS_IMAGE)})")
    return ENCODEURS_IMAGE[nom]()
