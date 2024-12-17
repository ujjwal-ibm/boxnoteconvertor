# BoxToDocx

A Python command-line tool to convert Box Notes to HTML and Microsoft Word (docx) documents while preserving formatting, tables, and images.

## Features

- Convert Box documents to HTML and DOCX formats
- Support for images, tables, and formatted text
- Batch processing of multiple documents
- Optional image downloading with Box authentication or API token
- Choice to generate HTML and images in separate folder
- Comprehensive logging

## Installation

```bash
pip3 install boxtodocx
```

## Usage

### Basic Conversion
```bash
boxtodocx input.boxnote -d output_directory
```

### With Image Export (Using Credentials)
```bash
boxtodocx input.boxnote -d output_directory --export-images \
    --box-id your@email.com \
    --box-pwd yourpassword \
    --link login-link-id \
    --id user-field-id \
    --pwd password-field-id
```

### With Image Export (Using API Token)
```bash
boxtodocx input.boxnote -d output_directory --export-images --api-token YOUR_API_TOKEN
```

### Process Directory
```bash
boxtodocx directory_path --directory -d output_directory
```

### Generate HTML and Images
```bash
boxtodocx input.boxnote -d output_directory --generate-html
```

### Available Options
```
Options:
  --generate-html      Generate HTML and save images in separate folder
  --api-token TEXT     Box API token for direct download
  --directory          Process all Box documents in a directory
  --mfa-otp TEXT       MFA code (one-time password)
  --mfa-btn-id TEXT    ID of button to submit MFA code
  --mfa-otp-id TEXT    ID of input field for MFA code
  --mfa-link TEXT      Div ID to click for MFA
  --pwd TEXT           Password field for Box login
  --id TEXT            User ID field for Box login
  --link TEXT          Div ID for additional login step
  --box-pwd TEXT       Box login password
  --box-id TEXT        Box login email
  --export-images      Export images from Box documents
  -d, --dest-dir PATH  Destination directory for output files
  --help               Show this message and exit
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.