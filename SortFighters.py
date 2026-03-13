import pandas as pd
import numpy as np

def clean_fighters_biometrics(input_csv='ufc_fighters_profiles.csv', output_csv='ufc_fighters_final.csv'):
    print(f"A carregar {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # 1. Substituir os '--' por NaN (Not a Number)
    df = df.replace('--', np.nan)
    
    # 2. Converter Data de Nascimento (DOB) para formato Datetime
    df['DOB'] = pd.to_datetime(df['DOB'], format='%b %d, %Y', errors='coerce')
    
    # 3. Guardar o ficheiro final
    df.to_csv(output_csv, index=False)
    
    print(f"\nLimpeza concluída! Ficheiro guardado como: '{output_csv}'")
    print("\nConfirma a ordem das primeiras colunas:")
    print(list(df.columns)[:8])

if __name__ == "__main__":
    clean_fighters_biometrics()