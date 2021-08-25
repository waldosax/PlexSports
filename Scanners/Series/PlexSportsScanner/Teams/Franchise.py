
from StringUtils import *

from Team import *


class Franchise():
	def __init__(self, name=None, **kwargs):
		self.name = name or kwargs.get("name") or ""
		self.active = kwargs.get("active") == True
		self.description = deunicode(kwargs.get("description") or "") or None
		self.fromYear = int(kwargs.get("fromYear") or 0) or None
		self.toYear = int(kwargs.get("toYear") or 0) or None
		self.teams = dict()
		if kwargs.get("teams"):
			for team in kwargs["teams"].values():
				if isinstance(team, (Team)):
					self.teams.setdefault(team.fullName, team)
				else:
					self.teams.setdefault(team["fullName"] if team.get("fullName") else team.get("name"), Team(**team))

		pass

	def Augment(self, **kwargs):
		if not self.name: self.name = kwargs.get("name") or ""
		if not self.active: self.active = kwargs.get("active") == True
		if not self.description: self.description = deunicode(kwargs.get("description") or "") or None
		if not self.fromYear: self.fromYear = int(kwargs.get("fromYear") or 0) or None
		if not self.toYear: self.toYear = int(kwargs.get("toYear") or 0) or None

		if kwargs.get("teams"):
			for tm in kwargs["teams"].values():
				if isinstance(tm, (Team)):
					tmn = tm.fullName
					tmdct = tm.__dict__
				else:
					tmn = tm["fullName"] if tm.get("fullName") else tm.get("name")
					tmdct = tm

				foundTeam = False
				team = self.FindTeam(tmn)
				if team: team.Augment(**tmdct)
				else:
					if isinstance(tm, (Team)): self.teams.setdefault(tmn, tm)
					else:
						team = Team(**tmdct)
						self.teams.setdefault(tmn, team)
		pass

	def FindTeam(self, fullName, identity=None):
		if not fullName and not identity: return None
		for team in self.teams.values():

			fdct = team.identity.__dict__
			xdct = None

			if identity:
				if isinstance(identity, (TeamIdentity)): xdct = identity.__dict__
				else: xdct = identity

			if xdct:
				for testKey in xdct.keys():
					if xdct[testKey]:
						if testKey in fdct.keys():
							if fdct[testKey] == xdct[testKey]:
								return team


			if team.fullName == fullName: # TODO: Strip diacritics
				return team

	def __repr__(self):
		return self.name

class FranchiseDict(dict):
	def __init__(self, iterable=None):
		dict.__init__(self, iterable or {})

		self.__abbrevlookup = dict()

	def __hydrate_abbreviations(self):
		for franchise in dict.values(self):
			for team in franchise.teams.values():
				key = team.key
				if not key: continue
				self.__abbrevlookup.setdefault(key, team)

	def get(self, key):
		return self.__find(key)[1]

	def __getitem__(self, key):
		(foundKey, value) = self.__find(key)
		if foundKey == None:
			# TODO: Throw
			pass
		return value

	def __find(self, key):
		if key in dict.keys(self):
			return (key, dict.get(self, key))
		if not self.__abbrevlookup:
			self.__hydrate_abbreviations()

		if key in self.__abbrevlookup.keys():
			return (key, self.__abbrevlookup[key])

		return (None, None)

	def abbreviations(self):
		if not self.__abbrevlookup:
			self.__hydrate_abbreviations()
		return self.__abbrevlookup.keys()

	def franchisenames(self):
		return self.keys()

	def invalidate(self):
		self.__abbrevlookup.clear()


	def __repr__(self):
		return "\"Franchises\": {...}(%s)" % len(self)


