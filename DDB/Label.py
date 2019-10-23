import os
import json
import time
import logging
import importlib
import traceback
from DDB.Data import Reader


class GeneratorBase(object):
    """ The most base type """

    # def __init__(self):  # known special case of object.__init__
    #     """ Initialize self.  See help(type(self)) for accurate signature. """
    #     pass
    def requested_signal(self):
        """ Return list of tag of signals that processor need
        example:
            return ['IP', 'OH']
        """
        raise NotImplementedError('requested_signal')

    def run(self, data):
        """
        return tags of one shot
        example:
            result = {
                'NoData': False,        # 是否有数据
                'IsValidShot': True,    # 是否是有效放电
                'IsDisrupt': False,     # 是否破裂
                'RampDownTime': 0.0,    # 等离子体电流下降时间
                'CqTime': 0.0,          # 电流淬灭时间
                'CqDuration': 0.0,      # 电流淬灭持续时间
                'IpFlat': 0.0,          # 平顶电流大小
                'IsFlatTopDisrupt': False,      # 是否是平顶阶段破裂
                'IsRampUpDisrupt': False,       # 是否是上升阶段破裂
                'IsRampDownDisrupt': False,     # 是否是下降阶段破裂
                'IpCq': 0.0,            # 破裂时的等离子体电流
                'IsRunaway': False,     # 是否出现逃逸
                'RunawayDuration': 0.0, # 逃逸持续时间
                'RunawayIp': 0.0        # 逃逸电流大小
            }
            return result

        :param data
         format:
            data={
                'tag1':numpy.array([<signal>], [<time>]),
                'tag2':numpy.array([<signal>], [<time>]),
                'tag3':numpy.array([<signal>], [<time>]),
                ......
                }
        """
        raise NotImplementedError('run')


class TaskRunner:
    """
        TaskRunner
        example:
            tr = TaskRunner()
            tr.add(Instance1())
            tr.add(Instance2())
            ......
            tr.run(<shot list>, "MongoDB")

        """

    def __init__(self, config_path):
        """
        从配置文件中初始化TaskRunner
        :param config_path: json or dict
        """
        log_dir = os.path.abspath('.') + os.sep + 'log'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 创建handler，用于写入日志文件和控制台
        fh = logging.FileHandler(log_dir + os.sep + 'TaskRunner_log_{}.txt'.format(
            time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))))
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(filename)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        # load config
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                plugins = config['plugins']
                self.plugins = {}
                for plugin in plugins:
                    plugin_name, plugin_path = plugin.popitem()
                    self.plugins[plugin_name] = importlib.import_module(plugin_path).Generator()
                if len(config['shot']) == 2:
                    self.shots = range(config['shot'][0], config['shot'][1])
                else:
                    self.shots = config['shot']
                self.hdf5_path = config['hdf5']
                self.database = config['database']
        except FileNotFoundError as e:
            self.logger.info('{}'.format(e))
        except Exception as e:
            self.logger.info('配置文件{}格式错误,{}'.format(config_path, e))
        else:
            self.logger.info('Load config success')

    def run(self):
        reader = Reader(self.hdf5_path)
        for plugin in self.plugins.values():
            signals = plugin.requested_signal()
            for shot in self.shots:
                try:
                    data = reader.read_many(shot=shot, tags=signals)
                    result = plugin.run(data)
                except Exception as e:
                    self.logger.info('An error occurs in module {} @shot {}.\n{}\n{}'.format(
                        plugin.__class__.__name__, shot, e, traceback.format_exc()))
                    result = {}
                if self.database['type'] == "mongodb":
                    from pymongo import MongoClient
                    client = MongoClient(self.database['host'], self.database['port'])
                    db = client[self.database['database']]
                    col = db[self.database['collection']]
                    result['shot'] = shot
                    col.update_one(
                        {"shot": shot},
                        {"$set": result},
                        upsert=True
                    )
                elif self.database['type'] == "stdio":
                    print(result)
                else:
                    raise RuntimeError('配置文件db选项不正确,可选为:mongodb,stdio')