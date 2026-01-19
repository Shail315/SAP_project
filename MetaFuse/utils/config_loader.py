import yaml

def load_config():
    with open("configs/config.yaml") as f:
        return yaml.safe_load(f)
