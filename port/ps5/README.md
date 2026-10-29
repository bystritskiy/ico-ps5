# ICO на PS5

Нативный перенос `nathanialf/ico-pc`, upstream
`b55a34f65adaee73b68362aab355b076feebf108` от 29 октября 2026.
Игровой C-код компилируется для x86-64 PS5; PS2-эмулятор, BIOS и JIT не нужны.

## Состояние

Первая сборка `01.000.000`, title ID **PPSA99030**, название плитки **ICO**.
Скомпилированы и слинкованы игра, Vulkan-рендерер и 173 SPIR-V шейдеров,
SDL3 с VideoOut через публичный PS5 RADV, AudioOut и DualSense.
Работа на PS5 **пока не проверена**. Сборка и проверка контейнера не доказывают
работоспособность изображения, звука, управления или сохранений на консоли.
Подробности: [VALIDATION.md](VALIDATION.md).

## Запуск

Для личной проверки подготовлен файл
`dist/ICO-PS5-PPSA99030-with-game.ffpfsc` с данными из предоставленного ISO.
Положить его в каталог образов, который сканирует ShadowMountPlus, и открыть
плитку ICO. Нужна среда запуска нативных PS5 homebrew. Предполагаемая среда
для первой проверки: FW 13.40, kstuff-lite, ShadowMountPlus; ICO в ней ещё
не запускался. Установленный отдельно PS5SX2 не требуется.

Для разработки можно скопировать содержимое `dist/with-game/PPSA99030/`
в `/data/homebrew/PPSA99030/` и использовать монтирование папок ShadowMountPlus.
Одновременно держать папку и образ с одним title ID не следует.

Данные игры читаются из `/app0/ico.o2r` или
`/data/ico/PPSA99030/ico.o2r`. Настройки (`config.toml`, `ico-pc.ini`), `memcard/`,
кеши и `logs/ico-pc.log` — в `/data/ico/PPSA99030/`.
Ранний запуск пишет `logs/boot.log`, предыдущий — `boot.previous`.
При обновлении не заменять этот каталог. Оригинальные меню и настройки ICO
сохраняются, вывод — 1920×1080, исходный формат кадра и эффекты задаёт меню.

DualSense: ✕/○/□/△, крестовина, оба стика, L1/R1, L2/R2 соответствуют DualShock 2.
Options — Start, нажатие тачпада — Select. Есть вибрация и повторное открытие
контроллера после ошибки чтения. Сейчас реализован один контроллер;
двухпользовательское управление Yorda не подключено.

## Предоставленный ISO

`source/[PS2] ICO [PAL-Multi6].iso`, 1 805 615 104 байта, SHA-256
`485aa618adeb69415c70b6fededbc2743610451a666e9c48ea91f90c0a6602d7`.
Это пересборка с меню `PBPX_955.06`, оригинальным `SCES_507.60`, изменённым
`SCES_507.00` и дополнительным `DATA.D2`.
Оригинальные `SCES_507.60` и `DATA.DF` прошли штатную проверку upstream:
ELF SHA-1 `da3644c54c26fe760f3b6a591a5fc2eab396ed2b` и манифест DATA.DF.

`tools/prepare-ps5-data.py` меняет BOOT2 только во временной копии ISO в
`build/inputs/`, исключает DATA.D2 из её каталога и импортирует оригинальную
PAL-версию через штатный загрузчик. Исходный ISO не изменяется.
**В этой сборке используются оригинальные PAL-данные; перевод/изменения из
альтернативной версии ISO не перенесены.** Полный образ и игровые данные
исключены из Git. Без `--game` упаковщик собирает приложение без игры.

## Сборка на Mac

Нужны Git, Python 3, CMake, Ninja, LLVM 18, Docker и собранный публичный
PS5 RADV/SDK. Пины и контрольные суммы — `dependencies.json`.
При первой сборке можно использовать готовый кеш соседнего `rePOP-ps5`;
установленный SDK/RADV копируется в `build/deps/`, соседний проект не меняется:

```sh
python3 tools/setup-ps5.py \
  --runtime-cache ../rePOP-ps5/build/deps/PS5_Vulkan \
  --compiler-rt ../rePOP-ps5/build/deps/compiler-rt/libclang_rt.builtins-x86_64.a \
  --dxc-archive ../rePOP-ps5/build/deps/dxc/dxc.tar.gz --build-images
python3 tools/build-ps5.py
```

Без готового кеша сначала собрать указанные в `dependencies.json`
PS5_Vulkan/PS5_Mesa/PS5_PayloadSDK по их инструкциям. `setup-ps5.py` проверяет
SHA-256 RADV, libc и compiler-rt и отказывается от другой версии.
При checkout на macOS Git/iconv может повредить обратные слеши в EUC-JP
исходниках; setup восстанавливает исходные Git blobs через Python euc_jp.
Игровые исходники не патчатся. Символ игрового `inflate` получает отдельное
имя при компиляции PS5, чтобы не конфликтовать с zlib внутри RADV.

Для подготовки данных и проверки на хосте:

```sh
cmake -S . -B build/host -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DICO_HEADLESS=ON -DICO_LINK_EXE=ON -DICO_RHI_VULKAN=OFF \
  -DICO_RHI_MOLTENVK=OFF -DICO_RHI_OPENGL=OFF -DICO_DEPS_DIR="$PWD/build/deps"
cmake --build build/host --target ico_pc -j8
python3 tools/prepare-ps5-data.py 'source/[PS2] ICO [PAL-Multi6].iso' \
  --host-exe build/host/ICO.app/Contents/MacOS/ICO
```

Подпись, упаковка и обратная сверка всех файлов:

```sh
python3 tools/package-ps5.py --game build/game/ico.o2r \
  --pack-python /path/to/python-with-mkpfs
```

Для образа без игры опустить `--game`. Нужен MkPFS 1.1.0.
Квитанция сборки — `dist/with-game/verification.json` (или `dist/app/`),
Квитанция содержит commit и SHA-256 исходников; упаковщик отказывается
упаковывать старую сборку после изменения исходников.
Логи сборки — `build/ps5/`, проверки данных — `build/validation/`.
Упаковщик проверяет FSELF и отсутствие экспортов в приложении, выполняет
MkPFS `--verify`, распаковывает образ и сравнивает каждый файл по SHA-256.

## Платформенный слой

- Public PayloadSDK, Clang 18, `x86_64-sie-ps5`, emulated TLS, сегменты 16 КиБ.
- SDL3 offscreen WSI получает `VK_KHR_display` от статически подключённого
  RADV. Окно 1080p получает клавиатурный фокус без оконного менеджера.
- libScePad питает виртуальный SDL gamepad: сохраняются upstream bindings,
  меню, мёртвые зоны и обратная вибрация.
- SDL audio backend `ps5`: AudioOut 256 кадров, 48 кГц, S16 stereo;
  преобразование формата, ресемплинг и очередь — штатные SDL и ico-pc.
- Сигнальный контекст использует проверенную PS5-структуру из SDK, включая
  смещение mcontext 64 байта; перезапуск процесса через desktop exec отключён.
- Ошибки пишутся в лог и отправляются системным уведомлением PS5.

Лицензии: [NOTICE.md](NOTICE.md), MIT исходного порта и условия GPL для
подключённого PS5 runtime. Пакет с данными игры предназначен для личного
использования; исходники не содержат ресурсов игры.
