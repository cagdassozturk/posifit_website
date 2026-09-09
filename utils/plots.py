import pandas as pd
import plotly.graph_objects as go

# Updated to use the new dataset
CSV_PATH = "data/LUX_2026_V6_Training.csv"

def get_instance_data(trans, shgc, win_u):
    df = pd.read_csv(CSV_PATH)
    filtered = df.loc[
        ((df["transmittance"] - trans).abs() < 2) &
        ((df["window_shgc"] - shgc).abs() < 0.05) &
        ((df["window_u"] - win_u).abs() < 0.2)
    ]
    if filtered.empty:
        return None
    return filtered.iloc[0].to_dict()

def get_better_instance(trans, shgc, win_u):
    df = pd.read_csv(CSV_PATH)
    df["total_energy"] = df["heating_load"] + df["cooling_load"]
    # daha düşük enerji kullanan ilk çözümü al
    better = df.sort_values("total_energy").iloc[0]
    return better.to_dict()

def create_comparison_graph(selected, alternative):
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

def load_all_data():
    """
    Tüm veriyi yükleyen fonksiyon - comparison_callbacks.py'de kullanılmak üzere
    """
    try:
        df = pd.read_csv(CSV_PATH)
        return df
    except FileNotFoundError:
        print(f"Warning: {CSV_PATH} dosyası bulunamadı!")
        # Alternatif dosya yolları deneyebilirsiniz
        try:
            df = pd.read_csv("lux_sim14000_ResAll_buildingTotal_shuffled.csv")
            return df
        except FileNotFoundError:
            print("Veri dosyası bulunamadı!")
            return pd.DataFrame()  # Boş DataFrame döndür
    except Exception as e:
        print(f"Veri yüklenirken hata oluştu: {e}")
        return pd.DataFrame()
