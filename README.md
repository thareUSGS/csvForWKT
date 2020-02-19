# csvForWKT

csvForWKT is a python script that creates a WKT-crs for some bodies from the solar system. The content
that is filled in the WKT-crs comes from the report of IAU Working Group on Cartographic.


## 1- Synopsis

This document provides the motivation of the project and the different instructions to run and test the script. 

## 2- Motivation

It exists several coordinate reference systems (CRS) for each body in the solar system. For interoperability 
issues between the data providers, the IAU identifiers must be defined. Each IAU identifier is related to a 
CRS, which is defined in the WKT-crs standard. The use of the WKT-crs allows the GIS tools to understand the 
semantic of the CRS definition. In addition to that, the use of this standard is important so that the IAU identifier can be standardized at OGC later on.

## 3- Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### 3.1- Prerequisities

What things you need to install the software and how to install them

```
numpy
pandas
```

### 3.2 - Running the script


```
git clone https://github.com/PlanetMap/csvForWKT.git 
cd csvForWKT
```

```
python3 ./main.py > result.wkts
```

A results directory will be created. This directory contains the CSV files. the WKT-crs are defined in the 
result.wkts file

### 3.3 Running the tests

```
python3 -m unittest -v test
```

This command created one file per WKT on which gdalsrsinfo is run to validate the WKT
