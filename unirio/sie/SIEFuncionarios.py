# coding=utf-8
from unirio.sie import SIEException
from unirio.sie.base import SIE


class SIEFuncionarioID(SIE):
    path = "V_FUNCIONARIO_IDS"

    def __init__(self):
        super(SIEFuncionarioID, self).__init__()
        self.cacheTime *= 10

    def getFuncionarioIDs(self, cpf):
        return self.api.get(self.path, params={"CPF": cpf}).content[0]


class SIEFuncionarios(SIE):
    path = "FUNCIONARIOS" # TODO Isso tá me enganando. Não existe consulta a essa tabela!

    ID_GRUPO_ADMIN_PROJETOS_PESQUISA = 107

    def __init__(self):
        """ """

        super(SIEFuncionarios, self).__init__()

    def getEscolaridade(self, ID_FUNCIONARIO):
        """


        :rtype : dict
        :param ID_FUNCIONARIO: Identificador único de funcionário na tabela FUNCIONARIOS
        :return: Um dicionário contendo chaves relativas a escolaridade
        :raise e:
        """
        try:
            return self.api.get(
                self.path,
                {"ID_FUNCIONARIO": ID_FUNCIONARIO},
                ["ESCOLARIDADE_ITEM", "ESCOLARIDADE_TAB"]
            ).content[0]
        except ValueError as e:
            raise SIEException("Não foi possível encontrar o funcionário.", e)

    def get_funcionario_by_id_usuario(self, id_usuario):

        where = {
            "ORDERBY": "ID_CONTRATO_RH",
            "SORT": "DESC",
            "ID_USUARIO": id_usuario
        }

        funcionario = self.api.get_single_result("V_FUNCIONARIOS", where)

        return funcionario



    def get_funcionario(self, cpf):
        return self.api.get("V_FUNCIONARIOS", params={"CPF": cpf}).content[0]

    def is_adm(self,id_usuario):
        where = {
            'ID_USUARIO':id_usuario,
            'ID_GRUPO':self.ID_GRUPO_ADMIN_PROJETOS_PESQUISA # TODO Adicionar questão de super usuários?
        }

        return self.api.get_single_result("V_USUARIOS_GRUPOS",where,bypass_no_content_exception=True)


class SIEDocentes(SIE):
    path = "V_DOCENTES"

    COD_ATIVO = 1

    def __init__(self):
        super(SIEDocentes, self).__init__()

    def getDocentes(self):
        params = {
            "SITUACAO_ITEM": self.COD_ATIVO
        }
        fields = [
            "MATR_EXTERNA",
            "NOME_DOCENTE"
        ]
        return self.api.get(self.path, params, fields)

    def get_docente(self,cpf):
        params = {
            "SITUACAO_ITEM": self.COD_ATIVO,
            "CPF":cpf
        }
        fields = [
            "MATR_EXTERNA",
            "NOME_DOCENTE"
        ]

        return self.api.get_single_result(self.path,params)

    def is_prof_camara_pesquisa(self, id_usuario):
        where = {
            'ID_USUARIO': id_usuario,
        }

        return self.api.get_single_result("V_MEMBROS_CAMARA", where, bypass_no_content_exception=True)


