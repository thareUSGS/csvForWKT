# /usr/bin/env python3
import os

import numpy as np
import pandas as pd

from .bodyWKT import TemplateWKTFactory
from .iprojectedwkt import IProjectedCRS


class Crs2WKT:
    """
    Create WKT from a CSV file
    """    

    def __init__(self, path = None, filename = 'naifcodes_radii_m_wAsteroids_IAU2015.csv'):
        """Constructor
        
        Keyword Arguments:
            path {str} -- Path where the CSV file is located (default: {None})
            filename {str} -- filename (default: {'naifcodes_radii_m_wAsteroids_IAU2015.csv'})
        """        
        pathFile = path if path is not None else os.path.dirname(os.path.realpath(__file__)) + '/../data/'
        self._df = pd.read_csv(pathFile+filename)               
        self._ellipsoid = None
        self._datum = None
        self._planetodetic = None
        self._projection = None
        self._wkt = None


    def _merge_planetodetic_data(self):
        """Merge ellipsoid, datum and planetodic tables
        
        Returns:
            pandas -- information for creating non projected CRS
        """
        datum = self._datum.copy()
        ellipsoid = self._ellipsoid.copy()                
        datum['datum'] = datum['authority'].apply(str) + ':' + datum['version'].apply(str) + ':' + datum['code'].apply(str)
        datum = datum[['name', 'datum', 'body', 'ellipsoid', 'primeMeridianName', 'primeMeridianValue']]
        datum = datum.rename(columns = {'name':'datum_name'})

        ellipsoid['ellipsoid'] = ellipsoid['authority'].apply(str) + ':' + ellipsoid['version'].apply(str) + ':' + ellipsoid['code'].apply(str)        
        ellipsoid = ellipsoid[['name', 'ellipsoid', 'semiMajorAxis', 'semiMedianAxis', 'semiMinorAxis', 'inverseFlatenning', 'remark']]
        ellipsoid = ellipsoid.rename(columns = {'name':'ellipsoid_name'})
        data = pd.merge(self._planetodetic, datum, on = 'datum')
        data = pd.merge(data, ellipsoid, on = 'ellipsoid') 

        return data             

    def _merge_projection(self, data):
        """Merge projection and non projected tables
        
        Arguments:
            data {pandas} -- Non projected table
        
        Returns:
            pandas -- information for creating projected CRS
        """    
        dataProjected = data.copy()
        dataProjected['baseCRS'] = dataProjected['authority'].apply(str) + ':' + dataProjected['version'].apply(str) + ':' + dataProjected['code'].apply(str)
        dataProjected = dataProjected.rename(columns = {'authority':'authority_baseCrs', 'version':'version_baseCrs', 'code':'code_baseCrs', 'name':'name_baseCrs'})
        projection = self._projection.rename(columns = {'id':'projection_id'})
        dataProjected = pd.merge(projection, dataProjected, on = 'baseCRS')  
        return dataProjected
    

    def _compute_wkts(self):
        """Compute WKTs
        """       
        self._wkt = {}
        col_names =  ['code', 'wkt']
        wkts  = pd.DataFrame(columns = col_names)
        planetodeticData = self._merge_planetodetic_data()   
        projectedPlanetodeticData = self._merge_projection(planetodeticData)
        for index, row in planetodeticData.iterrows():
            wkt = TemplateWKTFactory.create(row)
            wkts = wkts.append({'code': row['code'], 'wkt': wkt}, ignore_index = True)
        
        for index, row in projectedPlanetodeticData.iterrows():
            wkt = TemplateWKTFactory.create(row)
            wkts = wkts.append({'code': row['code'], 'wkt': wkt}, ignore_index = True) 

        wkts = wkts.sort_values(by = 'code') 
        exception = []
        for index, wkt in  wkts.iterrows():
            try:
                wkt['wkt'].computeWKT()
                self._wkt[wkt['code']] = wkt['wkt'].getWKT()
            except Exception as err:
                msg = "%s %s %s"%(err, wkt['code'], wkt['wkt'])
                exception.append(msg)

        if len(exception)>0:
            raise Exception(msg)
        

    def __skip_records(self, df):
        """Skip records when IAU2015_Semimajor != -1 or IAU2015_Axisb != -1 or IAU2015_Semiminor != -1
        
        Arguments:
            df {pandas} -- pandas containing the IAU CSV file
        
        Returns:
            pandas -- IAU data without records for which IAU2015_Semimajor != -1 or IAU2015_Axisb != -1 or IAU2015_Semiminor != -1
        """    
        return self._df.query("IAU2015_Semimajor != -1 and IAU2015_Axisb != -1 and IAU2015_Semiminor != -1")

    def __process_longitude_positive(self, df):
        """Define the positive longitudes in ographic CRS based on the rotation sens.
         The general rule is the following:
        * Direct rotation has longitude positive to West
        * Retrograde rotation has longitude positive to East
        A special case is done for Sun/Earth/Moon for historical reasons for which longitudes
        are positive to East independently of the rotation sens

        Arguments:
            df {pandas} -- pandas containing the IAU CSV file
        
        Returns:
            pandas -- IAU information with updated longitude sens
        """       
        df = df.replace(to_replace = "Direct", value = "west")
        df = df.replace(to_replace = "Retrograde", value = "east")
        historic = df.query("Body == 'Sun' or Body == 'Moon' or Body == 'Earth'")
        historic = historic.copy()
        historic.loc[:, 'rotation'] = "east"
        df.update(historic)
        return df

    def __process_zero_longitude(self, df):
        """Set default values for origin_lon_pos/origin_long_name
        
        Arguments:
            df {pandas} -- pandas containing the IAU CSV file
        
        Returns:
            pandas -- IAU information with updated longitude value and position
        """      
        df.loc[df['origin_lon_pos'].isnull(), 'origin_lon_pos'] = "0.0"
        df.loc[df['origin_long_name'].isnull(), 'origin_long_name'] = 'Reference_Meridian'
        return df                


    def __ellipsoid(self, df):
        """Computes the ellipsoid.
        
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
        * remark

        When the semiMedianAxis is empty then the ellipsoid is biaxial otherwise we consider a triaxial body with 
        semi-minor < semiMedian (axisb) < semiMajor   

        General case:
        --  --  --  --  --  -- -

                                        / --  -- - > sphere with semi-major radius(ellipse case)   /* interoperability */
        bodies shape  --  --  --  >  sphere  /  OR
                      |     (code: 00) \
                      |                 \ --  --  --  > sphere with median radius(triaxial case)      /* interoperability */
                      |AND
                      |      / --  -- - > ellipse /* Physics case for twoaxial bodies
                      |_____/  OR    (code: 01) 
                            \     
                             \ --  -- - > triaxial /* Physics case for triaxial bodies
                                     (code :02)

        Special cases:
        --  --  --  --  --  -- -
        1/ Use R_m = (a+b+c)/3 as mean radius when mean radius is not defined ( = -1)

        Arguments:
            df {pandas} -- pandas containing the IAU CSV file
        
        Returns:
            pandas -- a new table with IAU information with the following reference ellipsoid : sphere, ellipse, triaxial
        """        
        # load the selected columns and rename them to match the required columns
        ellipsoid = df[['Naif_id', 'Body', 'IAU2015_Semimajor', 'IAU2015_Axisb', 'IAU2015_Semiminor', 'IAU2015_Mean']]
        ellipsoid = ellipsoid.rename(columns = {"Naif_id": "code", "Body":"name", "IAU2015_Semimajor":"semiMajorAxis", "IAU2015_Axisb":"semiMedianAxis", "IAU2015_Semiminor":"semiMinorAxis"})
        ellipsoid['Naif_id'] = ellipsoid['code']
        # duplicate rows for handling code 00, 01, 02
        ellipsoid = ellipsoid.append([ellipsoid]*2, ignore_index = True)
        # Add IAU authority as a vector
        ellipsoid.insert(0, "authority", ['IAU']*len(ellipsoid.code))
        # Add version as a vector
        ellipsoid.insert(1, "version", [2015]*len(ellipsoid.code))
        # Add en empty inverse flatenning column
        ellipsoid = ellipsoid.assign(inverseFlatenning = "")
        ellipsoid = ellipsoid.assign(remark = "")

        # Create cases
        ellipsoid.loc[0::3, 'type'] = 'SPHERE'
        ellipsoid.loc[0::3, 'code'] *= 100 
        ellipsoid.loc[0::3, 'name'] = ellipsoid.loc[0::3, 'name'].str[:] + ' (' + ellipsoid.loc[0::3, 'version'].apply(str) + ') - Sphere'
        ellipsoid.loc[0::3, 'inverseFlatenning'] = 0

        ellipsoid.loc[1::3, 'type'] = 'ELLIPSE'
        ellipsoid.loc[1::3, 'code'] = ellipsoid.loc[1::3, 'code'] * 100 + 1
        ellipsoid.loc[1::3, 'name'] = ellipsoid.loc[1::3, 'name'].str[:] + ' (' + ellipsoid.loc[1::3, 'version'].apply(str) + ')'        
        ellipsoid.loc[1::3, 'inverseFlatenning'] =  ellipsoid.loc[1::3, 'semiMajorAxis'] / (ellipsoid.loc[1::3, 'semiMajorAxis'] - ellipsoid.loc[1::3, 'semiMinorAxis'])
        ellipsoid['inverseFlatenning'] = ellipsoid['inverseFlatenning'].replace(np.nan, 0)

        ellipsoid.loc[2::3, 'type'] = 'TRIAXIAL'
        ellipsoid.loc[2::3, 'code'] =  ellipsoid.loc[2::3, 'code'] * 100 + 2
        ellipsoid.loc[2::3, 'name'] = ellipsoid.loc[2::3, 'name'].str[:] + ' (' + ellipsoid.loc[2::3, 'version'].apply(str) + ')'  

        # Exceptions to the general cases         
           # case1 =  > Use R_m = (a+b+c)/3 as mean radius when mean radius is not defined 
        ellipseBodyToRemove = ellipsoid.query("IAU2015_Mean == -1 and (type != 'TRIAXIAL' and type != 'SPHERE')")
        ellipsoid = ellipsoid.drop(ellipseBodyToRemove.index) 
        medianSphereToSet = ellipsoid.query("IAU2015_Mean == -1 and type == 'SPHERE'")
        ellipsoid.loc[medianSphereToSet.index, 'IAU2015_Mean'] = (ellipsoid.loc[medianSphereToSet.index, 'semiMajorAxis'] \
            + ellipsoid.loc[medianSphereToSet.index, 'semiMinorAxis'] + ellipsoid.loc[medianSphereToSet.index, 'semiMedianAxis']) / 3
        ellipsoid.loc[medianSphereToSet.index, 'remark'] += "Use R_m = (a+b+c)/3 as mean radius. "


        # Spherical case            
            # set mean radius for triaxial bodies
        triaxialBodies = ellipsoid.query("semiMajorAxis != semiMedianAxis and semiMinorAxis != semiMedianAxis and type == 'SPHERE'")            
        ellipsoid.loc[triaxialBodies.index, 'semiMajorAxis'] = ellipsoid.loc[triaxialBodies.index, 'IAU2015_Mean']
        ellipsoid.loc[triaxialBodies.index, 'semiMinorAxis'] = ellipsoid.loc[triaxialBodies.index, 'IAU2015_Mean']
        ellipsoid.loc[triaxialBodies.index, 'semiMedianAxis'] = ""
        ellipsoid.loc[triaxialBodies.index, 'remark'] += "Use mean radius as sphere radius for interoperability. " 
           # set semi major radius for ellipse bodies
        sphere = ellipsoid.query("type == 'SPHERE'")   
        noTriaxialBodies_index = pd.Index(list(set(sphere.index.tolist()).difference(set(triaxialBodies.index.tolist()))))
        ellipsoid.loc[noTriaxialBodies_index, 'semiMinorAxis'] = ellipsoid.loc[noTriaxialBodies_index, 'semiMajorAxis']
        ellipsoid.loc[noTriaxialBodies_index, 'semiMedianAxis'] = ""
        ellipsoid.loc[noTriaxialBodies_index, 'remark'] = "Use semi-major radius as sphere for interoperability. "
          

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

        # Remove remark when there the body is really a sphere
        remarkNoSphericalApprox = ellipsoid.query("type == 'ELLIPSE' and semiMajorAxis == semiMinorAxis")
        for i in remarkNoSphericalApprox.index:
            naifID = remarkNoSphericalApprox.loc[i, 'Naif_id']
            sphere = ellipsoid.query("type == 'SPHERE' and Naif_id == "+str(naifID))
            ellipsoid.loc[sphere.index, 'remark'] = ""

        ellipsoid['remark'] += 'Source of IAU Coordinate systems: doi://10.1007/s10569-017-9805-5'

        # sort by code
        ellipsoid = ellipsoid.sort_values(by = 'code')
        ellipsoid = ellipsoid.astype({'code': int}) 

        return ellipsoid

    def __datum(self, df, ellipsoid):
        """Compute the datum
        
        Information to save:
        * authority
        * version
        * code
        * name
        * body
        * ellipsoid (linked to ellipsoid)
        * primeMeridianName
        * primeMeridianValue

        Arguments:
            df {pandas} -- IAU information
            ellipsoid {pandas} -- ellipsoid information
        
        Returns:
            pandas -- datum information
        """     

        # we create the fatum based on the ellipsoid
        datum = ellipsoid[['Naif_id', 'type', 'authority', 'version', 'code', 'name']]                
        # We extract only the interesting columns from the CSV
        df_datum = df[['Naif_id', 'Body', 'origin_long_name', 'origin_lon_pos']]
        # we rename the columns to match the required columns
        df_datum = df_datum.rename(columns = {"Body": "body", "origin_long_name":"primeMeridianName", "origin_lon_pos":"primeMeridianValue"})
        # we merge the two tables by adding columns from the first table to the second table
        datum = pd.merge(datum, df_datum, on = 'Naif_id')    
        # we add the link to the ellipsoid
        datum['ellipsoid'] = datum['authority'].apply(str) + ':' + datum['version'].apply(str) + ':' + datum['code'].apply(str)
        # we reorganize the columns
        datum = datum[['Naif_id', 'type', 'authority', 'version', 'code', 'name', 'body', 'ellipsoid', 'primeMeridianName', 'primeMeridianValue']]
        # we sort by code
        datum = datum.sort_values(by = 'code')

        return datum       

    def __split_datum_case(self, df):
        """From datum information, split the information into two categories : ographic, ocentric
        
        Arguments:
            df {pandas} -- datum information
        
        Returns:
            (pandas, pandas) -- (ographic, ocentric)
        """   
        # By default, each datum is ocentric. In an ocentric CRS, the longitude is always positive to East
        ocentric = df
        # When the longitude direction is not null, we know the rotation sens so we could use an ographic rotation
        # For historical reasons, longitudes for Sun/Moon/Earth are positives to East for ographic/ocentric CRS. In addition, Sun and Moon have
        # a spherical shape. So we do not need to consider the ographic CRS for Sun/Moon because ographic definition = ocentric definition
        ographic = df[df.longitudeDirection.notnull()].query("Body != 'Sun' and Body != 'Moon'")
        return (ographic, ocentric)


    def __planetodetic(self, df, datum):
        """Compute the planetodetic information according to IAU and datum information
        
        Planetodetic could be ocentric or ographic. ocentric has csType = spherical where as ographic has csType = ellipsoidal
        ocentric as even values" and "ographic as odd"
        Information:
        * authority
        * version
        * code
        * name
        * datum
        * csType (ellipsoidal or spherical)
        * longitudeDirection 

        xxx00 =  > Ocentric on a Sphere. If triaxial use Mean, even if elliptical use Semi-major axis as a sphere, Always East.
        xxx01 =  > Ographic on ellipse (West or East, depending on body rotation)
        xxx02 =  > Ocentric on ellipse (always East)
        xxx03 =  > Ographic on Triaxial, (West or East, depending on body rotation)
        xxx04 =  > Ocentric on Triaxial, East (for more advanced applications, not for map projections, like ISIS3, VICAR, ...) 
                
        Arguments:
            df {pandas} -- IAU information
            datum {pandas} -- datum information
        
        Returns:
            pandas -- planetodetic information
        """      
        df = df.rename(columns = {'rotation':'longitudeDirection'})
        df_planeto = pd.merge(datum[['Naif_id', 'authority', 'version', 'code', 'name', 'ellipsoid', 'type']], df[['Naif_id', 'longitudeDirection', 'Body']], on = 'Naif_id')

        ographic, ocentric = self.__split_datum_case(df_planeto)    
                
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
        ocentric['name'] = ocentric['name'].str[:] + ' / Ocentric'
        
        sphereEast = ographic.query("type == 'SPHERE'")
        ographic = ographic.drop(sphereEast.index)
        
        # small processing of ographic code
        ellipse = ographic.query("type == 'ELLIPSE'")
        ographic.loc[ellipse.index, 'code'] = ocentric.loc[ellipse.index, 'Naif_id'] * 100 +1
        ographic.loc[ellipse.index, 'id'] = 1

        triaxial = ographic.query("type == 'TRIAXIAL'")
        ographic.loc[triaxial.index, 'code'] = ographic.loc[triaxial.index, 'Naif_id'] * 100 +3
        ographic.loc[triaxial.index, 'id'] = 3

        ographic.insert(5, 'csType', 'ellipsoidal')
        ographic['name'] = ographic['name'].str[:] + ' / Ographic'

        # longitude ographic is always to East for small bodies, comets, dwarf planets
        ographicToEast = ographic.query("code >= 900")
        ographic.loc[ographicToEast.index, 'longitudeDirection'] = 'east'

        odetic = pd.concat([ocentric, ographic])
        odetic = odetic.rename(columns = {'ellipsoid':'datum'})
        odetic = odetic.drop(columns = ['Body'])    
        odetic = odetic.sort_values(by = 'code')
        odetic = odetic.astype({'code': int, 'id': int})
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
        data = IProjectedCRS.getProjectionCode()

        planetodeticCopy = planetodetic.copy()
        columns = ['proj_id', 'authority', 'version', 'id', 'name', 'method', 'parameter1Name', 'parameter1Value', 'parameter2Name', 'parameter2Value', 'parameter3Name', 'parameter3Value', 'parameter4Name', 'parameter4Value', 'parameter5Name', 'parameter5Value', 'parameter6Name', 'parameter6Value']
        df = pd.DataFrame(data, columns = columns)
        planetodeticCopy['baseCRS'] = planetodeticCopy['authority'].apply(str) + ':' + planetodeticCopy['version'].apply(str) + ":" + planetodeticCopy['code'].apply(str)
        projection_df = pd.merge(planetodeticCopy[['id', 'baseCRS', 'code']], df, on = 'id')    
        projection_df['code'] += projection_df['proj_id']
        projection_df.sort_values(by = 'code')  
        projection_df = projection_df.astype({'code': int})  
        return projection_df      

    def process(self):              
        df = self._df.copy()          
        df = self.__skip_records(df)
        df = self.__process_longitude_positive(df)
        df = self.__process_zero_longitude(df)

        self._ellipsoid = self.__ellipsoid(df)
        self._datum = self.__datum(df, self._ellipsoid)        
        self._planetodetic = self.__planetodetic(df, self._datum)
        self._projection = self.__projection(self._planetodetic)   
        self._compute_wkts()   

    def getWkts(self):
        return self._wkt    


    def save(self):    
        if os.path.isdir("results"):
            for i in os.listdir("results"):
                os.remove(os.path.join("results", i))
            os.rmdir("results") 
        os.mkdir("results")           
        ellipsoid = self._ellipsoid[['authority', 'version', 'code', 'name', 'semiMajorAxis', 'semiMedianAxis', 'semiMinorAxis', 'inverseFlatenning', 'remark']]
        ellipsoid.to_csv(r'results/ellipsoid.csv', index = False)

        datum = self._datum[['authority', 'version', 'code', 'name', 'body', 'ellipsoid', 'primeMeridianName', 'primeMeridianValue']]
        datum.to_csv(r'results/datum.csv', index = False)

        planetodetic = self._planetodetic[['authority', 'version', 'code', 'name', 'datum', 'csType', 'longitudeDirection']]
        planetodetic.to_csv(r'results/planetodetic.csv', index = False)

        projection = self._projection[['authority', 'version', 'code', 'name', 'baseCRS', 'method', 'parameter1Name', 'parameter1Value', 'parameter2Name', 'parameter2Value', 'parameter3Name', 'parameter3Value', 'parameter4Name', 'parameter4Value', 'parameter5Name', 'parameter5Value', 'parameter6Name', 'parameter6Value']]
        projection.to_csv(r'results/projection.csv', index = False)

        wkts = self.getWkts()
        for code, wkt in wkts.items():
            print(wkt)
