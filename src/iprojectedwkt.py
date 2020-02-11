#/usr/bin/env python3

from abc import ABC, abstractmethod, ABCMeta
from iwkt import IWKT
from string import Template
import math
import numpy as np
from enum import Enum

class DATUM(Enum):
    SPHERE = 0
    ELLIPSOID_OGRAPHIC = 1
    ELLIPSOID_OCENTRIC = 2
    TRIAXIAL_OGRAPHIC = 3
    TRIAXIAL_OCENTRIC = 4


class IProjectedCRS(ABC, IWKT):
    __metaclass__ = ABCMeta

    def __init__(self):
        self._projectedCrs = """PROJCRS["$projection_name",
    $keywordOdetic["$name",
        $datum
    ],
    CONVERSION["$conversion_name",
        METHOD["$method_name"$method_id],
        $params
    ],
    $cs,
    ID["$authority", $code, $version]
]
"""
        self._wkt = None    
        # build from http://www.epsg-registry.org/ and from http://geotiff.maptools.org/proj_list / http://docs.opengeospatial.org/is/19-008r4/19-008r4.html
        self._authorityMapping = {
            "Lambert Azimuthal Equal Area (Spherical)" : ["EPSG", 1027],
            "Equidistant Cylindrical" : ["EPSG", 1028],
            "Equidistant Cylindrical (Spherical)": ["EPSG", 1029],
            "Scale factor at natural origin": ["EPSG", 8805, "SCALEUNIT[\"unity\",1.0, ID[\"EPSG\", 9201]]"],
            "False easting": ["EPSG", 8806, "LENGTHUNIT[\"metre\", 1, ID[\"EPSG\", 9001]]"],
            "False northing": ["EPSG", 8807, "LENGTHUNIT[\"metre\", 1, ID[\"EPSG\", 9001]]"],
            "Latitude of natural origin": ["EPSG", 8801, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"],
            "Longitude of natural origin": ["EPSG", 8802, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"],
            "Latitude of false origin": ["EPSG", 8821, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"],            
            "Longitude of false origin": ["EPSG", 8822, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"],
            "Latitude of 1st standard parallel": ["EPSG", 8823, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"],
            "Latitude of 2nd standard parallel": ["EPSG", 8824, "ANGLEUNIT[\"degree\", 0.017453292519943295, ID[\"EPSG\", 9102]]"],
            "Easting at false origin": ["EPSG", 8826, "LENGTHUNIT[\"metre\", 1, ID[\"EPSG\", 9001]]"],
            "Northing at false origin": ["EPSG", 8827, "LENGTHUNIT[\"metre\", 1, ID[\"EPSG\", 9001]]"],            
            "Sinusoidal": ["GeoTIFF", 24],
            "Robinson" : ["GeoTIFF", 23],            
            "Transverse Mercator" : ["EPSG",9807],
            "Lambert Conic Conformal (2SP)": ["EPSG", 9802],
            "Stereographic": ["EPSG", 9810],
            "Lambert Azimuthal Equal Area": ["EPSG", 9820],
            "Albers Equal Area" : ["EPSG", 9822],
            "Orthographic" : ["EPSG", 9840]
        }         

    def _computeParameters(self, data):
        paramTemp = Template(self._parameter)
        paramsList = [('parameter1Name', 'parameter1Value'), ('parameter2Name', 'parameter2Value'), ('parameter3Name', 'parameter3Value'), ('parameter4Name', 'parameter4Value'), ('parameter5Name', 'parameter5Value'), ('parameter6Name', 'parameter6Value')]
        params=[]
        for name, value in paramsList:
            if math.isnan(data[value]):
                pass
            else:
                idAndUnit = self._authorityMapping[data[name]]
                params.append(paramTemp.substitute(param_key=data[name], param_val=data[value], param_unit=idAndUnit[2], param_code=idAndUnit[0], param_code_value=idAndUnit[1]))
        return params

    def _computeMethodID(self, data):
        idTemp = Template(self._methodID)
        if data['method'] in self._authorityMapping:
            methodValue = self._authorityMapping[data['method']]
            authority = methodValue[0]
            code = methodValue[1]
            result = idTemp.substitute(
                method_autority=authority,method_code=code
            )
        else:
            result = ""
        return result  

    @staticmethod
    def getProjectionCode():
        data = [        
        [10, "IAU", "2005", DATUM.SPHERE.value, "Equirectangular, clon = 0", "Equidistant Cylindrical (Spherical)", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],        
        [11, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Equirectangular, clon = 0", "Equidistant Cylindrical", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],        
        [12, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Equirectangular, clon = 0", "Equidistant Cylindrical", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],        
        [13, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Equirectangular, clon = 0", "Equidistant Cylindrical", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],        
        [14, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Equirectangular, clon = 0", "Equidistant Cylindrical", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],        
        [15, "IAU", "2005", DATUM.SPHERE.value, "Equirectangular, clon = 180", "Equidistant Cylindrical", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],           
        [16, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Equirectangular, clon = 180", "Equidistant Cylindrical", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],           
        [17, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Equirectangular, clon = 180", "Equidistant Cylindrical", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],           
        [18, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Equirectangular, clon = 180", "Equidistant Cylindrical", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],           
        [19, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Equirectangular, clon = 180", "Equidistant Cylindrical", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, "Latitude of 1st standard parallel", 0, np.nan, np.nan, np.nan, np.nan],                   
        [20, "IAU", "2005", DATUM.SPHERE.value, "Sinusoidal, clon = 0", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [21, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Sinusoidal, clon = 0", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [22, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Sinusoidal, clon = 0", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [23, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Sinusoidal, clon = 0", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [24, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Sinusoidal, clon = 0", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [25, "IAU", "2005", DATUM.SPHERE.value, "Sinusoidal, clon = 180", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [26, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Sinusoidal, clon = 180", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [27, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Sinusoidal, clon = 180", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [28, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Sinusoidal, clon = 180", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [29, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Sinusoidal, clon = 180", "Sinusoidal", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [30, "IAU", "2005", DATUM.SPHERE.value, "North Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", 90, np.nan, np.nan],                   
        [31, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "North Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", 90, np.nan, np.nan],                   
        [32, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "North Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", 90, np.nan, np.nan],                   
        [33, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "North Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", 90, np.nan, np.nan],                   
        [34, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "North Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", 90, np.nan, np.nan],                           
        [35, "IAU", "2005", DATUM.SPHERE.value, "South Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", -90, np.nan, np.nan],               
        [36, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "South Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", -90, np.nan, np.nan],               
        [37, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "South Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", -90, np.nan, np.nan],               
        [38, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "South Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", -90, np.nan, np.nan],               
        [39, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "South Polar, clon = 0", "Stereographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 1, "Latitude of natural origin", -90, np.nan, np.nan],               
        [40, "IAU", "2005", DATUM.SPHERE.value, "Mollweide, clon = 0", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [41, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Mollweide, clon = 0", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [42, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Mollweide, clon = 0", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [43, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Mollweide, clon = 0", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [44, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Mollweide, clon = 0", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [45, "IAU", "2005", DATUM.SPHERE.value, "Mollweide, clon = 180", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [46, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Mollweide, clon = 180", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [47, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Mollweide, clon = 180", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [48, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Mollweide, clon = 180", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [49, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Mollweide, clon = 180", "Mollweide", "False easting", 0, "False northing", 0, "Longitude of natural origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [50, "IAU", "2005", DATUM.SPHERE.value, "Robinson, clon = 0", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [51, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Robinson, clon = 0", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [52, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Robinson, clon = 0", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [53, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Robinson, clon = 0", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [54, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Robinson, clon = 0", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [55, "IAU", "2005", DATUM.SPHERE.value, "Robinson, clon = 180", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan], 
        [56, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Robinson, clon = 180", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan], 
        [57, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Robinson, clon = 180", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan], 
        [58, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Robinson, clon = 180", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan], 
        [59, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Robinson, clon = 180", "Robinson", "False easting", 0, "False northing", 0, "Longitude of false origin", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        [60, "IAU", "2005", DATUM.SPHERE.value, "Tranverse Mercator", "Transverse Mercator", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 0.9996, "Latitude of natural origin", 0, np.nan, np.nan],                   
        [61, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Tranverse Mercator", "Transverse Mercator", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 0.9996, "Latitude of natural origin", 0, np.nan, np.nan],                   
        [62, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Tranverse Mercator", "Transverse Mercator", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 0.9996, "Latitude of natural origin", 0, np.nan, np.nan],                   
        [63, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Tranverse Mercator", "Transverse Mercator", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 0.9996, "Latitude of natural origin", 0, np.nan, np.nan],                   
        [64, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Tranverse Mercator", "Transverse Mercator", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Scale factor at natural origin", 0.9996, "Latitude of natural origin", 0, np.nan, np.nan],                           
        [65, "IAU", "2005", DATUM.SPHERE.value, "Orthographic", "Orthographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 90, np.nan, np.nan, np.nan, np.nan],                   
        [66, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Orthographic", "Orthographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 90, np.nan, np.nan, np.nan, np.nan],                   
        [67, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Orthographic", "Orthographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 90, np.nan, np.nan, np.nan, np.nan],                   
        [68, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Orthographic", "Orthographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 90, np.nan, np.nan, np.nan, np.nan],                   
        [69, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Orthographic", "Orthographic", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 90, np.nan, np.nan, np.nan, np.nan],                           
        [70, "IAU", "2005", DATUM.SPHERE.value, "Lambert Conic Conformal", "Lambert Conic Conformal (2SP)", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 0, "Latitude of 1st standard parallel", -20, "Latitude of 2nd standard parallel", 20],        
        [71, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Lambert Conic Conformal", "Lambert Conic Conformal (2SP)", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 0, "Latitude of 1st standard parallel", -20, "Latitude of 2nd standard parallel", 20],        
        [72, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Lambert Conic Conformal", "Lambert Conic Conformal (2SP)", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 0, "Latitude of 1st standard parallel", -20, "Latitude of 2nd standard parallel", 20],        
        [73, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Lambert Conic Conformal", "Lambert Conic Conformal (2SP)", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 0, "Latitude of 1st standard parallel", -20, "Latitude of 2nd standard parallel", 20],        
        [74, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Lambert Conic Conformal", "Lambert Conic Conformal (2SP)", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 0, "Latitude of 1st standard parallel", -20, "Latitude of 2nd standard parallel", 20],        
        [75, "IAU", "2005", DATUM.SPHERE.value, "Lambert Azimuthal Equal Area (Spherical)", "Lambert Azimuthal Equal Area (Spherical)", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 0, np.nan, np.nan, np.nan, np.nan],        
        [76, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Lambert Azimuthal Equal Area", "Lambert Azimuthal Equal Area", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 90, np.nan, np.nan, np.nan, np.nan],        
        [77, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Lambert Azimuthal Equal Area", "Lambert Azimuthal Equal Area", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 90, np.nan, np.nan, np.nan, np.nan],        
        [78, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Lambert Azimuthal Equal Area", "Lambert Azimuthal Equal Area", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 90, np.nan, np.nan, np.nan, np.nan],        
        [79, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Lambert Azimuthal Equal Area", "Lambert Azimuthal Equal Area", "False easting", 0, "False northing", 0, "Longitude of natural origin", 0, "Latitude of natural origin", 90, np.nan, np.nan, np.nan, np.nan],        
        [80, "IAU", "2005", DATUM.SPHERE.value, "Albers Equal Area", "Albers Equal Area", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 40, "Latitude of 1st standard parallel", 60, "Latitude of 2nd standard parallel", 20],        
        [81, "IAU", "2005", DATUM.ELLIPSOID_OGRAPHIC.value, "Albers Equal Area", "Albers Equal Area", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 40, "Latitude of 1st standard parallel", 60, "Latitude of 2nd standard parallel", 20],        
        [82, "IAU", "2005", DATUM.ELLIPSOID_OCENTRIC.value, "Albers Equal Area", "Albers Equal Area", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 40, "Latitude of 1st standard parallel", 60, "Latitude of 2nd standard parallel", 20],        
        [83, "IAU", "2005", DATUM.TRIAXIAL_OGRAPHIC.value, "Albers Equal Area", "Albers Equal Area", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 40, "Latitude of 1st standard parallel", 60, "Latitude of 2nd standard parallel", 20],        
        [84, "IAU", "2005", DATUM.TRIAXIAL_OCENTRIC.value, "Albers Equal Area", "Albers Equal Area", "Easting at false origin", 0, "Northing at false origin", 0, "Longitude of false origin", 0, "Latitude of false origin", 40, "Latitude of 1st standard parallel", 60, "Latitude of 2nd standard parallel", 20]
        ]   
        return data     

        # # It seems it is OK the next GDAL release : https://github.com/OSGeo/gdal/pull/101
        # # Need to check projection parameters when fixed in GDAL
        # AUTO_OBLIQUE_CYLINDRICAL = {  # Auto Oblique Cylindrical Equal Area -- Problem for this projection
        #     "code": 78,
        #     "projection": "Oblique_Cylindrical_Equal_Area",
        #     "parameters": {
        #         "False_Easting": 0,
        #         "False_Northing": 0,
        #         "Central_Meridian": 0.0,
        #         "Standard_Parallel_1": 0.0
        #     }
        # }



    @abstractmethod
    def getProjectionName(self): raise NotImplementedError

    @abstractmethod
    def getKeywordOdetic(self): raise NotImplementedError

    @abstractmethod
    def getName(self): raise NotImplementedError    

    @abstractmethod
    def getDatum(self): raise NotImplementedError        

    @abstractmethod
    def getConversionName(self): raise NotImplementedError    

    @abstractmethod
    def getMethodName(self): raise NotImplementedError  

    @abstractmethod
    def getMethodId(self): raise NotImplementedError   

    @abstractmethod
    def getParameters(self): raise NotImplementedError

    @abstractmethod
    def getCs(self): raise NotImplementedError

    @abstractmethod
    def getAuthority(self): raise NotImplementedError

    @abstractmethod
    def getCode(self): raise NotImplementedError 

    @abstractmethod
    def getVersion(self): raise NotImplementedError  

    @abstractmethod
    def getRemark(self): raise NotImplementedError 

    def computeWKT(self):
        projected_crs = Template(self._projectedCrs)  
        self._wkt = projected_crs.substitute(
            projection_name=self.getProjectionName(), keywordOdetic=self.getKeywordOdetic(), name=self.getName(),
            datum=self.getDatum(), conversion_name=self.getConversionName(), method_name=self.getMethodName(),
            method_id=self.getMethodId(), params=self.getParameters(), cs=self.getCs(),
            authority=self.getAuthority(), code=self.getCode(), version=self.getVersion()
        )

    def getWKT(self):
        return self._wkt
