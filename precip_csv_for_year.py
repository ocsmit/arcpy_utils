#------------------------------------------------------------------------------
# Name: precip_csv_for_year.py
# Author: Owen Smith, Zach Pilgrim, University of North Georgia IESA
# Purpose: Filter precipitation csv for efficient data processing in Operation 
#          Odocoileus
#------------------------------------------------------------------------------

import os
import pandas as pd
import arcpy

def filter_precip_to_shp(in_csv, out_csv, out_shp):

	data = pd.read_csv(in_csv, skiprows=10)

	data_tmp = data[['Date', 'ppt (inches)', 'Latitude', 'Longitude']]
	data_1980 = data_tmp.query('Date == 1980')

	export = data_1980.to_csv(out_csv, index = None, header=True)
	
	arcpy.management.XYTableToPoint(out_csv, out_shp, 'Longitude', 'Latitude')
	
	print('Complete.')
