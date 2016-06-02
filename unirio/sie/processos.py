# -*- coding: utf-8 -*-
from unirio.sie.base import SIE


__author__ = 'carlos.faruolo'


class SIEProcesso(SIE):
    def __init__(self):
        super(SIEProcesso, self).__init__()
        self.path = NotImplementedError
        self.lmin = 0
        self.lmax = 1000

    def get_content(self, params=None):
        """
        :rtype : APIPOSTResponse
        :type params: dict
        """
        if not params:
            params = {}
        limits = {"LMIN": self.lmin, "LMAX": self.lmax}
        for k, v in params.items():
            params[k] = str(params[k]).upper()
        params.update(limits)

        processos = self.api.get(self.path, params)
        if processos:
            return processos.content
        else:
            return list()


class SIEProcessoDados(SIEProcesso):
    def __init__(self):
        super(SIEProcessoDados, self).__init__()
        self.path = "V_PROCESSOS_DADOS"

    def get_processos(self, params=None):
        if not params:
            params = {}
        return self.get_content(params)

    def get_processo_dados(self, id_documento):
        params = {"ID_DOCUMENTO": id_documento}
        content = self.get_processos(params)
        return content[0]


class SIEProcessoTramitacoes(SIEProcesso):
    def __init__(self):
        super(SIEProcessoTramitacoes, self).__init__()
        self.path = "V_PROCESSOS_TRAMITACOES"

    def get_tramitacoes(self, num_processo):
        params = {"NUM_PROCESSO": num_processo, "ORDERBY": "DT_ENVIO"}
        return self.get_content(params)
