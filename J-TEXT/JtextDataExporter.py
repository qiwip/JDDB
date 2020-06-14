import sys
from MDSplus import connection
import numpy as np
from scipy import signal
import logging
import traceback
import os
import time


sys.path.append('..')
from DDB.Data import Exporter, Reader


class JTEXTDataExporter:
    def __init__(self, root=None):
        """connect to mdsplus server and init data importer"""
        if root:
            self.exporter = Exporter(root)
            self.reader = Reader(root)
        else:
            self.exporter = Exporter()
            self.reader = Reader()
        # log
        log_dir = os.path.abspath('') + os.sep + 'log'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level=logging.INFO)
        handler = logging.FileHandler(log_dir + os.sep + 'JTEXTDataExporter_log_{}.txt'.format(
            time.strftime("%Y_%m_%d %H:%M:%S", time.localtime(time.time()))))
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.logger.addHandler(console)

    def download(self, shots=None, tags=None, sample_rate=None):
        """Download J-TEXT data
        @:param shots: shot list
        @:param tags: tag list
        @:param sr: sample rate for resample(kHz), if sr<sr0: do resample, else: do nothing
        :return: null
        """
        if shots is None or len(shots) == 0:
            raise ValueError('Param Error, '
                             'shot list can\'t be Empty!')
        if tags is None or len(tags) == 0:
            raise ValueError('Param Error, '
                             'tag list can\'t be Empty!')
        self.logger.info('Start download data')
        for shot in shots:
            try:
                c = connection.Connection('211.67.27.245')
                c.openTree('jtext', shot=shot)
                for tag in tags:
                    try:
                        if tag in self.reader.tags(shot):
                            self.logger.info('shot:{}, tag:{}, already exits.'.format(shot, tag))
                            continue
                        data = np.array(c.get(tag))
                        time = np.array(c.get(r'DIM_OF(BUILD_PATH({}))'.format(tag)))
                        if data.shape[0] == 0 or time.shape[0] == 0:
                            self.logger.info('shot:{}, tag:{}, Shape of signal or dim_of(signal) is 0')
                        elif abs(data.shape[0] - time.shape[0]) > 10:
                            self.logger.info('shot:{}, tag:{}, Shape of signal and dim_of(signal) not equal')
                        else:
                            if 0 < data.shape[0] - time.shape[0] < 10:
                                data = data[:time.shape[0]]
                            if 0 < time.shape[0] - data.shape[0] < 10:
                                time = time[:data.shape[0]]
                            sr0 = int(len(data) / (time[-1] - time[0]) / 10) * 10

                            if sample_rate and sample_rate < sr0/100:
                                num = sample_rate * (int(round(time[-1] * 1000 - time[0] * 1000)))
                                data = signal.resample(data, num)
                                duration = (time[-1] - time[0]) / num
                                time = []
                                for i in range(num):
                                    time.append(i*duration)
                            result = self.exporter.save(shot, tag, data, time)
                            if result == 0:
                                self.logger.info('shot:{}, tag:{}, Finish.'.format(shot, tag))
                            elif result == -1:
                                self.logger.info('shot:{}, tag:{}, already exits.'.format(shot, tag))
                    except Exception as e:
                        self.logger.info('shot:{}, tag:{}, error occurs:{}.'.
                                         format(shot, tag, e))
                c.closeTree('jtext', shot=shot)
                c.disconnect()
            except Exception as err:
                self.logger.info('shot {} is Empty, reason: {}\n{}'.format(shot, err, traceback.format_exc()))
                if 'SS-W-SUCCESS' in '{}'.format(err):
                    self.logger.info('stop at shot {}\n{}'.format(shot, traceback.format_exc()))
                    exit(-1)


if __name__ == '__main__':
    shots = [i for i in range(1064035, 1066650)]
    tags = ["\\ip", "\\Bt", "\\POLARIS_Den_v09", "\\lin_den_ch06", "\\axuv_ca_01", "\\vs_c3_aa001", "\\vs_ha_aa001", "\\sxr_cb_024", "\\sxr_cc_049", "\\Iohp", "\\Ivfp", "\\Ihfp", "\\MA_POL_CA01T", "\\MA_TOR1_R01", "\\MA_TOR1_R09"]
    jdi = JTEXTDataExporter('/nas/hdf5')
    jdi.download(shots, tags)
