from sie.tests.base import SIETestCase
from unirio.api.result import *
from unirio.api.exceptions import *
from datetime import date, timedelta

__author__ = 'diogomartins'


class TestOrgaosProjsPesquisa(SIETestCase):
    path = 'V_PROJETOS_ORGAOS'
    DUMMY_ID = 999999999999

    def __init__(self, *args, **kwargs):
        super(TestOrgaosProjsPesquisa, self).__init__(*args, **kwargs)
        self.valid = self.api.get(self.path).first()

        from sie.SIEProjetosPesquisa import SIEOrgaosProjsPesquisa
        self.orgaos = SIEOrgaosProjsPesquisa()

    def test_get_valid_orgao(self):
        orgao = self.orgaos.get_orgao(self.valid['ID_ORGAO_PROJETO'])
        self.assertEqual(self.valid, orgao)

    def test_get_invalid_orgao(self):
        orgao = self.orgaos.get_orgao(self.DUMMY_ID)
        self.assertEqual(orgao, {})

    def test_get_orgaoes_valid_projeto(self):
        projeto = self.api.get(TestProjetosPesquisa.path).first()
        orgs = self.orgaos.get_orgaos(projeto['ID_PROJETO'])
        self.assertIsInstance(orgs, list)
        self.assertTrue(len(orgs) >= 1, "Lista deve conter pelo menos um item")

    def test_get_orgaoes_invalid_projeto(self):
        orgs = self.orgaos.get_orgaos(self.DUMMY_ID)
        self.assertIsInstance(orgs, list)
        self.assertTrue(len(orgs) == 0)

    def test_cadastra_orgao_valid_projeto(self):
        projeto = self.api.get(TestProjetosPesquisa.path).first()
        orgao = self.orgaos.get_orgao(projeto['ID_PROJETO'])
        dummy_orgao = {
            'ID_PROJETO': projeto['ID_PROJETO'],
            'ID_UNIDADE': orgao['ID_ORIGEM'],
            'DT_INICIAL': date.today(),
            'DT_FINAL': date.today() + timedelta(days=100),
            'VL_CONTRIBUICAO': 100,
            'OBS_ORG_PROJETO': self._random_string(50),
            'FUNCAO_ORG_ITEM': orgao['FUNCAO_ORG_ITEM']
        }
        result = self.orgaos.cadastra_orgao(dummy_orgao)
        self.assertIsInstance(result, APIPOSTResponse)

    def test_cadastra_orgao_empty_orgao(self):
        with self.assertRaises(APIException):
            self.orgaos.cadastra_orgao({})

    def test_atualizar_orgao_invalid_parameters(self):
        result = self.orgaos.atualizar_orgao(self._dummy_dict())
        self.assertFalse(result)

    def test_atualizar_orgao_valid_parameters(self):
        orgao = self.api.get(self.orgaos.path).first()
        orgao['OBS_ORG_PROJETO'] = self._random_string(15)
        result = self.orgaos.atualizar_orgao(orgao)
        self.assertTrue(result)

        updated_orgao = self.api.get(self.orgaos.path, {'ID_ORGAO_PROJETO': orgao['ID_ORGAO_PROJETO']}).first()
        self.assertEqual(orgao['OBS_ORG_PROJETO'], updated_orgao['OBS_ORG_PROJETO'])


class TestParticipantesProjsPesquisa(SIETestCase):
    def setUp(self):
        pass


class TestProjetosPesquisa(SIETestCase):
    path = 'V_PROJETOS_PESQUISA'
    pass


