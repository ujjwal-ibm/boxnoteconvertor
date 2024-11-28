# BoxNote to docx Converter

A Python command-line tool to convert Box Notes to Microsoft Word (docx) documents with preservation of formatting, tables, and images.

## Features

- Convert single BoxNote files to docx
- Batch convert entire directories of BoxNote files
- Preserve formatting, tables, and images
- Support for Box API authentication
- Simple command-line interface

## Installation

```bash

pip3 install .
```

## Usage

### Basic Usage

Convert a single file:
```bash
boxtodocx example.boxnote
```

Convert all files in a directory:
```bash
boxtodocx /path/to/directory
```

### Advanced Options

```bash
boxtodocx --help

Options:
  -d, --dir TEXT     Work directory for temporary files
  -t, --token TEXT   Box access token
  -o, --output TEXT  Output file name (only for single file conversion)
  -u, --user TEXT    Box user id
  -v, --verbose      Enable verbose logging
  --help            Show this message and exit
```

## Authentication

To use Box API features (like image downloading), you need to provide a Box access token:

```bash
boxtodocx input.boxnote -t "your_box_token" -u "your_user_id"
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.