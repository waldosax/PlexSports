class AssertionException(Exception):
	def __init__(self, message, **kwargs):
		self.__dict__ = kwargs
		self.message = message

