# /usr/bin/env python3

from abc import ABC, abstractmethod, ABCMeta
from iwkt import IWKT
from string import Template

class IGeodeticCRS(ABC, IWKT):
    __metaclass__ = ABCMeta

    def __init__(self):
        self._geodeticCrs = """GEODCRS["$name",
    $datum,
    $cs,
    ID["$authority", $code, $version], REMARK["$remark"]
]
"""
        self._wkt = None

    @abstractmethod
    def getName(self): raise NotImplementedError    

    @abstractmethod
    def getCs(self): raise NotImplementedError

    @abstractmethod
    def getDatum(self): raise NotImplementedError

    @abstractmethod
    def getAuthority(self): raise NotImplementedError

    @abstractmethod
    def getCode(self): raise NotImplementedError 

    @abstractmethod
    def getVersion(self): raise NotImplementedError  

    @abstractmethod
    def getRemark(self): raise NotImplementedError            

    def computeWKT(self):
        geodetic_crs = Template(self._geodeticCrs)  
        self._wkt = geodetic_crs.substitute(
            name=self.getName(), datum=self.getDatum(), cs=self.getCs(),
            authority=self.getAuthority(), code=self.getCode(), version=self.getVersion(),
            remark=self.getRemark()
        )

    def getWKT(self):
        return self._wkt

