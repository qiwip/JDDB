import DDB
from pymongo import MongoClient
from DDB.Service import Query
from DDB.Data import Reader
import random
from scipy import signal


ddb = Query()
my_query = {'IsValidShot': True, 'IsDisrupt': False}
shots = ddb.query(my_query)
my_query = {'IsValidShot': True, 'IsDisrupt': True, 'CqTime': {"$gte": 0.05}, 'IpFlat': {'$gte': 110}}
shots += ddb.query(my_query)
config = DDB.get_config()
database = config['output']
client = MongoClient(database['host'], int(database['port']))
db = client[database['database']]
param = db[database['collection']+'归一化参数']

tags = [r'\Bt', r'\Ihfp', r'\Ivfp', r'\MA_POL_CA01T', r'\MA_POL_CA02T', r'\MA_POL_CA03T', r'\MA_POL_CA05T', r'\MA_POL_CA06T', r'\MA_POL_CA07T', r'\MA_POL_CA19T', r'\MA_POL_CA20T', r'\MA_POL_CA21T', r'\MA_POL_CA22T', r'\MA_POL_CA23T', r'\MA_POL_CA24T', r'\axuv_ca_01', r'\ip', r'\sxr_cb_024', r'\sxr_cc_049', r'\vs_c3_aa001', r'\vs_ha_aa001']
reader = Reader(root_path='/nas/hdf5_new')
result = dict()
for tag in tags:
    result = {'max': None, 'min': None}
    sample = random.sample(shots, 50)
    for shot in sample:
        try:
            dig, time = reader.read_one(shot, tag)
            # 低通滤波
            ba = signal.butter(8, 0.04, 'lowpass')
            ip_ = signal.filtfilt(ba[0], ba[1], dig)
            # 中值滤波
            dig = signal.medfilt(dig, 15)
            info = ddb.tag(shot)
            if info['IsDisrupt']:
                t1 = info['CqTime']
            else:
                t1 = info['RampDownTime']
            dig = dig[(0.05 <= time) & (time <= t1)]
            if result['max'] is None:
                result['max'] = max(dig)
                result['min'] = min(dig)
            if result['max'] < max(dig):
                result['max'] = max(dig)
            if result['min'] > min(dig):
                result['min'] = min(dig)
        except Exception as e:
            print(e)
    param.update_one(
                {"tag": tag},
                {"$set": result},
                upsert=True
            )
    print(tag, result)
