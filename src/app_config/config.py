from configparser import ConfigParser


def main():
    config_parser: ConfigParser = ConfigParser()
    config_parser.read("app_config.ini.bak")
    print(config_parser)
    print(config_parser.items())
    for item in config_parser.items():
        print(item)


if __name__ == "__main__":
    main()
