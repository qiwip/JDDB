import os
import h5py
import math
import numpy as np
import traceback
import DDB


class Exporter:
    """Export data from any other database to hdf5 files
    Examples
    --------
    >>> from DDB.Data import Exporter
    >>> exporter = Exporter(root_path='D:\\J-TEXT')
    >>> data = [0.1, 0.5, 0.3, 0.4, 0.2]
    >>> time = [0, 0.1, 0.2, 0.3, 0.4]
    >>> exporter.save(1051234,'\\ip',data,time)
    """
    def __init__(self, root_path=None):
        if root_path:
            self.hdf5path = root_path
        else:
            config = DDB.get_config()
            self.hdf5path = config['path']['hdf5']
        if not os.path.exists(self.hdf5path):
            os.mkdir(self.hdf5path)

    def save(self, shot: int, tag: str, data=None, time=None) -> int:
        """
        Save diagnostic data to a hdf5 file
        :param data: Diagnostic data, an array
        :param time: Time axis of diagnostic data
        :param shot: Shot number
        :param tag: Tag of diagnosis
        :return: code(0:success-1:tag already exits, -2:other failure)
        """
        path = str(math.floor(shot / 100) * 100)
        if not os.path.exists(self.hdf5path + os.sep + path):
            os.mkdir(self.hdf5path + os.sep + path)
        file_path = self.hdf5path + os.sep + path + os.sep + '{}.hdf5'.format(shot)

        try:
            h5f = h5py.File(file_path)
            if tag in h5f.keys():
                return -1
            data = np.array(data)

            if time is None:
                dataset = h5f.create_dataset('/{}'.format(tag), data=data)
                dataset.attrs.create('SampleRate', -1)
                dataset.attrs.create('StartTime', -1)
            else:
                time = np.array(time)
                fs = len(data) / (time[-1] - time[0]) if len(time) > 1 else 0
                start_time = time[0] if len(time) > 1 else 0
                dataset = h5f.create_dataset('/{}'.format(tag), data=data)
                dataset.attrs.create('SampleRate', fs)
                dataset.attrs.create('StartTime', start_time)
            return 0
        except Exception as e:
            traceback.print_exc(e)
            return -2


class Reader:
    """
    Read diagnostic data from local hdf5 file
    Examples
    --------
    >>> from DDB.Data import Reader
    >>> reader = Reader(root_path='D:\\J-TEXT')
    >>> data = reader.read_one(1054173, '\\ip')
    >>> import matplotlib.pyplot as plt
    >>> plt.plot(data[1], data[0], 'go-', 'ro')
    >>> plt.show()
    >>> tags = ['\\ip', '\\bt']
    >>> data_dict = reader.read_many(1054342, tags)
    >>> ip, ip_time = data_dict['\\ip']
    """
    def __init__(self, root_path=None):
        if root_path:
            self.hdf5path = root_path
        else:
            config = DDB.get_config()
            self.hdf5path = config['path']['hdf5']
        if not os.path.exists(self.hdf5path):
            raise ValueError('Path {} does n\'t exist.')

    def tags(self, shot: int):
        """get tags of a shot
        @:param shot: Shot number, integer
        @:return:Tags of Diagnostic signal

        TODO: fix bugs
        """
        try:
            path = str(math.floor(shot / 100) * 100)
            file_path = self.hdf5path + os.sep + path + os.sep + '{}.hdf5'.format(shot)
            h5f = h5py.File(file_path, 'r')
            return [i for i in h5f.keys()]
        except Exception as e:
            print(e)
        return []

    def read_one(self, shot: int, tag: str):
        """Read data from hdf5 files
        @:param shot: Shot number, integer
        @:param tag: Tag of diagnostic signal, string
        @return: Diagnostic signal data and its time axis, tuple, (diagnostic data, time axis)
        TODO: fix bugs
        """
        path = str(math.floor(shot/100)*100)
        file_path = self.hdf5path + os.sep + path + os.sep + '{}.hdf5'.format(shot)
        f = h5py.File(file_path, 'r')
        dataset = f.get(tag)
        if dataset:
            data = dataset[:]
            fs = dataset.attrs.get('SampleRate')
            st = dataset.attrs.get('StartTime')
            f.close()
            # 重新生成时间
            if fs < 0:
                return data
            time_axis = []
            for i in range(data.shape[0]):
                time_axis.append(st+i*(1/fs))
            return data, np.array(time_axis)

    def read_many(self, shot=None, tags=None):
        """Read data from hdf5 files
        @:param shot: Shot number, integer
        @:param tag: Tag list of diagnostic signal, list
        @return: Diagnostic signal data and its time axis, dictionaries, "key(tag)":(diagnostic data, time axis)

        TODO: fix bugs
        """

        path = str(math.floor(shot/100)*100)
        file_path = self.hdf5path + os.sep + path + os.sep + '{}.hdf5'.format(shot)
        f = h5py.File(file_path, 'r')

        data_dict = {}
        for tag in tags:
            dataset = f.get(tag)
            if dataset:
                data = dataset[:]
                fs = dataset.attrs.get('SampleRate')
                st = dataset.attrs.get('StartTime')
                if fs < 0:
                    data_dict[tag] = (np.array(data))
                else:
                    time_axis = []
                    for i in range(data.shape[0]):
                        time_axis.append(st + i * (1 / fs))
                    data_dict[tag] = (np.array(data), np.array(time_axis))

        f.close()
        return data_dict
