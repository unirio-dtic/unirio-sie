# coding=utf-8
from datetime import date
from unirio.sie import SIE, SIEFuncionarios, SIEBolsistas, SIEBolsas, SIETabEstruturada

__author__ = 'diogomartins'


class SIEParticipantesProjs(SIE):
    def __init__(self):
        super(SIEParticipantesProjs, self).__init__()
        self.path = "PARTICIPANTES_PROJ"

    def criarParticipanteCoordenador(self, ID_PROJETO, funcionario):
        """
        FUNCAO_TAB = 6003       => Papel do participante de um projeto
        FUNCAO_ITEM = 1         => Coordenador
        SITUACAO = A            => Ao adicionar um participante, ele estará ativo(A)

        :param ID_PROJETO: Identificador único de uma entrada na tabela PROJETOS
        :param funcionario: Dicionário de IDS de um funcionário
        :rtype : unirio.api.apiresult.APIPostResponse
        """
        escolaridade = SIEFuncionarios().getEscolaridade(funcionario["ID_FUNCIONARIO"])
        participante = {
            "TITULACAO_ITEM": escolaridade["ESCOLARIDADE_ITEM"],
            "ID_PESSOA": funcionario["ID_PESSOA"],
            "ID_CONTRATO_RH": funcionario["ID_CONTRATO_RH"]
            # "DESCR_MAIL": funcionario["DESCR_MAIL"],   # TODO deveria constar na session.funcionario
        }

        return self._criarParticipante(ID_PROJETO, 1, participante)

    def criarParticipanteBolsista(self, projeto, aluno, edicao):
        """
        TITULACAO_ITEM = 9      => Superior Incompleto
        FUNCAO_ITEM = 3         => Bolsista

        :param aluno: Dicionário de atributos de um aluno
        :rtype : unirio.api.apiresult.APIPostResponse
        """
        ID_BOLSISTA = SIEBolsistas().criarBolsista(SIEBolsas().getBolsa(6), edicao, aluno, projeto).insertId

        participante = {
            "ID_PESSOA": aluno["ID_PESSOA"],
            "ID_CURSO_ALUNO": aluno["ID_CURSO_ALUNO"],
            "TITULACAO_ITEM": 9,
            "DESCR_MAIL": aluno["DESCR_MAIL"],
            "ID_BOLSISTA": ID_BOLSISTA
        }

        return self._criarParticipante(projeto['ID_PROJETO'], 3, participante)

    def _criarParticipante(self, ID_PROJETO, FUNCAO_ITEM, participante={}):
        """
        FUNCAO_TAB = 6003       => Papel do participante de um projeto

        FUNCAO_ITEM previstas na TAB_ESTRUTURADA:

        1 => Coordenador
        2 => Orientador
        3 => Bolsista
        4 => Participante Voluntário
        5 => Pesquisador Colaborador
        6 => Co-orientador
        10 => Apresentador
        11 => Autor
        12 => Co-autor
        13 => Executor
        14 => Estagiário
        15 => Acompanhante
        16 => Monitoria não subsidiada
        20 => Não definida
        17 => Orientador de aluno
        50 => Candidato a bolsista

        :type ID_PROJETO: int
        :param ID_PROJETO: Identificador único de uma projeto na tabela PROJETOS
        :type FUNCAO_ITEM: int
        :param FUNCAO_ITEM: Identificador úncio de uma descrição de função. Identificadores possíveis podem ser
                            encontrados na TAB_ESTRUTURADA, COD_TABELA 6003
        :rtype : unirio.api.apiresult.APIPostResponse
        """
        participante.update({
            "CARGA_HORARIA": 20,
            "CH_SUGERIDA": 20,
            "DT_INICIAL": date.today(),
            "ID_PROJETO": ID_PROJETO,
            "FUNCAO_ITEM": FUNCAO_ITEM,
            "FUNCAO_TAB": 6003,
            "ID_PESSOA": participante["ID_PESSOA"],
            "SITUACAO": "A",
            "TITULACAO_TAB": 168,
        })

        return self.api.post(self.path, participante)

    def descricaoDeFuncaoDeParticipante(self, participante):
        """
        Dado um parcipante, o método retorna a descrição textual de sua função no projeto

        :type participante: dict
        :rtype : str
        :param participante: Um dicionário correspondente a uma entrada da tabela PARTICIPANTES_PROJ que contenha pelo
        menos a chave FUNCAO_ITEM
        """
        try:
            return SIETabEstruturada().descricaoDeItem(participante["FUNCAO_ITEM"], 6003)
        except AttributeError:
            return "Não foi possível recuperar"

    def getParticipantes(self, params):
        """

        :rtype : list
        """
        params.update({
            'LMIN': 0,
            'LMAX': 9999
        })

        try:
            return self.api.get(self.path, params).content
        except (ValueError, AttributeError):
            return None

    def getBolsistas(self, ID_PROJETO):
        params = {
            'ID_PROJETO': ID_PROJETO,
            'FUNCAO_ITEM': 3
        }
        return self.getParticipantes(params)

    def getParticipacoes(self, pessoa, params={}):
        """

        :param pessoa: Um dicionário da view V_FUNCIONARIO_IDS
        :param params: Um dicionários de parâmetros a serem utilizados na busca
        :return: Uma lista de participações em projetos
        :rtype: list
        """
        params.update({
            "ID_PESSOA": pessoa["ID_PESSOA"],
            "LMIN": 0,
            "LMAX": 9999
        })

        try:
            return self.api.get(self.path, params).content
        except ValueError:
            return []

    def getParticipante(self, ID_PARTICIPANTE):
        params = {
            'ID_PARTICIPANTE': ID_PARTICIPANTE,
            'LMIN': 0,
            'LMAX': 1
        }
        return self.api.get(self.path, params).first()

    def removerParticipante(self, ID_PARTICIPANTE):
        self.api.delete(self.path, {"ID_PARTICIPANTE": ID_PARTICIPANTE})

    def removerParticipantesFromProjeto(self, ID_PROJETO):
        params = {
            "ID_PROJETO": ID_PROJETO,
            "LMIN": 0,
            "LMAX": 99999
        }
        try:
            participantes = self.api.get(self.path, params, ['ID_PARTICIPANTE'])
            for p in participantes.content:
                self.removerParticipante(p['ID_PARTICIPANTE'])
        except ValueError:
            print "Nenhum participante para remover do projeto %d" % ID_PROJETO

    def inativarParticipante(self, participante):
        """
        Dado um participante, o método inativa o mesmo e a bolsa referente.

        :type participante: dict
        :param participante: Uma entrada da tabela PARTICIPANTES_PROJ, contendo as keys ID_PARTICIPANTE e ID_BOLSISTA
        """
        params = {
            'ID_PARTICIPANTE': participante['ID_PARTICIPANTE'],
            'SITUACAO': 'I',
            'DT_FINAL': date.today()
        }
        self.api.put(self.path, params)
        SIEBolsistas().inativarBolsista(participante['ID_BOLSISTA'])