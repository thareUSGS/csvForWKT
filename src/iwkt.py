#/usr/bin/env python3

from abc import ABCMeta, abstractmethod

class IWKT:
    __metaclass__ = ABCMeta

    @classmethod
    def version(self): return "2.0"

    @abstractmethod
    def getWKT(self): raise NotImplementedError

    @abstractmethod
    def computeWKT(self): raise NotImplementedError