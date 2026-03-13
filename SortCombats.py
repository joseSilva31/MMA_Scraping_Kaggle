import pandas as pd

def sort_ufc_dataset(input_csv='ufc_gold_dataset.csv', output_csv='ufc_gold_dataset_final.csv'):
    print(f"A carregar o ficheiro {input_csv}...")
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Erro: O ficheiro {input_csv} não foi encontrado.")
        return

    # 1. Converter a coluna de texto para formato de Data (Datetime)
    # O formato do site é "March 07, 2026"
    print("A converter datas...")
    df['Event_Date'] = pd.to_datetime(df['Event_Date'], format='%b %d, %Y', errors='coerce')

    # 2. Ordenar do mais antigo para o mais recente (ascending=True)
    print("A ordenar cronologicamente...")
    df = df.sort_values(by='Event_Date', ascending=True)

    # 3. (Opcional) Resetar o index para ficar certinho de 0 até ao fim
    df = df.reset_index(drop=True)

    # 4. Guardar no novo ficheiro
    df.to_csv(output_csv, index=False)
    
    print(f"Sucesso! O teu dataset organizado foi guardado como: '{output_csv}'")
    print(f"Total de combates prontos para Machine Learning: {len(df)}")

if __name__ == "__main__":
    sort_ufc_dataset()