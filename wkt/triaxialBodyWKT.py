from string import Template

import pandas as pd

from .igeodeticwkt import IGeodeticCRS
from .iprojectedwkt import IProjectedCRS
from .iwkt import DATUM


class TriaxialBody(IGeodeticCRS):
    def __init__(self, data: pd.Series):
        IGeodeticCRS.__init__(self)
        datum_template_str: str = """DATUM["$datum_name",
            TRIAXIAL["$ellipsoide_name", $semi_major, $semi_median, $semi_minor, LENGTHUNIT["metre", 1, ID["EPSG", 9001]]]$anchor
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
            semi_major=data["semiMajorAxis"],
            semi_median=data["semiMedianAxis"],
            semi_minor=data["semiMinorAxis"],
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
    def longitude_direction(self):
        return self.__data["longitudeDirection"]


class ProjectedTriaxialBody(TriaxialBody, IProjectedCRS):
    def __init__(self, data: pd.Series, keywordOdetic: str):
        TriaxialBody.__init__(self, data)
        IProjectedCRS.__init__(self)
        self.__keyword_odetic: str = keywordOdetic
        parameter_template_str: str = """PARAMETER["$param_key", $param_val, $param_unit, ID["$param_code", $param_code_value]]"""
        method_id_template_str: str = """,ID["$method_autority",$method_code]"""
        cs_template_str: str = """CS[Cartesian, 2],
    AXIS["$longAxis", $longitudeDirection, ORDER[1]],
    AXIS["Northing (N)", north, ORDER[2]],
    LENGTHUNIT["metre", 1, ID[\"EPSG\", 9001]]"""
        self.__parameter_template = Template(parameter_template_str)
        self.__method_id_template = Template(method_id_template_str)
        self.__cs_template: Template = Template(cs_template_str)
        self.__data = data

    @property
    def name(self) -> str:
        __doc__ = IProjectedCRS.name.__doc__
        cs_name: str
        if self.__data["projection_id"] == DATUM.SPHERE.value:
            cs_name = "Sphere"
        elif self.__data["projection_id"] == DATUM.TRIAXIAL_OCENTRIC.value:
            cs_name = "Ocentric"
        elif self.__data["projection_id"] == DATUM.TRIAXIAL_OGRAPHIC.value:
            cs_name = "Ographic"
        else:
            raise Exception("DATUM not supported")

        return self.__data["name"] + " / " + cs_name

    @property
    def projection_name(self) -> str:
        __doc__ = IProjectedCRS.projection_name.__doc__
        return self.__data["name"]

    @property
    def conversion_name(self) -> str:
        __doc__ = IProjectedCRS.conversion_name.__doc__
        return self.__data["name"]

    @property
    def method_name(self) -> str:
        __doc__ = IProjectedCRS.method_name.__doc__
        return self.__data["method"]

    @property
    def method_id(self) -> str:
        __doc__ = IProjectedCRS.method_id.__doc__
        return self._compute_method_id(self.method_id_template, self.__data)

    @property
    def parameters(self) -> str:
        __doc__ = IProjectedCRS.parameters.__doc__
        return ",\n        ".join(
            self._compute_parameters(self.parameter_template, self.__data)
        )

    @property
    def keyword_odetic(self) -> str:
        __doc__ = IProjectedCRS.keyword_odetic.__doc__
        return self.__keyword_odetic

    @property
    def cs_template(self) -> Template:
        return self.__cs_template

    @property
    def parameter_template(self) -> Template:
        return self.__parameter_template

    @parameter_template.setter
    def parameter_template(self, value: Template):
        self.__parameter_template = value

    @property
    def method_id_template(self) -> Template:
        return self.__method_id_template

    @method_id_template.setter
    def method_id_template(self, value: Template):
        self.__method_id_template = value


class OcentricTriaxial(TriaxialBody):
    """Ocentric triaxial body
    """

    def __init__(self, data: pd.Series):
        """Init

        Args:
            data (pd.Series): planetocentric CRS
        """
        TriaxialBody.__init__(self, data)
        cs_template: str = """CS[spherical, 3],
    AXIS["Planetocentric latitude (U)", north, ORDER[1], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
    AXIS["Planetocentric longitude (V)", $longitudeDirection, ORDER[2], ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]],
    AXIS["Radius (R)", up, ORDER[3], LENGTHUNIT["metre", 1, ID["EPSG", 9001]]]"""
        self.__cs_template: Template = Template(cs_template)

    @property
    def cs(self) -> str:
        """Returns the coordinate system.

        Triaxial bodies are asteroid/comets. The longitude for these bodies are always positive to East.

        Returns:
            str: The coordinate system
        """
        assert self.longitude_direction == "east", (
            "longitude Direction must be east, not %s" % self.longitude_direction
        )
        return self.__cs_template.substitute(
            longitudeDirection=self.longitude_direction
        )


class OgraphicTriaxial(TriaxialBody):
    """Ographic triaxial body
    """

    def __init__(self, data: pd.Series):
        """Init

        Args:
            data (pd.Series): planetographic CRS
        """

        TriaxialBody.__init__(self, data)
        cs_template: str = """CS[ellipsoidal, 2],
    AXIS["Latitude (B)", north, ORDER[1]],
    AXIS["Longitude (L)", $longitudeDirection, ORDER[2]],
    ANGLEUNIT["degree", 0.017453292519943295, ID["EPSG", 9122]]"""
        self.__cs_template: Template = Template(cs_template)

    @property
    def cs(self) -> str:
        """Returns the coordinate system.

        Triaxial bodies are asteroid/comets. The longitude for these bodies are always positive to East.

        Returns:
            str: The coordinate system
        """
        return self.__cs_template.substitute(
            longitudeDirection=self.longitude_direction
        )


class ProjectedOcentricTriaxial(ProjectedTriaxialBody):
    """Projected planetocentric CRS for a triaxial body
    """

    def __init__(self, data: pd.Series):
        """Init

        Args:
            data (pd.Series): planetocentric CRS
        """
        ProjectedTriaxialBody.__init__(self, data, "BASEGEODCRS")

    @property
    def cs(self) -> str:
        """Returns the coordinate system.

        Triaxial bodies are asteroid/comets. The longitude for these bodies are always positive to East.

        Returns:
            str: the coordinate system
        """
        assert self.longitude_direction == "east", (
            "longitude Direction must be east, not %s" % self.longitude_direction
        )
        return self.cs_template.substitute(
            longitudeDirection="east", longAxis="Easting (E)"
        )


class ProjectedOgraphicTriaxial(ProjectedTriaxialBody):
    """Projected planetographic CRS for a triaxial body
    """

    def __init__(self, data: pd.Series):
        """Init

        Args:
            data (pd.Series): planetographic CRS
        """
        ProjectedTriaxialBody.__init__(self, data, "BASEGEOGCRS")

    @property
    def cs(self) -> str:
        """Returns the coordinate system.

        Triaxial bodies are asteroid/comets. The longitude for these bodies are always positive to East.

        Returns:
            str: The coordinate system
        """
        return self.cs_template.substitute(
            longitudeDirection="east", longAxis="Easting (E)"
        )

