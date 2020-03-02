"""
分析ECE信号，获取等离子体热淬灭信息
==========
先滤波，然后按步长向后计算小区间内斜率，获取热淬灭时间

"""
from DDB.Label import GeneratorBase
import numpy as np
from scipy import signal as signal


class Generator(GeneratorBase):

    def __init__(self):
        pass

    def requested_signal(self):
        """ Return list of tag of signals that processor need"""
        return [
            r'\Bt',
            r'\ECE_CH01_raw', r'\ECE_CH02_raw', r'\ECE_CH03_raw', r'\ECE_CH04_raw', r'\ECE_CH05_raw', r'\ECE_CH06_raw',
            r'\ECE_CH07_raw', r'\ECE_CH08_raw', r'\ECE_CH09_raw', r'\ECE_CH10_raw', r'\ECE_CH11_raw', r'\ECE_CH12_raw',
            r'\ECE_CH13_raw', r'\ECE_CH14_raw', r'\ECE_CH15_raw', r'\ECE_CH16_raw', r'\ECE_CH17_raw', r'\ECE_CH18_raw',
            r'\ECE_CH19_raw', r'\ECE_CH20_raw', r'\ECE_CH21_raw', r'\ECE_CH22_raw', r'\ECE_CH23_raw', r'\ECE_CH24_raw'
        ]

    def run(self, data):
        result = {
            'TqTime': 0.0,  #
            'TqDuration': 0.0,  # 
        }
        try:
            bt, time = data['\Bt']
            start = np.where(time > 0)[0][0]
            end = np.where(time > 0.4)[0][0]
            bt = bt[start:end]
            bt = np.average(bt)
            # 计算选择哪道信号
            # bt*56/frequency*105*-105
            frequency = [94.5, 96.5, 98.5, 100.5, 102.5, 104.5, 106.5, 108.5, 110.5, 112.5, 114.5, 116.5, 118.5,
                         120.5, 122.5, 124.5, 80.5, 82.5, 84.5, 86.5, 88.5, 90.5, 92.5, 94.5]
            position = 256
            channel = 0
            for i in range(0, 24):
                if abs(bt * 56 / frequency[i] * 105 - 105) < position:
                    position = abs(bt * 56 / frequency[i] * 105 - 105)
                    channel = i
            channel += 1
            if channel < 10:
                tag = r'\ECE_CH0{}_raw'.format(channel)
            else:
                tag = r'\ECE_CH{}_raw'.format(channel)
            ece, time = data[tag]
            time = time - 0.2
            if channel in [11, 13, 17, 18, 19, 20, 21, 22, 23, 24]:
                ece = - ece

            # 分析ece信号
            start = np.where(time >= 0)[0][0]
            ece = ece[start:]
            time = time[start:]
            ece = signal.medfilt(ece, 31)
            # 归一化
            ece = ece / np.max(ece)
            interval = 2500

            i = 0
            while i < len(ece) - interval:
                # 斜率
                k = np.polyfit(time[i:i + interval], ece[i:i + interval], 1)[0]
                # 平顶阶段
                if -100 > k:
                    result['TqTime'] = time[int(i + interval / 2)]
                    ece = ece[i:]
                    time = time[i:]
                    end = np.where(ece <= (np.min(ece)+0.1))[0][0]
                    result['TqDuration'] = time[end] - result['TqTime']
                    return result
                i += 100
            return result
        except Exception as e:
            print(e)
            return {}