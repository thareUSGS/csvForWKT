#/usr/bin/env python3
import pandas as pd
import os

def readData():
    path = os.path.dirname(os.path.realpath(__file__)) + '/../data'
    df = pd.read_csv(path+'/naifcodes_radii_m_wAsteroids_IAU2015.csv')
    df = df.query("IAU2015_Semimajor!=-1 and IAU2015_Axisb!=-1 and IAU2015_Semiminor!=-1 and IAU2015_Mean!=-1")
    return df

def splitDatumCase(df):
    odetic = df[df.rotation.notnull()].query("Body!='Sun' and Body!='Moon'")
    ocentric = df
    return (odetic, ocentric)

def ellipsoid(df):
    ellipsoid = df[['Naif_id', 'Body','IAU2015_Semimajor','IAU2015_Semiminor']]
    ellipsoid.insert(0,"authority",['IAU']*len(df.Naif_id))
    ellipsoid.insert(1,"version",[2015]*len(df.Naif_id))
    ellipsoid = ellipsoid.rename(columns={"Naif_id": "code", "Body":"name", "IAU2015_Semimajor":"semiMajorAxis", "IAU2015_Semiminor":"semiMinorAxis"})
    ellipsoid.loc[:,'code'] *= 100
    ellipsoid['name']= ellipsoid['name'].str[:] + ' (' + ellipsoid['version'].apply(str) + ')'
    ellipsoid = ellipsoid.assign(inverseFlatenning="")
    ellipsoid.insert(5,"semiMedianAxis","")
    ellipsoid.to_csv(r'ellipsoid.csv', index = False)

def datum(df):
    datum = df[['Naif_id', 'Body','origin_long_name','origin_lon_pos']]
    datum.insert(0,"authority",['IAU']*len(df.Naif_id))
    datum.insert(1,"version",[2015]*len(df.Naif_id))
    datum = datum.rename(columns={"Naif_id": "code","Body":"body", "origin_long_name":"primeMeridianName", "origin_lon_pos":"primeMeridianValue"})
    datum.loc[:,'code'] *= 100
    datum['name']= datum['body'].str[:] + ' (' + datum['version'].apply(str) + ')'
    datum['ellipsoid'] =  datum['authority'].str[:] + ':' + datum['version'].apply(str) + ':' + datum['code'].apply(str)
    datum = datum[['authority', 'version', 'code', 'body', 'ellipsoid', 'primeMeridianName', 'primeMeridianValue']]
    datum.to_csv(r'datum.csv', index = False)

def planetodetic(df):
    planetodetic = df[['Naif_id', 'Body','rotation']]
    planetodetic.insert(0,"authority",['IAU']*len(df.Naif_id))
    planetodetic.insert(1,"version",[2015]*len(df.Naif_id))
    planetodetic = planetodetic.rename(columns={"Naif_id": "code","Body":"name","rotation":"longitudeDirection"})
    planetodetic.loc[:,'code'] = planetodetic.loc[:,'code'] * 100 + 1
    planetodetic['name']= planetodetic['name'].str[:] + ' (' + planetodetic['version'].apply(str) + ') / Geodetic'
    planetodetic = planetodetic.replace(to_replace ="Direct", value="west")
    planetodetic = planetodetic.replace(to_replace ="Retrograde", value="east")
    # handle historical reasons
    idx = (df.query("Body=='Earth'").index)[0]
    planetodetic.at[idx,'longitudeDirection'] = "east"   
    planetodetic.to_csv(r'planetodetic.csv', index = False)

def projected(df):
    pass

df = readData()
ellipsoid(df)
datum(df)
odetic, ocentric = splitDatumCase(df)
planetodetic(odetic)

