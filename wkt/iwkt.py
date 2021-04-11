"""Module for handling the interface of WKT2."""

from abc import abstractmethod
from enum import Enum
from typing import Dict


class DATUM(Enum):
    SPHERE = 0
    ELLIPSOID_OGRAPHIC = 1
    ELLIPSOID_OCENTRIC = 2
    TRIAXIAL_OGRAPHIC = 3
    TRIAXIAL_OCENTRIC = 4


class IWKT:
    """Interface for creating the WKT2."""

    @property
    def version(self) -> str:
        """Returns the version of the WKT2 standard.

        Returns:
            str: The version of the WKT2 standard
        """
        return "2.0"

    @property
    @abstractmethod
    def wkt(self) -> Dict:
        """Returns the WKT.

        Raises:
            NotImplementedError: When the method is not implemented

        Returns:
            Dict: The WKT as code: wkt string
        """
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def computeWKT(self):
        """Compute the WKT.

        Raises:
            NotImplementedError: When the method is not implemented
        """
        raise NotImplementedError("Not implemented")

