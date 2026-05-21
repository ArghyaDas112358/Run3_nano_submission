import json
import subprocess
import os
import datetime
import argparse
import sys

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, desc="", unit=""):
        total = len(iterable)
        for i, item in enumerate(iterable):
            sys.stdout.write(f"\r{desc}: {i+1}/{total} {unit}s ")
            sys.stdout.flush()
            yield item
        print()

def parse_args():
    parser = argparse.ArgumentParser(description="Download NanoAOD data via XRootD")
    parser.add_argument("--year", required=True, type=str, choices=["2022", "2022EE", "2023", "2023BPix", "2024"], help="Year of the dataset")
    parser.add_argument("--dataset", required=True, type=str, help="Dataset name (e.g., JetMET, Muon, EGamma)")
    parser.add_argument("--user", default=os.environ.get("CERN_USER"),
                        required=os.environ.get("CERN_USER") is None,
                        type=str, help="Username for EOS path (defaults to $CERN_USER from .env)")
    parser.add_argument("--campaign", required=False, default="NanoAODv15Scouting24", type=str, help="Campaign name")
    return parser.parse_args()

def main():
    args = parse_args()

    # The Purdue XRootD redirector and your logical file name (LFN) base
    redirector = "root://eos.cms.rcac.purdue.edu/"
    base_lfn = f"/store/user/{args.user}/production/Scouting/{args.campaign}/data_{args.year}"
    
    prod_id = datetime.datetime.now().strftime("%y%m%d_%H%M%S")

    json_file = f"datasets/DATA_{args.year}.json"
    if not os.path.exists(json_file):
        print(f"Error: Could not find {json_file}")
        return

    with open(json_file, 'r') as f:
        data = json.load(f)

    dataset_dict = data.get(args.dataset, {})
    if not dataset_dict:
        print(f"Error: No datasets found for '{args.dataset}' in {json_file}")
        return

    print(f"Starting download for {args.dataset} ({args.year}) into:")
    print(f"  {redirector}/{base_lfn}")

    for sample_name, dataset_path in dataset_dict.items():
        dataset_tag = dataset_path.split('/')[2] 
        
        # Build the remote target directory path
        target_lfn = f"{base_lfn}/{sample_name}/{dataset_tag}/{prod_id}"
        
        print(f"\n--- Processing {sample_name} ---")
        
        # Create the remote directory using xrdfs (bypassing the read-only mount)
        subprocess.run(["xrdfs", redirector, "mkdir", "-p", target_lfn])
        
        das_query = f"file dataset={dataset_path}"
        result = subprocess.run(['dasgoclient', '-query', das_query], capture_output=True, text=True)
        files = [f for f in result.stdout.strip().split('\n') if f]
        
        if not files:
            print(f"No files found in DAS for {sample_name}")
            continue
            
        pbar = tqdm(files, unit="file")
        
        for file_path in pbar:
            file_name = file_path.split('/')[-1]
            source_url = f"root://cmsxrootd.fnal.gov/{file_path}"
            dest_url = f"{redirector}/{target_lfn}/{file_name}"
            
            pbar.set_description(f"Copying {file_name[:30]}...") 
            
            subprocess.run(["xrdcp", "-f", "-s", source_url, dest_url])

    print("\nAll downloads complete!")

if __name__ == "__main__":
    main()