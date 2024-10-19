# Extract-Google-Takeout-Contents
A script that extracts the contents of Google Takeout data preserving folder structure.

# Synopsis

```bash
python3 extract --source /path/to/source/folder --destination /path/to/output/folder
```

When executed, the contents of the source folder and all its chunked archives should be extracted to 
the destination folder with the folder structure preserved

# Tests

```bash
python3 test.py
```