class SIEException(Exception):
    """ Bad things happens. """
    def __init__(self, msg, cause=None, *args, **kwargs):
        """
        An exception when using the SIE DAO.
        :type msg: str
        :type cause: BaseException
        """
        super(SIEException, self).__init__(*args, **kwargs)
        self.msg = msg
        self.cause = cause

    def __str__(self):
        return self.msg + "\n\tCaused by " + str(type(self.cause)) + ": " + str(self.cause) + "\n\t"
