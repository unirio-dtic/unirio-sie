from sie import SIEException
from sie.tests.base import SIETestCase

__author__ = 'diogomartins'


class TestTabEstruturada(SIETestCase):
    COD_TABELA_INVALIDO = 9999999999
    ITEM_TABELA_INVALIDO = 9999999999

    def __init__(self, *args, **kwargs):
        super(TestTabEstruturada, self).__init__(*args, **kwargs)

        from sie.SIETabEstruturada import SIETabEstruturada
        self.valid_entry = self.api.get(SIETabEstruturada.path, {"ITEM_TABELA_MIN": 1}).first()

    def setUp(self):
        from sie.SIETabEstruturada import SIETabEstruturada
        self.tab = SIETabEstruturada()

    def test_descricao_de_item_valido(self):
        descricao = self.tab.descricaoDeItem(self.valid_entry['ITEM_TABELA'], self.valid_entry['COD_TABELA'])
        self.assertEqual(descricao, self.valid_entry['DESCRICAO'])

    def test_descricao_de_item_invalido(self):
        with self.assertRaises(SIEException):
            self.tab.descricaoDeItem(self.ITEM_TABELA_INVALIDO, self.COD_TABELA_INVALIDO)

    def test_items_de_codigo_valido(self):
        items = self.tab.itemsDeCodigo(self.valid_entry['COD_TABELA'])
        self.assertIsInstance(items, list)
        for item in items:
            if item['ITEM_TABELA'] == self.valid_entry['ITEM_TABELA']:
                self.assertEqual(item['DESCRICAO'], self.valid_entry['DESCRICAO'])

    def test_items_de_codigo_invalido(self):
        with self.assertRaises(SIEException):
            self.tab.itemsDeCodigo(self.COD_TABELA_INVALIDO)

    def test_drop_down_cod_valido(self):
        items = self.tab.get_drop_down_options(self.valid_entry['COD_TABELA'])
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

    def test_drop_down_cod_invalido(self):
        items = self.tab.get_drop_down_options(self.COD_TABELA_INVALIDO)
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 0)

    def test_drop_down_cod_valido_com_valores_proibidos(self):
        valores_proibidos = (1, 2,)
        items = self.tab.get_drop_down_options(self.valid_entry['COD_TABELA'], valores_proibidos)

        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

        for i, descricao in items:
            if i in valores_proibidos:
                self.fail(i + " nao deveria estar na lista de items")

    def test_get_lista_estados_federacao(self):
        estados = self.tab.get_lista_estados_federacao()
        self.assertIsInstance(estados, list)
        self.assertGreater(len(estados), 0)