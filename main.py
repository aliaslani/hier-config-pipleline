from pathlib import Path
from hier_config import WorkflowRemediation, get_hconfig, Platform
from hier_config.utils import read_text_from_file


def write_config(config, filename):
    """Write configuration to a file in Cisco-style format.
    
    Args:
        config: The configuration object to write
        filename: Path to the output file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for line in config.all_children_sorted():
                f.write(f"{line.cisco_style_text()}\n")
        return True
    except IOError as e:
        print(f"Error writing to {filename}: {e}")
        return False


def main(
    running_file,
    generated_file,
    platform=Platform.CISCO_IOS,
):
    """Main function for workflow remediation.
    
    Args:
        running_file: Path to the running configuration file
        generated_file: Path to the generated/hardened configuration file
        platform: Platform type (default: CISCO_IOS)
        
    Returns:
        dict: Status information about the operation
    """
    # Validate input files exist
    if not Path(running_file).exists():
        print(f"Error: Running config file '{running_file}' does not exist")
        return {"success": False, "error": f"Running config file not found: {running_file}"}
    
    if not Path(generated_file).exists():
        print(f"Error: Generated config file '{generated_file}' does not exist")
        return {"success": False, "error": f"Generated config file not found: {generated_file}"}

    try:
        running_text = read_text_from_file(running_file)
        generated_text = read_text_from_file(generated_file)

        running = get_hconfig(platform, running_text)
        generated = get_hconfig(platform, generated_text)

        workflow = WorkflowRemediation(running, generated)

        # Write remediation config
        if not write_config(
            workflow.remediation_config,
            "remediation.txt",
        ):
            return {"success": False, "error": "Failed to write remediation.txt"}

        # Write rollback config
        if not write_config(
            workflow.rollback_config,
            "rollback.txt",
        ):
            return {"success": False, "error": "Failed to write rollback.txt"}

        # Generate future config
        remediation_config = workflow.remediation_config
        remediation_lines = (
            remediation_config.all_children_sorted()
        )

        future_config = running.future(remediation_config)

        if not write_config(
            future_config,
            "future.txt",
        ):
            return {"success": False, "error": "Failed to write future.txt"}

        print("Generated:")
        print("  remediation.txt")
        print("  rollback.txt")
        print("  future.txt")
        
        return {
            "success": True,
            "files_generated": ["remediation.txt", "rollback.txt", "future.txt"]
        }

    except Exception as e:
        print(f"Error processing configurations: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    running_file = (
        input("Running config file path: ").strip()
        or "before.txt"
    )

    generated_file = (
        input("Generated config file path: ").strip()
        or "hardened.txt"
    )

    result = main(running_file, generated_file)
    
    if not result["success"]:
        print(f"\nOperation failed: {result.get('error', 'Unknown error')}")
        exit(1)
