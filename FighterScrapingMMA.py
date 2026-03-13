import requests
from bs4 import BeautifulSoup
import pandas as pd
import string
import time
import os

def scrape_fighters_profiles(csv_name='ufc_fighters_profiles.csv'):
    alphabet = string.ascii_lowercase 
    
    print("A iniciar a extração do perfil completo dos lutadores (Modo Otimizado)...")
    
    # --- LÓGICA DE MEMÓRIA (CHECKPOINT) ---
    scraped_urls = set()
    if os.path.exists(csv_name):
        try:
            df_existente = pd.read_csv(csv_name)
            if 'Fighter_URL' in df_existente.columns:
                scraped_urls = set(df_existente['Fighter_URL'].dropna())
                print(f"Ficheiro existente encontrado! {len(scraped_urls)} lutadores já gravados. A saltar duplicados...\n")
        except Exception as e:
            print(f"Aviso ao ler ficheiro antigo: {e}")
            
    for letter in alphabet:
        print(f"\n--- A extrair todos os lutadores da letra: {letter.upper()} ---")
        
        # O teu URL otimizado que carrega todos os lutadores de uma vez
        url = f"http://ufcstats.com/statistics/fighters?char={letter}&page=all"
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table', class_='b-statistics__table')
            if not table: continue
                
            rows = table.find('tbody').find_all('tr')[1:] # Ignorar cabeçalho
            
            new_fighters_data = []
            novos_nesta_letra = 0
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 0:
                    link_tag = cols[0].find('a')
                    fighter_url = link_tag['href'] if link_tag else None
                    
                    # Se já temos este lutador no CSV, saltamos imediatamente
                    if fighter_url and fighter_url in scraped_urls:
                        continue 
                        
                    first_name = cols[0].text.strip()
                    last_name = cols[1].text.strip()
                    full_name = f"{first_name} {last_name}".strip()
                    
                    height = cols[3].text.strip()
                    weight = cols[4].text.strip()
                    reach = cols[5].text.strip()
                    stance = cols[6].text.strip()
                    
                    wins = cols[7].text.strip()
                    losses = cols[8].text.strip()
                    draws = cols[9].text.strip()
                    
                    career_stats = {
                        'DOB': 'N/A', 'SLpM': '0.00', 'Str_Acc': '0%', 'SApM': '0.00', 
                        'Str_Def': '0%', 'TD_Avg': '0.00', 'TD_Acc': '0%', 
                        'TD_Def': '0%', 'Sub_Avg': '0.0'
                    }
                    
                    # Entrar no perfil individual para buscar as métricas avançadas
                    if fighter_url:
                        try:
                            f_resp = requests.get(fighter_url, timeout=10)
                            f_soup = BeautifulSoup(f_resp.text, 'html.parser')
                            
                            def get_f_stat(label):
                                tag = f_soup.find('i', string=lambda t: t and label in t)
                                return tag.next_sibling.strip() if tag and tag.next_sibling else "0"
                            
                            career_stats['DOB'] = get_f_stat('DOB:')
                            career_stats['SLpM'] = get_f_stat('SLpM:')
                            career_stats['Str_Acc'] = get_f_stat('Str. Acc.:')
                            career_stats['SApM'] = get_f_stat('SApM:')
                            career_stats['Str_Def'] = get_f_stat('Str. Def:')
                            career_stats['TD_Avg'] = get_f_stat('TD Avg.:')
                            career_stats['TD_Acc'] = get_f_stat('TD Acc.:')
                            career_stats['TD_Def'] = get_f_stat('TD Def.:')
                            career_stats['Sub_Avg'] = get_f_stat('Sub. Avg.:')
                            
                        except Exception as e:
                            print(f"     [ERRO] A ler perfil de {full_name}: {e}")
                        
                        time.sleep(0.3) # Pausa crucial para não ser bloqueado
                    
                    new_fighters_data.append({
                        'Fighter_Name': full_name, 'Height': height, 'Weight': weight,
                        'Reach': reach, 'Stance': stance, 'DOB': career_stats['DOB'],
                        'Wins': wins, 'Losses': losses, 'Draws': draws,
                        'SLpM': career_stats['SLpM'], 'Str_Acc': career_stats['Str_Acc'],
                        'SApM': career_stats['SApM'], 'Str_Def': career_stats['Str_Def'],
                        'TD_Avg': career_stats['TD_Avg'], 'TD_Acc': career_stats['TD_Acc'],
                        'TD_Def': career_stats['TD_Def'], 'Sub_Avg': career_stats['Sub_Avg'],
                        'Fighter_URL': fighter_url
                    })
                    
                    if fighter_url:
                        scraped_urls.add(fighter_url)
                    novos_nesta_letra += 1
            
            # Gravar incrementalmente no fim de cada letra
            if new_fighters_data:
                df_temp = pd.DataFrame(new_fighters_data)
                df_temp.to_csv(csv_name, mode='a', header=not os.path.exists(csv_name), index=False)
                print(f"    [OK] {novos_nesta_letra} novos lutadores gravados na letra {letter.upper()}.")
            else:
                print(f"    [INFO] Todos os lutadores da letra {letter.upper()} já estavam no CSV.")
            
        except Exception as e:
            print(f"Erro ao processar a letra {letter}: {e}")
            
    print(f"\n--- RECOLHA CONCLUÍDA! O teu ficheiro '{csv_name}' está atualizado. ---")

if __name__ == "__main__":
    scrape_fighters_profiles()