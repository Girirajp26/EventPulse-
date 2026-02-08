"""
Event Analyzer - AI-Powered Event Insights Generator
Uses OpenAI API to analyze event data and generate actionable insights for any organization
Enhanced with budget analysis, ROI metrics, and demographic insights
"""

import os
import json
import pandas as pd
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class EventAnalyzer:
    def __init__(self, org_name="Your Organization"):
        """Initialize the analyzer with OpenAI API"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file!")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.org_name = org_name
        
    def load_event_data(self, filepath='data/compiled_events.xlsx'):
        """Load event data from Excel file"""
        try:
            df = pd.read_excel(filepath, sheet_name='Events')
            print(f"Loaded {len(df)} events from {filepath}")
            
            # Try to load demographics
            try:
                demo_df = pd.read_excel(filepath, sheet_name='Demographics')
                self.demographics = demo_df.iloc[0].to_dict() if len(demo_df) > 0 else None
                print("Demographics data loaded")
            except:
                self.demographics = None
            
            return df
        except FileNotFoundError:
            print(f"Error: File not found at {filepath}")
            print("Run 'python src/extract_events.py' first to compile event data")
            return None
        except Exception as e:
            # Try loading without sheet name for backwards compatibility
            try:
                df = pd.read_excel(filepath)
                self.demographics = None
                return df
            except:
                print(f"Error loading file: {e}")
                return None
    
    def convert_to_serializable(self, obj):
        """Convert numpy/pandas types to Python native types for JSON serialization"""
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, dict):
            return {key: self.convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_serializable(item) for item in obj]
        elif pd.isna(obj):
            return None
        return obj
    
    def prepare_data_summary(self, df):
        """Prepare a comprehensive summary of the event data for AI analysis"""
        
        # Basic metrics
        summary = {
            "total_events": int(len(df)),
            "date_range": f"{df['Date'].min().strftime('%b %Y')} to {df['Date'].max().strftime('%b %Y')}",
            "event_types": {k: int(v) for k, v in df['Event Type'].value_counts().to_dict().items()},
            "avg_attendance": float(round(df['Actual Attendance'].mean(), 1)),
            "total_attendees": int(df['Actual Attendance'].sum()),
            "total_registered": int(df['Expected Attendance'].sum()),
            "attendance_rate": float(round(df['Actual Attendance'].sum() / df['Expected Attendance'].sum() * 100, 1)),
        }
        
        # Financial metrics (if available)
        if 'Total Budget' in df.columns and df['Total Budget'].notna().any():
            total_budget = df['Total Budget'].sum()
            summary["total_budget"] = float(round(total_budget, 2))
            summary["avg_budget_per_event"] = float(round(total_budget / len(df), 2))
            summary["cost_per_attendee"] = float(round(total_budget / df['Actual Attendance'].sum(), 2))
            
            # Calculate ROI indicators
            events_with_budget = df[df['Total Budget'].notna()]
            if len(events_with_budget) > 0:
                summary["avg_cost_per_attendee"] = float(round(
                    events_with_budget['Total Budget'].sum() / events_with_budget['Actual Attendance'].sum(), 2
                ))
        
        # Performance metrics
        summary["best_performing_event"] = df.loc[df['Actual Attendance'].idxmax(), 'Event Name']
        summary["highest_attendance"] = int(df['Actual Attendance'].max())
        
        # Calculate attendance rate for each event and find best
        df['Attendance Rate'] = df['Actual Attendance'] / df['Expected Attendance'] * 100
        best_rate_idx = df['Attendance Rate'].idxmax()
        summary["best_conversion_event"] = df.loc[best_rate_idx, 'Event Name']
        summary["best_conversion_rate"] = float(round(df.loc[best_rate_idx, 'Attendance Rate'], 1))
        
        # Add event-by-event details
        events_detail = []
        for _, row in df.iterrows():
            event = {
                "name": str(row['Event Name']),
                "type": str(row['Event Type']),
                "date": str(row['Date'].strftime('%Y-%m-%d') if hasattr(row['Date'], 'strftime') else row['Date']),
                "expected": int(row['Expected Attendance']),
                "actual": int(row['Actual Attendance']),
                "attendance_rate": float(round((row['Actual Attendance'] / row['Expected Attendance'] * 100), 1))
            }
            
            if 'Total Budget' in df.columns and pd.notna(row.get('Total Budget')):
                event["budget"] = float(round(row['Total Budget'], 2))
                event["cost_per_attendee"] = float(round(row['Total Budget'] / row['Actual Attendance'], 2))
            
            events_detail.append(event)
        
        summary['events'] = events_detail
        
        # Add demographics if available
        if self.demographics:
            summary['demographics'] = {k: int(v) for k, v in self.demographics.items() if v > 0}
        
        # Calculate Engagement Score (0-100)
        engagement_score = self.calculate_engagement_score(df, summary)
        summary['engagement_score'] = engagement_score
        
        return summary
    
    def calculate_engagement_score(self, df, summary):
        """
        Calculate an overall engagement score (0-100) based on multiple factors:
        - Attendance rate (40% weight)
        - Consistency (20% weight) - standard deviation of attendance rates
        - Growth trend (20% weight) - are numbers improving over time?
        - Efficiency (20% weight) - cost per attendee if budget data available
        """
        score = 0
        breakdown = {}
        
        # 1. Attendance Rate Score (40 points max)
        # 85%+ = 40pts, 75% = 30pts, 65% = 20pts, below = proportional
        att_rate = summary['attendance_rate']
        if att_rate >= 85:
            att_score = 40
        elif att_rate >= 75:
            att_score = 30 + (att_rate - 75) * 1
        elif att_rate >= 65:
            att_score = 20 + (att_rate - 65) * 1
        else:
            att_score = max(0, att_rate * 0.3)
        breakdown['attendance'] = round(att_score, 1)
        score += att_score
        
        # 2. Consistency Score (20 points max)
        # Lower standard deviation = more consistent = better
        rates = [e['attendance_rate'] for e in summary['events']]
        if len(rates) > 1:
            std_dev = np.std(rates)
            # std_dev of 0 = perfect (20pts), std_dev of 20+ = poor (0pts)
            consistency_score = max(0, 20 - std_dev)
            breakdown['consistency'] = round(consistency_score, 1)
            score += consistency_score
        else:
            breakdown['consistency'] = 15  # Default for single event
            score += 15
        
        # 3. Growth Trend Score (20 points max)
        # Compare first half vs second half of events
        sorted_events = sorted(summary['events'], key=lambda x: x['date'])
        if len(sorted_events) >= 2:
            mid = len(sorted_events) // 2
            first_half_avg = np.mean([e['actual'] for e in sorted_events[:mid]])
            second_half_avg = np.mean([e['actual'] for e in sorted_events[mid:]])
            
            if second_half_avg >= first_half_avg:
                growth_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100 if first_half_avg > 0 else 0
                growth_score = min(20, 10 + growth_pct * 0.5)
            else:
                decline_pct = ((first_half_avg - second_half_avg) / first_half_avg) * 100
                growth_score = max(0, 10 - decline_pct * 0.5)
            breakdown['growth'] = round(growth_score, 1)
            score += growth_score
        else:
            breakdown['growth'] = 10
            score += 10
        
        # 4. Efficiency Score (20 points max) - if budget data available
        if 'cost_per_attendee' in summary and summary['cost_per_attendee'] > 0:
            # Lower cost = better. Assume $10/person is excellent, $5 is average, $2 or less is great
            cpa = summary['cost_per_attendee']
            if cpa <= 3:
                eff_score = 20
            elif cpa <= 5:
                eff_score = 18
            elif cpa <= 10:
                eff_score = 15
            elif cpa <= 20:
                eff_score = 10
            else:
                eff_score = max(0, 20 - cpa * 0.3)
            breakdown['efficiency'] = round(eff_score, 1)
            score += eff_score
        else:
            # No budget data, give average score
            breakdown['efficiency'] = 12
            score += 12
        
        # Determine grade
        if score >= 90:
            grade = 'A+'
        elif score >= 85:
            grade = 'A'
        elif score >= 80:
            grade = 'A-'
        elif score >= 75:
            grade = 'B+'
        elif score >= 70:
            grade = 'B'
        elif score >= 65:
            grade = 'B-'
        elif score >= 60:
            grade = 'C+'
        elif score >= 55:
            grade = 'C'
        elif score >= 50:
            grade = 'C-'
        else:
            grade = 'D'
        
        return {
            'score': round(score, 1),
            'grade': grade,
            'breakdown': breakdown
        }
    
    def analyze_with_ai(self, data_summary):
        """Use OpenAI to analyze the event data"""
        print("\nAnalyzing data with OpenAI...")
        
        # Convert summary to JSON-serializable format
        serializable_summary = self.convert_to_serializable(data_summary)
        
        # Build dynamic prompt based on available data
        budget_section = ""
        if "total_budget" in data_summary:
            budget_section = """
6. **Financial Analysis** (Budget efficiency, cost per attendee trends, ROI recommendations)"""
        
        demographics_section = ""
        if "demographics" in data_summary:
            demographics_section = """
7. **Audience Insights** (Demographics breakdown and targeting recommendations)"""
        
        prompt = f"""You are an expert data analyst and strategic advisor helping "{self.org_name}" 
optimize their event performance. Analyze the following comprehensive event data and provide executive-level insights.

EVENT DATA SUMMARY:
{json.dumps(serializable_summary, indent=2)}

Provide a professional analysis with these sections:

1. **Executive Summary** (2-3 sentences highlighting the most important findings)

2. **Key Performance Indicators**
   - Overall attendance performance
   - Best and worst performing events
   - Trend analysis

3. **Event Type Analysis** (Which types of events perform best and why?)

4. **Attendance Patterns & Trends** (Seasonal patterns, growth trends, conversion rates)

5. **Predictions for Future Events** (Data-driven attendance forecasts for each event type){budget_section}{demographics_section}

8. **Strategic Recommendations** (5 specific, actionable recommendations prioritized by impact)

Format your response professionally for board presentation. Use clear headings and bullet points."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            insights = response.choices[0].message.content
            print("AI Analysis complete!")
            return insights
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
    
    def generate_predictions(self, df):
        """Generate attendance predictions for each event type"""
        predictions = {}
        
        for event_type in df['Event Type'].unique():
            type_data = df[df['Event Type'] == event_type]
            avg_attendance = type_data['Actual Attendance'].mean()
            avg_rate = (type_data['Actual Attendance'].sum() / type_data['Expected Attendance'].sum() * 100)
            
            pred = {
                "avg_attendance": float(round(avg_attendance, 0)),
                "attendance_rate": float(round(avg_rate, 1)),
                "sample_size": int(len(type_data)),
                "min_attendance": int(type_data['Actual Attendance'].min()),
                "max_attendance": int(type_data['Actual Attendance'].max())
            }
            
            # Add budget metrics if available
            if 'Total Budget' in df.columns and type_data['Total Budget'].notna().any():
                budget_data = type_data[type_data['Total Budget'].notna()]
                if len(budget_data) > 0:
                    pred["avg_budget"] = float(round(budget_data['Total Budget'].mean(), 2))
                    pred["avg_cost_per_attendee"] = float(round(
                        budget_data['Total Budget'].sum() / budget_data['Actual Attendance'].sum(), 2
                    ))
            
            predictions[event_type] = pred
        
        return predictions
    
    def save_results(self, insights, predictions, data_summary):
        """Save analysis results to JSON file for the dashboard"""
        # Convert everything to serializable format
        results = {
            "timestamp": datetime.now().isoformat(),
            "org_name": self.org_name,
            "data_summary": self.convert_to_serializable(data_summary),
            "ai_insights": insights,
            "predictions": self.convert_to_serializable(predictions)
        }
        
        # Add demographics if available
        if self.demographics:
            results["demographics"] = self.convert_to_serializable(self.demographics)
        
        # Calculate and add engagement score
        engagement_score = self.calculate_engagement_score(data_summary)
        if engagement_score:
            results["engagement_score"] = engagement_score
            print(f"\nEngagement Score: {engagement_score['score']:.1f} ({engagement_score['grade']})")
        
        # Create output directory if it doesn't exist
        os.makedirs('dashboard/data', exist_ok=True)
        
        output_path = 'dashboard/data/analysis_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {output_path}")
        return output_path
    
    def run_analysis(self, filepath='data/compiled_events.xlsx'):
        """Run the complete analysis pipeline"""
        print("=" * 60)
        print(f"EVENT ANALYZER - AI-Powered Insights")
        print(f"Organization: {self.org_name}")
        print("=" * 60)
        
        # Load data
        df = self.load_event_data(filepath)
        if df is None:
            return
        
        # Prepare summary
        print("\nPreparing data summary...")
        data_summary = self.prepare_data_summary(df)
        
        # Display quick stats
        print(f"\n--- Quick Stats ---")
        print(f"Total Events: {data_summary['total_events']}")
        print(f"Total Attendees: {data_summary['total_attendees']:,}")
        print(f"Average Attendance: {data_summary['avg_attendance']:.0f}")
        print(f"Overall Attendance Rate: {data_summary['attendance_rate']:.1f}%")
        if 'total_budget' in data_summary:
            print(f"Total Budget: ${data_summary['total_budget']:,.2f}")
            print(f"Cost per Attendee: ${data_summary['cost_per_attendee']:.2f}")
        
        # Generate predictions
        print("\nGenerating predictions...")
        predictions = self.generate_predictions(df)
        
        # AI Analysis
        insights = self.analyze_with_ai(data_summary)
        if insights is None:
            return
        
        # Display insights
        print("\n" + "=" * 60)
        print("AI-GENERATED INSIGHTS")
        print("=" * 60)
        print(insights)
        print("=" * 60)
        
        # Save results
        output_path = self.save_results(insights, predictions, data_summary)
        
        print("\nAnalysis complete!")
        print(f"Results saved to: {output_path}")
        print("Open dashboard/index.html in your browser to view the dashboard!")


def main():
    """Main function to run the analyzer"""
    try:
        # Set your organization name here
        org_name = "Society of Indian Americans"
        
        analyzer = EventAnalyzer(org_name=org_name)
        analyzer.run_analysis()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have a .env file with your OPENAI_API_KEY")
        print("2. Run 'pip install -r requirements.txt' to install dependencies")
        print("3. Run 'python src/extract_events.py' first to compile event data")


if __name__ == "__main__":
    main()
