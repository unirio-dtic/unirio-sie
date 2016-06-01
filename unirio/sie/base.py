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
