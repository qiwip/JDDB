from pymongo import MongoClient
import DDB


class Query:
    """
    查询J-TEXT破裂数据库的内容
    For example:
    >>> db = Query()   # 默认host='211.67.27.7', port=27071
    >>> db.tag(1046810)
        {'shot': '1046810', 'CqDuration': 0.0, 'CqTime': 0.0, 'IpCq': 0.0, 'IpFlat': 202.8784696689742, 'IsDisrupt': False, 'IsFlatTopDisrupt': False, 'IsRampDownDisrupt': False, 'IsRampUpDisrupt': False, 'IsRunaway': False, 'IsValidShot': True, 'NoData': False, 'RampDownTime': 0.48910004768371573, 'RunawayDuration': 0.0, 'RunawayIp': 0.0, 'TqDuration': 0.0, 'TqTime': 0.0}
    >>> my_query = {'IsDisrupt': True, 'IpFlat':{'$gt':50}}
    >>> db.query(my_query)
        [1046770, 1046794, 1046795, 1046806, 1046800, 1046809, 1046826, 1046828, 1046832, 1046835, 1046858,..., 1049184, 1050467, 1052286, 1050560, 1052295]
    """

    def __init__(self):
        config = DDB.get_config()
        database = config['output']
        self.client = MongoClient(database['host'], int(database['port']))
        self.db = self.client[database['database']]
        self.col = self.db[database['collection']]

    def tag(self, shot):
        """
        :param shot: shot number
        :return: 破裂数据库中的标签,字典类型,没有数据 or 没放起来电返回None
        目前的内容：
            NoData              dtype:Bool        是否有数据
            IsValidShot         dtype:Bool        是否是有效放电
            IsDisrupt           dtype:Bool        是否破裂
            RampDownTime        dtype:float       等离子体电流下降时间
            CqTime              dtype:float       电流淬灭时间
            CqDuration          dtype:float       电流淬灭持续时间
            IpFlat              dtype:float       平顶电流大小
            IsFlatTopDisrupt    dtype:Bool        是否是平顶阶段破裂
            IsRampUpDisrupt     dtype:Bool        是否是上升阶段破裂
            IsRampDownDisrupt   dtype:Bool        是否是下降阶段破裂
            IpCq                dtype:float       破裂时的等离子体电流
            IsRunaway           dtype:Bool        是否出现逃逸
            RunawayDuration     dtype:float       逃逸持续时间
            RunawayIp           dtype:float       逃逸电流大小
            TqTime              dtype:float       电流淬灭时间
            TqDuration          dtype:float       电流淬灭持续时间
        """
        result = self.col.find_one(
            {'shot': shot}, {'_id': 0}
        )

        return result

    def query(self, filter=None):
        """
        按给出的条件查询符合的炮
        :param filter:
                Specify Conditions Using Query Operators:
                    { <field1>: { <operator1>: <value1> }, ... }
                For example:
                    {"IsDisrupt": True, "IpFlat": {"$gt": 100}}
                '$lt'  : <
                '$lte' : <=
                '$gt'  : >
                '$gte' : >=
                '$ne'  : !=
                Specify OR Conditions:
                {"$or": [{"IsDisrupt": True}, {"IpFlat": {"$gt": 100}}]}
                Specify AND Conditions:
                {"IsDisrupt": True, "IpFlat": {"$gt": 100}}
        :return shot number list, dtype:int
        """
        if filter is None:
            filter = {}
        result = self.col.find(
            filter, {'_id': 0}
        )
        shots = []
        for each in result:
            shots.append(int(each['shot']))
        return shots


class Evaluator:
    pass


if __name__ == '__main__':
    db = Query()
    # my_query = {'IsValidShot': True, 'RampDownTime': 0, 'CqTime': 0}
    # my_query = {'RampDownTime': 0, 'CqTime': 0}
    my_query = {'IsValidShot': True}
    shots = db.query(my_query)
    print(shots)
    print(len(shots))
    # tag = db.tag(1059767)
    # print(tag)
