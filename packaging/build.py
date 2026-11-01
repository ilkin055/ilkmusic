"""ilkmusic-in portativ Windows paketini yığır: dist\\ilkmusic\\ qovluğu və dist\\ilkmusic.zip.

Paketdə öz Python-u, paketlər, FFmpeg, tətbiq və ikonlu ilkmusic.exe var. Qarşı tərəfə heç nə quraşdırmaq lazım olmur.

İşə salmaq (layihə qovluğundan):
    "%USERPROFILE%\\.venvs\\mahni-app\\Scripts\\python.exe" packaging\\build.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGING = ROOT / "packaging"
DIST = ROOT / "dist"
OUT = DIST / "ilkmusic"

# venv-in baza Python-u (rəsmi NuGet paketi): reyestrsiz, qovluq kimi köçürülə bilir.
PYTHON_HOME = Path(sys.base_prefix)
FFMPEG_HOME = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "ffmpeg"
CSC = Path(os.environ["WINDIR"]) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def step(message: str) -> None:
    print(f"==> {message}", flush=True)


def folder_mb(path: Path) -> float:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e6


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    step(f"Python runtime: {PYTHON_HOME}")
    shutil.copytree(PYTHON_HOME, OUT / "python", ignore=IGNORE)

    step("Python paketləri (requirements.txt)")
    subprocess.run(
        [
            str(OUT / "python" / "python.exe"), "-m", "pip", "install", "-q",
            "--disable-pip-version-check", "--no-warn-script-location",
            "-r", str(ROOT / "requirements.txt"),
        ],
        check=True,
    )

    step("FFmpeg (yalnız ffmpeg.exe və ffprobe.exe; GPL lisenziyası ilə birlikdə)")
    (OUT / "ffmpeg").mkdir()
    for exe in ("ffmpeg.exe", "ffprobe.exe"):
        shutil.copy2(FFMPEG_HOME / "bin" / exe, OUT / "ffmpeg" / exe)
    shutil.copy2(FFMPEG_HOME / "LICENSE", OUT / "ffmpeg" / "LICENSE.txt")
    shutil.copy2(FFMPEG_HOME / "README.txt", OUT / "ffmpeg" / "README.txt")

    step("Tətbiq faylları")
    shutil.copytree(ROOT / "app", OUT / "app", ignore=IGNORE)
    shutil.copy2(ROOT / "run.py", OUT / "run.py")
    # Notepad-in Azərbaycan hərflərini düzgün göstərməsi üçün BOM ilə yazırıq.
    readme = (PACKAGING / "OXU.txt").read_text(encoding="utf-8")
    (OUT / "OXU.txt").write_text(readme, encoding="utf-8-sig")

    step("Başladıcı: ilkmusic.exe")
    subprocess.run(
        [
            str(CSC), "/nologo", "/target:winexe", "/optimize+", "/codepage:65001",
            f"/win32icon:{ROOT / 'ilkmusic.ico'}",
            f"/out:{OUT / 'ilkmusic.exe'}",
            "/r:System.Windows.Forms.dll",
            str(PACKAGING / "launcher.cs"),
        ],
        check=True,
    )

    step("ZIP arxivi")
    zip_path = Path(shutil.make_archive(str(DIST / "ilkmusic"), "zip", root_dir=DIST, base_dir="ilkmusic"))
    print(f"Qovluq: {OUT} ({folder_mb(OUT):.0f} MB)")
    print(f"Hazırdır: {zip_path} ({zip_path.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
