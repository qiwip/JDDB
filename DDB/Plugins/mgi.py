"""
分析真空室气压
==========
通过滤波算法找到等离子体平顶电流大小，开始下降时间等信息

"""
from DDB.Label import GeneratorBase
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


class Generator(GeneratorBase):

    def __init__(self):
        pass

    def requested_signal(self):
        return [r'\vp']

    def run(self, data):
        result = {
            'MGI': False  # 是否是MGI
        }
        try:
            vp, time = data[r'\vp']
            plt.figure(0)
            plt.plot(time, vp)
            plt.show()
            start = np.where(time > 0.2)[0][0]
            end = np.where(time > 2)[0][0]
            vp = vp[start:end]
            time = time[start:end]
            vp = signal.medfilt(vp, 5)
            vp[vp > 50] = 0

            if vp.max() > 0.003:
                result['MGI'] = True
            return result
        except Exception as e:
            print(e)
            return {}