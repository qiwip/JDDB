"""
分析磁探针信号，获取锁模信息
这个需要优化，不应该依赖其他标签
==========
算法:

"""
from DDB.Label import GeneratorBase
import numpy as np
from scipy import signal
from DDB.Service import Query


class Generator(GeneratorBase):

    def __init__(self):
        pass

    def requested_signal(self):
        return [r'\MA_POL_CA01T',
                r'\exsad1', r'\exsad2', r'\exsad3', r'\exsad4', r'\exsad5',
                r'\exsad6', r'\exsad7', r'\exsad8', r'\exsad9', r'\exsad10'
                ]

    def run(self, data):
        result = {
            'IsLockedMode': False,  # 是否发生锁模
            'LockedModeTime': 0.0  # 锁模时间
            # 'IsUnLockedMode': False,  # 是否解锁
            # 'UnLockedModeTime': 0.0  # 解锁时间
        }

        shot = data['shot']
        db = Query()
        tag = db.tag(shot)

        if tag['IsRampUpDisrupt'] is True:
            return result
        if tag['IsDisrupt'] is True:
            end_t = tag['CqTime']
        else:
            end_t = tag['RampDownTime']

        # mirnov信号
        mirnov_t = data['\MA_POL_CA01T']
        if mirnov_t.shape[0] == 2 and mirnov_t.shape[1] != 0:
            mirnov = mirnov_t[0]
            time = mirnov_t[1]
        else:
            result['NoData'] = True
            return result

        # 截取信号
        start = np.where(time >= 0.05)[0][0]
        if time[-1] < end_t:
            end = len(time)
        else:
            end = np.where(time >= end_t)[0][0]

        mirnov = mirnov[start:end]
        time = time[start:end]
        # 信号分析
        # 采样率
        sampling_rate = 250000
        # FFT采样点数
        frame_size = 1024

        # 低通滤波
        # scipy.signal.butter(N, Wn, btype='low', analog=False, output='ba')
        # N:滤波器的阶数
        # Wn:归一化截止频率.计算公式Wn = 2 * 截止频率 / 采样频率
        # 滤除50kHz以上的成分,截止频率50000
        wn = 2 * 10000 / sampling_rate

        # plt.figure(0)
        # plt.subplot(211)
        # plt.title(u'滤波前')
        # plt.plot(time, mirnov)
        [b, a] = signal.butter(3, wn, 'low')
        mirnov = signal.filtfilt(b, a, mirnov)

        # plt.subplot(212)
        # plt.title(u'滤波后')
        # plt.plot(time, mirnov)
        # plt.xlabel('time/s')

        # plt.figure(1, figsize=(19.20, 10.80))
        # plt.subplot(311)
        # plt.plot(time, mirnov)

        # FFT
        i = 0
        max_sqe = []
        max_sqe_t = []
        window = np.hanning(frame_size)

        while i < len(mirnov)-frame_size:
            frames = mirnov[i:i+frame_size]
            frames *= window
            mirnov_fft = np.fft.rfft(frames) / frame_size
            freqs = np.linspace(0, sampling_rate/2, int(frame_size/2+1))
            mirnov_fft = 20 * np.log10(np.clip(np.abs(mirnov_fft), 1e-20, 1e100))

            # plt.figure()
            # plt.subplot(211)
            # plt.plot(time[i:i+frameSize], mirnov[i:i + frameSize])
            # plt.subplot(212)
            # plt.plot(freqs, mirnov_fft)
            # plt.show()

            max_sqe.append(freqs[np.argmax(mirnov_fft)])
            max_sqe_t.append(time[int(i + frame_size/2)])
            i += 100

        # 中值滤波,平滑处理
        max_sqe = signal.medfilt(max_sqe, 31)

        # plt.subplot(312)
        # plt.scatter(max_sqe_t, max_sqe)

        exsad1_t = data['\exsad1']
        if exsad1_t.shape[0] == 2 and exsad1_t.shape[1] != 0:
            exsad1 = exsad1_t[0]
            exsad1_time = exsad1_t[1]
        else:
            result['NoData'] = True
            return result

        exsad7_t = data['\exsad7']
        if exsad7_t.shape[0] == 2 and exsad7_t.shape[1] != 0:
            exsad7 = exsad7_t[0]
            exsad7_time = exsad7_t[1]
        else:
            result['NoData'] = True
            return result

        exsad_resample = []
        for time in max_sqe_t:
            index1 = np.where(exsad1_time >= time)[0][0]
            index2 = np.where(exsad7_time >= time)[0][0]
            exsad_resample.append(exsad1[index1]*100/2.35 - exsad7[index2]*100/1.79)

        exsad_resample = signal.medfilt(exsad_resample, 31)
        for i in range(int(len(max_sqe_t)/2), len(max_sqe_t)):
            if max_sqe[i] < 1000 and np.fabs(exsad_resample[i]) > 10:
                result['IsLockedMode'] = True
                result['LockedModeTime'] = max_sqe_t[i]

        # plt.subplot(313)
        # plt.plot(max_sqe_t, exsad_resample)
        # # plt.scatter(max_sqe_t, exsad7_resample)
        # plt.xlabel('time/s')
        # plt.show()
        # shot = data['shot']
        # plt.savefig('image\\mirnov' + os.sep + '{}.png'.format(shot), dpi=300)
        # plt.close(1)

        return result
