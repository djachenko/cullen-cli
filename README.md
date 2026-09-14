# cullen-cli

Applies photo culling decisions made in the Cullen iOS app to the source files on disk.

## Commands

```
cullen cull [PATHS...] [--file culled.json]   # sort sources into category folders
cullen flop PATH [FILE] [--dry-run]           # move category folders back up
cullen relocate PATH [ROOT]                   # find exported decision files and put them into their photosets
```

## `culled.json`

The contract between the app and the CLI. Lives in the photoset root.

```json
{
  "name": "26.03.22.fen_init_lab",
  "decisions": {
    "good": ["ZSC_2541", "ZSC_2542"],
    "bad": ["ZSC_2543"]
  }
}
```

Categories are arbitrary keys; values are file stems. Every file whose stem is listed moves into the folder named after its category, next to where it was found.
