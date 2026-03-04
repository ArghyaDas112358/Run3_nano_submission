import json
import subprocess
import os
import datetime
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, desc="", total=None, unit=""):
        # Fallback if tqdm isn't installed
        total = total or len(list(iterable))
        for i, item in enumerate(iterable):
            sys.stdout.write(f"\r{desc}: {i+1}/{total} {unit}s ")
            sys.stdout.flush()
            yield item
        print()

def parse_args():
    parser = argparse.ArgumentParser(description="Download Scouting NanoAOD data via XRootD")
    parser.add_argument("--year", required=True, type=str, choices=["2022", "2023", "2024"], help="Year of the dataset")
    parser.add_argument("--user", required=False, default="das214", type=str, help="Username for EOS path")
    parser.add_argument("--campaign", required=False, default="NanoAODv15Scouting24", type=str, help="Campaign name")
    parser.add_argument("--threads", required=False, default=12, type=int, help="Number of parallel downloads")
    return parser.parse_args()

def main():
    args = parse_args()

    redirector = "root://eos.cms.rcac.purdue.edu/"
    base_lfn = f"/store/user/{args.user}/production/Scouting/{args.campaign}/data_{args.year}"
    
    prod_id = datetime.datetime.now().strftime("%y%m%d_%H%M%S")

    json_file = "datasets/Scouting_DATA.json"
    if not os.path.exists(json_file):
        print(f"Error: Could not find {json_file}")
        return

    with open(json_file, 'r') as f:
        data = json.load(f)

    dataset_dict = data.get(args.year, {})
    if not dataset_dict:
        print(f"Error: No datasets found for year '{args.year}' in {json_file}")
        return

    print(f"Starting parallel download for Scouting ({args.year}) using {args.threads} threads into:")
    print(f"  {redirector}/{base_lfn}")

    for sample_name, dataset_path in dataset_dict.items():
        dataset_tag = dataset_path.split('/')[2] 
        target_lfn = f"{base_lfn}/{sample_name}/{dataset_tag}/{prod_id}"
        
        print(f"\n--- Processing {sample_name} ---")
        
        subprocess.run(["xrdfs", redirector, "mkdir", "-p", target_lfn])
        
        das_query = f"file dataset={dataset_path}"
        result = subprocess.run(['dasgoclient', '-query', das_query], capture_output=True, text=True)
        files = [f for f in result.stdout.strip().split('\n') if f]
        
        if not files:
            print(f"No files found in DAS for {sample_name}")
            continue
            
        print(f"Found {len(files)} files. Starting transfer...")

        # The function that each thread will run
        def download_file(file_path):
            file_name = file_path.split('/')[-1]
            source_url = f"root://cmsxrootd.fnal.gov/{file_path}"
            dest_url = f"{redirector}/{target_lfn}/{file_name}"
            
            # capture_output suppresses the xrdcp text so it doesn't break our progress bar
            subprocess.run(["xrdcp", "-f", "-s", source_url, dest_url], capture_output=True)
            return file_name

        # Multithreading magic
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = [executor.submit(download_file, f) for f in files]
            
            # Wrap as_completed in tqdm to get a live updating progress bar
            for future in tqdm(as_completed(futures), total=len(files), desc=f"{sample_name}", unit="file"):
                pass 

    print("\nAll downloads complete!")

if __name__ == "__main__":
    main()