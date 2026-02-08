"""
Metrics Information Component

Provides detailed explanations for complex metrics in a user-friendly format.
"""

import streamlit as st

# Dictionary of metric explanations (only non-obvious metrics)
METRIC_EXPLANATIONS = {
    # === ZONE DEL CAMPO ===
    "_zone_header": {
        "title": "🗺️ Zone del Campo",
        "text": """
**Z1 (Zona Difensiva)**: Terzo difensivo (x < 40)
**Z2 (Zona Centrale)**: Centrocampo (40 ≤ x < 80)
**Z3 (Zona Offensiva)**: Terzo offensivo (x ≥ 80)
"""
    },

    # === BUILD-UP ===
    "buildup_sequences": {
        "title": "Azioni da Difesa (Z1)",
        "text": "Tutte le sequenze offensive che **partono dalla zona difensiva**. Include build-up progressivo, diretto e incompleto."
    },
    "buildup_progressive": {
        "title": "Build-up Progressivo (Z1→Z2→Z3)",
        "text": "Azioni che partono dalla difesa e **attraversano tutte le zone** in sequenza. Stile di gioco paziente, possesso palla strutturato."
    },
    "buildup_direct": {
        "title": "Build-up Diretto (Z1→Z3)",
        "text": "Azioni che partono dalla difesa e **saltano il centrocampo** (lancio lungo, verticalizzazione rapida)."
    },
    "buildup_progressive_ratio": {
        "title": "% Stile Progressivo",
        "text": "Tra i build-up riusciti (che arrivano in Z3), quanti sono progressivi vs diretti. **Alto = gioco paziente**, basso = gioco verticale."
    },
    "buildup_success_rate": {
        "title": "% Build-up Riusciti",
        "text": "Percentuale di build-up che raggiungono la zona offensiva (Z3). Misura l'efficacia nel risalire il campo dalla difesa."
    },

    # === TRANSIZIONI ===
    "transition_z2_sequences": {
        "title": "Azioni da Centrocampo (Z2)",
        "text": "Sequenze offensive che **partono dal centrocampo**. Non include azioni che partono dalla difesa o dalla trequarti."
    },
    "transition_z3_sequences": {
        "title": "Azioni da Trequarti (Z3)",
        "text": "Sequenze offensive che **partono già nella zona offensiva** (es. dopo un recupero alto)."
    },
    "counter_attacks": {
        "title": "Contropiedi",
        "text": "Transizioni rapide dopo recupero palla con **superiorità numerica o spazi aperti**. Identificati da StatsBomb con 'From Counter'."
    },
    "fast_attacks": {
        "title": "Attacchi Rapidi (<15s)",
        "text": "Qualsiasi azione che raggiunge la zona offensiva in **meno di 15 secondi**. Include anche azioni da possesso consolidato ma eseguite velocemente."
    },
    "sot_per_recovery_z2": {
        "title": "Efficienza Recupero Z2",
        "text": "Tiri in porta ogni 100 recuperi palla in centrocampo. Misura quanto la squadra **sfrutta i recuperi** in zona centrale."
    },
    "sot_per_recovery_z3": {
        "title": "Efficienza Recupero Z3",
        "text": "Tiri in porta ogni 100 recuperi palla in zona offensiva. Misura l'efficacia del **pressing alto**."
    },

    # === xG / xA ===
    "xg_goals_difference": {
        "title": "Gol vs xG Atteso",
        "text": "Differenza tra gol segnati e xG. **Positivo = overperforming** (segna più del previsto), **negativo = underperforming**."
    },
    "xga_difference": {
        "title": "xGA - Gol Subiti",
        "text": "Differenza tra xG concesso e gol subiti. **Positivo = difesa/portiere efficace**, negativo = si subisce più del previsto."
    },
    "xa_per_key_pass": {
        "title": "Qualità Passaggi Chiave",
        "text": "xA medio per passaggio chiave. Misura la **qualità delle occasioni create**, non solo la quantità."
    },
    "goals_per_xa": {
        "title": "Efficienza Assist",
        "text": "Gol segnati diviso xA generato. Misura quanto i **compagni finalizzano** le occasioni create."
    },

    # === DUELLI ===
    "aerial_duels_offensive": {
        "title": "Duelli Aerei in Attacco",
        "text": "Duelli aerei vinti quando la **squadra ha il possesso** (es. dopo lancio lungo nostro). Normalizzati per 100 lanci lunghi."
    },
    "aerial_duels_defensive": {
        "title": "Duelli Aerei in Difesa",
        "text": "Duelli aerei vinti quando l'**avversario ha il possesso** (es. dopo lancio lungo avversario). Normalizzati per 100 lanci lunghi avversari."
    },
    "ground_duels_offensive": {
        "title": "Contrasti Offensivi",
        "text": "Contrasti vinti in fase di **gegenpressing** (subito dopo aver perso palla). Normalizzati per 100 palle perse."
    },
    "ground_duels_defensive": {
        "title": "Contrasti Difensivi",
        "text": "Contrasti vinti quando l'**avversario attacca**. Normalizzati per 100 passaggi avversari in zona difensiva."
    },

    # === PRESSING ===
    "ppda": {
        "title": "PPDA (Pass per Az. Dif.)",
        "text": "Passaggi avversari concessi per ogni azione difensiva. **Più basso = pressing più aggressivo**."
    },
    "counterpressing": {
        "title": "Azioni Gegenpressing",
        "text": "Azioni di pressing **immediato dopo perdita palla** (entro 5 secondi). Stile Klopp/Guardiola."
    },
    "pressing_high": {
        "title": "Pressing in Z3 (Alto)",
        "text": "Azioni di pressing nella **zona offensiva avversaria**. Indica un pressing alto e aggressivo."
    },

    # === PALLE INATTIVE ===
    "sot_per_100_corners": {
        "title": "Efficienza Corner",
        "text": "Tiri in porta ogni 100 corner battuti. Misura quanto la squadra **crea pericolo dai corner**."
    },
    "sot_per_100_indirect_sp": {
        "title": "Efficienza Inattive Ind.",
        "text": "Tiri in porta ogni 100 palle inattive indirette (corner + punizioni con cross + rimesse). Misura l'efficienza complessiva."
    },
    "set_piece_shots_total": {
        "title": "Tiri per 100 Inattive",
        "text": "Tiri generati ogni 100 palle inattive totali. Misura la **capacità di creare occasioni** da situazioni ferme."
    },

    # === ALTRE ===
    "shots_per_box_touch": {
        "title": "Tiri ogni 100 Tocchi Area",
        "text": "Percentuale di tocchi in area che diventano tiri. Misura la **decisione in area**: alto = tira spesso, basso = gioca troppo."
    },
    "turnovers_per_touch": {
        "title": "% Palle Perse",
        "text": "Percentuale di tocchi che risultano in perdita palla. **Più basso = migliore conservazione** del possesso."
    },
}


def render_metrics_info_button():
    """
    Render a popover button that shows metric explanations.
    Uses st.popover for a floating popup experience.
    """
    with st.popover("ℹ️ Guida alle Metriche", use_container_width=False):
        _render_metrics_explanations()


def _render_metrics_explanations():
    """Render the metric explanations content."""
    st.markdown("### 📊 Guida alle Metriche")
    st.markdown("---")

    # Zone del campo (always show first)
    zone_info = METRIC_EXPLANATIONS["_zone_header"]
    st.markdown(f"**{zone_info['title']}**")
    st.markdown(zone_info['text'])
    st.markdown("---")

    # Group explanations by category
    categories = {
        "🏗️ Build-up": ["buildup_sequences", "buildup_progressive", "buildup_direct",
                       "buildup_progressive_ratio", "buildup_success_rate"],
        "⚡ Transizioni": ["transition_z2_sequences", "transition_z3_sequences",
                          "counter_attacks", "fast_attacks",
                          "sot_per_recovery_z2", "sot_per_recovery_z3"],
        "📈 xG / xA": ["xg_goals_difference", "xga_difference",
                      "xa_per_key_pass", "goals_per_xa"],
        "💪 Duelli": ["aerial_duels_offensive", "aerial_duels_defensive",
                     "ground_duels_offensive", "ground_duels_defensive"],
        "🎯 Pressing": ["ppda", "counterpressing", "pressing_high"],
        "⚽ Palle Inattive": ["sot_per_100_corners", "sot_per_100_indirect_sp",
                             "set_piece_shots_total"],
        "📊 Altre": ["shots_per_box_touch", "turnovers_per_touch"],
    }

    for cat_name, metric_keys in categories.items():
        with st.expander(cat_name, expanded=False):
            for key in metric_keys:
                if key in METRIC_EXPLANATIONS:
                    info = METRIC_EXPLANATIONS[key]
                    st.markdown(f"**{info['title']}**")
                    st.markdown(info['text'])
                    st.markdown("")  # spacing
