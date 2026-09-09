import pandas as pd
import plotly.graph_objects as go

# Turkiye dataset path
CSV_PATH_TURKIYE = "data/turkiye/TUR_ParametricStudy_10292025.csv"

def get_instance_data_turkiye(trans, shgc, win_u):
    df = pd.read_csv(CSV_PATH_TURKIYE)
    filtered = df.loc[
        ((df["transmittance"] - trans).abs() < 2) &
        ((df["window_shgc"] - shgc).abs() < 0.05) &
        ((df["window_u"] - win_u).abs() < 0.2)
    ]
    if filtered.empty:
        return None
    return filtered.iloc[0].to_dict()

def get_better_instance_turkiye(trans, shgc, win_u):
    df = pd.read_csv(CSV_PATH_TURKIYE)
    df["total_energy"] = df["heating_load"] + df["cooling_load"]
    better = df.sort_values("total_energy").iloc[0]
    return better.to_dict()

def create_comparison_graph_turkiye(selected, alternative):
    categories = ['Heating Load', 'Cooling Load', 'CO₂ Emission']
    selected_vals = [
        selected.get('heating_load', 0),
        selected.get('cooling_load', 0),
        selected.get('co2', 0)
    ]
    alt_vals = [
        alternative.get('heating_load', 0),
        alternative.get('cooling_load', 0),
        alternative.get('co2', 0)
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=categories, y=selected_vals, name="Selected"))
    fig.add_trace(go.Bar(x=categories, y=alt_vals, name="Cheaper Option"))

    fig.update_layout(barmode='group', title="Comparison of Loads and CO₂")
    return fig

def load_all_data_turkiye():
    """Load all Turkiye data for callbacks"""
    try:
        df = pd.read_csv(CSV_PATH_TURKIYE)
        
        # Apply column mapping to match expected format
        column_mapping = {
            'extWall_u': 'wall_u',
            'shgc': 'window_shgc',
            'total_idealHeating': 'heating_load',
            'total_idealCooling': 'cooling_load'
        }
        df = df.rename(columns=column_mapping)
        
        # Add co2 column if it doesn't exist
        if 'co2' not in df.columns:
            df['co2'] = 0
        
        return df
    except FileNotFoundError:
        print(f"Warning: {CSV_PATH_TURKIYE} file not found!")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading Turkiye data: {e}")
        return pd.DataFrame()

