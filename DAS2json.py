#!/usr/bin/env python
from __future__ import division, print_function

import os
import copy
import json
from argparse import ArgumentParser


if __name__ == "__main__":

	parser = ArgumentParser(description="MergeLumis")
	parser.add_argument("file", action="store", type=str, default="", help="Name of file with datasets from DAS. ")
	parser.add_argument('-n', "--show", dest="show", action="store_false", default=True, help="Display result in terminal. ")
	parser.add_argument("-o", "--output", dest="output", action="store", type=str, default="", help="Name of json file for storing output. ")
	parser.add_argument("--debug", dest="debug", action="store_true", default=False, help="Turn on debug output")
	parser.add_argument('-b', "--batch", dest="batch", action="store_true", default=False, help="Run in batch mode")
	
	args = parser.parse_args()


	result = ""

	with open(os.path.expandvars(args.file), "r") as infile:
		for line in infile.readlines(): 
			line = line.rstrip("\n") #line.replace("\n", "").replace("\r", "")
			key = line.split("/")[1] # the dataset begins with a "/" so need the key after that
			result += "\"{}\": \"{}\",\n".format(key, line)


	if(args.show): print(result)

	if (args.output != ""): 
		with open(args.output, "w") as outfile: 
			outfile.write("{")
			outfile.write(result)
			outfile.write("}")
			#json.dump(results, outfile, ensure_ascii=False, sort_keys=False) #encoding="utf8", 

