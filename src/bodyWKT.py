#/usr/bin/env python3
from abc import ABCMeta, abstractmethod
from biaxialBodyWKT import PlanetOcentricEllipsoid, PlanetOgraphicEllipsoid, ProjectionOcentricEllipsoid, ProjectionOgraphicEllipsoid
from triaxialBodyWKT import OcentricTriaxial, OgraphicTriaxial, ProjectionOcentricTriaxial, ProjectionOgraphicTriaxial

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
            instance = ProjectionOcentricEllipsoid(data)
        elif idWKT == 1:
            instance = ProjectionOgraphicEllipsoid(data)
        elif idWKT == 2:
            instance = ProjectionOcentricEllipsoid(data)
        else:
            raise "This datum is not ellipsoidal"
        return instance

    @staticmethod
    def createProjectedTriaxialCrs(data, idWKT):
        assert 'baseCRS' in data and data['type'] == 'TRIAXIAL', "this CRS is not triaxial but %s" %data['type']
        if idWKT == 3: 
            instance = ProjectionOgraphicTriaxial(data)
        elif idWKT == 4:
            instance = ProjectionOcentricTriaxial(data)
        else:
            raise "This datum is not triaxial" 
        return instance       
