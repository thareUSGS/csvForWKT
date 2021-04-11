"""
This module handles a body with an oblate ellispoid and its projection.

ISO 19111:2007 allows an oblate ellipsoid to be defined through semi-major
axis (a) and either semi-minor axis (b) or inverse flattening (1/f). If
semi-minor axis is used as the second defining parameter the value for inverse
flattening to be shown in the WKT string should be calculated from
1/f  =  a / (a – b).

ISO 19111:2007 also allows for the earth model to be a sphere, for which 1/f is
infinite. In this International Standard if the earth model is a sphere
<inverse flattening> shall be given an artificial value of zero.
"""
from string import Template

import pandas as pd

from .igeodeticwkt import IGeodeticCRS
from .iprojectedwkt import IProjectedCRS
from .iwkt import DATUM


class BiaxialBody(IGeodeticCRS):
    """A BiaxialBody is a body with an oblate ellipsoid.
    This class is responsible for creating the WKT2 of an oblate ellipsoid.

    .. code-block::

        Example:
        GEODCRS["Mars (2015) / Ographic",
            DATUM["Mars (2015)",
                    ELLIPSOID["Mars (2015)", 3396190.0, 169.8944472236118, LENGTHUNIT["metre", 1]],
                    ANCHOR["Viking 1 lander: 47.951370000000004 W"]
                ],
                PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
            CS[ellipsoidal, 2],
            AXIS["Latitude (B)", north, ORDER[1]],
            AXIS["Longitude (L)", west, ORDER[2]],
            ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]],
            ID["IAU", 49901, 2015], REMARK["Source of IAU Coordinate systems: doi://10.1007/s10569-017-9805-5"]
        ]
    """

    def __init__(self, data: pd.Series):
        """Init the class.

        Args:
            data (pd.Series): biaxial elements
        """
        IGeodeticCRS.__init__(self)
        datum_template_str: str = """DATUM["$datum_name",
            ELLIPSOID["$ellipsoide_name", $radius, $inverse_flat, LENGTHUNIT["metre", 1]]$anchor
        ],
        PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]]"""
        anchor_template_str: str = """,\n            ANCHOR["$primeMeridianName: $primeMeridianValue"]"""
        datum_template: Template = Template(datum_template_str)
        anchor_template: Template = Template(anchor_template_str)
        self.__datum: str = self.__compute_datum(datum_template, anchor_template, data)
        self.__data: pd.Series = data

    def __compute_datum(
        self, datum_template: Template, anchor_template: Template, data: pd.Series
    ) -> str:
        """Compute the DATUM element in WKT.

        .. code-block::

            Example:
            DATUM["Mars (2015)",
                    ELLIPSOID["Mars (2015)", 3396190.0, 169.8944472236118, LENGTHUNIT["metre", 1]],
                    ANCHOR["Viking 1 lander: 47.951370000000004 W"]
                ],
                PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],


        Args:
            datum_template (Template): datum template
            anchor_template (Template): anchor template
            data (pd.Series): biaxial elements

        Returns:
            str: the DATUM element in WKT
        """
        anchor: str
        if data["primeMeridianName"] == "Reference_Meridian":
            anchor = ""
        else:
            anchor = anchor_template.substitute(
                primeMeridianName=data["primeMeridianName"],
                primeMeridianValue=data["primeMeridianValue"],
            )

        return datum_template.substitute(
            datum_name=data["datum_name"],
            ellipsoide_name=data["ellipsoid_name"],
            radius=data["semiMajorAxis"],
            inverse_flat=data["inverseFlatenning"],
            anchor=anchor,
        )

    @property
    def datum(self) -> str:
        __doc__ = IGeodeticCRS.datum.__doc__
        return self.__datum

    @property
    def name(self) -> str:
        __doc__ = IGeodeticCRS.name.__doc__
        return self.__data["name"]

    @property
    def authority(self) -> str:
        __doc__ = IGeodeticCRS.authority.__doc__
        return self.__data["authority"]

    @property
    def code(self) -> int:
        __doc__ = IGeodeticCRS.code.__doc__
        return self.__data["code"]

    @property
    def version(self) -> str:
        __doc__ = IGeodeticCRS.version.__doc__
        return self.__data["version"]

    @property
    def remark(self) -> str:
        __doc__ = IGeodeticCRS.remark.__doc__
        return self.__data["remark"]

    @property
    def longitude_direction(self) -> str:
        """Returns the longitude direction.

        Returns:
            str: The longitude direction
        """
        return self.__data["longitudeDirection"]


class ProjectedBiaxialBody(BiaxialBody, IProjectedCRS):
    """A ProjectedBiaxialBody is a body with an oblate ellipsoid that it is
    projected on a plane .

    This class is responsible for creating the WKT2 of a projected oblate ellipsoid.

    .. code-block::

        Example:
        PROJCRS["Equirectangular, clon = 0",
            BASEGEOGCRS["Equirectangular, clon = 0 / Ographic",
                DATUM["Mars (2015)",
                    ELLIPSOID["Mars (2015)", 3396190.0, 169.8944472236118, LENGTHUNIT["metre", 1]],
                    ANCHOR["Viking 1 lander: 47.951370000000004"]
                ],
                PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]]
            ],
            CONVERSION["Equirectangular, clon = 0",
                METHOD["Equidistant Cylindrical",ID["EPSG",1028]],
                PARAMETER["False easting", 0, LENGTHUNIT["metre", 1, ID["EPSG", 9001]], ID["EPSG", 8806]],
                PARAMETER["False northing", 0, LENGTHUNIT["metre", 1, ID["EPSG", 9001]], ID["EPSG", 8807]],
                PARAMETER["Longitude of natural origin", 0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]], ID["EPSG", 8802]],
                PARAMETER["Latitude of 1st standard parallel", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]], ID["EPSG", 8823]]
            ],
            CS[Cartesian, 2],
            AXIS["Westing (W)", west, ORDER[1]],
            AXIS["Northing (N)", north, ORDER[2]],
            LENGTHUNIT["metre", 1, ID["EPSG", 9001]],
            ID["IAU", 49911, 2015]
        ]
    """

    def __init__(self, data: pd.Series, keywordOdetic: str):
        """Init the class.

        Args:
            data (pd.Series): biaxial elements
            keywordOdetic (str) : keyword odetic (meaning ographic or ocentric)
        """
        BiaxialBody.__init__(self, data)
        IProjectedCRS.__init__(self)
        self.__keyword_odetic = keywordOdetic
        parameter_template_str: str = """PARAMETER["$param_key", $param_val, $param_unit, ID["$param_code", $param_code_value]]"""
        method_id_template_str: str = """,ID["$method_autority",$method_code]"""
        self.__method_id_template = Template(method_id_template_str)
        self.__parameter_template = Template(parameter_template_str)
        self.__data: pd.Series = data

    @property
    def name(self) -> str:
        """Returns the name of the projected coordinate system.

        Note:
            the name of the projected coordinate system is the projection
            name plus the ocentric/ographic word

        Raises:
            Exception: DATUM not supported

        Returns:
            str: The name of the projected coordinate system
        """
        cs_name: str
        if self.__data["projection_id"] == DATUM.SPHERE.value:
            cs_name = "Sphere"
        elif self.__data["projection_id"] == DATUM.ELLIPSOID_OCENTRIC.value:
            cs_name = "Ocentric"
        elif self.__data["projection_id"] == DATUM.ELLIPSOID_OGRAPHIC.value:
            cs_name = "Ographic"
        else:
            raise Exception("DATUM not supported")

        return self.__data["name"] + " / " + cs_name

    @property
    def projection_name(self) -> str:
        """Returns the projection name.

        Returns:
            str: The projection name
        """
        return self.__data["name"]

    @property
    def conversion_name(self) -> str:
        """Returns the conversion name.

        Returns:
            str: The conversion name
        """
        return self.__data["name"]

    @property
    def method_name(self) -> str:
        """Returns the method name.

        Returns:
            str: The method name
        """
        return self.__data["method"]

    @property
    def method_id(self) -> str:
        """Returns the method ID.

        Returns:
            str: The method ID
        """
        return self._compute_method_id(self.method_id_template, self.__data)

    @property
    def parameters(self) -> str:
        """Returns the projection parameters.

        Returns:
            str: The projection parameters
        """
        return ",\n        ".join(
            self._compute_parameters(self.parameter_template, self.__data)
        )

    @property
    def keyword_odetic(self) -> str:
        """Returns the keyword odetic.

        Returns:
            str: the keyword odetic
        """
        return self.__keyword_odetic

    @property
    def parameter_template(self) -> Template:
        """Returns the parameter template.

        Returns:
            Template: The parameter template
        """
        return self.__parameter_template

    @parameter_template.setter
    def parameter_template(self, value: Template):
        """Sets the parameter template

        Args:
            value (Template): The template to set
        """
        self.__parameter_template = value

    @property
    def method_id_template(self) -> Template:
        """Returns the method ID template.

        Returns:
            Template: The method ID template
        """
        return self.__method_id_template

    @method_id_template.setter
    def method_id_template(self, value: Template):
        """Sets the method ID template.

        Args:
            value (Template): the template to set
        """
        self.__method_id_template = value


class PlanetOgraphicEllipsoid(BiaxialBody):
    """Create a planetographic WKT based on an ellipsoid reference.

    .. code-block::

        Example:
        GEODCRS["Mars (2015) / Ographic",
            DATUM["Mars (2015)",
                    ELLIPSOID["Mars (2015)", 3396190.0, 169.8944472236118, LENGTHUNIT["metre", 1]],
                    ANCHOR["Viking 1 lander: 47.951370000000004 W"]
                ],
                PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
            CS[ellipsoidal, 2],
            AXIS["Latitude (B)", north, ORDER[1]],
            AXIS["Longitude (L)", west, ORDER[2]],
            ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]],
            ID["IAU", 49901, 2015], REMARK["Source of IAU Coordinate systems: doi://10.1007/s10569-017-9805-5"]
        ]
    """

    def __init__(self, data: pd.Series):
        """Init the class.

        Args:
            data (pd.Series): biaxial elements
        """
        BiaxialBody.__init__(self, data)
        cs_template_str: str = """CS[ellipsoidal, 2],
    AXIS["Latitude (B)", north, ORDER[1]],
    AXIS["Longitude (L)", $longitudeDirection, ORDER[2]],
    ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]"""
        self.__cs_template: Template = Template(cs_template_str)

    @property
    def cs(self) -> str:
        """Returns the axis of the coordinate system.

        Returns:
            str: The axis of the coordinate system
        """
        return self.__cs_template.substitute(
            longitudeDirection=self.longitude_direction
        )


class PlanetOcentricEllipsoid(BiaxialBody):
    """Create a planetocentric WKT based on an ellipsoid reference.

    .. code-block::

        Example:
        GEODCRS["Mars (2015) / Ocentric",
            DATUM["Mars (2015)",
                    ELLIPSOID["Mars (2015)", 3396190.0, 169.8944472236118, LENGTHUNIT["metre", 1]],
                    ANCHOR["Viking 1 lander: 47.951370000000004"]
                ],
                PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
            CS[spherical, 3],
            AXIS["Planetocentric latitude (U)", north, ORDER[1], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
            AXIS["Planetocentric longitude (V)", east, ORDER[2], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
            AXIS["Radius (R)", up, ORDER[3], LENGTHUNIT["metre", 1, ID["EPSG", 9001]]],
            ID["IAU", 49902, 2015], REMARK["Source of IAU Coordinate systems: doi://10.1007/s10569-017-9805-5"]
        ]
    """

    def __init__(self, data: pd.Series):
        """Init the class.

        Args:
            data (pd.Series): biaxial elements
        """
        BiaxialBody.__init__(self, data)
        cs_template: str = """CS[spherical, 3],
    AXIS["Planetocentric latitude (U)", north, ORDER[1], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
    AXIS["Planetocentric longitude (V)", $longitudeDirection, ORDER[2], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
    AXIS["Radius (R)", up, ORDER[3], LENGTHUNIT["metre", 1, ID["EPSG", 9001]]]"""
        self.__cs_template: Template = Template(cs_template)

    @property
    def cs(self) -> str:
        """Returns the axis of the coordinate system.

        Returns:
            str: The axis of the coordinate system
        """
        return self.__cs_template.substitute(
            longitudeDirection=self.longitude_direction
        )


class ProjectedOcentricEllipsoid(ProjectedBiaxialBody):
    """Create a planetocentric WKT based on an ellipsoid reference that it is projected.

    .. code-block::

        Example:
        PROJCRS["Equirectangular, clon = 0",
            BASEGEODCRS["Equirectangular, clon = 0 / Ocentric",
                DATUM["Mars (2015)",
                    ELLIPSOID["Mars (2015)", 3396190.0, 169.8944472236118, LENGTHUNIT["metre", 1]],
                    ANCHOR["Viking 1 lander: 47.951370000000004"]
                ],
                PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]]
            ],
            CONVERSION["Equirectangular, clon = 0",
                METHOD["Equidistant Cylindrical",ID["EPSG",1028]],
                PARAMETER["False easting", 0, LENGTHUNIT["metre", 1, ID["EPSG", 9001]], ID["EPSG", 8806]],
                PARAMETER["False northing", 0, LENGTHUNIT["metre", 1, ID["EPSG", 9001]], ID["EPSG", 8807]],
                PARAMETER["Longitude of natural origin", 0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]], ID["EPSG", 8802]],
                PARAMETER["Latitude of 1st standard parallel", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]], ID["EPSG", 8823]]
            ],
            CS[Cartesian, 2],
            AXIS["Easting (E)", east, ORDER[1]],
            AXIS["Northing (N)", north, ORDER[2]],
            LENGTHUNIT["metre", 1, ID["EPSG", 9001]],
            ID["IAU", 49912, 2015]
        ]
    """

    def __init__(self, data: pd.Series):
        ProjectedBiaxialBody.__init__(self, data, "BASEGEODCRS")
        cs_template: str = """CS[Cartesian, 2],
    AXIS["$longAxis", $longitudeDirection, ORDER[1]],
    AXIS["Northing (N)", north, ORDER[2]],
    LENGTHUNIT["metre", 1, ID[\"EPSG\", 9001]]"""
        self.__cs_template: Template = Template(cs_template)
        parameter_template_str: str = """PARAMETER["$param_key", $param_val, $param_unit, ID["$param_code", $param_code_value]]"""
        method_id_template_str: str = """,ID["$method_autority",$method_code]"""
        self.__parameter_template = Template(parameter_template_str)
        self.__method_id_template = Template(method_id_template_str)

    @property
    def cs(self) -> str:
        """Returns the axis of the coordinate system.

        Returns:
            str: The axis of the coordinate system
        """
        assert self.longitude_direction == "east", (
            "longitude Direction must be east for ocentric CRS, not %s"
            % self.longitude_direction
        )
        longAxis = (
            "Easting (E)" if self.longitude_direction == "east" else "Westing (W)"
        )
        return self.__cs_template.substitute(
            longitudeDirection=self.longitude_direction, longAxis=longAxis
        )


class ProjectedOgraphicEllipsoid(ProjectedBiaxialBody):
    """Create a planetographic WKT based on an ellipsoid reference that it is projected.

    .. code-block::

        Example:
        PROJCRS["Equirectangular, clon = 0",
            BASEGEOGCRS["Equirectangular, clon = 0 / Ographic",
                DATUM["Mars (2015)",
                    ELLIPSOID["Mars (2015)", 3396190.0, 169.8944472236118, LENGTHUNIT["metre", 1]],
                    ANCHOR["Viking 1 lander: 47.951370000000004"]
                ],
                PRIMEM["Reference Meridian", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]]
            ],
            CONVERSION["Equirectangular, clon = 0",
                METHOD["Equidistant Cylindrical",ID["EPSG",1028]],
                PARAMETER["False easting", 0, LENGTHUNIT["metre", 1, ID["EPSG", 9001]], ID["EPSG", 8806]],
                PARAMETER["False northing", 0, LENGTHUNIT["metre", 1, ID["EPSG", 9001]], ID["EPSG", 8807]],
                PARAMETER["Longitude of natural origin", 0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]], ID["EPSG", 8802]],
                PARAMETER["Latitude of 1st standard parallel", 0.0, ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]], ID["EPSG", 8823]]
            ],
            CS[Cartesian, 2],
            AXIS["Westing (W)", west, ORDER[1]],
            AXIS["Northing (N)", north, ORDER[2]],
            LENGTHUNIT["metre", 1, ID["EPSG", 9001]],
            ID["IAU", 49911, 2015]
        ]
    """

    def __init__(self, data: pd.Series):
        ProjectedBiaxialBody.__init__(self, data, "BASEGEOGCRS")
        cs_template: str = """CS[Cartesian, 2],
    AXIS["$longAxis", $longitudeDirection, ORDER[1]],
    AXIS["Northing (N)", north, ORDER[2]],
    LENGTHUNIT["metre", 1, ID[\"EPSG\", 9001]]"""
        self.__cs_template: Template = Template(cs_template)

    @property
    def cs(self) -> str:
        """Returns the axis of the coordinate system.

        Returns:
            str: The axis of the coordinate system
        """
        longAxis = (
            "Easting (E)" if self.longitude_direction == "east" else "Westing (W)"
        )
        return self.__cs_template.substitute(
            longitudeDirection=self.longitude_direction, longAxis=longAxis
        )
