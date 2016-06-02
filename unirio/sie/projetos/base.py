# coding=utf-8

from datetime import date, datetime, timedelta

from deprecate import deprecated

from unirio.api.exceptions import NoContentException, APIException

from unirio.sie.base import SIE
from unirio.sie.documentos import SIEDocumentoDAO, SIETiposDocumentosDAO, SIEAssuntosDAO
from unirio.sie.projetos import SIEClassifProjetos
from unirio.sie.projetos.orgaos import SIEOrgaosProjetos
from unirio.sie.projetos.participantes import SIEParticipantesProjs
from unirio.sie.tab_estruturada import SIETabEstruturada


class SIEProjetos(SIE):
    TIPO_DOCUMENTO = -1

    def __init__(self):
        super(SIEProjetos, self).__init__()
        self.path = "PROJETOS"

    def getProjeto(self, ID_PROJETO):
        """
        Dado o identificador único de um projeto na tabela PROJETOS, a função retorna um dicionáio
        correspondente. A requisição é cacheada.

        :param ID_PROJETO: Identificador único de um projeto
        :type ID_PROJETO: int
        :return: Uma entrada na tabela PROJETOS
        :rtype : dict
        """
        params = {
            'LMIN': 0,
            'LMAX': 1,
            'ID_PROJETO': ID_PROJETO
        }

        return self.api.get_single_result(self.path, params)

    def getProjetoDados(self, ID_PROJETO):
        """
        Dado o identificador único de um projeto na tabela PROJETOS, a função retorna um dicionáio
        correspondente a uma entrada na view V_PROJETOS_DADOS, que é uma juncão das tabelas PROJETOS,
        PARTICIPANTES_PRJ, DOCUMENTOS, CLASSIFICACAO_PRJ

        :param ID_PROJETO: Identificador único de um projeto
        :type ID_PROJETO: int
        :return: Uma entrada na view V_PROJETOS_DADOS
        :rtype: dict
        """
        params = {
            'LMIN': 0,
            'LMAX': 1,
            'ID_PROJETO': ID_PROJETO
        }

        try:
            return self.api.get("V_PROJETOS_DADOS", params).first()
        except NoContentException:
            return None

    def getCoordenador(self, ID_PROJETO):
        """
        Dado um ID_PROJETO, a função retorna o seu coordenador, na forma de um dicionário representativo de uma entrada
        na tabela PESSOAS.

        :param ID_PROJETO: Identificador único de um projeto na tabela PROJETOS
        :return: Uma entrada na tabela PESSOAS
        :rtype : dict
        """
        params = {
            'LMIN': 0,
            'LMAX': 1,
            'ID_PROJETO': ID_PROJETO,
            'FUNCAO_ITEM': 1
        }

        try:
            c = self.api.get("PARTICIPANTES_PROJ", params).first()
            return self.api.get("PESSOAS", {"ID_PESSOA": c['ID_PESSOA']}).first()
        except NoContentException:
            return None

    def getDisciplina(self, ID_PROJETO):
        """
        Dado um identificador único na tabela de PROJETOS, a função retornará uma string correspondente ao nome da
        disciplina, de acordo com a classificaçao do projeto

        :rtype : str
        :param ID_PROJETO: Identificador único de uma entrada na tabela PROJETOS
        :return: Nome de uma disciplina
        """
        params = {
            'LMIN': 0,
            'LMAX': 1,
            'ID_PROJETO': ID_PROJETO
        }

        try:
            return self.api.get("V_PROJETOS_DADOS", params).first()['NOME_DISCIPLINA']
        except NoContentException:
            return None

    def projetosDeEnsino(self, edicao, params=None):
        """

        :type edicao: gluon.storage.Storage
        :param edicao: Uma entrada da tabela `edicao`
        :type params: dict
        :param params: Um dicionário de parâmetros a serem usados na busca
        :rtype : list
        :return: Uma lista de projetos de ensino
        """
        if not params:
            params = {}

        params.update({
            "ID_CLASSIFICACAO": 40161,
            "DT_INICIAL": edicao.dt_inicial_projeto,
            "LMIN": 0,
            "LMAX": 99999
        })

        return self.api.get(self.path, params).content

    def projetosDadosEnsino(self, edicao, params=None):
        """

        :type edicao: gluon.storage.Storage
        :param edicao: Uma entrada da tabela `edicao`
        :type params: dict
        :param params: Um dicionário de parâmetros a serem usados na busca
        :rtype : list
        :return: Uma lista de projetos de ensino
        """
        if not params:
            params = {}

        params.update({
            "ID_CLASSIFICACAO": 40161,
            "DT_INICIAL": edicao.dt_inicial_projeto,
            "LMIN": 0,
            "LMAX": 99999
        })

        return self.api.get('V_PROJETOS_DADOS', params).content

    @staticmethod
    def isAvaliado(projeto):
        """
        0 => Situação do projeto da Instituição
        1 => Concluído/Publicado
        2 => Em andamento
        4 => Suspenso
        5 => Cancelado
        6 => Renovado
        7 => Cancelado - Res. Interna
        8 => Em tramite para registro
        9 => Indeferido

        :type projeto: dict
        :param projeto: Dicionário correspondente a uma entrada na tabela PROJETOS
        :rtype bool
        """
        # TODO discituir se usar uma lista estática é uma solução aceitável ou se deveria ser realizada uma consulta na TAB_ESTRUTURADA
        if projeto["SITUACAO_ITEM"] in range(1, 10):
            return True

    @deprecated
    def salvarProjeto(self, projeto, funcionario, edicao):
        """
        EVENTO_TAB              => Tipos de Eventos
        EVENTO_ITEM = 1         => Não se aplica
        TIPO_PUBLICO_TAB        => Público alvo
        TIPO_PUBLICO_ITEM = 8   => 3o grau
        AVALIACAO_TAB           => Avaliação dos projetos da Instituição
        AVALIACAO_ITEM = 2      => Pendente de avaliacao

        :type projeto: dict
        :param projeto: Um projeto a ser inserido no banco
        :type funcionario: dict
        :param funcionario: Dicionário de IDS de um funcionário
        :type edicao: gluon.storage.Storage
        :param edicao: Uma entrada da tabela `edicao`
        :return: Um dicionário contendo a entrada uma nova entrada da tabela PROJETOS
        """
        novoDocumento = SIEDocumentoDAO().criar_documento(215, funcionario)
        projeto.update({
            "ID_DOCUMENTO": novoDocumento["ID_DOCUMENTO"],
            "ID_UNIDADE": SIECursosDisciplinas().getIdUnidade(projeto['ID_CURSO']),
            "NUM_PROCESSO": novoDocumento["NUM_PROCESSO"],
            "EVENTO_TAB": 6028,
            "EVENTO_ITEM": 1,
            "TIPO_PUBLICO_TAB": 6002,
            "TIPO_PUBLICO_ITEM": 8,
            "ACESSO_PARTICIP": "S",
            "PAGA_BOLSA": "S",
            "DT_INICIAL": edicao.dt_inicial_projeto,
            "DT_REGISTRO": date.today(),
            "AVALIACAO_TAB": 6010,
            "AVALIACAO_ITEM": 2
        })

        novoProjeto = self.api.post(self.path, projeto)
        projeto.update({"ID_PROJETO": novoProjeto.insertId})

        return projeto

    def avaliarProjeto(self, ID_PROJETO, avaliacao):
        """
        Método utilizado para avaliar um projeto

        avaliacao = 9           => indeferido (Indeferido)
        avaliacao = 2           => deferido (Em andamento)
        AVALIACAO_ITEM = 3      => Avaliado
        AVALIACAO_ITEM = 4      => Avaliado fora do prazo

        :type ID_PROJETO: int
        :type avaliacao: int
        :param ID_PROJETO: Identificador único de um PROJETO
        :param avaliacao: Um inteiro correspondente a uma avaliação
        """
        try:
            self.api.put(
                self.path,
                {
                    "ID_PROJETO": ID_PROJETO,
                    "AVALIACAO_ITEM": 3,
                    "SITUACAO_ITEM": avaliacao,
                    "DT_ULTIMA_AVAL": date.today()
                }
            )
            self.tramitarDocumentoProjeto(ID_PROJETO, avaliacao)
        except APIException:
            raise APIException("Não foi possível atualizar o estado da avaliação de um projeto.")

    @deprecated
    def removerProjeto(self, ID_PROJETO):
        """
        Dada uma entrada na tabela PROJETOS, a função busca e remove essa entrada após buscar e remover o DOCUMENTO
        relacionado, os partifipantes deste projeto, seu orgão e classificação

        :param ID_PROJETO: Identificador único de uma entrada na tabela PROJETOS
        """
        projeto = self.getProjeto(ID_PROJETO)
        SIEParticipantesProjs().removerParticipantesFromProjeto(projeto['ID_PROJETO'])
        SIEOrgaosProjetos().removerOrgaosProjetosDeProjeto(projeto['ID_PROJETO'])
        SIEClassifProjetos().removerClassifProjetosDeProjeto(projeto['ID_PROJETO'])

        if projeto["ID_DOCUMENTO"]:
            # Se existe documento relacionado a este documento.
            documento = SIEDocumentoDAO().obter_documento(projeto['ID_DOCUMENTO'])
            SIEDocumentoDAO().remover_documento(documento)
        else:
            # print "Nenhum documento relacionado ao projeto %d" % ID_PROJETO # TODO Colocar logging?
            pass

        self.api.delete(self.path, {"ID_PROJETO": ID_PROJETO})

    def situacoes(self):
        """
        A função retorna uma lista de dicionários com as possíveis situações (SITUACAO_ITEM) de um projeto

        :rtype : list
        :return: Lista de dicionários contendo as chaves `ITEM_TABELA` e `DESCRICAO`
        """
        return SIETabEstruturada().itemsDeCodigo(6011)

    def documento_inicial_padrao(self):
        # todo Property ?

        infos_tipo_documento = SIETiposDocumentosDAO().obter_parametros_tipo_documento(self.TIPO_DOCUMENTO)
        assunto_relacionado = SIEAssuntosDAO().get_by_id(infos_tipo_documento['ID_ASSUNTO_PADRAO'])

        return {
            "ID_TIPO_DOC": self.TIPO_DOCUMENTO,
            "ID_PROCEDENCIA": self.usuario["ID_CONTRATO_RH"],
            "ID_PROPRIETARIO": self.usuario["ID_USUARIO"],
            "ID_CRIADOR": self.usuario["ID_USUARIO"],
            "TIPO_PROCEDENCIA": "S",
            "TIPO_INTERESSADO": "S",
            "ID_INTERESSADO": self.usuario["ID_CONTRATO_RH"],
            "SITUACAO_ATUAL": 1,
            "TIPO_PROPRIETARIO": 20,  # Indica a restrição de usuário
            # "TIPO_ORIGEM": 20,  # atualizacao do sie Out/2015
            "DT_CRIACAO": date.today(),
            "HR_CRIACAO": datetime.now().time().strftime("%H:%M:%S"),
            "IND_ELIMINADO": "N",
            "IND_AGENDAMENTO": "N",
            "IND_RESERVADO": "N",
            "IND_EXTRAVIADO": "N",
            "TEMPO_ESTIMADO": 1,
            "ID_ASSUNTO": assunto_relacionado['ID_ASSUNTO'],
            "RESUMO_ASSUNTO": assunto_relacionado['DESCR_ASSUNTO'],
            "DT_LIMITE_ARQ": date.today() + timedelta(days=int(assunto_relacionado['TEMPO_ARQUIVAMENTO']))
        # TODO Se for None, qual o comportamento esperado?
            # "OBSERVACOES": ?? Não estamos usando.
            # "SEQUENCIA": 1  # atualizacao do sie Out/2015
        }


# todo: WTF isso ta fazendo aqui?
class SIECursosDisciplinas(SIE):
    def __init__(self):
        super(SIECursosDisciplinas, self).__init__()
        self.path = "V_CURSOS_DISCIPLINAS"

    def getCursos(self, params=None):
        if not params:
            params = {}

        params.update({
            "LMIN": 0,
            "LMAX": 99999,
            "ORDERBY": "NOME_CURSO",
            "DISTINCT": "T"
        })
        fields = [
            "NOME_CURSO",
            "ID_CURSO"
        ]
        return self.api.get(self.path, params, fields).content

    def getCursosGraduacao(self):
        """
        NIVEL_CURSO_ITEM = 3    => Graduação

        :rtype : list
        :return: Returna uma lista de cursos de graduação
        """
        params = {"NIVEL_CURSO_ITEM": 3}
        return self.getCursos(params)

    def getDisciplinas(self, ID_CURSO, filtroObrigatorias=False):
        params = {
            "LMIN": 0,
            "LMAX": 9999,
            "ID_CURSO": ID_CURSO,
            "ORDERBY": "NOME_DISCIPLINA"
        }
        if filtroObrigatorias:
            params["OBRIGATORIA"] = "S"
        fields = [
            "NOME_DISCIPLINA",
            "COD_DISCIPLINA"
        ]
        return self.api.get(self.path, params, fields).content

    def getIdUnidade(self, ID_CURSO):
        """
        :type ID_CURSO: int
        :rtype : int
        """
        params = {
            "ID_CURSO": ID_CURSO
        }
        fields = ["ID_UNIDADE"]
        return self.api.get(self.path, params, fields).first()["ID_UNIDADE"]
