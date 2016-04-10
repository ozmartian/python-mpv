class MpvError(BaseException):

    def __init__(self, func, error_code, reason, args):
        self.func = func
        self.error_code = error_code
        self.reason = reason
        self.args = args

    def __str__(self):
        return '"{}" {}. {}'.format(self.func, self.reason, self.args)
