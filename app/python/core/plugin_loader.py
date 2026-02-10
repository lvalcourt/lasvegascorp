import importlib.util
import json
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parents[1] / "plugins"


def list_plugins():
    plugins = []
    for manifest in PLUGIN_DIR.rglob("manifest.json"):
        data = json.loads(manifest.read_text())
        data["path"] = str(manifest.parent)
        plugins.append(data)
    return plugins


def load_plugin(entry: str, base_path: Path):
    # entry format: "module:callable"
    mod_name, func_name = entry.split(":", 1)
    module_path = base_path / f"{mod_name}.py"
    spec = importlib.util.spec_from_file_location(mod_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return getattr(module, func_name)
