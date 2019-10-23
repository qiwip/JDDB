"""
分析等离子体电流，获取等离子体电流相关的信息
==========
通过滤波算法找到等离子体平顶电流大小，开始下降时间等信息

"""
from DDB.Label import GeneratorBase
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


class MGI(GeneratorBase):

    def __init__(self):
        pass

    def device(self):
        return 'J-TEXT'

    def get_request_signal(self):
        return [r'\vp']

    def calculate(self, data):
        result = {
            'MGI': False  # 是否是MGI
        }
        vp_t = data[r'\vp']

        if vp_t.shape[0] == 2 and vp_t.shape[1] != 0:
            vp = vp_t[0]
            time = vp_t[1]
        else:
            result['NoData'] = True
            return result
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
