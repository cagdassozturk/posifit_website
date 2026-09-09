import pandas as pd
import plotly.graph_objects as go

# Hungary dataset path
CSV_PATH_HUNGARY = "data/hungary/HUN_ParametricStudy_10312025_Ataberk_MLP.csv"

def get_instance_data_hungary(trans, shgc, win_u):
    df = pd.read_csv(CSV_PATH_HUNGARY)
    filtered = df.loc[
        ((df["transmittance"] - trans).abs() < 2) &
        ((df["shgc"] - shgc).abs() < 0.05) &
        ((df["window_u"] - win_u).abs() < 0.2)
    ]
    if filtered.empty:
        return None
    return filtered.iloc[0].to_dict()

def get_better_instance_hungary(trans, shgc, win_u):
    df = pd.read_csv(CSV_PATH_HUNGARY)
    df["total_energy"] = df["total_idealHeating"] + df["total_idealCooling"]
    better = df.sort_values("total_energy").iloc[0]
    return better.to_dict()

def create_comparison_graph_hungary(selected, alternative):
    categories = ['Heating Load', 'Cooling Load', 'CO₂ Emission']
    selected_vals = [
        selected.get('total_idealHeating', 0),
        selected.get('total_idealCooling', 0),
        selected.get('co2', 0)
    ]
    alt_vals = [
        alternative.get('total_idealHeating', 0),
        alternative.get('total_idealCooling', 0),
        alternative.get('co2', 0)
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=categories, y=selected_vals, name="Selected"))
    fig.add_trace(go.Bar(x=categories, y=alt_vals, name="Cheaper Option"))

    fig.update_layout(barmode='group', title="Comparison of Loads and CO₂")
    return fig

def load_all_data_hungary():
    """Load all Hungary data for callbacks"""
    try:
        df = pd.read_csv(CSV_PATH_HUNGARY)
        
        # Insert baseline as first row for Hungary
        baseline_hungary = {
            'Version': 'baseline',
            'window_u': 2.85,
            'shgc': 0.5,
            'roof_u': 0.77,
            'extWall_u': 0.48,
            'transmittance': None,
            'total_idealHeating': 61868.78963,
            'total_idealCooling': 14153.77104
        }
        # Add any other columns with default values
        for col in df.columns:
            if col not in baseline_hungary:
                baseline_hungary[col] = None
        
        baseline_df = pd.DataFrame([baseline_hungary])
        df = pd.concat([baseline_df, df], ignore_index=True)
        
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
        print(f"Warning: {CSV_PATH_HUNGARY} file not found!")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading Hungary data: {e}")
        return pd.DataFrame()
