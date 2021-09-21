"""This module handles a factory for creating the template."""
from typing import Union

import pandas as pd

from .biaxialBodyWKT import (
    PlanetOcentricEllipsoid,
    PlanetOgraphicEllipsoid,
    ProjectedOcentricEllipsoid,
    ProjectedOgraphicEllipsoid,
)
from .iwkt import DATUM
from .triaxialBodyWKT import (
    OcentricTriaxial,
    OgraphicTriaxial,
    ProjectedOcentricTriaxial,
    ProjectedOgraphicTriaxial,
)


class TemplateWKTFactory(object):
    @staticmethod
    def create(
        data: pd.Series,
    ) -> Union[
        ProjectedOgraphicTriaxial,
        ProjectedOcentricTriaxial,
        ProjectedOcentricEllipsoid,
        ProjectedOgraphicEllipsoid,
        PlanetOcentricEllipsoid,
        PlanetOgraphicEllipsoid,
        OgraphicTriaxial,
        OcentricTriaxial,
    ]:
        """Create a coordinate reference system.

        Args:
            data (pd.Series): cartographic elements

        Returns:
            Union[ ProjectedOgraphicTriaxial, ProjectedOcentricTriaxial, ProjectedOcentricEllipsoid, ProjectedOgraphicEllipsoid, PlanetOcentricEllipsoid, PlanetOgraphicEllipsoid, OgraphicTriaxial, OcentricTriaxial]: Acoordinate reference system
        """
        instance: Union[
            ProjectedOgraphicTriaxial,
            ProjectedOcentricTriaxial,
            ProjectedOcentricEllipsoid,
            ProjectedOgraphicEllipsoid,
            PlanetOcentricEllipsoid,
            PlanetOgraphicEllipsoid,
            OgraphicTriaxial,
            OcentricTriaxial,
        ]
        idWKT = data["id"]
        if "baseCRS" in data and data["type"] == "TRIAXIAL":
            instance = TemplateWKTFactory.createProjectedTriaxialCrs(data, idWKT)
        elif "baseCRS" in data:
            instance = TemplateWKTFactory.createProjectedEllipsoidCrs(data, idWKT)
        else:
            instance = TemplateWKTFactory.createPlanetodeticCrs(data, idWKT)
        return instance

    @staticmethod
    def createPlanetodeticCrs(
        data: pd.Series, idWKT: int
    ) -> Union[
        PlanetOcentricEllipsoid,
        PlanetOgraphicEllipsoid,
        OgraphicTriaxial,
        OcentricTriaxial,
    ]:
        """Create a planetodetic coordinate reference system (not projected).

        Args:
            data (pd.Series): cartaographic elements
            idWKT (int): Datum

        Raises:
            Exception: DATUM not supported]

        Returns:
            Union[ PlanetOcentricEllipsoid, PlanetOgraphicEllipsoid, OgraphicTriaxial, OcentricTriaxial, ]: A planetodetic coordinate reference system (not projected)
        """
        assert "baseCRS" not in data
        if idWKT == DATUM.SPHERE.value:
            instance = PlanetOcentricEllipsoid(data)
        elif idWKT == DATUM.ELLIPSOID_OGRAPHIC.value:
            instance = PlanetOgraphicEllipsoid(data)
        elif idWKT == DATUM.ELLIPSOID_OCENTRIC.value:
            instance = PlanetOcentricEllipsoid(data)
        elif idWKT == DATUM.TRIAXIAL_OGRAPHIC.value:
            instance = OgraphicTriaxial(data)
        elif idWKT == DATUM.TRIAXIAL_OCENTRIC.value:
            instance = OcentricTriaxial(data)
        else:
            raise Exception("DATUM not supported")
        return instance

    @staticmethod
    def createProjectedEllipsoidCrs(
        data: pd.Series, idWKT: int
    ) -> Union[ProjectedOcentricEllipsoid, ProjectedOgraphicEllipsoid]:
        """Create a projected coordinate reference system based on an ellipsoid body.

        Args:
            data (pd.Series): cartographic elements
            idWKT (int): Datum

        Raises:
            Exception: This datum is not ellipsoidal

        Returns:
            Union[ProjectedOcentricEllipsoid, ProjectedOgraphicEllipsoid]: A projected coordinate reference system based on an ellipsoid body
        """
        assert "baseCRS" in data
        if idWKT == DATUM.SPHERE.value:
            instance = ProjectedOcentricEllipsoid(data)
        elif idWKT == DATUM.ELLIPSOID_OGRAPHIC.value:
            instance = ProjectedOgraphicEllipsoid(data)
        elif idWKT == DATUM.ELLIPSOID_OCENTRIC.value:
            instance = ProjectedOcentricEllipsoid(data)
        else:
            raise Exception("This datum is not ellipsoidal")
        return instance

    @staticmethod
    def createProjectedTriaxialCrs(
        data: pd.Series, idWKT: int
    ) -> Union[ProjectedOgraphicTriaxial, ProjectedOcentricTriaxial]:
        """[summary]

        Args:
            data (pd.Series): [description]
            idWKT (int): [description]

        Raises:
            Exception: This datum is not triaxial

        Returns:
            Union[ProjectedOgraphicTriaxial, ProjectedOcentricTriaxial]: [description]
        """
        assert "baseCRS" in data and data["type"] == "TRIAXIAL", (
            "this CRS is not triaxial but %s" % data["type"]
        )
        if idWKT == DATUM.TRIAXIAL_OGRAPHIC.value:
            instance = ProjectedOgraphicTriaxial(data)
        elif idWKT == DATUM.TRIAXIAL_OCENTRIC.value:
            instance = ProjectedOcentricTriaxial(data)
        else:
            raise Exception("This datum is not triaxial")
        return instance
