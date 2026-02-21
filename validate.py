"""Validate the auto_calibrate custom component structure and syntax."""
import ast
import json
import os
import sys

COMPONENT_DIR = "custom_components/auto_calibrate"

REQUIRED_FILES = [
    "__init__.py",
    "config_flow.py",
    "const.py",
    "manifest.json",
    "sensor.py",
    "services.yaml",
    "translations/en.json",
]

errors = []
warnings = []


def check_file_exists(rel_path: str) -> bool:
    full = os.path.join(COMPONENT_DIR, rel_path)
    if not os.path.isfile(full):
        errors.append(f"MISSING: {rel_path}")
        return False
    return True


def check_python_syntax(rel_path: str) -> bool:
    full = os.path.join(COMPONENT_DIR, rel_path)
    try:
        with open(full) as f:
            source = f.read()
        ast.parse(source, filename=rel_path)
        return True
    except SyntaxError as e:
        errors.append(f"SYNTAX ERROR in {rel_path}: {e}")
        return False


def check_json(rel_path: str) -> dict | None:
    full = os.path.join(COMPONENT_DIR, rel_path)
    try:
        with open(full) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"JSON ERROR in {rel_path}: {e}")
        return None


def validate_manifest(data: dict) -> None:
    required_keys = ["domain", "name", "version", "config_flow"]
    for key in required_keys:
        if key not in data:
            errors.append(f"manifest.json missing required key: {key}")
    if data.get("domain") != "auto_calibrate":
        errors.append(f"manifest.json domain should be 'auto_calibrate', got '{data.get('domain')}'")
    if data.get("config_flow") is not True:
        errors.append("manifest.json config_flow should be true")


def validate_translations(data: dict) -> None:
    if "config" not in data:
        errors.append("translations/en.json missing 'config' section")
        return
    config = data["config"]
    if "step" not in config:
        errors.append("translations/en.json missing 'config.step' section")
    if "error" not in config:
        warnings.append("translations/en.json missing 'config.error' section")


def validate_const_exports(rel_path: str) -> None:
    full = os.path.join(COMPONENT_DIR, rel_path)
    with open(full) as f:
        source = f.read()
    required = ["DOMAIN", "CONF_SOURCE_ENTITY"]
    for name in required:
        if name not in source:
            errors.append(f"const.py missing expected constant: {name}")


def validate_init_has_setup(rel_path: str) -> None:
    full = os.path.join(COMPONENT_DIR, rel_path)
    with open(full) as f:
        source = f.read()
    if "async_setup_entry" not in source:
        errors.append("__init__.py missing async_setup_entry")
    if "async_unload_entry" not in source:
        errors.append("__init__.py missing async_unload_entry")


def validate_sensor_class(rel_path: str) -> None:
    full = os.path.join(COMPONENT_DIR, rel_path)
    with open(full) as f:
        source = f.read()
    checks = [
        ("RestoreSensor", "sensor.py should use RestoreSensor for state persistence"),
        ("native_value", "sensor.py should define native_value property"),
        ("extra_state_attributes", "sensor.py should define extra_state_attributes"),
        ("reset_calibration", "sensor.py should have reset_calibration method"),
        ("async_added_to_hass", "sensor.py should implement async_added_to_hass"),
        ("min_raw", "sensor.py should track min_raw"),
        ("max_raw", "sensor.py should track max_raw"),
    ]
    for token, msg in checks:
        if token not in source:
            errors.append(msg)


def main() -> int:
    print("=" * 60)
    print("Auto-Calibrate Sensor Integration Validator")
    print("=" * 60)

    print("\n[1/6] Checking required files...")
    for f in REQUIRED_FILES:
        exists = check_file_exists(f)
        status = "OK" if exists else "MISSING"
        print(f"  {status}: {f}")

    print("\n[2/6] Checking Python syntax...")
    py_files = [f for f in REQUIRED_FILES if f.endswith(".py")]
    for f in py_files:
        if os.path.isfile(os.path.join(COMPONENT_DIR, f)):
            ok = check_python_syntax(f)
            print(f"  {'OK' if ok else 'FAIL'}: {f}")

    print("\n[3/6] Validating manifest.json...")
    manifest = check_json("manifest.json")
    if manifest:
        validate_manifest(manifest)
        print("  OK: manifest.json is valid")

    print("\n[4/6] Validating translations/en.json...")
    translations = check_json("translations/en.json")
    if translations:
        validate_translations(translations)
        print("  OK: translations/en.json is valid")

    print("\n[5/6] Checking const.py exports...")
    if os.path.isfile(os.path.join(COMPONENT_DIR, "const.py")):
        validate_const_exports("const.py")
        print("  OK: const.py has required constants")

    print("\n[6/6] Validating component structure...")
    if os.path.isfile(os.path.join(COMPONENT_DIR, "__init__.py")):
        validate_init_has_setup("__init__.py")
        print("  OK: __init__.py structure")
    if os.path.isfile(os.path.join(COMPONENT_DIR, "sensor.py")):
        validate_sensor_class("sensor.py")
        print("  OK: sensor.py structure")

    print("\n" + "=" * 60)
    if errors:
        print(f"RESULT: {len(errors)} error(s) found\n")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1
    elif warnings:
        print(f"RESULT: All checks passed with {len(warnings)} warning(s)\n")
        for w in warnings:
            print(f"  WARN: {w}")
        return 0
    else:
        print("RESULT: All checks passed! Integration is structurally valid.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
