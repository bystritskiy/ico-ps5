> [!WARNING]
> **Early development test build.** This PS5 port is experimental and is not a stable release.
> Expect bugs, crashes and incomplete features.

<h1 align="center">ICO for PS5</h1>

<p align="center">
  <b>ICO, the PlayStation 2 game, ported as a native app<br>
  for homebrew-enabled PS5 consoles.</b>
</p>

<p align="center">
  <a href="#install"><b>Install</b></a>
  &nbsp;·&nbsp;
  <a href="#controls">Controls</a>
  &nbsp;·&nbsp;
  <a href="#settings">Settings</a>
  &nbsp;·&nbsp;
  <a href="#reporting-a-bug">Report a bug</a>
</p>

> [!IMPORTANT]
> **Bring your own game.**
> This project does not include or distribute copyrighted game files. Use a dump of your own original disc.
> Please do not request or share game downloads here.

## What it is

An unofficial PS5 port of [nathanialf/ico-pc](https://github.com/nathanialf/ico-pc), based on
v0.10.0. The game's C code is compiled for PS5, with DualSense input and Vulkan rendering.
The port includes the bob-ttz and cobra838 Russian translations.

## Highlights

- **Native PS5 build**, without a PS2 emulator or BIOS.
- **DualSense input**, including vibration.
- **In-game options** for resolution, aspect ratio and visual effects.
- **Disc-image import** from console storage or USB.

## Requirements

- A homebrew-enabled PS5 with ShadowMountPlus and an FTP server.
- A dump of your own supported PS2 disc. Supported editions and image names are listed in
  the [PS5 install guide](port/ps5/README.md).
- About **1 GB free** for imported game data, in addition to the source image.

## Install

1. **The app.** Download the app ZIP from [Releases](../../releases).
   Extract its `PPSA99031` folder to `/data/homebrew/` on the console.
2. **Your disc.** For the European release, copy the image to
   `/data/ico/PPSA99031/Ico_PAL.iso`. Other supported editions use different names;
   see [disc formats and USB import](port/ps5/README.md).
3. **Play.** Start **ICO** and allow a few minutes for the first import.
   The app checks the image and creates `/data/ico/PPSA99031/ico.o2r`.
   After a successful import, the source image can be removed.

**To update,** replace the `PPSA99031` app folder and keep `/data/ico/PPSA99031/`.
Existing imported data, settings and memory cards stay in that directory.

## Controls

The DualSense follows the DualShock 2 layout by button position.

| PlayStation 2 | DualSense |
|---|---|
| Cross / Circle / Square / Triangle | Cross / Circle / Square / Triangle |
| L1 / R1, L2 / R2 | L1 / R1, L2 / R2 |
| Start | Options |
| Select | Touchpad click |

Only one controller is connected by the PS5 port. The second-player Yorda mode is not available.

## Settings

Use **Options** for internal resolution, aspect ratio and visual effects.
The PS5 output uses 3840×2160 when available, otherwise the highest available 60 Hz mode.
Upstream's [options guide](https://github.com/nathanialf/ico-pc/blob/main/docs/OPTIONS.md)
describes the menus; platform-specific features may differ in this experimental build.

## Your files

Imported data, settings, memory cards, caches and logs are stored in `/data/ico/PPSA99031/`.
The logs include `logs/ico-pc.log`, `logs/boot.log` and `logs/pad.log`.

**Options → Extras** uses `ico-backup.zip` in that directory for backup and restore.
A new backup replaces the previous one.

## Known issues

This is an early development build. Full-game stability and feature parity with upstream
are not established. See [PS5 validation records](port/ps5/VALIDATION.md) for tested behavior.
Upstream's Windows, Linux, Android and Apple installation instructions do not apply to this PS5 app.

## Reporting a bug

Open an [issue](../../issues) with the app version, firmware, disc edition, steps to reproduce,
expected result and actual result. Attach relevant logs from `/data/ico/PPSA99031/logs/`.
Do not attach game files or disc images. Report PS5-specific problems here rather than upstream.

## For developers

See the [PS5 build and packaging guide](port/ps5/README.md).
For the original port's design, see the
[upstream architecture](https://github.com/nathanialf/ico-pc/blob/main/docs/port/ARCHITECTURE.md).

## Credits

- [ico-pc](https://github.com/nathanialf/ico-pc) and the original
  [ICO source reconstruction](https://github.com/nathanialf/ico): nathanialf and contributors.
- Russian translations: bob-ttz and cobra838.
- PS5 runtime: PS5_Vulkan, PS5_PayloadSDK, PS5_Mesa and SDL.
- PS5 port: [bystritskiy](https://github.com/bystritskiy).

## License

The original port's code is MIT licensed ([LICENSE](LICENSE)). The linked PS5 runtime also
imposes GPL terms on the combined executable. See [third-party notices](port/ps5/NOTICE.md).
These licenses grant no rights to the game or its data.

## Legal notice

This is an unofficial fan project, independent of nathanialf, Sony Interactive Entertainment
and Team Ico. *ICO*, PlayStation, PS5 and DualSense are trademarks of their respective owners.
