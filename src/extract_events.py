"""
Event Data Extractor
Extracts event data from SIA Event Management Excel files and compiles them for analysis
Includes budget, attendance demographics, and performance metrics
"""

import pandas as pd
import os
from datetime import datetime

def extract_budget_data(filepath):
    """Extract budget information from workbook"""
    try:
        budget = pd.read_excel(filepath, sheet_name='Budget', header=None)
        
        total_cost = None
        
        # Look for Overall Total or Total Cost
        for i in range(len(budget)):
            for j in range(len(budget.columns)):
                cell = str(budget.iloc[i, j]) if pd.notna(budget.iloc[i, j]) else ''
                
                if 'Overall Total' in cell or 'TOTAL' in cell.upper():
                    # Look for number in same row or next columns
                    for k in range(j+1, min(j+5, len(budget.columns))):
                        val = budget.iloc[i, k]
                        if pd.notna(val) and isinstance(val, (int, float)) and val > 100:
                            total_cost = float(val)
                            break
                    if total_cost:
                        break
            if total_cost:
                break
        
        return total_cost
        
    except Exception as e:
        return None


def extract_demographics(filepath):
    """Extract attendee demographics from Attendee Data sheet"""
    try:
        attendees = pd.read_excel(filepath, sheet_name='Attendee Data', header=None)
        
        demographics = {
            'Freshman': 0,
            'Sophomore': 0,
            'Junior': 0,
            'Senior': 0,
            'Graduate': 0,
            'Alumni': 0,
            'Other': 0
        }
        
        for i in range(len(attendees)):
            for j in range(len(attendees.columns)):
                val = str(attendees.iloc[i, j]).lower() if pd.notna(attendees.iloc[i, j]) else ''
                
                if 'freshman' in val:
                    demographics['Freshman'] += 1
                elif 'sophmore' in val or 'sophomore' in val:
                    demographics['Sophomore'] += 1
                elif 'junior' in val:
                    demographics['Junior'] += 1
                elif 'senior' in val:
                    demographics['Senior'] += 1
                elif 'graduate' in val or 'grad' in val or 'masters' in val or 'phd' in val:
                    demographics['Graduate'] += 1
                elif 'alumni' in val:
                    demographics['Alumni'] += 1
        
        # Only return if we found meaningful data
        total = sum(demographics.values())
        if total > 5:
            return demographics
        return None
        
    except Exception as e:
        return None


def extract_event_from_workbook(filepath):
    """Extract event info from an event management workbook"""
    try:
        # Get event name and date from Overview sheet
        overview = pd.read_excel(filepath, sheet_name='Overview', header=None)
        
        event_name = None
        event_date = None
        
        # Find event name (usually row 1, col 1)
        for i in range(min(5, len(overview))):
            for j in range(min(3, len(overview.columns))):
                val = overview.iloc[i, j]
                if pd.notna(val) and isinstance(val, str) and len(val) > 3:
                    if event_name is None and 'Event' not in str(val) and 'NaN' not in str(val):
                        event_name = val
                        break
            if event_name:
                break
        
        # Find event date
        for i in range(len(overview)):
            for j in range(len(overview.columns)):
                val = overview.iloc[i, j]
                if pd.notna(val):
                    if isinstance(val, datetime):
                        event_date = val
                        break
                    elif 'Event Date' in str(overview.iloc[i, j-1] if j > 0 else ''):
                        event_date = val
                        break
            if event_date:
                break
        
        # Get attendance from RSVP Snapshot
        registered = None
        attended = None
        
        try:
            rsvp = pd.read_excel(filepath, sheet_name='RSVP Snapshot', header=None)
            
            # Look for TOTAL RSVPs and attendance
            for i in range(len(rsvp)):
                for j in range(len(rsvp.columns)):
                    cell = str(rsvp.iloc[i, j]) if pd.notna(rsvp.iloc[i, j]) else ''
                    
                    if 'TOTAL' in cell.upper() and 'RSVP' in cell.upper():
                        if j + 1 < len(rsvp.columns) and pd.notna(rsvp.iloc[i, j+1]):
                            registered = int(rsvp.iloc[i, j+1])
                        if j + 2 < len(rsvp.columns) and pd.notna(rsvp.iloc[i, j+2]):
                            attended = int(rsvp.iloc[i, j+2])
                    
                    if 'Raw Tickets' in cell:
                        if j + 1 < len(rsvp.columns) and pd.notna(rsvp.iloc[i, j+1]):
                            registered = int(rsvp.iloc[i, j+1])
                        if j + 2 < len(rsvp.columns) and pd.notna(rsvp.iloc[i, j+2]):
                            attended = int(rsvp.iloc[i, j+2])
                            
        except Exception as e:
            print(f"  Could not read RSVP Snapshot: {e}")
        
        # Get budget data
        budget = extract_budget_data(filepath)
        
        # Get demographics
        demographics = extract_demographics(filepath)
        
        return {
            'Event Name': event_name,
            'Date': event_date,
            'Expected Attendance': registered,
            'Actual Attendance': attended,
            'Total Budget': budget,
            'Demographics': demographics
        }
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None


def determine_event_type(event_name):
    """Determine event type based on event name"""
    if event_name is None:
        return "Other"
    
    name_lower = event_name.lower()
    
    if any(x in name_lower for x in ['garba', 'diwali', 'holi', 'navratri']):
        return "Cultural Festival"
    elif any(x in name_lower for x in ['bollywood', 'blackout', 'mehndi', 'sangeet']):
        return "Cultural Show"
    elif any(x in name_lower for x in ['formal', 'dinner', 'banquet', 'gala']):
        return "Formal"
    elif any(x in name_lower for x in ['sima', 'matchmaking', 'dating']):
        return "Social"
    elif any(x in name_lower for x in ['workshop', 'career', 'professional', 'networking']):
        return "Professional"
    elif any(x in name_lower for x in ['sports', 'cricket', 'volleyball', 'tournament']):
        return "Sports"
    elif any(x in name_lower for x in ['welcome', 'freshers', 'orientation']):
        return "Welcome"
    else:
        return "Cultural"


def extract_all_events(data_folder='data'):
    """Extract events from all Excel files in the data folder"""
    events = []
    all_demographics = {}
    
    for filename in os.listdir(data_folder):
        if filename.endswith('.xlsx') and 'Event Management' in filename:
            filepath = os.path.join(data_folder, filename)
            print(f"Processing: {filename}")
            
            event_data = extract_event_from_workbook(filepath)
            
            if event_data and event_data['Event Name']:
                event_data['Event Type'] = determine_event_type(event_data['Event Name'])
                
                # Aggregate demographics
                if event_data['Demographics']:
                    for key, val in event_data['Demographics'].items():
                        all_demographics[key] = all_demographics.get(key, 0) + val
                
                events.append(event_data)
                print(f"  Event: {event_data['Event Name']}")
                print(f"    Date: {event_data['Date']}")
                print(f"    Expected: {event_data['Expected Attendance']}, Actual: {event_data['Actual Attendance']}")
                if event_data['Total Budget']:
                    print(f"    Budget: ${event_data['Total Budget']:,.2f}")
            else:
                print(f"  Could not extract event data")
    
    return events, all_demographics


def save_compiled_data(events, demographics, output_path='data/compiled_events.xlsx'):
    """Save compiled events to Excel"""
    if not events:
        print("No events to save!")
        return None
    
    # Create main events dataframe
    df_data = []
    for e in events:
        df_data.append({
            'Event Name': e['Event Name'],
            'Date': e['Date'],
            'Event Type': e['Event Type'],
            'Expected Attendance': e['Expected Attendance'],
            'Actual Attendance': e['Actual Attendance'],
            'Total Budget': e.get('Total Budget')
        })
    
    df = pd.DataFrame(df_data)
    df = df.sort_values('Date')
    
    # Save with multiple sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Events', index=False)
        
        if demographics:
            demo_df = pd.DataFrame([demographics])
            demo_df.to_excel(writer, sheet_name='Demographics', index=False)
    
    print(f"\nCompiled data saved to: {output_path}")
    print(f"Total events: {len(df)}")
    print("\nEvents Summary:")
    print(df[['Event Name', 'Date', 'Event Type', 'Actual Attendance', 'Total Budget']].to_string())
    
    if demographics:
        print("\nAggregate Demographics:")
        for k, v in demographics.items():
            if v > 0:
                print(f"  {k}: {v}")
    
    return output_path


def main():
    print("=" * 60)
    print("EVENT DATA EXTRACTOR - Enhanced")
    print("=" * 60)
    
    events, demographics = extract_all_events()
    
    if events:
        save_compiled_data(events, demographics)
        print("\nNext step: Run 'python src/analyzer.py' to analyze this data!")
    else:
        print("\nNo events found. Make sure your Event Management Excel files are in the data/ folder.")


if __name__ == "__main__":
    main()
