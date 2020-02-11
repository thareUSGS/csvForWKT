#/usr/bin/env python3
from abc import ABCMeta, abstractmethod
from biaxialBodyWKT import PlanetOcentricEllipsoid, PlanetOgraphicEllipsoid, ProjectedOcentricEllipsoid, ProjectedOgraphicEllipsoid
from triaxialBodyWKT import OcentricTriaxial, OgraphicTriaxial, ProjectedOcentricTriaxial, ProjectedOgraphicTriaxial

#https://stackoverflow.com/questions/8212053/private-constructor-in-python
#https://www.edureka.co/community/16286/create-a-constant-in-python

class TemplateWKTFactory(object):

    @staticmethod
    def create(data):
        instance = None
        idWKT = data['id']
        if 'baseCRS' in data and data['type'] == 'TRIAXIAL':
            instance = TemplateWKTFactory.createProjectedTriaxialCrs(data, idWKT)
        elif 'baseCRS' in data:
            instance = TemplateWKTFactory.createProjectedEllipsoidCrs(data, idWKT)
        else:
            instance = TemplateWKTFactory.createPlanetodeticCrs(data, idWKT)
        return instance

    @staticmethod
    def createPlanetodeticCrs(data, idWKT):
        assert 'baseCRS' not in data
        if idWKT == 0: 
            instance = PlanetOcentricEllipsoid(data)
        elif idWKT == 1:
            instance = PlanetOgraphicEllipsoid(data)
        elif idWKT == 2:
            instance = PlanetOcentricEllipsoid(data)
        elif idWKT == 3:
            instance = OgraphicTriaxial(data)
        elif idWKT == 4:
            instance = OcentricTriaxial(data)
        else:
            raise "Error"  
        return instance

    @staticmethod
    def createProjectedEllipsoidCrs(data, idWKT):
        assert 'baseCRS' in data
        if idWKT == 0: 
            instance = ProjectedOcentricEllipsoid(data)
        elif idWKT == 1:
            instance = ProjectedOgraphicEllipsoid(data)
        elif idWKT == 2:
            instance = ProjectedOcentricEllipsoid(data)
        else:
            raise "This datum is not ellipsoidal"
        return instance

    @staticmethod
    def createProjectedTriaxialCrs(data, idWKT):
        assert 'baseCRS' in data and data['type'] == 'TRIAXIAL', "this CRS is not triaxial but %s" %data['type']
        if idWKT == 3: 
            instance = ProjectedOgraphicTriaxial(data)
        elif idWKT == 4:
            instance = ProjectedOcentricTriaxial(data)
        else:
            raise "This datum is not triaxial" 
        return instance       
