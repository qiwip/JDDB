
# 破裂数据库(Disruption database)说明

## 包结构

```c
DDB
└─── Data
|    └── importer
|    └── reader
|
└─── Label
|    └── GeneratorBase
|    └── xxGenerator
|    └── TaskRunner
|
└─── Severvice
     └── Query
     └── Evaluater

```

* Data模块提供将数据存入hdf5文件和从hdf5读取诊断数据的API，实现数据的统一化存储。
* Label模块提供为炮打标签的功能，用户可以继承GeneratorBase，实现其中的requested_signal和run方法，requested_signal获得该Generator计算所需数据的tag，run方法计算并返回标签信息。TaskRunner可以自动调用这些Generator，为其准备所需数据并调用其run方法得到返回值后将结果存入MongoDB。
* Service提供用户接口。Query可以指定条件查询炮的标签；Evaluater可以在破裂预测时对结果进行评估。

> 文件中还包含了J-TEXT读取数据的程序`JtextDataImporter.py`

## Label

### 1. GeneratorBase

各种生成标签插件的基类，定义了两个接口:

```python
def requested_signal():
    raise NotImplementedError('requested_signal')

def run(data):
    raise NotImplementedError('run')
```

### 2. TaskRunner

自动调用各种生成标签的插件去生成一些标签。以前是通过在程序里```add(插件类())```的方式添加，现在改为配置文件配置。

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

在初始化的时候，读取配置文件，再import配置里面给的包名，调用其接口进行计算。
