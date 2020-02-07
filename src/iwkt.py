#/usr/bin/env python3

from abc import ABCMeta, abstractmethod

class IWKT:
    __metaclass__ = ABCMeta

    @classmethod
    def version(self): return "2.0"

    @abstractmethod
    def getWkt(self): raise NotImplementedError

    @abstractmethod
    def _computeWkt(self, data): raise NotImplementedError