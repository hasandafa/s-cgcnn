#!/usr/bin/env python
"""
s-CGCNN Version 0.1 - Complete Pipeline Runner
Runs data acquisition and structure interpolation end-to-end
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add to path
sys.path.append(str(Path(__file__).parent))

from src.data_acquisition.mp_fetcher import MPFetcher
from src.data_acquisition.structure_interpolator import StructureInterpolator
from src.utils.logger_config import setup_logger


def print_banner():
    """Print s-CGCNN banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                          s-CGCNN v0.1                             ║
    ║     Simplified Graph Neural Networks for AlGaAs Screening         ║
    ║                                                                   ║
    ║     Data Acquisition & Structure Interpolation Pipeline          ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"    Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("    " + "="*67 + "\n")


def check_prerequisites():
    """Check if all prerequisites are met."""
    logger = setup_logger("prerequisites_check")
    
    logger.info("Checking prerequisites...")
    
    # Check API key
    api_key_file = Path("config/mp_api_key.txt")
    if not api_key_file.exists():
        logger.error("✗ API key file not found!")
        print("\n❌ ERROR: Materials Project API key not found!")
        print("   Please create: config/mp_api_key.txt")
        print("   Get your key from: https://next-gen.materialsproject.org/api\n")
        return False, None
    
    with open(api_key_file, 'r') as f:
        api_key = f.read().strip()
    
    if not api_key or len(api_key) < 10:
        logger.error("✗ Invalid API key!")
        print("\n❌ ERROR: API key appears invalid!")
        print("   Check your config/mp_api_key.txt file\n")
        return False, None
    
    logger.info("✓ API key found")
    
    # Check directories
    for dir_path in ["data", "data/raw", "data/structures", "logs"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    logger.info("✓ Directory structure verified")
    
    return True, api_key


def step_1_fetch_mp_data(api_key: str) -> bool:
    """Step 1: Fetch data from Materials Project."""
    print("\n" + "="*70)
    print("STEP 1: Fetching Data from Materials Project")
    print("="*70)
    
    logger = setup_logger("step1_fetch", log_file="logs/v0.1_pipeline_step1.log")
    
    try:
        fetcher = MPFetcher(api_key, output_dir="data/raw")

        # Check if data already exists
        gaas_data = fetcher.load_saved_data("GaAs")
        alas_data = fetcher.load_saved_data("AlAs")
        
        if gaas_data and alas_data:
            print("\n✓ MP data already exists, skipping fetch")
            print(f"  • GaAs: {gaas_data['structure'].composition}")
            print(f"  • AlAs: {alas_data['structure'].composition}")
            logger.info("Using existing MP data")
            return True
        
        print("\n→ Fetching from Materials Project API...")
        print("  This may take 1-2 minutes...\n")
        
        start_time = time.time()
        all_data = fetcher.fetch_all_materials()
        elapsed = time.time() - start_time
        
        if len(all_data) == 2:
            print(f"\n✅ Step 1 Complete ({elapsed:.1f}s)")
            print(f"  • Fetched {len(all_data)} materials")
            logger.info(f"Step 1 completed in {elapsed:.1f}s")
            return True
        else:
            print("\n❌ Step 1 Failed - Incomplete data fetch")
            logger.error("Step 1 failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Step 1 Failed: {e}")
        logger.error(f"Step 1 failed: {e}")
        return False


def step_2_generate_structures() -> bool:
    """Step 2: Generate interpolated structures."""
    print("\n" + "="*70)
    print("STEP 2: Generating AlₓGa₁₋ₓAs Structures")
    print("="*70)
    
    logger = setup_logger("step2_interpolate", log_file="logs/v0.1_pipeline_step2.log")
    
    try:
        # Load MP data
        fetcher = MPFetcher("", output_dir="data/raw")
        gaas_data = fetcher.load_saved_data("GaAs")
        alas_data = fetcher.load_saved_data("AlAs")
        
        if not gaas_data or not alas_data:
            print("\n❌ MP data not found. Run Step 1 first!")
            logger.error("MP data not available")
            return False
        
        print("\n→ Initializing structure interpolator...")
        interpolator = StructureInterpolator(
            gaas_structure=gaas_data["structure"],
            alas_structure=alas_data["structure"],
            supercell_size=[2, 2, 2],
            output_dir="data/structures"
        )
        
        print("→ Generating 41 compositions (x = 0.0 to 1.0, step 0.025)...")
        print("  This may take 1-2 minutes...\n")
        
        start_time = time.time()
        results = interpolator.generate_all_structures(
            x_start=0.0,
            x_end=1.0,
            x_step=0.025
        )
        elapsed = time.time() - start_time
        
        if len(results) == 41:
            print(f"\n✅ Step 2 Complete ({elapsed:.1f}s)")
            print(f"  • Generated {len(results)} structures")
            print(f"  • CIF files: data/structures/cif/")
            print(f"  • Metadata: data/structures/metadata/")
            logger.info(f"Step 2 completed in {elapsed:.1f}s")
            return True
        else:
            print(f"\n⚠️ Step 2 Incomplete: {len(results)}/41 structures")
            logger.warning(f"Only {len(results)}/41 structures generated")
            return False
            
    except Exception as e:
        print(f"\n❌ Step 2 Failed: {e}")
        logger.error(f"Step 2 failed: {e}")
        return False


def step_3_summary():
    """Display final summary."""
    print("\n" + "="*70)
    print("PIPELINE SUMMARY")
    print("="*70)
    
    # Check outputs
    cif_dir = Path("data/structures/cif")
    metadata_dir = Path("data/structures/metadata")
    
    cif_files = list(cif_dir.glob("*.cif")) if cif_dir.exists() else []
    json_files = list(metadata_dir.glob("AlGaAs*.json")) if metadata_dir.exists() else []
    
    print(f"\n📊 Output Files:")
    print(f"  • CIF files: {len(cif_files)}/41")
    print(f"  • Metadata files: {len(json_files)}/41")
    
    if len(cif_files) == 41 and len(json_files) == 41:
        print(f"\n✅ All outputs generated successfully!")
    else:
        print(f"\n⚠️ Some outputs missing")
    
    print(f"\n📁 Data Structure:")
    print(f"  data/")
    print(f"  ├── raw/")
    print(f"  │   ├── mp_2534_GaAs.json")
    print(f"  │   └── mp_2172_AlAs.json")
    print(f"  └── structures/")
    print(f"      ├── cif/ ({len(cif_files)} files)")
    print(f"      └── metadata/ ({len(json_files)} files)")
    
    print(f"\n📋 Logs:")
    print(f"  • Pipeline logs: logs/v0.1_pipeline_step*.log")
    print(f"  • Detailed logs: logs/v0.1_*.log")
    
    print("\n" + "="*70)


def main():
    """Main pipeline execution."""
    print_banner()
    
    # Track overall timing
    pipeline_start = time.time()
    
    # Check prerequisites
    prereq_ok, api_key = check_prerequisites()
    if not prereq_ok:
        print("\n❌ Pipeline aborted due to missing prerequisites\n")
        sys.exit(1)
    
    print("✓ Prerequisites verified\n")
    
    # Step 1: Fetch MP data
    step1_ok = step_1_fetch_mp_data(api_key)
    if not step1_ok:
        print("\n❌ Pipeline aborted at Step 1\n")
        sys.exit(1)
    
    # Step 2: Generate structures
    step2_ok = step_2_generate_structures()
    if not step2_ok:
        print("\n⚠️ Pipeline completed with warnings\n")
    
    # Summary
    step_3_summary()
    
    # Final timing
    pipeline_elapsed = time.time() - pipeline_start
    
    print("\n" + "="*70)
    if step1_ok and step2_ok:
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print(f"   Total time: {pipeline_elapsed:.1f}s (~{pipeline_elapsed/60:.1f} min)")
        print("\n💡 Next Steps:")
        print("   1. Run tests: python '1. Data Acquisition and Structure Interpolation Testing.py'")
        print("   2. Explore data: check data/structures/")
        print("   3. Move to Version 0.2: Visualization")
    else:
        print("⚠️ PIPELINE COMPLETED WITH ISSUES")
        print(f"   Check logs for details: logs/v0.1_pipeline_*.log")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}\n")
        sys.exit(1)