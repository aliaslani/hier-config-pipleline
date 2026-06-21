from pathlib import Path
from hier_config import WorkflowRemediation, get_hconfig, Platform
from hier_config.utils import read_text_from_file


def write_config(config, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for line in config.all_children_sorted():
            f.write(f"{line.cisco_style_text()}\n")


def main(
    running_file,
    generated_file,
    platform=Platform.CISCO_IOS,
):
    running_text = read_text_from_file(running_file)
    generated_text = read_text_from_file(generated_file)

    running = get_hconfig(platform, running_text)
    generated = get_hconfig(platform, generated_text)

    workflow = WorkflowRemediation(running, generated)

    write_config(
        workflow.remediation_config,
        "remediation.txt",
    )

    write_config(
        workflow.rollback_config,
        "rollback.txt",
    )
    remediation_config = workflow.remediation_config
    remediation_lines = (
        remediation_config.all_children_sorted()
    )

    future_config = running.future(remediation_config)

    write_config(
        future_config,
        "future.txt",
    )

    print("Generated:")
    print("  remediation.txt")
    print("  rollback.txt")
    print("  future.txt")


if __name__ == "__main__":
    running_file = (
        input("Running config file path: ").strip()
        or "before.txt"
    )

    generated_file = (
        input("Generated config file path: ").strip()
        or "hardened.txt"
    )

    main(running_file, generated_file)