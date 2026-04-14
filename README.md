
---

# 📦 IMPPAT 2.0 Bulk Downloader

A Python command-line tool to **retrieve, filter, view, and download phytochemicals** from the IMPPAT 2.0 database.

This script enables:

* 📦 **Bulk download of compounds (with optional filtering)**
* 🔍 **Single compound retrieval**
* 📊 **Physicochemical property inspection (CLI)**
* 📁 **Structure download in docking-ready formats (PDBQT/SDF)**

It is designed for **computational drug discovery workflows**, especially for preparing ligand datasets for docking and simulation studies.

---

## 🚀 Features

* 🔍 Retrieve compounds using **plant species** or **IMPHY ID**
* ⚗️ Apply **drug-likeness filtering (Lipinski and Veber rules)**
* 📊 View **physicochemical properties** directly in terminal
* 📁 Download structures in:

  * `pdbqt` (default, docking-ready)
  * `sdf`
* 🔁 Automatically **skips already downloaded files**
* 📦 Supports **bulk download with filtering**
* ⏱ Adjustable request delay for stable execution

---

## 📥 Installation

### Requirements

* Python 3.x

### Install dependencies

```bash
pip install requests beautifulsoup4
```

---

## ▶️ Running the Script

Run the script using Python:

```bash
python imppat_downloader.py [OPTIONS]
```

> ❗ No need for `chmod +x` — the script is executed directly with Python.

---

## 📌 Modes of Operation

The script works in **two mutually exclusive modes**:

---

### 🔹 1. Bulk Mode (Plant-Based)

Fetch all phytochemicals associated with a plant.

```bash
python imppat_downloader.py --plant "Ocimum tenuiflorum"
```

✔ Processes all compounds
✔ Supports filtering, property viewing, and downloading

---

### 🔹 2. Single Compound Mode

Fetch or inspect a specific compound using its IMPHY ID.

```bash
python imppat_downloader.py --id IMPHY011396
```

---

## 🔧 Command-Line Options

---

### 🔹 `--plant "NAME"`

* Specifies plant species for bulk extraction
* Enables **bulk download and filtering**

📁 Output folder:

```
IMPPAT_<plant_name>/
```

---

### 🔹 `--id IMPHY_ID`

* Specifies a single compound
* Used for targeted retrieval

📁 Output folder:

```
IMPPAT_OUTPUT/
```

---

### 🔹 `--show physchem`

Displays **physicochemical properties only** in terminal.

Includes:

* Molecular weight
* LogP
* Hydrogen bond donors/acceptors
* Other molecular descriptors

Example:

```bash
--show physchem
```

✔ Works in both bulk and single modes
❗ Properties are **displayed only (not saved to files)**

---

### 🔹 `--filter [RULES]` *(Bulk Mode Only)*

Filters compounds using drug-likeness rules:

* `lipinski`
* `veber`

Example:

```bash
--filter lipinski veber
```

✔ Only compounds passing **all selected rules** are processed

---

### 🔹 `--format [FORMATS]`

Specifies structure format(s) to download:

* `pdbqt` (default)
* `sdf`

Examples:

```bash
--format sdf
--format pdbqt sdf
```

---

### 🔹 `--no-download`

Disables file download.

Used when you only want to **view properties**.

```bash
--no-download
```

---

### 🔹 `--delay SECONDS`

Controls delay between requests (default: 0.5 seconds):

```bash
--delay 1.0
```

✔ Helps maintain stable execution for large datasets

---

## 📚 Usage Examples

---

### 🔹 1. Basic Bulk Download

```bash
python imppat_downloader.py --plant "Ocimum tenuiflorum"
```

✔ Downloads all compounds in **PDBQT format**

---

### 🔹 2. Bulk Download with Filtering

```bash
python imppat_downloader.py \
--plant "Ocimum tenuiflorum" \
--filter lipinski
```

---

### 🔹 3. Filter + Multiple Formats

```bash
python imppat_downloader.py \
--plant "Ocimum tenuiflorum" \
--filter lipinski veber \
--format pdbqt sdf
```

---

### 🔹 4. Bulk Property Viewing (No Download)

```bash
python imppat_downloader.py \
--plant "Ocimum tenuiflorum" \
--show physchem \
--no-download
```

✔ Displays properties for all compounds
✔ No files are downloaded

---

### 🔹 5. Combined Workflow (Recommended)

```bash
python imppat_downloader.py \
--plant "Ocimum tenuiflorum" \
--filter lipinski veber \
--show physchem \
--format pdbqt sdf \
--delay 0.5
```

✔ Filters + displays + downloads in one run

---

### 🔹 6. Single Compound – View Properties (No Download)

```bash
python imppat_downloader.py \
--id IMPHY011396 \
--show physchem \
--no-download
```

✔ Displays physicochemical properties
✔ ❗ Prevents structure download

---

### 🔹 7. Single Compound – Download

```bash
python imppat_downloader.py --id IMPHY011396
```

✔ Downloads structure in default format

---

### 🔹 8. Single Compound – View + Download

```bash
python imppat_downloader.py \
--id IMPHY011396 \
--show physchem \
--format sdf
```

✔ Shows properties
✔ Downloads structure

---

## 📂 Output Structure

### Bulk Mode

```
IMPPAT_<plant_name>/
    IMPHYXXXXX.pdbqt
    IMPHYXXXXX.sdf
```

---

### Single Compound Mode

```
IMPPAT_OUTPUT/
    IMPHYXXXXX.pdbqt
```

---

## 📊 Execution Behavior

During execution, the script:

* Displays progress for each compound
* Indicates:

  * ✔ Successful downloads
  * ❌ Missing files (not available on server)
  * 🔁 Skipped files (already downloaded)
  * ⚠️ Filtered-out compounds

---

## ⚠️ Important Notes

* Only **physicochemical properties** are supported for display
* Properties are **view-only (CLI)** — not saved to files
* If `--no-download` is not used, files will be downloaded by default
* Duplicate downloads are automatically avoided
* Some compounds may not have structure files (normal behavior)
* Filtering works only with **Lipinski and Veber rules**

---

## 🧪 Recommended Workflow (CADD)

1. Apply filtering:

   ```bash
   --filter lipinski veber
   ```
2. Download structures:

   ```bash
   --format pdbqt
   ```
3. Use in docking tools (AutoDock, Vina, etc.)

---

## 📜 License

For academic and research use.
Please cite the IMPPAT database where applicable.

---

