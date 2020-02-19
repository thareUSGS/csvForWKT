#/usr/bin/env python3
from string import Template
from abc import ABC, abstractmethod, ABCMeta
from .iprojectedwkt import IProjectedCRS
from .igeodeticwkt import IGeodeticCRS
import numpy

class Body(ABC):
    __metaclass__ = ABCMeta
    def __init__(self, data):
        datum_template = """DATUM["$datum_name",
            ELLIPSOID["$ellipsoide_name", $radius, $inverse_flat, LENGTHUNIT["metre", 1]]$anchor
        ],
        PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]]"""    
        self._anchor = """,\n            ANCHOR["$primeMeridianName: $primeMeridianValue"]"""
        self._datum_template= Template(datum_template)    
        self._data = data    

    def getDatumBody(self):
        if self._data['primeMeridianName'] == "Reference_Meridian":
            anchor = ""
        else:
            templ = Template(self._anchor)
            anchor = templ.substitute(primeMeridianName=self._data['primeMeridianName'], primeMeridianValue=self._data['primeMeridianValue'])
                  
        return self._datum_template.substitute(
            datum_name=self._data['datum_name'], ellipsoide_name=self._data['ellipsoid_name'],
            radius=self._data['semiMajorAxis'], inverse_flat=self._data['inverseFlatenning'],
            anchor=anchor
        )                          

class BiaxialBody(Body, IGeodeticCRS):

    def __init__(self, data):
        Body.__init__(self, data)
        IGeodeticCRS.__init__(self)  

    def getDatum(self):
        return self.getDatumBody()

    def getName(self):
        return self._data['name']     

    def getAuthority(self):
        return self._data['authority']

    def getCode(self): 
        return self._data['code']

    def getVersion(self):
        return self._data['version']

    def getRemark(self):
        return self._data['remark']             


class ProjectedBiaxialBody(Body, IProjectedCRS):

    def __init__(self, data, keywordOdetic):
        Body.__init__(self, data)
        IProjectedCRS.__init__(self)
        self._keywordOdetic = keywordOdetic   
        self._parameter = """PARAMETER["$param_key", $param_val, $param_unit, ID["$param_code", $param_code_value]]"""
        self._methodID = """,ID["$method_autority",$method_code]"""  

    def getDatum(self):
        return self.getDatumBody()            

    def getName(self):
        return self._data['name']     

    def getAuthority(self):
        return self._data['authority']

    def getCode(self): 
        return self._data['code']

    def getVersion(self):
        return self._data['version']

    def getRemark(self):
        return self._data['remark']                                  

    def getProjectionName(self): 
        return self._data['name']
    
    def getConversionName(self):
        return self._data['name']

    def getMethodName(self):
        return self._data['method']

    def getMethodId(self):
        return self._computeMethodID(self._data) 

    def getParameters(self):
        return ",\n        ".join(self._computeParameters(self._data))    

    def getKeywordOdetic(self):
        return self._keywordOdetic       
                                       

class PlanetOgraphicEllipsoid(BiaxialBody):
    
    def __init__(self, data):
        BiaxialBody.__init__(self, data)
        cs_template = """CS[ellipsoidal, 2],
    AXIS["Latitude (B)", north, ORDER[1]],
    AXIS["Longitude (L)", $longitudeDirection, ORDER[2]],
    ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]"""   
        self._cs_template= Template(cs_template)        

    def getCs(self):
        return self._cs_template.substitute(longitudeDirection=self._data['longitudeDirection'])


class PlanetOcentricEllipsoid(BiaxialBody):

    def __init__(self, data):
        BiaxialBody.__init__(self, data)
        cs_template  = """CS[spherical, 3],
    AXIS["Planetocentric latitude (U)", north, ORDER[1], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
    AXIS["Planetocentric longitude (V)", $longitudeDirection, ORDER[2], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
    AXIS["Radius (R)", up, ORDER[3], LENGTHUNIT["metre", 1, ID["EPSG", 9001]]]"""  
        self._cs_template= Template(cs_template)          

    def getCs(self):
        return self._cs_template.substitute(longitudeDirection=self._data['longitudeDirection'])



class ProjectedOcentricEllipsoid(ProjectedBiaxialBody):

    def __init__(self, data):
        ProjectedBiaxialBody.__init__(self, data, "BASEGEODCRS")
        cs_template = """CS[Cartesian, 2],
    AXIS["$longAxis", $longitudeDirection, ORDER[1]],
    AXIS["Northing (N)", north, ORDER[2]],
    LENGTHUNIT["metre", 1, ID[\"EPSG\", 9001]]"""
        self._cs_template= Template(cs_template)
        self._parameter = """PARAMETER["$param_key", $param_val, $param_unit, ID["$param_code", $param_code_value]]"""
        self._methodID = """,ID["$method_autority",$method_code]"""            
          
    def getCs(self):
        assert self._data['longitudeDirection'] == 'east', "longitude Direction must be east for ocentric CRS, not %s"%self._data['longitudeDirection']
        longAxis = "Easting (E)" if self._data['longitudeDirection'] == 'east' else "Westing (W)"
        return self._cs_template.substitute(longitudeDirection=self._data['longitudeDirection'], longAxis=longAxis)       
                 

class ProjectedOgraphicEllipsoid(ProjectedBiaxialBody):

    def __init__(self, data):
        ProjectedBiaxialBody.__init__(self, data, "BASEGEOGCRS")
        cs_template = """CS[Cartesian, 2],
    AXIS["$longAxis", $longitudeDirection, ORDER[1]],
    AXIS["Northing (N)", north, ORDER[2]],
    LENGTHUNIT["metre", 1, ID[\"EPSG\", 9001]]"""
        self._cs_template= Template(cs_template)          

    def getCs(self):
        longAxis = "Easting (E)" if self._data['longitudeDirection'] == 'east' else "Westing (W)"
        return self._cs_template.substitute(longitudeDirection=self._data['longitudeDirection'], longAxis=longAxis)        
        