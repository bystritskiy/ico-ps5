# Tile art

| File | Origin |
|---|---|
| `icon.png` | built-in image_gen via `codex exec`, 1254×1254, prompt in `prompts/icon.txt` |
| `background.png` | built-in image_gen via `codex exec`, 1672×941, prompt in `prompts/background.txt` |
| `logo.png` | "ICO" in Big Caslon on a transparent background, drawn with Pillow, for RecompStore |
| `banner-source.png` | built-in image_gen via `codex exec` from `icon.png` and `background.png`, 1672×941, prompt in `prompts/banner.txt`; cropped to `../media/banner.jpg` 2000×640 for the README |

`tools/build-presentation.py` (Pillow, etcpak, texture2ddecoder) writes `../sce_sys/icon0.png`
512×512, `pic0.dds` and `pic1.dds` 3840×2160 BC7 and `pic1.png` 1920×1080, decodes the BC7
back and records the hashes in `presentation.json`.

Checked on the console 2026-11-26 (FW 13.40, ShadowMountPlus): the shell showed the new
icon and background after the folder was registered again; the title and Play button sit
over the calm left side.
