import abc
from .adapters import ADAPTER


class SIE(object):
    __metaclass__ = abc.ABCMeta
    cacheTime = 86400

    def __init__(self, adapter=ADAPTER):
        """
        :type adapter: SIEDAOBaseAdapter
        """

        self.__adapter = adapter()
        self.api = self.__adapter.api
        self.usuario = self.__adapter.usuario

    def handle_blob(self, arquivo):
        # TODO descarta @staticmethod...
        return self.__adapter.handle_blob(arquivo)


class BaseDAO(SIE):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def path(self):
        pass

    def get(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        if 'uid' in kwargs:
            return self.api.get_single_result(self.path, kwargs['uid'])
        raise NotImplementedError

    def search(self, *args, **kwargs):
        return self.api.get(self.path, *args, **kwargs)

    def delete(self, uid):
        return self.api.delete(uid)

    def insert(self, data):
        return self.api.post(self.path, data)

    def update(self, data):
        return self.api.put(self.path, data)
