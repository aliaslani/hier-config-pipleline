Here is a clean, professional `README.md` tailored for your script, written for real-world usage, DevOps workflows, and GitHub presentation:

---

````markdown
# Network Configuration Remediation Tool (Hier Config)

This project uses the Python `hier-config` library to generate **remediation, rollback, and future-state configurations** by comparing a running network configuration with a desired (generated/hardened) configuration.

It is designed for network automation workflows involving Cisco IOS devices, but can be extended to other platforms supported by `hier-config`.

---

## 🚀 Features

- Generates **remediation configuration** (commands needed to reach desired state)
- Generates **rollback configuration** (undo changes safely)
- Produces **future state configuration** (final expected running config)
- Supports Cisco IOS (default) and other Hier Config platforms
- Outputs clean, sorted Cisco-style configuration files
- Simple CLI input-based workflow

---

## 📦 Requirements

- Python 3.9+
- `hier-config >= 3.6.0`

Install dependency:

```bash
pip install hier-config
````

---

## 📁 Input Files

You need two configuration files:

### 1. Running configuration

Current device configuration:

```
before.txt
```

### 2. Generated / Desired configuration

Target hardened or intended configuration:

```
hardened.txt
```

---

## ⚙️ How It Works

The script performs the following steps:

1. Reads running and desired configuration files
2. Parses them using `hier-config`
3. Compares both configurations
4. Generates:

   * Remediation commands
   * Rollback commands
   * Future (final) configuration
5. Writes results into output files

---

## ▶️ Usage

Run the script:

```bash
python main.py
```

You will be prompted:

```
Running config file path:
Generated config file path:
```

Press Enter to use defaults:

* `before.txt`
* `hardened.txt`

---

## 📤 Output Files

After execution, three files will be generated:

### 1. remediation.txt

Commands required to transform the running config into the desired state.

### 2. rollback.txt

Commands to revert remediation changes.

### 3. future.txt

Final expected configuration after remediation is applied.

---

## 🧠 Example Workflow

```text
before.txt   → Current device config
hardened.txt → Desired secure config

            ↓

remediation.txt → Apply changes
rollback.txt    → Undo changes
future.txt      → Final state
```

---

## 🛠️ Configuration

Default platform is:

```python
Platform.CISCO_IOS
```

You can change it in code:

```python
main(running_file, generated_file, platform=Platform.CISCO_IOS)
```

Supported platforms include:

* CISCO_IOS
* CISCO_NXOS
* CISCO_IOSXR
* ARISTA_EOS
* JUNIPER_JUNOS

---

## 📌 Notes

* Ensure configuration files are valid CLI-style configs
* Output is sorted using `all_children_sorted()`
* Encoding is UTF-8 for compatibility with all Cisco-style text
* Designed for automation pipelines and CI/CD network validation

---

## 🧪 Example Use Case

* Network hardening validation
* Configuration drift detection
* Pre/post change validation
* Backup vs intended state reconciliation
* GitOps-style network automation workflows

---

## 📚 Powered By

* [hier-config](https://github.com/netdevops/hier_config)

---

## 📄 License

This project is intended for educational and automation use.


---

## ✍️ Author

Network Automation Script using Python + Hier Config

```

