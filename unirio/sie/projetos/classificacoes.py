# coding=utf-8
from deprecate import deprecated
from unirio.api import APIException, NoContentException
from unirio.sie import SIE
from unirio.sie.exceptions import SIEException

__author__ = 'diogomartins'


class SIEClassificacoesPrj(SIE):
    COD_CLASSIFICACAO_PRJ_CAMARA_PESQUISA = 33
    COD_CLASSIFICACAO_PRJ_CLASSIFICACAO_CNPQ = 3
    COD_CLASSIFICACAO_PRJ_COMITE_ETICA = 32
    COD_CLASSIFICACAO_PRJ_GRUPO_CNPQ = 4
    ITEM_PARECER_COMITE_ETICA_NAO_SE_APLICA = 40172

    def __init__(self):
        super(SIEClassificacoesPrj, self).__init__()
        self.path = "CLASSIFICACOES_PRJ"

    def getClassificacoesPrj(self, classificacaoItem, codigo):
        """
        Talvez devesse se chamar get_classificacao_projeto


        CLASSIFICACAO_ITEM  => 1 - Tipos de Projetos, 41 - Disciplina vinculada
        CODIGO PARA CLASSIFICACAO_ITEM = 1 => 1 - Ensino, 2 - Pesquisa, 3 - Extensão, 4 - Desenvolvimento institucional

        :type classificacaoItem: int
        :type codigo: int
        :param classificacaoItem:
        :param codigo: COD_DISCIPLINA de uma disciplina do SIE
        :rtype : list
        :return: Uma lista de dicionários com os tipos de projetos
        """
        params = {
            'CLASSIFICACAO_ITEM': classificacaoItem,
            'CODIGO': codigo
        }
        fields = [
            'ID_CLASSIFICACAO',
            'DESCRICAO'
        ]
        return self.api.get(self.path, params, fields).content

    def get_descricao_classificacoes_by_ids(self,lista_ids_classificacao):
        """
        Passada uma lista de id_classificacao, retorna a descricao para cada uma.
        :param lista_ids_classificacao:
        :return:
        """
        params = {
            'LMIN': 0,
            'LMAX': 9999,
            "ID_CLASSIFICACAO_SET": lista_ids_classificacao
        }

        fields = ['ID_CLASSIFICACAO', "DESCRICAO"]

        return self.api.get(self.path, params, fields)

    def get_classificacoes_proj(self, classificacao_item):
        """
        CLASSIFICACAO_ITEM  => 1 - Tipos de Projetos, 41 - Disciplina vinculada
        CODIGO PARA CLASSIFICACAO_ITEM = 1 => 1 - Ensino, 2 - Pesquisa, 3 - Extensão, 4 - Desenvolvimento institucional

        :type classificacao_item: int
        :param classificacao_item:
        :rtype : list
        :return: Uma lista de dicionários com os tipos de projetos
        """
        params = {
            'CLASSIFICACAO_ITEM': classificacao_item,
            "ORDERBY": "DESCRICAO",
            "SORT": 'ASC'
        }
        params.update({
            'LMIN': 0,
            'LMAX': 9999
        })
        fields = ["ID_CLASSIFICACAO", "DESCRICAO", "CODIGO", "ID_CLASSIF_SUP"]
        return self.api.get(self.path, params, fields).content

    def get_camaras_pesquisa(self):
        try:
            camaras_dict = self.get_classificacoes_proj(self.COD_CLASSIFICACAO_PRJ_CAMARA_PESQUISA)
            camaras = [(d[u'ID_CLASSIFICACAO'], d[u'DESCRICAO'].encode('utf-8')) for d in camaras_dict]
        except AttributeError:
            camaras = None

        return camaras

    def get_classificacoes_cnpq(self):
        try:
            classif_dict = self.get_classificacoes_proj(self.COD_CLASSIFICACAO_PRJ_CLASSIFICACAO_CNPQ)
            classif = [(d[u'ID_CLASSIFICACAO'], d[u'DESCRICAO'].encode('utf-8'), d[u'ID_CLASSIF_SUP']) for d in
                       classif_dict]
        except AttributeError:
            classif = None

        return classif

    def get_grupos_cnpq(self):
        try:
            grupo_dict = self.get_classificacoes_proj(self.COD_CLASSIFICACAO_PRJ_GRUPO_CNPQ)
            grupos = [(d[u'ID_CLASSIFICACAO'], d[u'DESCRICAO'].encode('utf-8'), d[u'ID_CLASSIF_SUP']) for d in
                      grupo_dict]
        except AttributeError:
            grupos = None

        return grupos

    def get_comites_etica(self):
        try:
            comites_dict = self.get_classificacoes_proj(self.COD_CLASSIFICACAO_PRJ_COMITE_ETICA)
            comites = [(d[u'ID_CLASSIFICACAO'], d[u'DESCRICAO'].encode('utf-8')) for d in comites_dict]
        except AttributeError:
            comites = None

        return comites


class SIEClassifProjetos(SIE):
    def __init__(self):
        super(SIEClassifProjetos, self).__init__()
        self.path = "CLASSIF_PROJETOS"

    @deprecated
    def criarClassifProjetos(self, ID_PROJETO, ID_CLASSIFICACAO):
        """

        :type ID_PROJETO: int
        :param ID_PROJETO: Identificador único de um projeto
        :type ID_CLASSIFICACAO: int
        :param ID_CLASSIFICACAO: Identificador único da classificação de um projeto
        :rtype: unirio.api.result.APIPOSTResponse
        """
        classifProj = {
            "ID_PROJETO": ID_PROJETO,
            "ID_CLASSIFICACAO": ID_CLASSIFICACAO
        }

        try:
            return self.api.post(self.path, classifProj)
        except APIException as e:
            raise SIEException("Não foi possível criar uma nova classificação para o projeto.", e)

    @deprecated
    def removerClassifProjetos(self, ID_CLASSIF_PROJETO):
        self.api.delete(self.path, {"ID_CLASSIF_PROJETO": ID_CLASSIF_PROJETO})

    @deprecated
    def removerClassifProjetosDeProjeto(self, ID_PROJETO):
        params = {
            "ID_PROJETO": ID_PROJETO,
            "LMIN": 0,
            "LMAX": 9999
        }
        try:
            classifs = self.api.get(self.path, params, ["ID_CLASSIF_PROJETO"], bypass_no_content_exception=True)
            for classif in classifs:
                self.removerClassifProjetos(classif['ID_CLASSIF_PROJETO'])
        except APIException as e:
            raise SIEException("Falha ao remover classificações", e)

    @deprecated
    def getClassifProjetos(self, ID_PROJETO):
        params = {
            "ID_PROJETO": ID_PROJETO,
            "LMIN": 0,
            "LMAX": 9999
        }
        try:
            return self.api.get(self.path, params)
        except ValueError:
            return None

    @deprecated
    def getClassifProjetosEnsino(self, ID_PROJETO):
        try:
            return self.getClassifProjetos(ID_PROJETO).content[0]
        except ValueError:
            return None

    @deprecated
    def atualizar(self, ID_CLASSIF_PROJETO, ID_CLASSIFICACAO):
        raise NotImplementedError
        # self.db.log_admin.insert(
        #             acao='update',
        #             valores=ID_CLASSIFICACAO,
        #             tablename='CLASSIF_PROJETOS',
        #             colname='ID_CLASSIFICACAO',
        #             uid=ID_CLASSIF_PROJETO,
        #             user_id=current.auth.user_id,
        #             dt_alteracao=datetime.now()
        #     )
        # return self.api.put(self.path, {
        #     'ID_CLASSIF_PROJETO': ID_CLASSIF_PROJETO,
        #     'ID_CLASSIFICACAO': ID_CLASSIFICACAO
        # })

    def atualizar_classificacoes(self, id_projeto, classificacoes_cnpq, grupos, comite, camara):
        """

        :param id_projeto:
        :param classificacoes_cnpq:
        :param grupos:
        :param comite:
        :param camara:
        :return:
        """

        # pior maneira de se fazer isso: deletar o que tem, criar de novo.
        self.removerClassifProjetosDeProjeto(id_projeto)  # TRY???

        todas_classificacoes = camara + classificacoes_cnpq + comite + grupos

        for classificacao in todas_classificacoes:
            self.criarClassifProjetos(id_projeto, classificacao)

    def get_classif_projeto(self, params):

        params.update({
            "LMIN": 0,
            "LMAX": 9999,
        })
        try:
            res = self.api.get("V_PROJETOS_CLASSIFICACOES", params)
            return res.content if res is not None else []
        except (AttributeError, ValueError, NoContentException):
            return []

    def get_classificacoes_cnpq(self, id_projeto):

        params = {
            "ID_PROJETO": id_projeto,
            "CLASSIFICACAO_ITEM": SIEClassificacoesPrj.COD_CLASSIFICACAO_PRJ_CLASSIFICACAO_CNPQ
        }
        classificacoes_cnpq = self.get_classif_projeto(params)
        if classificacoes_cnpq:
            ids_classificacoes_cnpq = [row[u'ID_CLASSIFICACAO'] for row in classificacoes_cnpq]
            return ids_classificacoes_cnpq
        return []

    def get_grupos_cnpq(self, id_projeto):

        params = {
            "ID_PROJETO": id_projeto,
            "CLASSIFICACAO_ITEM": SIEClassificacoesPrj.COD_CLASSIFICACAO_PRJ_GRUPO_CNPQ
        }
        grupos_cnpq = self.get_classif_projeto(params)
        if grupos_cnpq:
            ids_grupos_cnpq = [row[u'ID_CLASSIFICACAO'] for row in grupos_cnpq]
            return ids_grupos_cnpq
        return []

    def get_camara_pesquisa(self, id_projeto):
        params = {
            "ID_PROJETO": id_projeto,
            "CLASSIFICACAO_ITEM": SIEClassificacoesPrj.COD_CLASSIFICACAO_PRJ_CAMARA_PESQUISA
        }
        camara_pesquisa = self.get_classif_projeto(params)
        if camara_pesquisa:
            return camara_pesquisa[0][u"ID_CLASSIFICACAO"]
        return None

    def get_comite_etica(self, id_projeto):
        params = {
            "ID_PROJETO": id_projeto,
            "CLASSIFICACAO_ITEM": SIEClassificacoesPrj.COD_CLASSIFICACAO_PRJ_COMITE_ETICA
        }
        comite_etica = self.get_classif_projeto(params)
        if comite_etica:
            return comite_etica[0][u"ID_CLASSIFICACAO"]
        return None