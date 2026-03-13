import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# ==========================================
# 1. FUNÇÕES DE LIMPEZA E CÁLCULO
# ==========================================

def clean_fraction(value_str):
    """Transforma '26 of 45' em (26, 45)"""
    try:
        parts = value_str.split(' of ')
        return int(parts[0]), int(parts[1])
    except: return 0, 0

def clean_time(time_str):
    """Converte '1:36' em 96 (segundos) para tempo de controlo"""
    try:
        if ':' not in time_str or time_str == '--': return 0
        m, s = time_str.split(':')
        return int(m) * 60 + int(s)
    except: return 0

def calculate_fight_duration(round_str, time_str):
    """Calcula a duração total do combate em segundos"""
    try:
        current_round = int(round_str)
        completed_rounds_sec = (current_round - 1) * 5 * 60
        m, s = time_str.split(':')
        current_round_sec = int(m) * 60 + int(s)
        return completed_rounds_sec + current_round_sec
    except:
        return 0

# ==========================================
# 2. MOTOR DE EXTRAÇÃO DE DETALHES
# ==========================================

def scrape_fight_details_gold(fight_url):
    try:
        response = requests.get(fight_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- CABEÇALHO E LUTADORES ---
        weight_class = soup.find('i', class_='b-fight-details__fight-title').text.strip()
        
        fighters = [p.text.strip() for p in soup.find_all('h3', class_='b-fight-details__person-name')]
        if len(fighters) < 2: return None
        
        status_tags = soup.find_all('i', class_='b-fight-details__person-status')
        statuses = [tag.text.strip() for tag in status_tags]
        winner = fighters[0] if (len(statuses) > 0 and statuses[0] == 'W') else (fighters[1] if (len(statuses) > 1 and statuses[1] == 'W') else "Draw/NC")

        # --- DETALHES DO COMBATE ---
        fight_details_div = soup.find('div', class_='b-fight-details__content')
        
        def get_detail(label_text):
            tag = fight_details_div.find('i', string=lambda s: s and label_text in s)
            return tag.next_sibling.strip() if tag and tag.next_sibling else "N/A"

        method = fight_details_div.find('i', style="font-style: normal").text.strip()
        end_round = get_detail("Round:")
        end_time = get_detail("Time:")
        time_format = get_detail("Time format:")
        
        total_fight_time_sec = calculate_fight_duration(end_round, end_time)

        # --- TABELAS ESTATÍSTICAS ---
        tables = soup.find_all('table')
        if len(tables) < 3: return None

        cols_totals = tables[0].find('tbody').find_all('tr')[0].find_all('td')
        def get_p_tot(idx): return [p.text.strip() for p in cols_totals[idx].find_all('p')]

        cols_sig = tables[2].find('tbody').find_all('tr')[0].find_all('td')
        def get_p_sig(idx): return [p.text.strip() for p in cols_sig[idx].find_all('p')]

        f1_sig_l, f1_sig_a = clean_fraction(get_p_tot(2)[0])
        f2_sig_l, f2_sig_a = clean_fraction(get_p_tot(2)[1])
        
        return {
            'Fight_URL': fight_url,
            'Fighter_1': fighters[0], 'Fighter_2': fighters[1], 'Winner': winner,
            'Weight_Class': weight_class,
            'Method': method, 'End_Round': end_round, 'End_Time': end_time,
            'Total_Fight_Time_Sec': total_fight_time_sec,
            'Time_Format': time_format,
            
            # Estatísticas Gerais
            'F1_KD': int(get_p_tot(1)[0]) if get_p_tot(1)[0].isdigit() else 0,
            'F2_KD': int(get_p_tot(1)[1]) if get_p_tot(1)[1].isdigit() else 0,
            'F1_Sig_Landed': f1_sig_l, 'F1_Sig_Att': f1_sig_a,
            'F2_Sig_Landed': f2_sig_l, 'F2_Sig_Att': f2_sig_a,
            'F1_TD_Landed': clean_fraction(get_p_tot(5)[0])[0], 'F2_TD_Landed': clean_fraction(get_p_tot(5)[1])[0],
            'F1_TD_Att': clean_fraction(get_p_tot(5)[0])[1], 'F2_TD_Att': clean_fraction(get_p_tot(5)[1])[1],
            'F1_Sub_Att': int(get_p_tot(7)[0]) if get_p_tot(7)[0].isdigit() else 0,
            'F2_Sub_Att': int(get_p_tot(7)[1]) if get_p_tot(7)[1].isdigit() else 0,
            'F1_Ctrl_Sec': clean_time(get_p_tot(9)[0]), 'F2_Ctrl_Sec': clean_time(get_p_tot(9)[1]),
            
            # Distribuição de Golpes (Apenas Landed)
            'F1_Head': clean_fraction(get_p_sig(3)[0])[0], 'F2_Head': clean_fraction(get_p_sig(3)[1])[0],
            'F1_Body': clean_fraction(get_p_sig(4)[0])[0], 'F2_Body': clean_fraction(get_p_sig(4)[1])[0],
            'F1_Leg': clean_fraction(get_p_sig(5)[0])[0], 'F2_Leg': clean_fraction(get_p_sig(5)[1])[0],
            'F1_Distance': clean_fraction(get_p_sig(6)[0])[0], 'F2_Distance': clean_fraction(get_p_sig(6)[1])[0],
            'F1_Clinch': clean_fraction(get_p_sig(7)[0])[0], 'F2_Clinch': clean_fraction(get_p_sig(7)[1])[0],
            'F1_Ground': clean_fraction(get_p_sig(8)[0])[0], 'F2_Ground': clean_fraction(get_p_sig(8)[1])[0]
        }
    except Exception as e:
        print(f"Erro na luta {fight_url}: {e}")
        return None

# ==========================================
# 3. ORQUESTRADOR (LOOP COM CHECKPOINT)
# ==========================================

def run_gold_scraper(csv_name='ufc_gold_dataset.csv', limit_events=None):
    base_url = "http://ufcstats.com/statistics/events/completed?page=all"
    
    print("A aceder à base de dados de eventos do UFC Stats...")
    soup = BeautifulSoup(requests.get(base_url).text, 'html.parser')
    
    event_links = [a['href'] for a in soup.find_all('a', class_='b-link_style_black')]
        
    if limit_events:
        event_links = event_links[:limit_events]

    print(f"Total de eventos na página: {len(event_links)}")

    # --- NOVO: LÓGICA DE MEMÓRIA ---
    scraped_urls = set()
    if os.path.exists(csv_name):
        try:
            df_existente = pd.read_csv(csv_name)
            if 'Fight_URL' in df_existente.columns:
                scraped_urls = set(df_existente['Fight_URL'].dropna())
                print(f"Ficheiro existente encontrado! {len(scraped_urls)} lutas já foram raspadas. A saltar duplicados...")
        except Exception as e:
            print(f"Aviso ao ler ficheiro antigo: {e}")

    all_data = []
    
    for i, event_url in enumerate(event_links):
        print(f"\n[{i+1}/{len(event_links)}] A processar Evento: {event_url}")
        
        try:
            e_soup = BeautifulSoup(requests.get(event_url).text, 'html.parser')
            
            date_tag = e_soup.find('li', class_='b-list__box-list-item')
            event_date = date_tag.text.replace('Date:', '').strip() if date_tag else "N/A"
            
            fight_links = [tr['data-link'] for tr in e_soup.find_all('tr', class_='b-fight-details__table-row') if tr.get('data-link')]
            print(f"   -> {len(fight_links)} lutas encontradas no evento.")
            
            novas_lutas = 0 # Contador para sabermos se fizemos algo novo
            
            for f_link in fight_links:
                # --- NOVO: VERIFICAÇÃO DE DUPLICADOS ---
                if f_link in scraped_urls:
                    continue # Salta imediatamente para a próxima luta sem fazer downloads!
                
                data = scrape_fight_details_gold(f_link)
                if data:
                    data['Event_Date'] = event_date
                    all_data.append(data)
                    scraped_urls.add(f_link) # Adiciona à memória para não repetir
                    novas_lutas += 1
                time.sleep(0.5)
                
            if all_data:
                df_temp = pd.DataFrame(all_data)
                df_temp.to_csv(csv_name, mode='a', header=not os.path.exists(csv_name), index=False)
                print(f"   [OK] {novas_lutas} novas lutas gravadas com sucesso.")
                all_data = []
            elif novas_lutas == 0:
                print(f"   [INFO] Evento já estava totalmente no CSV. A avançar...")
                
        except Exception as e:
            print(f"   [ERRO] Falha ao processar evento inteiro: {e}")
            continue

    print(f"\n--- RECOLHA CONCLUÍDA! ---")

# ==========================================
# 4. EXECUÇÃO
# ==========================================

if __name__ == "__main__":
    run_gold_scraper()