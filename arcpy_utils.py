# ------------------------------------------------------------------------------
# Name: arcpy_utils.py
# Author: Owen Smith, University of North Georgia IESA
# Purpose: Python module containing miscellaneous arcpy functions created for
# 		   various different uses.
# License: GNU v3.0 
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
	out_dir :: str: Directory where out_dir puts will be saved
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


def shp_extent(shp):
	for row in arcpy.da.SearchCursor(shp, ['SHAPE@']):
		extent = row[0].extent
		print('XMin: {}, YMin: {}'.format(extent.XMin, extent.YMin))
		print('XMax: {}, YMax: {}'.format(extent.XMax, extent.YMax))

		return extent.XMin, extent.YMin, extent.XMax, extent.YMax


def query_GLUT(glut_tif, out_raster, value_list):
	"""
	This function is created to query GLUT land cover rasters and create a
	new tif file of the selected values.
	---
	Parameters:
		glut_tif :: str : input GLUT raster
		out_raster :: str : output raster of selected values
		value_list :: list of int : values to query

	"""

	raster = arcpy.Raster(glut_tif)

	if len(value_list) == 1:
		clause = ["VALUE = %d" % value_list[i] for i in
				  range(len(value_list))]
		query_string = " ".join(clause)
		extract = arcpy.sa.ExtractByAttributes(glut_tif, query_string)

	if len(value_list) > 1:
		clause = ["VALUE = %d OR" % value_list[i] for i in
				  range(len(value_list))]
		query = " ".join(clause)
		query_string = query[:-3]
		extract = arcpy.sa.ExtractByAttributes(glut_tif, query_string)

	extract.save(out_raster)


def query_NLCD(nlcd_tif, out_raster, value_list):
	"""
	This function is created to query NLCD rasters and create a
	new tif file of the selected values.
	---
	Parameters:
		nlcd_tif :: str : input NLCD raster
		out_raster :: str : output raster of selected values
		value_list :: list of int : values to query

	"""

	raster = arcpy.Raster(nlcd_tif)

	if len(value_list) == 1:
		clause = ["VALUE = %d" % value_list[i] for i in
				  range(len(value_list))]
		query_string = " ".join(clause)
		extract = arcpy.sa.ExtractByAttributes(nlcd_tif, query_string)

	if len(value_list) > 1:
		clause = ["VALUE = %d OR" % value_list[i] for i in
				  range(len(value_list))]
		query = " ".join(clause)
		query_string = query[:-3]
		extract = arcpy.sa.ExtractByAttributes(nlcd_tif, query_string)

	extract.save(out_raster)


def elevChange_analysis(tif_path_list, out_dir):
	"""
	This function creates and aggregates temporal elevation change accros the
	input elevation tifs.
	It operates in two parts:
		1. Calculates differences between each individual elevation raster and
		   its subsequent raster for each input raster.
		   e.g. 1980 Elev - 1990 Elev, 1990 Elev - 2010 Elev, .... etc.
		   Each is saved as time_spanX.tif in the out put directory

		2. Creates an aggregated change raster across the entire temporal set.
		   Saved as AggElevCh.tif in the output directory

	Created as part of the ASABE 2020 research submission.
	---
	Parameters:
		tif_path_list :: list : List of all input elevation rasters
					** Rasters must be in correct temporal order
					   e.g. [Oldest, .... , Newest]
					   		[C:/tmp/1954Elev.tif, .... , C:/tmp/2000Elev.tif]
		out_dir :: str : Output directory where all rasters will be saved

    """
	if not os.path.exists(out_dir):
		os.mkdir(out_dir)
		print(out_dir, ' created.')
	arcpy.env.overwriteOutput = True
	spans = [(arcpy.Raster((tif_path_list[i + 1])) -
			  arcpy.Raster(tif_path_list[i])) for i
			  in range(len(tif_path_list) - 1)]
	agg_names = []
	for i in range(len(spans)):
		fileName = '%s/%s%d%s' % (out_dir, 'time_span', i, '.tif')
		agg_names.append(fileName)
		spans[i].save(fileName)
	agg = arcpy.sa.CellStatistics(agg_names, "MEAN")
	fileName = '%s/%s' % (out_dir, 'AggElevCh.tif')
	agg.save(fileName)

	print('Outputs saved to ', out_dir)
