# ------------------------------------------------------------------------------
# Name: arcpy_utils.py
# Author: Owen Smith, University of North Georgia IESA
# Purpose: Python module containing miscellaneous arcpy functions created for
# 		   various different uses.
# ------------------------------------------------------------------------------

import os
import pandas as pd
import arcpy


def add_naip(gt_point, naipqq_layer, naip_dir):
	"""
	This function adds naip imagery where a groundtruthing point is located
	into an arcgis pro project. Imagery is saved as a temporary layer in the
	memory of the arcgis pro project.
	---
	Parameters:
	gt_point :: str: Name of ground truthing point shapefile to add NAIP based
					 off of
	naipqq_layer :: str: NAIP Quarter Quad shapefile.
	naip_dir :: str: Directory in which all NAIP imagery is stored.
	"""

	arcpy.SelectLayerByAttribute_management(naipqq_layer, 'CLEAR_SELECTION')
	arcpy.SelectLayerByLocation_management(naipqq_layer, 'INTERSECT', gt_point)

	with arcpy.da.SearchCursor(naipqq_layer, ['FileName']) as cur:
		for row in sorted(cur):
			filename = '%s.tif' % row[0][:-13]
			print(filename)
			folder = filename[2:7]
			infile_path = '%s/%s/%s' % (naip_dir, folder, filename)
			tmp = 'in_memory/%s' % filename
			arcpy.MakeRasterLayer_management(infile_path, tmp)

	print('Complete')


def yearly_weather_csv_to_shp(in_csv, year, columns, out_dir, csv_name,
								shp_name):
	"""
	This function was created to aid with processing of yearly weather data .CSV
	files from prism.oregon.edu and create point shapefiles with the desired
	fields.

	Project: Operation Odocoileus - Zach Pilgrim
	---
	Parameters:
	in_csv :: str: File path of input .CSV file
	year :: int: Year being selected
	columns :: list: List of weather columns to use in final shapefile/.CSV
	out_dir :: str: Directory where out puts will be saved
	csv_name :: str: Name of final output .CSV, does not need file extension
	shp_name :: str: Name of final output shapefile, does not need
					 file extension
	"""

	data = pd.read_csv(in_csv, skiprows=10)
	fields = ['Name', 'Date', 'Latitude', 'Longitude']
	for i in columns:
		fields.append(i)

	data_tmp = data[fields]
	query = 'Date == %d' % year
	data_1980 = data_tmp.query(query)

	if not os.path.exists(out_dir):
		os.mkdir(out_dir)
	year_csv = '%s_%d%s' % (csv_name, year, '.csv')
	out_csv = '%s/%s' % (out_dir, year_csv)
	if os.path.exists(out_csv):
		print('Output CSV file exists already.')
	if not os.path.exists(out_csv):
		data_1980.to_csv(out_csv, index=None, header=True)
	year_shp = '%s_%d%s' % (shp_name, year, '.shp')
	out_shp = '%s/%s' % (out_dir, year_shp)
	if os.path.exists(out_shp):
		print('Output shapefile exists already')
	if not os.path.exists(out_shp):
		arcpy.management.XYTableToPoint(out_csv, out_shp, 'Longitude',
										'Latitude')
		delete_fields = ['Latitude', 'Longitude']
		arcpy.DeleteField_management(out_shp, delete_fields)

	print('Complete.')
