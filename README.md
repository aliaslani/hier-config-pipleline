````markdown
# Network Configuration Remediation Generator

A Python utility that automatically compares **non-hardened** and **hardened** network device configurations using the `hier_config` library and generates:

- **Remediation configuration** (commands required to harden the device)
- **Rollback configuration** (commands to revert the remediation)
- **Future configuration** (expected configuration after remediation)

The tool is designed to process multiple network platforms in a single run by organizing configuration files into platform-specific directories.

---

# Features

- Automatically discovers configuration pairs.
- Supports multiple network platforms supported by `hier_config`.
- Performs exact and fuzzy filename matching.
- Generates:
  - `remediation.txt`
  - `rollback.txt`
  - `future.txt`
- Copies the original configuration files into the output directory for traceability.
- Processes an entire directory tree in one execution.
- Reports unmatched configuration files.
- Handles duplicate and merge errors gracefully.

---

# Requirements

- Python 3.10+
- `hier_config`

Install dependencies:

```bash
pip install hier-config
```

---

# Directory Layout

The input directory must contain one subdirectory per platform.

Example:

```
running_config/
├── CISCO_IOS/
│   ├── router1_nonhardened.txt
│   ├── router1_hardened.txt
│   ├── router2_non-hardened.cfg
│   └── router2_harden.cfg
│
├── CISCO_XR/
│   ├── xr1_nonhardened.txt
│   └── xr1_hardened.txt
│
└── ARISTA_EOS/
    ├── leaf1_nonhardened.txt
    └── leaf1_hardened.txt
```

Each platform directory name should correspond to one of the platforms supported by `hier_config`.

---

# Supported Filename Patterns

The script recognizes several naming conventions.

## Non-hardened

Examples:

```
router_nonhardened.txt
router_non-hardened.txt
router_non_hardened.txt
router_non harden.txt
router_nonharden.cfg
```

## Hardened

Examples:

```
router_hardened.txt
router_harden.txt
router-hardened.cfg
```

The matching is case-insensitive.

---

# Pair Matching

The script first attempts an **exact filename match** after removing the
`hardened` / `nonhardened` keywords.

Example:

```
router1_nonhardened.txt
router1_hardened.txt
```

Both normalize to:

```
router1
```

If no exact match exists, the script performs **fuzzy matching** using Python's `SequenceMatcher`.

If the similarity score is at least **0.60**, the pair will be processed and a warning will be displayed.

Example output:

```
(fuzzy match, confidence=0.81 - verify this pairing)
```

---

# Output Structure

For every matched pair, the script creates a directory under the output folder.

Example:

```
output/
└── CISCO_IOS/
    └── router1_nonhardened/
        ├── router1_nonhardened.txt
        ├── router1_hardened.txt
        ├── remediation.txt
        ├── rollback.txt
        └── future.txt
```

The original configuration files are copied into the output directory for reference.

---

# Generated Files

## remediation.txt

Commands required to convert the running configuration into the hardened configuration.

---

## rollback.txt

Commands required to undo the remediation.

---

## future.txt

Expected configuration after remediation.

Normally this is produced using:

```python
running.future(remediation)
```

If the merge fails because of duplicate configuration nodes, the script automatically falls back to using the hardened configuration as the future-state approximation.

---

# Usage

Default usage:

```bash
python generate_remediation.py
```

This assumes:

```
running_config/
```

as the input directory and writes output to

```
output/
```

---

## Custom input directory

```bash
python generate_remediation.py \
    --configs-dir configs
```

---

## Custom output directory

```bash
python generate_remediation.py \
    --output-dir generated
```

---

## Specify a default platform

If a platform directory name cannot be mapped to a known `hier_config.Platform`,
the script falls back to a default platform.

Example:

```bash
python generate_remediation.py \
    --default-platform cisco_ios
```

Available values depend on the installed version of `hier_config`.

---

# Command-Line Options

| Option | Description |
|---------|-------------|
| `--configs-dir` | Input directory containing platform subdirectories. |
| `--output-dir` | Output directory. |
| `--default-platform` | Fallback `hier_config` platform if directory name cannot be mapped. |

---

# Example

Input:

```
running_config/
└── CISCO_IOS/
    ├── branch1_nonhardened.txt
    └── branch1_hardened.txt
```

Run:

```bash
python generate_remediation.py
```

Output:

```
=== CISCO_IOS -> Platform.CISCO_IOS ===

Found 1 pair(s).

Processing pair -> branch1_nonhardened/

Generated:
    remediation.txt
    rollback.txt
    future.txt

Done.
1 succeeded, 0 failed, 0 unmatched.
```

---

# Platform Resolution

Each platform directory name is mapped to a `hier_config.Platform`.

Examples:

```
CISCO_IOS
cisco-ios
Cisco IOS
CISCO_IOSXE
```

Normalization ignores:

- case
- spaces
- hyphens
- underscores

If no platform matches, a warning is printed and the default platform is used.

---

# Error Handling

The script reports:

- duplicate filenames
- unmatched configuration files
- fuzzy filename matches
- write failures
- merge failures
- processing exceptions

A non-zero exit code is returned if any pair fails to process.

---

# Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| `0` | All configuration pairs processed successfully. |
| `1` | One or more errors occurred or no valid input was found. |

---

# Notes

- The script processes only the **immediate** subdirectories under the input directory.
- Files that do not contain either `hardened` or `nonhardened` in their names are skipped.
- Filename matching is case-insensitive.
- Original configuration files are preserved in the output directory.
- Fuzzy matches should always be reviewed manually before use in production.

---

# Example Directory Tree

```
running_config/
├── CISCO_IOS/
│   ├── router1_nonhardened.txt
│   ├── router1_hardened.txt
│   ├── router2_non_hardened.cfg
│   └── router2_harden.cfg
│
├── CISCO_XR/
│   ├── edge1_nonhardened.txt
│   └── edge1_hardened.txt
│
└── ARISTA_EOS/
    ├── leaf01_nonhardened.txt
    └── leaf01_hardened.txt
```

Output:

```
output/
├── CISCO_IOS/
│   ├── router1_nonhardened/
│   └── router2_non_hardened/
│
├── CISCO_XR/
│   └── edge1_nonhardened/
│
└── ARISTA_EOS/
    └── leaf01_nonhardened/
```

---

# License

This project is provided as-is for automating network configuration remediation workflows using the `hier_config` library.
````


