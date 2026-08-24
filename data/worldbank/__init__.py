import json
from pathlib import Path


with (Path(__file__).parent / "config.json").open(encoding="utf-8") as config_file:
    _config = json.load(config_file)


request = _config["request"]
method = request["method"]
payload = request["payload"]
data_path = _config["response"]["data_path"]