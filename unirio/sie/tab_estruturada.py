# coding=utf-8
from unirio.sie.base import SIE
from unirio.sie.exceptions import SIEException
from unirio.sie.utils import encoded_tab_estruturada
from unirio.api.exceptions import NoContentException


class SIETabEstruturada(SIE):
    path = "TAB_ESTRUTURADA"

    COD_TABELA_ESTADOS = 206
    COD_IND_ATIVO = 'S'

    def __init__(self):
        super(SIETabEstruturada, self).__init__()
        self.cacheTime *= 2

    def descricaoDeItem(self, ITEM_TABELA, COD_TABELA):
        """
        Método de conveniência para

        :type ITEM_TABELA: int
        :type COD_TABELA: int
        :param ITEM_TABELA:
        :param COD_TABELA:
        :return:
        """
        params = {
            "ITEM_TABELA": ITEM_TABELA,
            "COD_TABELA": COD_TABELA,
            "LMIN": 0,
            "LMAX": 1
        }
        fields = ["DESCRICAO"]
        try:
            return self.api.get(self.path, params, fields).first()["DESCRICAO"]
        except NoContentException as e:
            raise SIEException("Descrição não encontrada.", e)

    def itemsDeCodigo(self, COD_TABELA):
        """
        Dado um COD_TABELA, a função retornará uma lista de dicionários de valores possíveis de ITEM_TABELA e sua
        DESCRICAO

        :param COD_TABELA: Identificador de único de um domínio de valores de uma tabela
        :raise AttributeError: Uma exception é disparada caso nenhum item seja encontrado para o COD_TABELA
        :rtype : list
        :return: Uma lista de dicionários contendo as chaves `ITEM_TABELA` e `COD_TABELA`
        """
        params = {
            "COD_TABELA": COD_TABELA,
            "LMIN": 0,
            "LMAX": 99999,
            "IND_ATIVO": self.COD_IND_ATIVO
        }
        fields = ["ITEM_TABELA", "DESCRICAO"]
        try:
            items = self.api.get(self.path, params, fields).content
            # Primeiro item de uma de ITEMS de uma TABELA é sempre a descrição do conteúdo
            return items[1:]
        except NoContentException as e:
            raise SIEException("Nenhum item encontreado para este código.", e)

    @encoded_tab_estruturada('utf-8')
    def get_drop_down_options(self, codigo_tabela, valores_proibidos=(0,)):
        """
        Dado um COD_TABELA, a função retornará uma lista de tuplas contendo o código do item e a descrição do mesmo

        :param COD_TABELA: Identificador de único de um domínio de valores de uma tabela
        :rtype : list
        :return: Uma lista de dicionários contendo as chaves `ITEM_TABELA` e `COD_TABELA`
        """
        try:
            itens = self.itemsDeCodigo(codigo_tabela)
            itens = filter(lambda x: x[u'ITEM_TABELA'] not in valores_proibidos, itens)
            return [d.values() for d in itens]
        except SIEException:
            return []

    def get_lista_estados_federacao(self):
        """
        :return: lista contendo listas ("CodOpcao","NomeOpcao")
        """

        return self.get_drop_down_options(self.COD_TABELA_ESTADOS)
