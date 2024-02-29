import yaml


class Config(object):
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        with open(self.config_file) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

    def update_config(self, key, value):
        self.config[key] = value
        with open(self.config_file, "w") as f:
            yaml.dump(self.config, f, allow_unicode=True)


global_config = Config().config
