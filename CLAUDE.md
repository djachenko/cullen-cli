# cullen-cli — Project Guide

Применяет решения отбора из iOS-приложения [Cullen](https://github.com/djachenko/Cullen) к исходникам на диске. Приложение экспортирует `culled.json`, эта утилита раскладывает равы по папкам-категориям.

> Память: `_claude/memory/index.md` — Бэклог: `_claude/backlog/index.md` — Прогресс: `_claude/progress/index.md`

---

## Связи с другими репо

| Репо | Что связывает |
|---|---|
| `Cullen` (iOS) | контракт `culled.json`: пишет `ExportDecisionsUseCase.swift`, описан в `Cullen/.claude/skills/cli.md`. Изменение формата — правка в обоих репо |
| `justin` | поставщик служебных папок (`justin/shared/models/photoset.py`, `justin/di/extractors.py`); будущий потребитель `cullen` как библиотеки |
| `justin_utils` | `bfs`, `frompath`/`DictableDataclass` |

Пакет на PyPI — `cullen`: `pipx install cullen` даёт команду, `pip install cullen` — библиотеку.

---

## Стек

| | |
|---|---|
| Python | 3.11+, `list[T]`, `T \| None` |
| CLI | Typer, сабаппы через `add_typer(subapp)` без имён, команды через `@app.command()` |
| Вывод | rich: `Progress` (cull, flop) и `Live`-стадии (relocate), оба `transient=True`, + итоговая таблица; Plain-ветка для не-tty (PyCharm) |
| Сборка | setuptools, `python-semantic-release`, `tag_format = v{version}` |
| Качество | ruff (line 120, `ANN` включён), mypy `strict`, pytest |

Запуск инструментов — бинари напрямую: `.venv/bin/pytest`, `.venv/bin/ruff check`, `.venv/bin/mypy src`.

---

## Структура

```
src/cullen/
├── __init__.py          # публичный API: DecisionsFile, load, ошибки, SERVICE_FOLDERS
├── decisions_file.py    # DecisionsFile (DictableDataclass) + load(path)
├── errors.py            # CullenError → DecisionsFileError → DecisionsFileMissingError; FlopError
├── service_folders.py   # плоский набор имён папок, которые cull не трогает
└── _cli/                # потребитель публичного API, не для импорта извне
    ├── main.py          # Typer + main() с обработкой CullenError, entry point cullen._cli.main:main
    ├── ui/              # console.py: Console/Task/Stage ABC; rich.py, plain.py — реализации; make_console() по isatty
    └── commands/        # cull.py, flop.py, relocate.py — по сабаппу на файл
tests/
├── conftest.py          # фикстуры create_files (дерево-словарь), photoset, tree
├── test_boundary.py     # граница SDK/CLI
└── test_<модуль>.py     # по файлу на команду, плюс cli, ui, decisions_file
```

**Граница SDK / CLI.** `_cli/` импортирует только `from cullen import ...` — как внешний потребитель, никаких `from cullen.decisions_file import`. `import cullen` обязан работать без typer/rich. Проверяется `tests/test_boundary.py`. Смысл: при разрастании SDK `_cli/` уезжает в отдельный дистрибутив без правки импортов.

---

## Команды

```
cullen cull [PATHS...] [--file culled.json]   # разложить сорсы по папкам-категориям
cullen flop [PATH] [FILE] [--dry-run]         # поднять папки-категории обратно (PATH по умолчанию — ..)
cullen relocate [PATHS...] [--root ROOT]      # найти экспортированные json и разнести по фотосетам
```

`cull *` — shell раскрывает глоб, команда принимает список и идёт по `sorted(paths)`. Сет без `culled.json` пропускается, остальные обрабатываются.

`relocate` берёт папки и файлы (по умолчанию — текущая папка), отбирает среди них файлы решений и обходит `ROOT` (по умолчанию `/`) в поисках фотосетов. Найденный файл переезжает в фотосет как `culled.json`, ненайденные перечисляются в конце.

---

## Контракт `culled.json`

Лежит в корне фотосета. `decisions` — категории → стемы файлов, `name` — id фотосета.

- **Стем без расширения.** Единица перемещения — стем: сайдкары (`.xmp`, `.JPG` рядом с `.RAF`) уезжают за равом сами, отдельной группировки нет
- **`name` — это `PhotosetId`, а не имя папки.** Совпадают, пока `JsonPhotosRepository` отдаёт `.string(filename)`; при `.int`/`.uuid` источнике `relocate` перестанет находить папки. Риск открыт

---

## Инварианты `cull` — не ломать

- **Служебные папки — плоский список имён, не эвристика.** Правила «папка без равов — производная» и «отсекать по превью» уже проверялись и отброшены: `not_signed`, `progress` и другие папки пайплайна `justin` содержат равы, но разбирать их нельзя. Список пополняет владелец руками
- **Категории создаются в той подпапке, где лежит файл.** Фотосет часто разбит на подпапки (локации, серии, панорамы), каждая отбирается независимо. Корень может не содержать ни одного исходника — это не повод не спускаться
- **`_flatten` перед `_distribute`.** Иначе повторный прогон по уже разложенному сету не пересортирует. Расплющиваются только папки с именами из `decisions`
- **В категории не спускаться** — иначе `good/good/`
- **`bfs` из `justin_utils`**, конвенция провайдера: делает работу, возвращает детей, `[]` = отсечь поддерево
- **`OSError` не ловится.** `rename` посреди обхода оставляет сет полуразложенным — трейсбек честнее аккуратной строчки. Исключение — отсутствующий файл решений: это `DecisionsFileMissingError`, пользовательский случай
- **Дефолт пути — `Path(".")`, не `Path.cwd()`** — второе замерзает на импорте

---

## Инварианты `relocate`

- **Фотосет — папка с именем из `name` и подпапкой `cullen/`**
- **Симлинки не разворачиваются** — `/Volumes/Macintosh HD` → `/` → `/Volumes/...` бесконечно
- **Скрытые и системные папки не обходятся.** Системные — `Relocator._SYSTEM_FOLDERS`, абсолютные пути от `/`. `PermissionError` на папке = отсечь поддерево
- **Обход останавливается, когда найдены все сеты** — иначе `/` обходится целиком

---

## Ошибки

`main()` оборачивает `app()`: ловит `CullenError` из любого сабаппа, печатает в stderr, `sys.exit(1)`. Свои ошибки — только для предвиденных случаев; системные пролетают трейсбеком.

---

## Git

- Semantic commits, GitHub Flow, `master` + ветки, merge только `--no-ff`, PR обязателен
- Ветка = имя файла в `_claude/progress/` без `.md`: `feat/26.09.15.relocate_refactor`
- Релиз делает `semantic-release` по коммитам в `master`, руками версию не трогать
- Автор: `Igor Djachenko <i.s.djachenko@gmail.com>`
