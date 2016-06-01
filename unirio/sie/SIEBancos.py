# coding=utf-8
from unirio.sie.base import SIE


class SIEBancos(SIE):
    def __init__(self):
        super(SIEBancos, self).__init__()
        self.path = "CAD_BANCOS"
        self.cacheTime *= 3

    def getBancos(self):
        params = {
            'LMIN': 0,
            'LMAX': 99999,
            'ORDERBY': 'NOME_BANCO'
        }
        fields = ['ID_BANCO', 'COD_BANCO', 'DV_BANCO', 'NOME_BANCO']
        return self.api.get(self.path, params, fields).content


class SIEAgencias(SIE):
    def __init__(self):
        super(SIEAgencias, self).__init__()
        self.path = "CAD_AGENCIAS"

    def getAgenciasDeBanco(self, ID_BANCO):
        params = {
            'LMIN': 0,
            'LMAX': 99999,
            'ID_BANCO': ID_BANCO,
            'ORDERBY': 'COD_AGENCIA'
        }
        fields = ['ID_AGENCIA', 'COD_AGENCIA', 'DV_AGENCIA', 'NOME_AGENCIA']
        return self.api.get(self.path, params, fields).content