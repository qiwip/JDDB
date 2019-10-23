import os
from DDB.Label import TaskRunner


if __name__ == '__main__':
    config_path = os.path.abspath('.') + os.sep + 'DDB' + os.sep + 'config.json'
    tr = TaskRunner(config_path)
    tr.run()
