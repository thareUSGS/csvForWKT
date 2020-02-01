#/usr/bin/env python3
import pandas as pd
import os
import numpy as np

class WKTcrs:

    def __init__(self, path = None, filename='naifcodes_radii_m_wAsteroids_IAU2015.csv'):
        pathFile = path if path is not None else os.path.dirname(os.path.realpath(__file__)) + '/../data/'
        self._df = pd.read_csv(pathFile+filename)               
        self._ellipsoid = None
        self._datum = None
        self._planetodetic = None
        self._projection = None
    

    def __skipRecords(self, df):
        """
        Skip records when IAU2015_Semimajor!=-1 or IAU2015_Axisb!=-1 or IAU2015_Semiminor!=-1
        """
        return self._df.query("IAU2015_Semimajor!=-1 and IAU2015_Axisb!=-1 and IAU2015_Semiminor!=-1")

    def __processLongitudePositive(self, df):
        """
        Define the positive longitudes in ographic CRS based on the rotation sens.
        The general rule is the following:
        * Direct rotation has longitude positive to West
        * Retrograde rotation has longitude positive to East
        A special case is done for Sun/Earth/Moon for historical reasons for which longitudes
        are positive to East independently of the rotation sens.        
        """
        df = df.replace(to_replace ="Direct", value="west")
        df = df.replace(to_replace ="Retrograde", value="east")
        historic = df.query("Body=='Sun' or Body=='Moon' or Body=='Earth'")
        historic = historic.copy()
        historic.loc[:,'rotation'] = "east"
        df.update(historic)
        return df

    def __processZeroLongitude(self, df):
        """ 
        Set default values for origin_lon_pos/origin_long_name  
        """
        df.loc[df['origin_lon_pos'].isnull(),'origin_lon_pos']="0.0"
        df.loc[df['origin_long_name'].isnull(),'origin_long_name']='Reference_Meridian'
        return df                


    def __ellipsoid(self, df):
        """
        Here, we define the ellipsoid of the planet.

        Information we need to save:
        * authority (ex:IAU)
        * version (ex: 2015)
        * code (ex: 39901)
        * name (ex: Earth (2015))
        * semiMajorAxis
        * semiMedianAxis
        * semiMinorAxis
        * inverseFlattening

        When the semiMedianAxis is empty then the ellipsoid is biaxial otherwise we consider a triaxial body with 
        semi-minor < semiMedian (axisb) < semiMajor   

        General case:
        -------------

                                        /-----> sphere with semi-major radius(ellipse case)   /* interoperability */
        bodies shape  ------>  sphere  /  OR
                      |     (code: 00) \
                      |                 \------> sphere with median radius(triaxial case)      /* interoperability */
                      |AND
                      |      /-----> ellipse /* Physics case for twoaxial bodies
                      |_____/  OR    (code: 01) 
                            \     
                             \-----> triaxial /* Physics case for triaxial bodies
                                     (code :02)

        Special cases:
        -------------
        1/ Use R_m = (a+b+c)/3 as mean radius when mean radius is not defined (=-1)
        """ 
        # load the selected columns and rename them to match the required columns   
        ellipsoid = df[['Naif_id', 'Body','IAU2015_Semimajor','IAU2015_Axisb','IAU2015_Semiminor', 'IAU2015_Mean']]
        ellipsoid = ellipsoid.rename(columns={"Naif_id": "code", "Body":"name", "IAU2015_Semimajor":"semiMajorAxis", "IAU2015_Axisb":"semiMedianAxis", "IAU2015_Semiminor":"semiMinorAxis"})
        ellipsoid['Naif_id'] = ellipsoid['code']
        # duplicate rows for handling code 00, 01, 02
        ellipsoid = ellipsoid.append([ellipsoid]*2,ignore_index=True)
        # Add IAU authority as a vector
        ellipsoid.insert(0,"authority",['IAU']*len(ellipsoid.code))
        # Add version as a vector
        ellipsoid.insert(1,"version",[2015]*len(ellipsoid.code))
        # Add en empty inverse flatenning column
        ellipsoid = ellipsoid.assign(inverseFlatenning="")


        # Create cases
        ellipsoid.loc[0::3,'type'] = 'SPHERE'
        ellipsoid.loc[0::3,'code'] *= 100 
        ellipsoid.loc[0::3,'name']= ellipsoid.loc[0::3, 'name'].str[:] + ' (' + ellipsoid.loc[0::3, 'version'].apply(str) + ') - Sphere'

        ellipsoid.loc[1::3,'type'] = 'ELLIPSE'
        ellipsoid.loc[1::3,'code'] = ellipsoid.loc[1::3,'code'] * 100 + 1
        ellipsoid.loc[1::3,'name'] = ellipsoid.loc[1::3, 'name'].str[:] + ' (' + ellipsoid.loc[1::3, 'version'].apply(str) + ')'         

        ellipsoid.loc[2::3,'type'] = 'TRIAXIAL'
        ellipsoid.loc[2::3,'code'] =  ellipsoid.loc[2::3,'code'] * 100 + 2
        ellipsoid.loc[2::3,'name'] = ellipsoid.loc[2::3, 'name'].str[:] + ' (' + ellipsoid.loc[2::3, 'version'].apply(str) + ')'  

        # Exceptions to the general cases         
           # case1 => Use R_m = (a+b+c)/3 as mean radius when mean radius is not defined 
        elipseBodyToRemove = ellipsoid.query("IAU2015_Mean == -1 and (type != 'TRIAXIAL' and type != 'SPHERE')")
        ellipsoid = ellipsoid.drop(elipseBodyToRemove.index) 
        medianSphereToSet = ellipsoid.query("IAU2015_Mean == -1 and type == 'SPHERE'")
        ellipsoid.loc[medianSphereToSet.index, 'IAU2015_Mean'] = (ellipsoid.loc[medianSphereToSet.index, 'semiMajorAxis'] \
            + ellipsoid.loc[medianSphereToSet.index, 'semiMinorAxis'] + ellipsoid.loc[medianSphereToSet.index, 'semiMedianAxis']) / 3

        # Spherical case
            # set mean radius for triaxial bodies
        triaxialBodies = ellipsoid.query("semiMajorAxis != semiMedianAxis and semiMinorAxis != semiMedianAxis and type == 'SPHERE'")            
        ellipsoid.loc[triaxialBodies.index, 'semiMajorAxis'] = ellipsoid.loc[triaxialBodies.index, 'IAU2015_Mean']
        ellipsoid.loc[triaxialBodies.index, 'semiMinorAxis'] = ellipsoid.loc[triaxialBodies.index, 'IAU2015_Mean']
        ellipsoid.loc[triaxialBodies.index, 'semiMedianAxis'] = ""
           # set semi major radius for ellipse bodies
        sphere = ellipsoid.query("type == 'SPHERE'")   
        noTriaxialBodies_index = pd.Index(list(set(sphere.index.tolist()).difference(set(triaxialBodies.index.tolist()))))
        ellipsoid.loc[noTriaxialBodies_index, 'semiMinorAxis'] = ellipsoid.loc[noTriaxialBodies_index, 'semiMajorAxis']
        ellipsoid.loc[noTriaxialBodies_index, 'semiMedianAxis'] = ""
          

        # Ellipse case
        triaxialBodies = ellipsoid.query("semiMajorAxis != semiMedianAxis and semiMinorAxis != semiMedianAxis and type == 'ELLIPSE'")    
        ellipse = ellipsoid.query("type == 'ELLIPSE'")   
        noTriaxialBodies_index = pd.Index(list(set(ellipse.index.tolist()).difference(set(triaxialBodies.index.tolist()))))         
        ellipsoid.loc[noTriaxialBodies_index, 'semiMedianAxis'] = ""
        ellipsoid = ellipsoid.drop(triaxialBodies.index) 

        # Triaxial case
        triaxialBodies = ellipsoid.query("semiMajorAxis != semiMedianAxis and semiMinorAxis != semiMedianAxis and type == 'TRIAXIAL'")    
        triaxial = ellipsoid.query("type == 'TRIAXIAL'")   
        noTriaxialBodies_index = pd.Index(list(set(triaxial.index.tolist()).difference(set(triaxialBodies.index.tolist()))))         
        ellipsoid = ellipsoid.drop(noTriaxialBodies_index) 


        # sort by code
        ellipsoid = ellipsoid.sort_values(by='code')
        ellipsoid = ellipsoid.astype({'code': int}) 

        return ellipsoid

    def __datum(self, df, ellipsoid):
        """
        Information to save:
        * authority
        * version
        * code
        * name
        * body
        * ellipsoid (linked to ellipsoid)
        * primeMeridianName
        * primeMeridianValue
        """
        # we create the fatum based on the ellipsoid
        datum = ellipsoid[['Naif_id', 'type', 'authority','version','code','name']]                
        # We extract only the interesting columns from the CSV
        df_datum = df[['Naif_id', 'Body','origin_long_name','origin_lon_pos']]
        # we rename the columns to match the required columns
        df_datum = df_datum.rename(columns={"Body": "body", "origin_long_name":"primeMeridianName", "origin_lon_pos":"primeMeridianValue"})
        # we merge the two tables by adding columns from the first table to the second table
        datum = pd.merge(datum, df_datum, on='Naif_id')    
        # we add the link to the ellipsoid
        datum['ellipsoid'] = datum['authority'].apply(str) + ':' + datum['version'].apply(str) + ':' + datum['code'].apply(str)
        # we reorganize the columns
        datum = datum[['Naif_id', 'type','authority','version','code','name','body','ellipsoid','primeMeridianName','primeMeridianValue']]
        # we sort by code
        datum = datum.sort_values(by='code')

        return datum       

    def __splitDatumCase(self, df):
        # By default, each datum is ocentric. In an ocentric CRS, the longitude is always positive to East
        ocentric = df
        # When the longitude direction is not null, we know the rotation sens so we could use an ographic rotation
        # For historical reasons, longitudes for Sun/Moon/Earth are positives to East for ographic/ocentric CRS. In addition, Sun and Moon have
        # a spherical shape. So we do not need to consider the ographic CRS for Sun/Moon because ographic definition = ocentric definition
        ographic = df[df.longitudeDirection.notnull()].query("Body!='Sun' and Body!='Moon'")
        return (ographic, ocentric)


    def __planetodetic(self, df, datum):
        """
        Planetodetic could be ocentric or ographic. ocentric has csType=spherical where as ographic has csType=ellipsoidal
        ocentric as even values" and "ographic as odd"
        Information:
        * authority
        * version
        * code
        * name
        * datum
        * csType (ellipsoidal or spherical)
        * longitudeDirection 

        xxx00 => Ocentric on a Sphere. If triaxial use Mean, even if elliptical use Semi-major axis as a sphere, Always East.
        xxx01 => Ographic on ellipse (West or East, depending on body rotation)
        xxx02 => Ocentric on ellipse (always East)
        xxx03 => Ographic on Triaxial, (West or East, depending on body rotation)
        xxx04 => Ocentric on Triaxial, East (for more advanced applications, not for map projections, like ISIS3, VICAR, ...)               
        """
        df = df.rename(columns={'rotation':'longitudeDirection'})
        df_planeto = pd.merge(datum[['Naif_id','authority','version','code','name','ellipsoid','type']], df[['Naif_id','longitudeDirection','Body']], on='Naif_id')

        ographic, ocentric = self.__splitDatumCase(df_planeto)    
                
        historicalReasons = ocentric.query("(Body == 'Sun' or Body == 'Moon') and type != 'SPHERE'")
        ocentric = ocentric.drop(historicalReasons.index)

        # a small processing to have ocentic with even code
        sphere = ocentric.query("type == 'SPHERE'")
        ocentric.loc[sphere.index, 'code'] = ocentric.loc[sphere.index, 'Naif_id'] * 100
        ocentric.loc[sphere.index, 'id'] = 0

        ellipse = ocentric.query("type == 'ELLIPSE'")
        ocentric.loc[ellipse.index, 'code'] = ocentric.loc[ellipse.index, 'Naif_id'] * 100 +2
        ocentric.loc[ellipse.index, 'id'] = 2

        triaxial = ocentric.query("type == 'TRIAXIAL'")
        ocentric.loc[triaxial.index, 'code'] = ocentric.loc[triaxial.index, 'Naif_id'] * 100 +4
        ocentric.loc[triaxial.index, 'id'] = 4

        ocentric['longitudeDirection'] = 'east'
        ocentric.insert(5, 'csType', 'spherical')
        ocentric['name']= ocentric['name'].str[:] + ' / Ocentric'
        
        sphereEast = ographic.query("type == 'SPHERE'")
        ographic = ographic.drop(sphereEast.index)
        
        # small processing ofr ographic code
        ellipse = ographic.query("type == 'ELLIPSE'")
        ographic.loc[ellipse.index, 'code'] = ocentric.loc[ellipse.index, 'Naif_id'] * 100 +1
        ographic.loc[ellipse.index, 'id'] = 1

        triaxial = ographic.query("type == 'TRIAXIAL'")
        ographic.loc[triaxial.index, 'code'] = ographic.loc[triaxial.index, 'Naif_id'] * 100 +3
        ographic.loc[triaxial.index, 'id'] = 3

        ographic.insert(5, 'csType', 'ellipsoidal')
        ographic['name']= ographic['name'].str[:] + ' / Ographic'

        odetic = pd.concat([ocentric, ographic])
        odetic = odetic.rename(columns={'ellipsoid':'datum'})
        odetic = odetic.drop(columns=['Body'])    
        odetic = odetic.sort_values(by='code')
        odetic = odetic.astype({'code': int})
        return odetic

    def __projection(self, planetodetic):
        """    
        Information:
        * authority
        * version
        * code
        * name
        * baseCRS
        * method
        * parameterName
        * parameterValue
        """
        data = [        
        [10, "IAU","2005",0, "Equirectangular, clon=0", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],        
        [11, "IAU","2005",1, "Equirectangular, clon=0", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],        
        [12, "IAU","2005",2, "Equirectangular, clon=0", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],        
        [13, "IAU","2005",3, "Equirectangular, clon=0", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],        
        [14, "IAU","2005",4, "Equirectangular, clon=0", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],        
        [15, "IAU","2005",0, "Equirectangular, clon=180", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],           
        [16, "IAU","2005",1, "Equirectangular, clon=180", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],           
        [17, "IAU","2005",2, "Equirectangular, clon=180", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],           
        [18, "IAU","2005",3, "Equirectangular, clon=180", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],           
        [19, "IAU","2005",4, "Equirectangular, clon=180", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],                   
        [20, "IAU","2005",0, "Sinusoidal, clon=0", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [21, "IAU","2005",1, "Sinusoidal, clon=0", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [22, "IAU","2005",2, "Sinusoidal, clon=0", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [23, "IAU","2005",3, "Sinusoidal, clon=0", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [24, "IAU","2005",4, "Sinusoidal, clon=0", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [25, "IAU","2005",0, "Sinusoidal, clon=180", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [26, "IAU","2005",1, "Sinusoidal, clon=180", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [27, "IAU","2005",2, "Sinusoidal, clon=180", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [28, "IAU","2005",3, "Sinusoidal, clon=180", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [29, "IAU","2005",4, "Sinusoidal, clon=180", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [30, "IAU","2005",0, "North Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", 90, np.nan, np.nan],                   
        [31, "IAU","2005",1, "North Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", 90, np.nan, np.nan],                   
        [32, "IAU","2005",2, "North Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", 90, np.nan, np.nan],                   
        [33, "IAU","2005",3, "North Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", 90, np.nan, np.nan],                   
        [34, "IAU","2005",4, "North Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", 90, np.nan, np.nan],                           
        [35, "IAU","2005",0, "South Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", -90, np.nan, np.nan],               
        [36, "IAU","2005",1, "South Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", -90, np.nan, np.nan],               
        [37, "IAU","2005",2, "South Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", -90, np.nan, np.nan],               
        [38, "IAU","2005",3, "South Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", -90, np.nan, np.nan],               
        [39, "IAU","2005",4, "South Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", -90, np.nan, np.nan],               
        [40, "IAU","2005",0, "Mollweide, clon=0", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [41, "IAU","2005",1, "Mollweide, clon=0", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [42, "IAU","2005",2, "Mollweide, clon=0", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [43, "IAU","2005",3, "Mollweide, clon=0", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [44, "IAU","2005",4, "Mollweide, clon=0", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        [45, "IAU","2005",0, "Mollweide, clon=180", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [46, "IAU","2005",1, "Mollweide, clon=180", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [47, "IAU","2005",2, "Mollweide, clon=180", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [48, "IAU","2005",3, "Mollweide, clon=180", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [49, "IAU","2005",4, "Mollweide, clon=180", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        [50, "IAU","2005",0, "Robinson, clon=0", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [51, "IAU","2005",1, "Robinson, clon=0", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [52, "IAU","2005",2, "Robinson, clon=0", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [53, "IAU","2005",3, "Robinson, clon=0", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [54, "IAU","2005",4, "Robinson, clon=0", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        [55, "IAU","2005",0, "Robinson, clon=180", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        [56, "IAU","2005",1, "Robinson, clon=180", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        [57, "IAU","2005",2, "Robinson, clon=180", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        [58, "IAU","2005",3, "Robinson, clon=180", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        [59, "IAU","2005",4, "Robinson, clon=180", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
        ]

        columns = ['proj_id','authority', 'version', 'id', 'name', 'method', 'parameter1Name', 'parameter1Value', 'parameter2Name', 'parameter2Value', 'parameter3Name', 'parameter3Value', 'parameter4Name', 'parameter4Value', 'parameter5Name', 'parameter5Value', 'parameter6Name', 'parameter6Value']
        df = pd.DataFrame(data, columns = columns)
        planetodetic['baseCRS'] = planetodetic['authority'].apply(str) + ':' + planetodetic['version'].apply(str) + ":" + planetodetic['code'].apply(str)
        projection_df = pd.merge(planetodetic[['id','baseCRS', 'code']], df, on='id')    
        projection_df['code'] += projection_df['proj_id']
        projection_df.sort_values(by='code')  
        projection_df = projection_df.astype({'code': int})  
        return projection_df      

    def process(self):              
        df = self._df.copy()          
        df = self.__skipRecords(df)
        df = self.__processLongitudePositive(df)
        df = self.__processZeroLongitude(df)

        result = self.__ellipsoid(df)
        self._ellipsoid = result[['authority','version','code','name','semiMajorAxis','semiMedianAxis','semiMinorAxis','inverseFlatenning']]

        result = self.__datum(df, result)
        self._datum = result[['authority','version','code','name','body','ellipsoid','primeMeridianName','primeMeridianValue']]
        
        result = self.__planetodetic(df, result)
        self._planetodetic = result[['authority','version','code','name','datum','csType','longitudeDirection']]

        result = self.__projection(result)  
        self._projection = result[['authority','version','code','name','baseCRS', 'method', 'parameter1Name', 'parameter1Value', 'parameter2Name', 'parameter2Value', 'parameter3Name', 'parameter3Value', 'parameter4Name', 'parameter4Value', 'parameter5Name', 'parameter5Value', 'parameter6Name', 'parameter6Value']]


    def save(self):       
        self._ellipsoid.to_csv(r'ellipsoid.csv', index = False)
        self._datum.to_csv(r'datum.csv', index = False)
        self._planetodetic.to_csv(r'planetodetic.csv', index = False)
        self._projection.to_csv(r'projection.csv', index = False)

if __name__ == "__main__":
    crs = WKTcrs()
    crs.process()
    crs.save()

