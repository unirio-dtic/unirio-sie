from unirio.sie.base import SIE


__author__ = 'raul'


class SIEParametrosDAO(SIE):
    def __init__(self):
        super(SIEParametrosDAO, self).__init__()

    def parametros_prod_inst(self):
        return self.api.get("PAR_PROD_INST", {}).first()
