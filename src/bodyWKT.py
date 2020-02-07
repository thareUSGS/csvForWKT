#/usr/bin/env python3
from abc import ABCMeta, abstractmethod
from biaxialBodyWKT import PlanetOcentricEllipsoid, PlanetOgraphicEllipsoid, ProjectionEllipsoid
from triaxialBodyWKT import OcentricTriaxial, OgraphicTriaxial, ProjectionTriaxial

#https://stackoverflow.com/questions/8212053/private-constructor-in-python
#https://www.edureka.co/community/16286/create-a-constant-in-python

class TemplateWKTFactory(object):

    @staticmethod
    def create(data):
        instance = None
        idWKT = data['id']
        if 'baseCRS' in data and data['type'] == 'TRIAXIAL':
            instance = ProjectionTriaxial(data)
        elif 'baseCRS' in data:
            instance = ProjectionEllipsoid(data)
        elif idWKT == 0: 
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
