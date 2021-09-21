"""Module for handling the interface of WKT2 for the geodetic coordinate reference system."""
from abc import abstractmethod
from string import Template
from typing import Dict

from .iwkt import IWKT


class IGeodeticCRS(IWKT):
    """Interface for creating the WKT2 of the geodetic coordinate reference system."""

    def __init__(self):
        self.__geodeticCrs = """GEODCRS["$name",
    $datum,
    $cs,
    ID["$authority", $code, $version], REMARK["$remark"]
]
"""
        self.__wkt = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the coordinate system.

        Raises:
            NotImplementedError: Not implemented

        Returns:
            str: The name of the coordinate system
        """
        raise NotImplementedError("Not implemented")

    @property
    @abstractmethod
    def cs(self) -> str:
        """Returns the axis of the coordinate system.

        Raises:
            NotImplementedError: Not implemented

        Returns:
            str: The axis of the coordinate system
        """
        raise NotImplementedError("Not implemented")

    @property
    @abstractmethod
    def datum(self) -> str:
        """Returns the DATUM element of the WKT2 string.

        Raises:
            NotImplementedError: Not implemented

        Returns:
            str: The DATUM element of the WKT2 string
        """
        raise NotImplementedError("Not implemented")

    @property
    @abstractmethod
    def authority(self) -> str:
        """Returns the authority's name of the coordinate system.

        Raises:
            NotImplementedError: Not implemented

        Returns:
            str: The authority's name of the coordinate system
        """
        raise NotImplementedError("Not implemented")

    @property
    @abstractmethod
    def code(self) -> int:
        """Returns the authority's code of the coordinate system.

        Raises:
            NotImplementedError: Not implemented

        Returns:
            int: The authority's code of the coordinate system
        """
        raise NotImplementedError("Not implemented")

    @property
    @abstractmethod
    def version(self) -> str:
        """Returns the authority's version of the coordinate system.

        Raises:
            NotImplementedError: Not implemented

        Returns:
            str: The authority's version of the coordinate system
        """
        raise NotImplementedError("Not implemented")

    @property
    @abstractmethod
    def remark(self) -> str:
        """Returns the remark.

        Raises:
            NotImplementedError: Not implemented

        Returns:
            str: The remark
        """
        raise NotImplementedError("Not implemented")

    def computeWKT(self):
        __doc__ = IWKT.computeWKT.__doc__
        geodetic_crs = Template(self.__geodeticCrs)
        self.__wkt = geodetic_crs.substitute(
            name=self.name,
            datum=self.datum,
            cs=self.cs,
            authority=self.authority,
            code=self.code,
            version=self.version,
            remark=self.remark,
        )

    @property
    def wkt(self) -> Dict:
        __doc__ = IWKT.wkt.__doc__
        return self.__wkt

