"""
One-Click Run Script for Event Analytics Dashboard
Extracts data from Excel files, runs AI analysis, and opens the dashboard
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path


def main():
    print("=" * 60)
    print("EVENT ANALYTICS DASHBOARD - One-Click Setup")
    print("=" * 60)
    
    # Get the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print(f"\nWorking directory: {project_dir}")
    
    # Step 1: Extract events from Excel files
    print("\n[Step 1/3] Extracting event data from Excel files...")
    extract_script = project_dir / "src" / "extract_events.py"
    
    if extract_script.exists():
        result = subprocess.run([sys.executable, str(extract_script)], capture_output=True, text=True)
        if result.returncode == 0:
            print("Event data extracted successfully!")
            print(result.stdout)
        else:
            print("Warning: Event extraction may have issues:")
            print(result.stderr)
    else:
        print("Warning: extract_events.py not found, skipping extraction")
    
    # Step 2: Run the AI analyzer
    print("\n[Step 2/3] Running AI analysis...")
    analyzer_script = project_dir / "src" / "analyzer.py"
    
    if analyzer_script.exists():
        result = subprocess.run([sys.executable, str(analyzer_script)], capture_output=True, text=True)
        if result.returncode == 0:
            print("AI analysis completed!")
            # Print just a summary, not the full output
            lines = result.stdout.split('\n')
            for line in lines[:20]:  # First 20 lines
                print(line)
            if len(lines) > 20:
                print("... (truncated)")
        else:
            print("Error during analysis:")
            print(result.stderr)
            return
    else:
        print("Error: analyzer.py not found!")
        return
    
    # Step 3: Open the dashboard
    print("\n[Step 3/3] Opening dashboard...")
    dashboard_path = project_dir / "dashboard" / "index.html"
    
    if dashboard_path.exists():
        # Convert to file:// URL
        url = dashboard_path.as_uri()
        print(f"Opening: {url}")
        webbrowser.open(url)
        print("\nDashboard opened in your default browser!")
    else:
        print(f"Dashboard not found at {dashboard_path}")
    
    print("\n" + "=" * 60)
    print("Setup complete! The dashboard should be open in your browser.")
    print("If the browser didn't open, manually open:")
    print(f"  {dashboard_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
