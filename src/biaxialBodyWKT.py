#/usr/bin/env python3
from string import Template
from abc import ABCMeta, abstractmethod
from iwkt import IWKT
import math


class BiaxialBody(IWKT):

    def __init__(self, data):
        template = """GEODCRS["$name",
    DATUM["$datum_name",
        ELLIPSOID["$ellipsoide_name", $radius, $inverse_flat, LENGTHUNIT["metre", 1]]],
        PRIMEM["$primeMeridianName", $primeMeridianValue, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9102]]],
    $cs,
    ID["$authority", $code, $version], REMARK["$remark"]]
    """    
        self._s = Template(template)    
        self._data = data

    @abstractmethod
    def getWkt(self): raise NotImplementedError

    @abstractmethod
    def _computeWkt(self, data): raise NotImplementedError
    

class PlanetOgraphicEllipsoid(BiaxialBody):
    
    def __init__(self, data):
        BiaxialBody.__init__(self, data)
        self._cs = """CS[ellipsoidal, 2],
        AXIS["Latitude (B)", north, ORDER[1]],
        AXIS["Longitude (L)", $longitudeDirection, ORDER[2]],
        ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9102]]"""      
        self._wkt = self._computeWKT(data) 

    def _computeWKT(self, data) :
        if data['primeMeridianValue'] != 0:
            primeMeridianValue = 0
            primeMeridianName = "Reference meridian "+str(data['primeMeridianValue']) + "° east from " + data['primeMeridianName']
        else:
            primeMeridianValue = data['primeMeridianValue']
            primeMeridianName = data['primeMeridianName']        
        csTemp = Template(self._cs)          
        cs = csTemp.substitute(longitudeDirection=data['longitudeDirection'])
        wkt = self._s.substitute(
            name=data['name'], datum_name=data['datum_name'], ellipsoide_name=data['ellipsoid_name'], 
            radius=data['semiMajorAxis'], inverse_flat=data['inverseFlatenning'], 
            primeMeridianName=primeMeridianName, primeMeridianValue=primeMeridianValue, cs=cs, 
            authority=data['authority'], code=data['code'], version=data['version'], remark=data['remark']
        )
        return wkt   

    def getWkt(self):
        return self._wkt                  


class PlanetOcentricEllipsoid(BiaxialBody):

    def __init__(self, data):
        BiaxialBody.__init__(self, data)
        self._cs = """CS[spherical, 3],
        AXIS["Planetocentric latitude (U)", north, ORDER[1], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9102]]],
        AXIS["Planetocentric longitude (V)", $longitudeDirection, ORDER[2], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9102]]],
        AXIS["Radius (R)", up, ORDER[3], LENGTHUNIT["metre", 1, ID["EPSG", 9001]]]"""  
        self._wkt = self._computeWKT(data)  

    def _computeWKT(self, data) :
        csTemp = Template(self._cs)  
        cs = csTemp.substitute(longitudeDirection=data['longitudeDirection'])        
        wkt = self._s.substitute(
            name=data['name'], datum_name=data['datum_name'], ellipsoide_name=data['ellipsoid_name'], 
            radius=data['semiMajorAxis'], inverse_flat=data['inverseFlatenning'], 
            primeMeridianName=data['primeMeridianName'], primeMeridianValue=data['primeMeridianValue'], cs=cs,
            authority=data['authority'], code=data['code'], version=data['version'], remark=data['remark']
        )
        return wkt  

    def getWkt(self):
        return self._wkt 


class ProjectionEllipsoid(BiaxialBody):

    def __init__(self, data):

        BiaxialBody.__init__(self, data)
        template = """
PROJCRS["$name",
BASEGEODCRS["$name_planetodetic",
    DATUM["$datum_name",
    ELLIPSOID["$ellipsoide_name", $radius, $inverse_flat, LENGTHUNIT["metre", 1, ID["EPSG", 9001]]]],
    PRIMEM["$primeMeridianName", $primeMeridianValue, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9102]]]],
CONVERSION["$name",
    METHOD["$method"],
    $params
$cs,
ID["$authority", $code, $version]]            
            """

        self._s = Template(template)

        self._cs = """CS[Cartesian, 2],
    AXIS["$longAxis", $longitudeDirection, ORDER[1]],
    AXIS["Northing (N)", north, ORDER[2]],
    LENGTHUNIT["metre", 1, ID[\"EPSG\", 9001]]"""

        self._parameter = """PARAMETER["$param_key", $param_val, $param_unit, ID["$param_code", $param_code_value]], """


        # build from http://www.epsg-registry.org/ and from http://geotiff.maptools.org/proj_list / http://docs.opengeospatial.org/is/19-008r4/19-008r4.html
        self._authorityMapping = {
            "Scale factor at natural origin": ["EPSG", 8805, "SCALEUNIT[\"unity\",1.0, ID[\"EPSG\", 9201]]"],
            "False easting": ["EPSG", 8806, "LENGTHUNIT[\"metre\", 1, ID[\"EPSG\", 9001]]"],
            "False northing": ["EPSG", 8807, "LENGTHUNIT[\"metre\", 1, ID[\"EPSG\", 9001]]"],
            "Longitude of natural origin": ["EPSG", 8802, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"],
            "Latitude of natural origin": ["EPSG", 8801, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"],
            "Equidistant Cylindrical" : ["EPSG", 1028],
            "Equidistant Cylindrical (Spherical)": ["EPSG", 1029],
            "Stereographic": ["EPSG", 9810],
            "Sinusoidal": ["GeoTIFF", 24],
            "Robinson" : ["GeoTIFF", 23],
            "Latitude of 1st standard parallel": ["EPSG", 8823, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"],
            "Longitude of false origin": ["EPSG", 8822, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"]
        } 
       
        self._wkt = self._computeWKT(data)              

    def _computeWKT(self, data) :
        csTemp = Template(self._cs)
        longAxis = None
        if data['longitudeDirection'] == "east":
            longAxis = "Easting (E)"
        else:
            longAxis = "Westing (W)"
        cs = csTemp.substitute(longAxis=longAxis, longitudeDirection=data['longitudeDirection'])
        paramTemp = Template(self._parameter)
        paramsList = [('parameter1Name', 'parameter1Value'), ('parameter2Name', 'parameter2Value'), ('parameter3Name', 'parameter3Value'), ('parameter4Name', 'parameter4Value'), ('parameter5Name', 'parameter5Value'), ('parameter6Name', 'parameter6Value')]
        params=""
        for name, value in paramsList:
            if math.isnan(data[value]):
                pass
            else:
                idAndUnit = self._authorityMapping[data[name]]
                params += paramTemp.substitute(param_key=data[name], param_val=data[value], param_unit=idAndUnit[2], param_code=idAndUnit[0], param_code_value=idAndUnit[1])
        wkt = self._s.substitute(            
            name_planetodetic=data['name'], datum_name=data['datum_name'], ellipsoide_name=data['ellipsoid_name'], 
            radius=data['semiMajorAxis'], inverse_flat=data['inverseFlatenning'], 
            primeMeridianName=data['primeMeridianName'], primeMeridianValue=data['primeMeridianValue'],cs=cs, name=data['name'], method=data['method'], params=params, 
            authority=data['authority'], code=data['code'], version=data['version']
        )
        return wkt

    def getWkt(self):
        return self._wkt        