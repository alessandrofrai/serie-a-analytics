# ⚽ Serie A 2015-2016 Team Analytics Dashboard

Dashboard interattiva per l'analisi delle squadre della Serie A 2015-2016 utilizzando i dati StatsBomb Open Data.

## 🎯 Caratteristiche

- **Visualizzazione squadre**: Griglia cliccabile con tutte le 20 squadre della Serie A
- **Gestione allenatori**: Supporto per combinazioni team+manager (es. cambio allenatore durante stagione)
- **Metriche p90**: Tutte le metriche sono normalizzate per 90 minuti
- **Ranking dinamico**: Classifiche basate su tutte le combinazioni team+manager, non solo sulle 20 squadre
- **Contributo giocatori**: Percentuale di contributo di ogni giocatore alle metriche di squadra
- **Visualizzazione formazione**: Campo con scala colori grigio→rosso (rosso = valori più alti)
- **TOPSIS**: Calcolo multi-criterio per metriche con volume e qualità

## 🏗️ Struttura Progetto

```
serie_a_analytics/
├── config/                 # Configurazioni
│   ├── settings.py         # Impostazioni generali
│   └── supabase_config.py  # Connessione database
├── data/                   # Moduli dati
│   ├── downloader.py       # Download StatsBomb
│   ├── processor.py        # Elaborazione eventi
│   └── zones.py            # Sistema 18 zone
├── metrics/                # Calcolo metriche
│   ├── attacking.py
│   ├── defending.py
│   ├── possession.py
│   ├── transition.py
│   ├── set_pieces.py
│   ├── pressing.py
│   └── topsis.py
├── database/               # Database
│   ├── models.py
│   ├── repository.py
│   └── schema.sql
├── scripts/                # Script di elaborazione
│   ├── 01_download_data.py
│   ├── 02_process_events.py
│   └── 03_calculate_metrics.py
├── streamlit_app/          # Interfaccia utente
│   ├── app.py
│   └── components/
└── tests/                  # Test
```

## 🚀 Quick Start

### 1. Setup Ambiente

```bash
# Clona il repository
git clone <repo-url>
cd serie_a_analytics

# Crea virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure: venv\Scripts\activate  # Windows

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Configura Ambiente

```bash
# Copia il file di esempio
cp .env.example .env

# Modifica .env con le tue credenziali Supabase
```

### 3. Scarica ed Elabora Dati

```bash
# Step 1: Scarica dati StatsBomb
python scripts/01_download_data.py

# Step 2: Elabora eventi
python scripts/02_process_events.py

# Step 3: Calcola metriche
python scripts/03_calculate_metrics.py
```

### 4. Avvia Dashboard

```bash
# Avvia Streamlit
streamlit run streamlit_app/app.py
```

## 📊 Categorie Metriche

| Categoria | Descrizione |
|-----------|-------------|
| **Attacking** | xG, tiri, gol, grandi occasioni |
| **Chance Creation** | xA, passaggi chiave, cross, filtranti |
| **Build-up** | Sequenze da zona difensiva, passaggi progressivi |
| **Transition** | Contropiedi, attacchi rapidi, transizioni per zona |
| **Possession** | Passaggi, conduzioni, tocchi in area |
| **Defending** | Contrasti, intercetti, duelli |
| **Pressing** | PPDA, recuperi alti, gegenpressing |
| **Set Pieces** | Corner, punizioni, rigori |

## 🎨 Sistema Colori

- **Grigio**: Valori bassi / contributo minore
- **Rosso**: Valori alti / contributo maggiore ("pericoloso" / importante)

Il colore indica l'importanza relativa: più un giocatore contribuisce a una metrica, più sarà visualizzato in rosso.

## ⚙️ Note Tecniche

### Team+Manager Combinations

Il sistema utilizza combinazioni `team_id + manager_id` come entità principali per il ranking.
Questo significa che:

- Se una squadra ha cambiato allenatore, avrà multiple combinazioni
- Il ranking non è su 20 squadre fisse, ma su N combinazioni (~22-25)
- Ogni combinazione rappresenta un "team diverso" dal punto di vista tattico

### Metriche p90

Tutte le metriche sono normalizzate per 90 minuti:
```
metrica_p90 = (metrica_totale / minuti_totali) × 90
```

### TOPSIS

Per metriche con componenti di volume e qualità, viene calcolato un punteggio TOPSIS:
- **Peso volume**: 35%
- **Peso qualità**: 65%

## 📝 Licenza

MIT License - Dati forniti da StatsBomb Open Data.

## 🙏 Credits

- **StatsBomb** per i dati open source
- **mplsoccer** per le visualizzazioni del campo
- **Streamlit** per il framework della dashboard
