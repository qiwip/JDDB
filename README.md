# 破裂数据库(Disruption database)说明

## 包结构

```c
DDB
└─── Data
|    └── Exporter
|    └── Reader
|
└─── Label
|    └── GeneratorBase
|    └── TaskRunner
|
└─── Severvice
     └── Query
     └── Evaluater

```

* Data模块提供将数据存入hdf5文件和从hdf5读取诊断数据的API,实现数据的统一化存储.
* Label模块提供为炮打标签的功能,用户可以继承GeneratorBase,实现其中的requested_signal和run方法,requested_signal获得该Generator计算所需数据的tag,run方法计算并返回标签信息.TaskRunner可以自动调用这些Generator,为其准备所需数据并调用其run方法得到返回值后将结果存入MongoDB.
* Service提供用户接口.Query可以指定条件查询炮的标签；Evaluater可以在破裂预测时对结果进行评估.

> 程序包中还包含了J-TEXT读取数据的程序`JtextDataImporter.py`

## Label

### 1. GeneratorBase

各种生成标签插件的基类,定义了两个接口:

```python
def requested_signal():
    raise NotImplementedError('requested_signal')

def run(data):
    raise NotImplementedError('run')
```
在实现自己的计算逻辑时,在DDB/Plugins/目录下增加python源文件,实现自己的计算类Generator,继承GeneratorBase类,同时实现这两个接口.requested_signal返回计算逻辑需要用到的诊断标签.在run里面写计算逻辑,返回一个字典类型的结果,key是标签,value是标签值.data为传入参数,字典类型,key为诊断的tag,value为一个元组,类型为numpy数组：(诊断,时间).

例子：
/DDB/Plugins/Generator1.py
```python
from DDB.Label import GeneratorBase


class Generator(GeneratorBase):

    def __init__(self):
        pass

    def requested_signal(self):
        return [r'\ip']

    def run(self, data):
        result = {
            'IsValidShot': True,  # 是否是有效放电
        }
        ip, time = data[r'\ip']
        if max(ip) < 80:
            result['IsValidShot'] = False
        return result
```
### 2. TaskRunner

自动调用各种生成标签的插件去生成一些标签.以前是通过在程序里```add(插件类())```的方式添加,现在改为配置文件配置.

```bash
[plugins]
ip = DDB.Plugins.IPGenerator

[shot]
start = 1064034
end = 1064648

[path]
hdf5 = D:\jtext\HDF5

[output]
type = mongodb
host = www.jtext.cn
port = 14617
database = DDB
collection = tags2019

```

在初始化的时候,读取配置文件,再import配置里面plugins里的包名,调用其接口进行计算.该类调用计算类的requested_signal获取所需诊断,使用Data类的接口读取数据之后,调用计算类的run计算.
得到的结果显示方式在配置文件里配置,[output]的type=stdio时直接打印到标准输入输出,为mongodb时存储到mongodb,mongodb的参数在配置文件中指定.

## Data

### 1.Exporter
该类用于将诊断写入hdf5,初始化参数是hdf5存放的根目录.提供一个借口save(data, time, shot, tag)
例子:
```python
from DDB.Data import Exporter
exporter = Exporter(root_path='D:\\J-TEXT')
data = [0.1, 0.5, 0.3, 0.4, 0.2]
time = [0, 0.1, 0.2, 0.3, 0.4]
exporter.save(data, time, 1051234, '\\ip')
```
### 2.Reader
该类用于读取诊断,初始化参数是hdf5存放的根目录.
接口:
* tags(shot): 返回一炮所有已有数据的tag 
* read_one(shot, tag): 读取一个诊断
* read_many(shot, tags): 读取多个诊断

例子:
```python
from DDB.Data import Reader
reader = Reader(root_path='D:\\J-TEXT')
data = reader.read_one(1054173, '\\ip')
import matplotlib.pyplot as plt
plt.plot(data[1], data[0], 'go-', 'ro')
plt.show()
tags = ['\\ip', '\\bt']
data_dict = reader.read_many(1054342, tags)
ip, ip_time = data_dict['\\ip']
```

## Service
### 1.Query
查询破裂数据库的标签,可以用条件过滤出炮号和获取一炮的标签

例子：
```python
from DDB.Service import Query

db = Query()
db.tag(1046810)
# {'shot': '1046810', 'CqDuration': 0.0, 'CqTime': 0.0, 'IpCq': 0.0, 'IpFlat': 202.8784696689742, 'IsDisrupt': False, 'IsFlatTopDisrupt': False, 'IsRampDownDisrupt': False, 'IsRampUpDisrupt': False, 'IsRunaway': False, 'IsValidShot': True, 'NoData': False, 'RampDownTime': 0.48910004768371573, 'RunawayDuration': 0.0, 'RunawayIp': 0.0, 'TqDuration': 0.0, 'TqTime': 0.0}
my_query = {'IsDisrupt': True, 'IpFlat':{'$gt':50}}
db.query(my_query)
# [1046770, 1046794, 1046795, 1046806, 1046800, 1046809, 1046826, 1046828, 1046832, 1046835, 1046858,..., 1049184, 1050467, 1052286, 1050560, 1052295]
```

