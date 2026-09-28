"""Descarga los modelos pesados que no se versionan en git (manifiesto: models.txt).

Uso:
    python scripts/download_models.py            # descarga lo que falte
    python scripts/download_models.py --check    # solo comprueba (exit 1 si falta algo)
    python scripts/download_models.py --force    # vuelve a descargar todo

La app (footfall.py) llama a ensure() al arrancar cuando se ejecuta desde código;
en el ejecutable empaquetado los modelos ya van incluidos y no se descarga nada.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "models.txt"
CHUNK = 1 << 20
RETRIES = 3
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 "
        "Shopping-Analytics-model-downloader"
    )
}


class Asset:
    def __init__(self, sha256: str, size: int, dest: Path, urls: list[str]):
        self.sha256 = sha256
        self.size = size
        self.dest = dest
        self.urls = urls

    @property
    def name(self) -> str:
        return str(self.dest.relative_to(ROOT))


def load_manifest(path: Path = MANIFEST) -> list[Asset]:
    assets = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sha, size, dest, urls = line.split()
            assets.append(
                Asset(
                    sha256=sha.lower(),
                    size=int(size),
                    dest=ROOT / dest.replace("/", __import__("os").sep),
                    urls=urls.split("|"),
                )
            )
    return assets


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def is_valid(asset: Asset) -> bool:
    if not asset.dest.is_file() or asset.dest.stat().st_size != asset.size:
        return False
    return sha256_file(asset.dest) == asset.sha256


def _fetch(url: str, part: Path, log) -> None:
    req = urllib.request.Request(url, headers=HEADERS)
    total = None
    done = 0
    last_report = 0.0
    with urllib.request.urlopen(req, timeout=120) as resp:
        length = resp.headers.get("Content-Length")
        if length and length.isdigit():
            total = int(length)
        with open(part, "wb") as out:
            while True:
                chunk = resp.read(CHUNK)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                now = time.monotonic()
                if now - last_report >= 1.0:
                    last_report = now
                    if total:
                        log(
                            f"    {done / 1e6:8.1f} / {total / 1e6:8.1f} MB"
                            f" ({100 * done // total}%)"
                        )
                    else:
                        log(f"    {done / 1e6:8.1f} MB")
    if total and part.stat().st_size != total:
        raise IOError(f"descarga incompleta ({part.stat().st_size} de {total} bytes)")


def download(asset: Asset, log=print) -> None:
    asset.dest.parent.mkdir(parents=True, exist_ok=True)
    part = asset.dest.with_suffix(asset.dest.suffix + ".part")
    errors = []
    for url in asset.urls:
        for attempt in range(1, RETRIES + 1):
            try:
                log(f"  -> {url}")
                if part.exists():
                    part.unlink()
                _fetch(url, part, log)
                digest = sha256_file(part)
                if digest != asset.sha256:
                    raise IOError(
                        f"sha256 incorrecto ({digest[:16]}... "
                        f"esperado {asset.sha256[:16]}...)"
                    )
                part.replace(asset.dest)
                log(f"  OK {asset.name}")
                return
            except (urllib.error.URLError, IOError, OSError) as exc:
                errors.append(f"{url}: {exc}")
                log(f"  intento {attempt}/{RETRIES} fallido: {exc}")
                if attempt < RETRIES:
                    time.sleep(2 * attempt)
                if part.exists():
                    part.unlink()
        log(f"  fuente agotada: {url}")
    raise RuntimeError(
        f"No se pudo descargar {asset.name}.\n    " + "\n    ".join(errors)
    )


def ensure(manifest: Path = MANIFEST, quiet: bool = False, log=print) -> list[str]:
    """Descarga los modelos que falten. Devuelve la lista de errores (vacía = OK)."""
    log = (lambda *a, **k: None) if quiet else log
    failures = []
    for asset in load_manifest(manifest):
        if is_valid(asset):
            log(f"  OK (ya presente) {asset.name}")
            continue
        log(f"Descargando {asset.name} ({asset.size / 1e6:.1f} MB)")
        try:
            download(asset, log)
        except Exception as exc:  # noqa: BLE001 - se informa y se sigue con el resto
            log(f"  ERROR: {exc}")
            failures.append(f"{asset.name}: {exc}")
    if not failures:
        log("Modelos listos.")
    return failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="solo comprueba")
    parser.add_argument("--force", action="store_true", help="re-descarga todo")
    parser.add_argument("--quiet", action="store_true", help="sin salida")
    args = parser.parse_args(argv)
    log = (lambda *a, **k: None) if args.quiet else print

    assets = load_manifest()
    if args.check:
        missing = [a.name for a in assets if not is_valid(a)]
        if missing:
            print("Faltan modelos:\n  " + "\n  ".join(missing))
            return 1
        print("Todos los modelos presentes y verificados.")
        return 0

    failures = []
    for asset in assets:
        if not args.force and is_valid(asset):
            log(f"OK (ya presente) {asset.name}")
            continue
        log(f"Descargando {asset.name} ({asset.size / 1e6:.1f} MB)")
        try:
            download(asset, log)
        except Exception as exc:  # noqa: BLE001
            log(f"ERROR: {exc}")
            failures.append(f"{asset.name}: {exc}")
    if failures:
        print("\nFallos:")
        for f in failures:
            print(f"  {f}")
        return 1
    log("Modelos listos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
