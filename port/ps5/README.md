# ICO на PS5

Нативный перенос `nathanialf/ico-pc`, upstream
`v0.10.0` (`e99d01813489d23f2a46264ca037b9ccf6899174`).
Игровой C-код компилируется для x86-64 PS5; PS2-эмулятор, BIOS и JIT не нужны.
Проект неофициальный и не связан с Sony Interactive Entertainment и Team Ico;
игра в пакет не входит, нужен образ своего диска.

## Состояние

Сборка `01.000.003`, title ID **PPSA99031**, название плитки **ICO**.
Что проверено на консоли и при каких условиях — [VALIDATION.md](VALIDATION.md).

## Установка (публичный пакет)

1. Установить приложение из ProsperoStore/RecompStore или распаковать
   `PPSA99031.zip` в `/data/homebrew/` (папка `PPSA99031/` в корне архива).
2. Положить образ своего диска под одним из имён `Ico_PAL`, `Ico_JPN`, `Ico_KOR`,
   `Ico_USA`, `Ico_CN`, `Ico_AUG6`, `Ico_JUN26` (`.iso`, `.chd`, `.bin`+`.cue`) в
   `/data/ico/PPSA99031/` или `/data/ico/` по FTP, либо в корень или папку `ico/`
   USB-накопителя (`/mnt/usb0` … `/mnt/usb7`). Поддерживаются те же семь дисков,
   что и в ico-pc; изменённые образы и репаки отклоняются проверкой upstream.
3. Запустить плитку. Первый запуск проверяет образ и копирует игровые файлы в
   `/data/ico/PPSA99031/ico.o2r` (около 1 ГБ свободного места, несколько минут);
   ход показывается системными уведомлениями. После этого образ можно удалить.

Настройки (`config.toml`, `ico-pc.ini`), `memcard/`, кеши и логи
(`logs/ico-pc.log`, ранний `logs/boot.log`, `logs/pad.log`) — в
`/data/ico/PPSA99031/`. При обновлении приложения этот каталог не трогать.
В Options → Extras резервное копирование и восстановление используют файл
`/data/ico/PPSA99031/ico-backup.zip`. Новая копия заменяет предыдущую.
Если образ не найден, приложение пишет причину в лог и в уведомление.

DualSense: ✕/○/□/△, крестовина, оба стика, L1/R1, L2/R2 соответствуют DualShock 2.
Options — Start, нажатие тачпада — Select, есть вибрация и повторное открытие
контроллера после ошибки чтения. Подключён один контроллер; режим второго
игрока (Yorda) не подключён. Вывод — режим VideoOut 3840×2160 (на дисплее без
него — наибольший 60 Гц режим); внутреннее разрешение, формат кадра и эффекты
задаёт меню Options.

## Личный пакет с игрой

Для собственной проверки упаковщик может положить `ico.o2r`, полученный из
своего ISO, прямо в приложение (`--game`). Такой пакет не публикуется.

Предоставленный `source/[PS2] ICO [PAL-Multi6].iso` (1 805 615 104 байта, SHA-256
`485aa618adeb69415c70b6fededbc2743610451a666e9c48ea91f90c0a6602d7`) — пересборка
с меню `PBPX_955.06`, оригинальным `SCES_507.60`, изменённым `SCES_507.00` и
дополнительным `DATA.D2`. `tools/prepare-ps5-data.py` меняет BOOT2 только во
временной копии в `build/inputs/`, исключает DATA.D2 из её каталога и импортирует
оригинальную PAL-версию через штатный загрузчик (ELF SHA-1
`da3644c54c26fe760f3b6a591a5fc2eab396ed2b` и манифест DATA.DF). Исходный ISO
не изменяется; перевод и изменения репака не переносятся.

## Сборка на Mac

Нужны Git, Python 3, CMake, Ninja, LLVM 18, Docker и собранный публичный
PS5 RADV/SDK. Пины и контрольные суммы — `dependencies.json`; оттуда же берётся
title ID для CMake (`ICO_PS5_DATA_DIR`) и упаковщика.
При первой сборке можно использовать готовый кеш соседнего `rePOP-ps5`;
установленный SDK/RADV копируется в `build/deps/`, соседний проект не меняется:

```sh
python3 tools/setup-ps5.py \
  --runtime-cache ../rePOP-ps5/build/deps/PS5_Vulkan \
  --compiler-rt ../rePOP-ps5/build/deps/compiler-rt/libclang_rt.builtins-x86_64.a \
  --dxc-archive ../rePOP-ps5/build/deps/dxc/dxc.tar.gz --build-images
python3 tools/build-ps5.py
```

`--devtools` у `build-ps5.py` включает DevLoop-снимок рендерера
(`/app0/devloop-shot`) и экспорт текстур без меню (`video.export_textures`);
такую сборку упаковщик помечает, а `release-ps5.py` отклоняет.

`setup-ps5.py` проверяет SHA-256 RADV, libc и compiler-rt и отказывается от
другой версии. При checkout на macOS iconv может заменить обратные слеши в
EUC-JP исходниках на полноширинные; setup восстанавливает Git blob только если
файл отличается лишь этим, иначе останавливается. Игровые исходники не
патчатся. Символ игрового `inflate` получает отдельное имя при компиляции PS5.

Данные для личного пакета и проверка на хосте:

```sh
cmake -S . -B build/host -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DICO_HEADLESS=ON -DICO_LINK_EXE=ON -DICO_RHI_VULKAN=OFF \
  -DICO_RHI_MOLTENVK=OFF -DICO_RHI_OPENGL=OFF -DICO_DEPS_DIR="$PWD/build/deps"
cmake --build build/host --target ico_pc -j8
python3 tools/prepare-ps5-data.py 'source/[PS2] ICO [PAL-Multi6].iso' \
  --host-exe build/host/ICO.app/Contents/MacOS/ICO
```

Подпись, упаковка и обратная сверка (MkPFS 1.1.0):

```sh
python3 tools/package-ps5.py --pack-python /path/to/python-with-mkpfs        # dist/app
python3 tools/package-ps5.py --game build/game/ico.o2r --pack-python …       # dist/with-game
```

Каталог `dist/<вид>/PPSA99031/` создаётся заново при каждом запуске.
Квитанция `dist/<вид>/verification.json` содержит commit, SHA-256 исходников и
каждого файла; упаковщик отказывается от сборки после изменения исходников,
проверяет FSELF и отсутствие экспортов, выполняет MkPFS `--verify` и сверяет
обратную распаковку.

## Публикация (ProsperoStore, RecompStore)

```sh
python3 tools/release-ps5.py
```

Работает только на закоммиченном дереве и по свежей `dist/app` без `--devtools`.
Делает `dist/release/PPSA99031.zip` (папка `PPSA99031/` в корне, только
`eboot.bin`, `sce_module/libc.prx`, `sce_sys/`, `licenses/`), архив исходников
GPL-частей `ICO-PS5-<версия>-third-party-source.tar.xz` (PS5_Vulkan,
PS5_PayloadSDK, PS5_Mesa на ревизиях из `dependencies.json`) и `release.json`
с SHA-256. `--allow-dirty` даёт пробный выпуск с суффиксом `-dirty`, не для
публикации.

Требования каталогов (проверены 2026-10-29):

- **ProsperoStore** ([руководство](https://github.com/darkxex/ps5-homebrew-catalog/blob/main/docs/submitting.md)):
  публичный GitHub-репозиторий, опубликованный release с тегом версии
  (`01.000.003`) и ZIP папки приложения; `.ffpfsc` не принимается. Запись
  `apps/PPSA99031.json` с URL asset и его SHA-256, `icon_url` на
  `port/ps5/sce_sys/icon0.png` по тегу, лицензия, категория; PR от владельца
  репозитория. В каждом релизе поднимать `contentVersion` и не заменять
  опубликованный asset.
- **RecompStore** ([форма](https://recompstore.com/submit)): GitHub-репозиторий,
  файл release (`.zip`), версия, title ID, описание, иконка ≥512×512, фон 16:9
  (лучше 3840×2160), логотип на прозрачном фоне, до 4 скриншотов с PS5.
  Отметка «не содержит игровых файлов» — публиковать только app-only ZIP.
- PPSA99031 на 2026-10-29 свободен в [реестре RecompStore](https://recompstore.com/ids)
  и в каталоге ProsperoStore. PPSA99030 занят (Forever Launcher), поэтому ID
  был сменён. Перед подачей проверить ещё раз; ID после релиза не менять.
- Указывать upstream ico-pc и его авторов, неофициальный характер и то, что
  игра не входит. Исполняемый файл в целом подпадает под GPL-3.0-or-later
  PS5_Vulkan/PayloadSDK ([NOTICE.md](NOTICE.md)): прикладывать архив исходников
  к каждому релизу.

## Платформенный слой

- Public PayloadSDK, Clang 18, `x86_64-sie-ps5`, emulated TLS, сегменты 16 КиБ.
- `mmap`/`mprotect` идут через `sceKernelMmap`/`sceKernelMprotect`
  (`src/memory_ps5.c`): прямой syscall из libc.a завершал title с
  SYSTEM_ILLEGAL_FUNCTION_CALL.
- SDL3 offscreen WSI получает `VK_KHR_display` от статически подключённого
  RADV; режим экрана SDL и окно — 3840×2160. Окно получает клавиатурный фокус
  без оконного менеджера.
- libScePad питает виртуальный SDL gamepad. PS2 libpad-shim переименован
  (`ico_ps2_scePadInit`/`ico_ps2_scePadRead`), чтобы не перекрывать системные
  символы. Между сэмплами пада сохраняется последнее состояние.
- SDL audio backend `ps5`: AudioOut 256 кадров, 48 кГц, S16 stereo;
  блокирующий вывод — в WaitDevice, вне mutex SDL.
- Лог: потоки libc подменяются без `dup`, `ico-pc.log` открыт на дозапись
  вместе с дескриптором диагностики.
- Сигнальный контекст использует PS5-структуру из SDK (смещение mcontext
  64 байта); перезапуск процесса через desktop exec отключён.
- Ошибки пишутся в лог и отправляются системным уведомлением PS5.

Лицензии: [NOTICE.md](NOTICE.md), MIT исходного порта и условия GPL для
подключённого PS5 runtime.
