#!/usr/bin/env python

"""
==================================================
 Project/Script Name
==================================================
 Author:        Marc Huwiler
 Created:       2025-08-18

 Description:
    Quick and dirty script to make json formatted dictionary entries
    for dataset names from CMS DAS system. 

 Usage:
    python3 DAS2json.py QCDdatasets.txt -o QCDfilesall.json

    dasgoclient --query="dataset=/QCD*/*RunIII2024Summer24MiniAODv6*/MINIAODSIM" | python3 DAS2json.py

 Notes:
    - Works both in Python 2 and Python 3
    - Can be used in a bash pipe chain
    
==================================================
"""

from __future__ import division, print_function

import os
import sys
import copy
import json
from argparse import ArgumentParser



def DatasetDictFromFile(filename): 
	result = ""

	with open(os.path.expandvars(filename), "r") as infile:
		for line in infile.readlines(): 
			line = line.rstrip("\n") #line.replace("\n", "").replace("\r", "")
			result += FormatLine(line)

	return result

def WriteDatasetDictToJson(result, filename): 
	with open(filename, "w") as outfile: 
			outfile.write("{")
			outfile.write(result)
			outfile.write("}")
			#json.dump(results, outfile, ensure_ascii=False, sort_keys=False) #encoding="utf8", 

def FormatFromCmdInput(cmdinput): 
	result = ""

	print(cmdinput)
	cmdinput = cmdinput.rstrip("\n")
	for line in cmdinput.split("\n"): 
			result += FormatLine(line)

	return result

def FormatLine(line): 
	key = line.split("/")[1] # the dataset begins with a "/" so need the key after that
	result = "\"{}\": \"{}\",\n".format(key, line)
	print(result)
	return result


if __name__ == "__main__":

	parser = ArgumentParser(description="MergeLumis")
	parser.add_argument("file", action="store", type=str, default="", help="Name of file with datasets from DAS. ")
	parser.add_argument('-n', "--show", dest="show", action="store_false", default=True, help="Display result in terminal. ")
	parser.add_argument("-o", "--output", dest="output", action="store", type=str, default="", help="Name of json file for storing output. ")
	parser.add_argument("--debug", dest="debug", action="store_true", default=False, help="Turn on debug output")
	parser.add_argument('-b', "--batch", dest="batch", action="store_true", default=False, help="Run in batch mode")


	# Reading input in case of command line usage 
	if not os.isatty(0):
		cmdinput = sys.stdin.read()
		datasets = FormatFromCmdInput(cmdinput)
		print(datasets)

	else: 
		args = parser.parse_args()
		datasets = DatasetDictFromFile(args.file)


		if(args.show): print(datasets)

		if (args.output != ""): 
			WriteDatasetDictToJson(datasets, args.output)
			

