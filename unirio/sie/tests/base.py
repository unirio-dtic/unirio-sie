import random
import string
from unirio.api import UNIRIOAPIRequest, APIServer
from gluon import current
from gluon.storage import Storage
import unittest

__author__ = 'diogomartins'
env = APIServer.LOCAL


class SIETestCase(unittest.TestCase):
    API_KEY_VALID = '9287c7e89bc83bbce8f9a28e7d448fa7366ce23f163d2c385966464242e0b387e3a34d0e205cb775d769a44047995075'

    def __init__(self, *args, **kwargs):
        super(SIETestCase, self).__init__(*args, **kwargs)
        self.api = UNIRIOAPIRequest(self.API_KEY_VALID, env, debug=True, cache=None)
        current.api = self.api
        current.session = Storage()
        current.session.usuario = Storage()

    def _random_string(self, length):
        return ''.join(random.choice(string.lowercase) for i in xrange(length))

    def _dummy_dict(self, size=3):
        return {self._random_string(5): self._random_string(10) for k in xrange(0, size)}
