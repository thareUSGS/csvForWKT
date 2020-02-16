import unittest
import logging
import os, sys, subprocess
from src import Crs2WKT
 

class WktTest(unittest.TestCase):

    def setUp(self):
        logging.debug("Start setUp")
        crs = Crs2WKT()
        crs.process()
        self.wkts = crs.getWkts()    
        logging.debug("Stop setUp")     

    def test_validation(self):
        """
        Test that WKT is valid
        """
        logging.debug("Start test_validation")
        i=0
        for code, wkt in self.wkts.items():
            with self.subTest(code=code):
                i = i+1
                logging.debug("--> Processing %s.wkt - %s/%s", code, i, len(self.wkts.items()))
                dirpath = os.getcwd()
                file = dirpath+"/tests_wkt/"+str(code)+".wkt"
                stream = subprocess.Popen(["docker", 
                "run", "--rm", 
                "-v", "/home:/home", 
                "osgeo/gdal:alpine-small-latest", "gdalsrsinfo",
                "-V", file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)                
                info, stderr = stream.communicate()  
                info = info.decode("utf-8")

                lines = info.split("\n")
                warning = [s for s in lines if ("ERROR" in s)]

                if len(warning) > 0 :
                    logging.warning("\t%s",warning)
                isSucceed = "Succeeds" in info
                logging.debug("\tisValid %s", isSucceed)
                if not isSucceed:
                    logging.error("\t%s",info)
                self.assertTrue(isSucceed) 
        logging.debug("Stop test_validation")

if __name__ == '__main__':
    # -log info
    logging.basicConfig(filename="result.log", filemode="w",level=logging.DEBUG)
    logging.debug("Computing WKT")
    crs = Crs2WKT()
    crs.process()
    wkts = crs.getWkts() 
    if os.path.isdir("tests_wkt"):
        for i in os.listdir("tests_wkt"):
            os.remove(os.path.join("tests_wkt", i))
        os.rmdir("tests_wkt") 
        os.mkdir("tests_wkt")

    logging.debug("Start WKTs generation")
    for code, wkt in wkts.items():
        f = open("tests_wkt/"+str(code)+".wkt", "w") 
        f.write(wkt)
        f.close() 
    logging.debug("Stop WKTs generation")   
    unittest.main()