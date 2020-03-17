from DDB.Label import TaskRunner
import configparser
import os


def get_config():
    config = configparser.ConfigParser()
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'config.ini')):
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    else:
        print('Can\'t find config file, use default.')
        config['plugins'] = {'IP': 'DDB.Plugins.VP'}
        config['shot'] = {'start': 1064034, 'end': 1066648}
        config['path'] = {'hdf5': 'HDF5'}
        config['output'] = {
            'type': 'mongodb',
            'host': '127.0.0.1',
            'port': 27017,
            'username': 'DDBUser',
            'password': 'tokamak!',
            'database': 'DDB',
            'collection': 'tags'
        }

        with open(os.path.join(os.path.dirname(__file__), 'config.ini'), 'w') as configfile:
            config.write(configfile)
    return config


if __name__ == '__main__':
    get_config()
