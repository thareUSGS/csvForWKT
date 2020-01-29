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
        """ 
        # load the selected columns and rename them to match the required columns   
        ellipsoid = df[['Naif_id', 'Body','IAU2015_Semimajor','IAU2015_Axisb','IAU2015_Semiminor']]
        ellipsoid = ellipsoid.rename(columns={"Naif_id": "code", "Body":"name", "IAU2015_Semimajor":"semiMajorAxis", "IAU2015_Axisb":"semiMedianAxis", "IAU2015_Semiminor":"semiMinorAxis"})       
        # Add IAU authority as a vector
        ellipsoid.insert(0,"authority",['IAU']*len(df.Naif_id))
        # Add version as a vector
        ellipsoid.insert(1,"version",[2015]*len(df.Naif_id))
        # Create the code ID
        ellipsoid.loc[:,'code'] *= 100        
        # create the column name
        ellipsoid['name']= ellipsoid['name'].str[:] + ' (' + ellipsoid['version'].apply(str) + ')'
        # Add en empty inverse flatenning column
        ellipsoid = ellipsoid.assign(inverseFlatenning="")
        # Get all biaxial bodies
        biaxialBody = ellipsoid.query("semiMajorAxis == semiMedianAxis or semiMajorAxis == semiMinorAxis")
        # set empty the semiMedianAxis (or axisb)for biaxial bodies (having a semiMedianAxis means we have a triaxial axis)
        ellipsoid.loc[biaxialBody.index, 'semiMedianAxis'] = ""
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
        datum = ellipsoid[['authority','version','code','name']]                
        # We extract only the interesting columns from the CSV
        df_datum = df[['Body','origin_long_name','origin_lon_pos']]
        # we rename the columns to match the required columns
        df_datum = df_datum.rename(columns={"Body": "body", "origin_long_name":"primeMeridianName", "origin_lon_pos":"primeMeridianValue"})
        # we merge the two tables by adding columns from the first table to the second table
        datum = pd.concat([datum, df_datum], axis=1, sort=False, join='inner')    
        # we add the link to the ellipsoid
        datum['ellipsoid'] = datum['authority'].apply(str) + ':' + datum['version'].apply(str) + ':' + datum['code'].apply(str)
        # we reorganize the columns
        datum = datum[['authority','version','code','name','body','ellipsoid','primeMeridianName','primeMeridianValue']]
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

        Information:
        * authority
        * version
        * code
        * name
        * datum
        * csType (ellipsoidal or spherical)
        * longitudeDirection
        """
        df = df.rename(columns={'rotation':'longitudeDirection'})
        df_planeto = pd.concat([datum[['authority','version','code','name','ellipsoid']], df[['longitudeDirection','Body']]], axis=1, sort=False, join='inner')    
        ographic, ocentric = self.__splitDatumCase(df_planeto)    
        ocentric['longitudeDirection'] = 'east'
        ocentric.insert(5, 'csType', 'spherical')
        ocentric.loc[:,'code'] += 1
        ocentric['name']= ocentric['name'].str[:] + ' / Ocentric'  
        ographic.insert(5, 'csType', 'ellipsoidal')
        ographic['name']= ographic['name'].str[:] + ' / Ographic'
        odetic = pd.concat([ocentric,ographic])
        odetic = odetic.rename(columns={'ellipsoid':'datum'})
        odetic = odetic.drop(columns=['Body'])    
        odetic = odetic.sort_values(by='code')
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
        ["IAU","2005",10, "Equirectangular, clon=0", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],        
        ["IAU","2005",12, "Equirectangular, clon=180", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],           
        ["IAU","2005",14, "Sinusoidal, clon=0", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        ["IAU","2005",16, "Sinusoidal, clon=180", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        ["IAU","2005",18, "North Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", 90, np.nan, np.nan],           
        ["IAU","2005",20, "South Polar, clon=0","Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", -90, np.nan, np.nan],               
        ["IAU","2005",22, "Mollweide, clon=0", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],         
        ["IAU","2005",24, "Mollweide, clon=180", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],        
        ["IAU","2005",26, "Robinson, clon=0", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        ["IAU","2005",28, "Robinson, clon=180", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 180, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],          
        ["IAU","2005",60, "Auto Sinusoidal", "Sinusoidal", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],                
        ["IAU","2005",62, "Auto Stereographic", "Stereographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, "Latitude_Of_Origin", 0, np.nan, np.nan],        
        ["IAU","2005",64, "Auto Transverse Mercator", "Transverse_Mercator", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 0.9996, "Latitude_Of_Origin", 0, np.nan, np.nan],          
        ["IAU","2005",66, "Auto Orthographic", "Orthographic", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Latitude_Of_Origin", 90, np.nan, np.nan, np.nan, np.nan],         
        ["IAU","2005",68, "Auto Equirectangular", "Equirectangular", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 180, "latitude_Of_Origin", 0, np.nan, np.nan, np.nan, np.nan],           
        ["IAU","2005",70, "Auto Lambert_Conformal_Conic", "Lambert_Conformal_Conic_2SP", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Standard_Parallel_1", -20, "Standard_Parallel_2", 20, "latitude_Of_Origin", 0],          
        ["IAU","2005",72, "Auto Lambert_Azimuthal_Equal_Area", "Lambert_Azimuthal_Equal_Area", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, "Latitude_Of_Center", 90, np.nan, np.nan, np.nan, np.nan],        
        ["IAU","2005",74, "Auto Mercator", "Mercator_1SP", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, "Scale_Factor", 1, np.nan, np.nan, np.nan, np.nan],            
        ["IAU","2005",76, "Auto Albers", "Albers_Conic_Equal_Area", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, "Standard_Parallel_1", 60, "Standard_Parallel_2", 20, "Latitude_Of_Center", 40],                    
        ["IAU","2005",80, "Auto Mollweide", "Mollweide", "False_Easting", 0, "False_Northing", 0, "Central_Meridian", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],            
        ["IAU","2005",82, "Auto Robinson", "Robinson", "False_Easting", 0, "False_Northing", 0, "Longitude_Of_Center", 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]                                    
        ]

        columns = ['authority', 'version', 'code', 'name', 'method', 'parameter1Name', 'parameter1Value', 'parameter2Name', 'parameter2Value', 'parameter3Name', 'parameter3Value', 'parameter4Name', 'parameter4Value', 'parameter5Name', 'parameter5Value', 'parameter6Name', 'parameter6Value']
        df = pd.DataFrame(data, columns = columns)
        df_proj = pd.DataFrame(columns = columns)
        for index, row in planetodetic.iterrows():
            id = row['authority'] + ":" + str(row['version']) + ":" + str(row['code'])        
            copy_df = df.copy()
            copy_df['name'] = row['name'] + ' / ' + copy_df['name'] 
            copy_df['baseCRS'] = id
            copy_df['code'] = copy_df['code'] + row['code']
            df_proj = pd.concat([df_proj, copy_df], sort=True)
        df_proj = df_proj[['authority','version','code','name','baseCRS','method', 'parameter1Name', 'parameter1Value', 'parameter2Name', 'parameter2Value', 'parameter3Name', 'parameter3Value', 'parameter4Name', 'parameter4Value', 'parameter5Name', 'parameter5Value', 'parameter6Name', 'parameter6Value']]
        df_proj.sort_values(by='code')    
        return df_proj

    def process(self):              
        df = self._df.copy()          
        df = self.__skipRecords(df)
        df = self.__processLongitudePositive(df)
        df = self.__processZeroLongitude(df)
        self._ellipsoid = self.__ellipsoid(df)
        self._datum = self.__datum(df, self._ellipsoid)
        self._planetodetic = self.__planetodetic(df, self._datum)
        self._projection = self.__projection(self._planetodetic)  

    def save(self):       
        self._ellipsoid.to_csv(r'ellipsoid.csv', index = False)
        self._datum.to_csv(r'datum.csv', index = False)
        self._planetodetic.to_csv(r'planetodetic.csv', index = False)
        self._projection.to_csv(r'projection.csv', index = False)

if __name__ == "__main__":
    crs = WKTcrs()
    crs.process()
    crs.save()

