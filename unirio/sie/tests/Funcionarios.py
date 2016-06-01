from sie import SIEException
from sie.tests.base import SIETestCase

__author__ = 'diogomartins'


class TestFuncionarios(SIETestCase):

    def __init__(self, *args, **kwargs):
        super(TestFuncionarios, self).__init__(*args, **kwargs)

        from sie.SIEFuncionarios import SIEFuncionarios, SIEFuncionarioID
        self.valid_entry = self.api.get(SIEFuncionarios.path).first()

    def setUp(self):
        from sie.SIEFuncionarios import SIEFuncionarios, SIEFuncionarioID
        self.dao = SIEFuncionarios()
