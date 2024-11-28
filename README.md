# boxnoteconvertor
A tool to convert boxnotes to docx(for now)


### **Getting Started with `boxtodocx`**

set up the core tool—`boxtodocx`. Follow these steps:

#### **1. Clone the Repository**
```bash
git clone https://github.com/ujjwal-ibm/boxnoteconvertor.git
```

#### **2. Navigate to the Tool Directory**
```bash
cd boxnoteconvertor/boxtodocx
```

#### **3. Install the Tool**
Install the package using Python’s package manager:
```bash
pip3 install .
```

#### **4. Verify Installation**
You can now use the command-line tool:
```bash
boxnotetodocx --help
```

#### **5. Conversion Examples**
- **Single File Conversion**:
  ```bash
  boxnotetodocx example.boxnote
  ```
- **Batch Conversion for a Directory**:
  ```bash
  boxnotetodocx /path/to/directory
  ```