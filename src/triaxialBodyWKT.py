#/usr/bin/env python3
from string import Template
from abc import ABC, abstractmethod, ABCMeta
from igeodeticwkt import IGeodeticCRS
from iprojectedwkt import IProjectedCRS
import numpy

class Body(ABC):
    __metaclass__ = ABCMeta
    def __init__(self, data):
        datum_template = """DATUM["$datum_name",
            TRIAXIAL["$ellipsoide_name", $semi_major, $semi_median, $semi_minor, LENGTHUNIT["metre", 1, ID["EPSG", 9001]]$anchor
        ],
        PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9102]]]"""    
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
            semi_major=self._data['semiMajorAxis'], semi_median=self._data['semiMedianAxis'], semi_minor=self._data['semiMinorAxis'],
            anchor=anchor
        )               

class TriaxialBody(Body, IGeodeticCRS):

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

class ProjectedTriaxialBody(Body, IProjectedCRS):

    def __init__(self, data, keywordOdetic):
        Body.__init__(self, data)
        IProjectedCRS.__init__(self)
        self._keywordOdetic = keywordOdetic   
        self._parameter = """PARAMETER["$param_key", $param_val, $param_unit, ID["$param_code", $param_code_value]]"""
        self._methodID = """,ID["$method_autority",$method_code]"""   
        cs_template = """CS[Cartesian, 2],
    AXIS["$longAxis", $longitudeDirection, ORDER[1]],
    AXIS["Northing (N)", north, ORDER[2]],
    LENGTHUNIT["metre", 1, ID[\"EPSG\", 9001]]"""
        self._cs_template= Template(cs_template)                               

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

class OcentricTriaxial(TriaxialBody):
    """Ocentric triaxial body
    """
    
    def __init__(self, data):
        """Constructor
        
        Arguments:
            data {pandas} -- planetocentric CRS
        """         
        TriaxialBody.__init__(self, data)
        cs_template = """CS[spherical, 3],
    AXIS["Planetocentric latitude (U)", north, ORDER[1], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9102]]],
    AXIS["Planetocentric longitude (V)", $longitudeDirection, ORDER[2], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9102]]],
    AXIS["Radius (R)", up, ORDER[3], LENGTHUNIT["metre", 1, ID["EPSG", 9001]]]"""  
        self._cs_template= Template(cs_template)   

    def getCs(self):
        """Returns the coordinate system
        Triaxial bodies are asteroid/comets. The longitude for these bodies are always positive to East.

        Returns:
            string -- the coordinate system
        """    
        assert self._data['longitudeDirection'] == 'east', "longitude Direction must be east, not %s"%self._data['longitudeDirection']
        return self._cs_template.substitute(longitudeDirection=self._data['longitudeDirection'])               


class OgraphicTriaxial(TriaxialBody):
    """Ographic triaxial body
    """

    def __init__(self, data):
        """Constructor
        
        Arguments:
            data {pandas} -- planetocentric CRS
        """         
        TriaxialBody.__init__(self, data)
        cs_template = """CS[ellipsoidal, 2],
    AXIS["Latitude (B)", north, ORDER[1]],
    AXIS["Longitude (L)", $longitudeDirection, ORDER[2]],
    ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9102]]"""          
        self._cs_template= Template(cs_template)

    def getCs(self):
        """Returns the coordinate system
        Triaxial bodies are asteroid/comets. The longitude for these bodies are always positive to East.

        Returns:
            string -- the coordinate system
        """  
        assert self._data['longitudeDirection'] == 'east', "longitude Direction must be east, not %s"%self._data['longitudeDirection']
        return self._cs_template.substitute(longitudeDirection=self._data['longitudeDirection'])            

class ProjectedOcentricTriaxial(ProjectedTriaxialBody):
    """Projected planetocentric CRS for a triaxial body
    """

    def __init__(self, data):
        """Constructor
        
        Arguments:
            data {pandas} -- planetocentric CRS
        """        
        ProjectedTriaxialBody.__init__(self, data, "BASEGEODCRS") 

    def getCs(self):
        """Returns the coordinate system
        Triaxial bodies are asteroid/comets. The longitude for these bodies are always positive to East.

        Returns:
            string -- the coordinate system
        """         
        assert self._data['longitudeDirection'] == 'east', "longitude Direction must be east, not %s"%self._data['longitudeDirection']
        return self._cs_template.substitute(longitudeDirection="east", longAxis="Easting (E)")                 

class ProjectedOgraphicTriaxial(ProjectedTriaxialBody):
    """Projected planetographic CRS for a triaxial body  
    """    

    def __init__(self, data):
        """Constructor
        
        Arguments:
            data {pandas} -- planetographic CRS
        """        
        ProjectedTriaxialBody.__init__(self, data, "BASEGEOGCRS")  

    def getCs(self):
        """Returns the coordinate system
        Triaxial bodies are asteroid/comets. The longitude for these bodies are always positive to East.

        Returns:
            string -- the coordinate system
        """        
        assert self._data['longitudeDirection'] == 'east', "longitude Direction must be east, not %s"%self._data['longitudeDirection']
        return self._cs_template.substitute(longitudeDirection="east", longAxis="Easting (E)")               
