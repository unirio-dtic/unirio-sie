# -*- coding: utf-8 -*-
from unirio.sie.base import SIE
from unirio.api.exceptions import APIException


class SIEPessoas(SIE):
    def __init__(self):
        super(SIEPessoas, self).__init__()
        self.path = 'PESSOAS'

    def getPessoa(self, ID_PESSOA):
        params = {
            'ID_PESSOA': ID_PESSOA,
            'LMIN': 0,
            'LMAX': 1
        }
        return self.api.get(self.path, params).content[0]

    def cadastrar_pessoa(self, params):
        """
        :param params: Parâmetros de inserção no banco de dados obrigatórios: Nome, Nome_UP, Nome Social e Natureza Jurídica
        :return:
        """
        try:

            pessoa = self.api.post(self.path, params)
        except APIException:
            pessoa = None
        return pessoa


class SIEDocPessoas(SIE):
    COD_CPF = 1

    def __init__(self):
        super(SIEDocPessoas, self).__init__()
        self.path = 'DOC_PESSOAS'

    def existe_cpf_cadastrado(self, cpf):

        params = {
            'LMIN': 0,
            'LMAX': 1,
            'ID_TDOC_PESSOA': self.COD_CPF,
            'NUMERO_DOCUMENTO': cpf
        }

        try:
            res = self.api.get(self.path, params)
            if res is not None and res.content:
                return True
            else:
                return False
        except (ValueError, AttributeError):
            return False


class SIEUsuarios(SIE):
    def __init__(self):
        super(SIEUsuarios, self).__init__()
        self.path = "USUARIOS"

    def get_usuario(self, cpf):
        params = {
            'LMIN': 0,
            'LMAX': 1,
            'LOGIN': cpf
        }
        return self.api.get(self.path, params).content[0]
