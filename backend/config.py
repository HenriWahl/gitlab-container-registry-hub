from argparse import ArgumentParser
from pathlib import Path

from munch import munchify
from yaml import safe_load
from yaml.scanner import ScannerError


# for now all requested URLs start with this suffix
API_SUFFIX = '/api/v4'
TIMEOUT = 60

def load_config(args):
    """
    load YAML config file
    """
    if Path(args.config_file).exists and \
            Path(args.config_file).is_file():
        with open(args.config_file) as config_file:
            try:
                # make config.option.suboption.key-notation of YAML
                config = munchify(safe_load(config_file))
            except ScannerError:
                exit(f"'{args.config_file}' is not valid config file")
    else:
        exit(f"'{args.config_file}' does not exist or is no file")

    # add commandline arguments
    for key, value in args.__dict__.items():
        if not key in config.__dict__.keys():
            config[key] = value
    return config


parser = ArgumentParser()
parser.add_argument('-c', '--config-file', type=str, required=True)
parser.add_argument('--load-data', action='store_true', default=False, required=False)
parser.add_argument('--dump-data', action='store_true', default=False, required=False)
parser.add_argument('--update-interval', type=int, default=1800, required=False)

config = load_config(parser.parse_args())


