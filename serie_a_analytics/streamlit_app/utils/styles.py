"""
Shared CSS styles for the Streamlit app.

This module contains all CSS styles used across the app pages.
Import and apply with: apply_custom_css()
"""

import streamlit as st


def apply_custom_css():
    """Apply the custom CSS styles to the page."""
    st.markdown(CSS_STYLES, unsafe_allow_html=True)


CSS_STYLES = """
<style>
    /* ============================================
       SCROLL ANCHORING FIX
       Prevents browser from auto-scrolling on rerun
       ============================================ */
    * {
        overflow-anchor: none !important;
    }

    /* ============================================
       DESIGN SYSTEM - COLOR PALETTE
       ============================================ */
    :root {
        /* Primary Brand Colors - Dark Blue */
        --brand-primary: #0c1929;
        --brand-secondary: #1a2d4a;

        /* Strength Colors (Green) */
        --strength-bg: #ecfdf5;
        --strength-bg-hover: #d1fae5;
        --strength-border: #10b981;
        --strength-accent: #059669;
        --strength-text: #065f46;
        --strength-badge-bg: #a7f3d0;

        /* Average Colors (Amber) */
        --average-bg: #fffbeb;
        --average-bg-hover: #fef3c7;
        --average-border: #f59e0b;
        --average-accent: #d97706;
        --average-text: #92400e;
        --average-badge-bg: #fde68a;

        /* Weakness Colors (Red) */
        --weakness-bg: #fef2f2;
        --weakness-bg-hover: #fee2e2;
        --weakness-border: #ef4444;
        --weakness-accent: #dc2626;
        --weakness-text: #991b1b;
        --weakness-badge-bg: #fecaca;

        /* Neutral Colors */
        --neutral-50: #fafafa;
        --neutral-100: #f5f5f5;
        --neutral-200: #e5e5e5;
        --neutral-300: #d4d4d4;
        --neutral-600: #525252;
        --neutral-700: #404040;
        --neutral-800: #262626;
    }

    /* ============================================
       MAIN HEADER
       ============================================ */
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem 1.5rem;
        background: linear-gradient(135deg, #0c1929 0%, #1a2d4a 50%, #243b5c 100%);
        color: white;
        border-radius: 12px;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        letter-spacing: -0.025em;
    }

    /* ============================================
       TEAM & MANAGER INFO
       ============================================ */
    .team-info-container {
        text-align: center;
        margin-bottom: 1.5rem;
    }

    .team-header {
        font-size: 3.5rem;
        font-weight: 700;
        color: var(--brand-primary);
        margin-bottom: 0.5rem;
        letter-spacing: 0.15em;
        font-variant: small-caps;
        text-transform: lowercase;
    }

    .team-logo-placeholder {
        font-size: 6rem;
        margin: 0.8rem 0;
        line-height: 1;
    }

    .team-logo {
        margin: 0.8rem 0;
        line-height: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .team-logo img {
        max-width: 100px;
        max-height: 100px;
        object-fit: contain;
    }

    .manager-name {
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--brand-secondary);
        margin-bottom: 0;
        letter-spacing: -0.01em;
    }

    .manager-matches {
        font-size: 1rem;
        font-weight: 400;
        color: #6b7280;
        margin-left: 0.3rem;
    }

    /* ============================================
       SECTION HEADERS (Strength/Average/Weakness)
       ============================================ */
    .strength-header {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.25);
        letter-spacing: 0.01em;
    }

    .average-header {
        background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(245, 158, 11, 0.25);
        letter-spacing: 0.01em;
    }

    .weakness-header {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(239, 68, 68, 0.25);
        letter-spacing: 0.01em;
    }

    /* ============================================
       CATEGORY LABELS (KPI Categories)
       ============================================ */
    .kpi-category {
        font-weight: 600;
        font-size: 0.8rem;
        color: var(--neutral-600);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 16px 0 8px 0;
        padding: 6px 10px;
        background: linear-gradient(90deg, var(--neutral-100) 0%, transparent 100%);
        border-radius: 6px;
        border-left: 3px solid var(--brand-primary);
    }

    /* ============================================
       METRIC CARD BUTTONS - ELEGANT DESIGN
       ============================================ */

    /* Base style for ALL metric buttons */
    .metric-card-container {
        margin-bottom: 6px;
    }

    /* Hide default Streamlit button styling */
    .metric-card-container div[data-testid="stButton"] > button {
        width: 100%;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        padding: 14px 16px !important;
        border-radius: 10px !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
        line-height: 1.4 !important;
    }

    /* ============================================
       DOWNLOAD PDF BUTTON
       ============================================ */
    div[data-testid="stDownloadButton"] > button {
        background: #dc2626 !important;
        color: #ffffff !important;
        border: none !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background: #b91c1c !important;
        color: #ffffff !important;
        border: none !important;
    }

    /* ============ STRENGTH CARD STYLE ============ */
    .metric-card-strength div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%) !important;
        border: 1px solid #a7f3d0 !important;
        color: #065f46 !important;
    }

    .metric-card-strength div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%) !important;
        border-color: #10b981 !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
        transform: translateY(-1px);
    }

    .metric-card-strength div[data-testid="stButton"] > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.15) !important;
    }

    /* ============ AVERAGE CARD STYLE ============ */
    .metric-card-average div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%) !important;
        border: 1px solid #fde68a !important;
        color: #92400e !important;
    }

    .metric-card-average div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
        border-color: #f59e0b !important;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2) !important;
        transform: translateY(-1px);
    }

    .metric-card-average div[data-testid="stButton"] > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(245, 158, 11, 0.15) !important;
    }

    /* ============ WEAKNESS CARD STYLE ============ */
    .metric-card-weakness div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%) !important;
        border: 1px solid #fecaca !important;
        color: #991b1b !important;
    }

    .metric-card-weakness div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%) !important;
        border-color: #ef4444 !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important;
        transform: translateY(-1px);
    }

    .metric-card-weakness div[data-testid="stButton"] > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(239, 68, 68, 0.15) !important;
    }

    /* ============================================
       TOGGLE BUTTONS (Forza/Medi/Deboli)
       ============================================ */
    .toggle-strength div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3) !important;
    }

    .toggle-strength-inactive div[data-testid="stButton"] > button {
        background: #ecfdf5 !important;
        color: #065f46 !important;
        border: 1px solid #a7f3d0 !important;
        box-shadow: none !important;
    }

    .toggle-strength-inactive div[data-testid="stButton"] > button:hover {
        background: #d1fae5 !important;
    }

    .toggle-average div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3) !important;
    }

    .toggle-average-inactive div[data-testid="stButton"] > button {
        background: #fffbeb !important;
        color: #92400e !important;
        border: 1px solid #fde68a !important;
        box-shadow: none !important;
    }

    .toggle-average-inactive div[data-testid="stButton"] > button:hover {
        background: #fef3c7 !important;
    }

    .toggle-weakness div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3) !important;
    }

    .toggle-weakness-inactive div[data-testid="stButton"] > button {
        background: #fef2f2 !important;
        color: #991b1b !important;
        border: 1px solid #fecaca !important;
        box-shadow: none !important;
    }

    .toggle-weakness-inactive div[data-testid="stButton"] > button:hover {
        background: #fee2e2 !important;
    }

    /* ============================================
       RANKING ITEMS
       ============================================ */
    .rank-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.75rem;
        min-width: 38px;
        text-align: center;
    }

    .rank-top {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        color: #065f46;
    }
    .rank-mid {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        color: #92400e;
    }
    .rank-low {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        color: #991b1b;
    }

    /* ============================================
       METRIC DETAIL HEADER
       ============================================ */
    .metric-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-header h3 {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    .metric-header p {
        margin: 6px 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }

    /* ============================================
       RANKING CONTAINER & ITEMS
       ============================================ */
    .ranking-container {
        max-height: 420px;
        overflow-y: auto;
        padding-right: 8px;
        scrollbar-width: thin;
        scrollbar-color: #d4d4d4 #f5f5f5;
    }

    .ranking-container::-webkit-scrollbar {
        width: 6px;
    }

    .ranking-container::-webkit-scrollbar-track {
        background: #f5f5f5;
        border-radius: 3px;
    }

    .ranking-container::-webkit-scrollbar-thumb {
        background: #d4d4d4;
        border-radius: 3px;
    }

    .ranking-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 4px;
        font-size: 0.88rem;
        background: var(--neutral-50);
        border: 1px solid var(--neutral-200);
        transition: all 0.15s ease;
    }

    .ranking-item:hover {
        background: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .ranking-item.highlight {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 2px solid #f59e0b;
        font-weight: 600;
    }

    /* ============================================
       PLAYER ITEMS
       ============================================ */
    .player-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 4px;
        font-size: 0.88rem;
        transition: all 0.15s ease;
    }

    .player-item:hover {
        transform: translateX(2px);
    }

    .player-contribution {
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* ============================================
       SECTION TITLES
       ============================================ */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--neutral-700);
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--brand-primary);
        letter-spacing: -0.01em;
    }

    /* ============================================
       NO METRICS MESSAGE
       ============================================ */
    .no-metrics-msg {
        color: var(--neutral-600);
        font-style: italic;
        padding: 20px;
        text-align: center;
        background: linear-gradient(135deg, var(--neutral-50) 0%, var(--neutral-100) 100%);
        border-radius: 10px;
        border: 1px dashed var(--neutral-300);
    }

    /* ============================================
       SCROLLABLE METRICS AREA
       ============================================ */
    .metrics-scroll-area {
        max-height: 500px;
        overflow-y: auto;
        padding-right: 8px;
        scrollbar-width: thin;
        scrollbar-color: #d4d4d4 #f5f5f5;
    }

    .metrics-scroll-area::-webkit-scrollbar {
        width: 6px;
    }

    .metrics-scroll-area::-webkit-scrollbar-track {
        background: #f5f5f5;
        border-radius: 3px;
    }

    .metrics-scroll-area::-webkit-scrollbar-thumb {
        background: #d4d4d4;
        border-radius: 3px;
    }

    /* ============================================
       GENERAL BUTTON IMPROVEMENTS
       ============================================ */
    div[data-testid="stButton"] > button {
        transition: all 0.2s ease !important;
    }

    /* Back button styling */
    .back-button div[data-testid="stButton"] > button {
        background: var(--neutral-100) !important;
        color: var(--neutral-700) !important;
        border: 1px solid var(--neutral-300) !important;
        font-weight: 500 !important;
    }

    .back-button div[data-testid="stButton"] > button:hover {
        background: var(--neutral-200) !important;
        border-color: var(--neutral-400) !important;
    }

    /* Primary button styling (type="primary") - Dark Blue Theme */
    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stButton"] > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #0c1929 0%, #1a2d4a 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(12, 25, 41, 0.3) !important;
    }

    div[data-testid="stButton"] > button[kind="primary"]:hover,
    div[data-testid="stButton"] > button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #1a2d4a 0%, #243b5c 100%) !important;
        box-shadow: 0 6px 16px rgba(12, 25, 41, 0.4) !important;
        transform: translateY(-1px);
    }

    /* ============================================
       PLAYER ANALYSIS SECTION
       ============================================ */
    .player-analysis-container {
        margin-top: 1.5rem;
        padding: 1rem;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }

    .player-analysis-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--brand-primary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--brand-primary);
    }

    .player-card {
        background: white;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .player-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .player-name {
        font-weight: 600;
        font-size: 0.95rem;
        color: #1f2937;
    }

    .player-role {
        font-size: 0.75rem;
        color: #6b7280;
        background: #f3f4f6;
        padding: 2px 8px;
        border-radius: 12px;
    }

    .insight-section {
        margin-top: 8px;
    }

    .insight-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }

    .insight-label-strength {
        color: #059669;
    }

    .insight-label-weakness {
        color: #dc2626;
    }

    .insight-item {
        font-size: 0.8rem;
        padding: 4px 8px;
        margin: 2px 0;
        border-radius: 6px;
        line-height: 1.3;
    }

    .insight-strength {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        color: #065f46;
        border-left: 3px solid #10b981;
    }

    .insight-weakness {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        color: #991b1b;
        border-left: 3px solid #ef4444;
    }

    .zscore-badge {
        display: inline-block;
        font-size: 0.65rem;
        padding: 1px 5px;
        border-radius: 4px;
        margin-left: 4px;
        font-weight: 600;
    }

    .zscore-positive {
        background: #d1fae5;
        color: #065f46;
    }

    .zscore-negative {
        background: #fee2e2;
        color: #991b1b;
    }

    .player-select-card {
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .player-select-card:hover {
        border-color: var(--brand-primary);
        box-shadow: 0 4px 12px rgba(26, 71, 42, 0.15);
    }

    .player-select-card.selected {
        border: 2px solid var(--brand-primary);
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 50%);
    }

    .no-analysis-msg {
        text-align: center;
        color: #6b7280;
        font-style: italic;
        padding: 1rem;
    }

    .api-key-notice {
        font-size: 0.75rem;
        color: #6b7280;
        text-align: center;
        margin-top: 0.5rem;
        padding: 8px;
        background: #f9fafb;
        border-radius: 6px;
    }

    /* ============================================
       KPI SUMMARY SECTION
       ============================================ */
    .kpi-summary-container {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #e2e8f0;
    }

    .kpi-category-header {
        font-weight: 600;
        font-size: 0.75rem;
        color: #4b5563;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
        padding-left: 2px;
    }

    .kpi-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 8px;
        margin: 2px 0;
        border-radius: 4px;
        font-size: 0.8rem;
        transition: all 0.15s ease;
    }

    .kpi-item:hover {
        transform: translateX(2px);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .kpi-strength {
        background: #ecfdf5;
        color: #059669;
    }

    .kpi-average {
        background: #fffbeb;
        color: #d97706;
    }

    .kpi-weakness {
        background: #fef2f2;
        color: #dc2626;
    }

    /* Expander styling */
    .stExpander {
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        margin-top: 12px !important;
    }

    .stExpander > div:first-child {
        background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%) !important;
        border-radius: 8px 8px 0 0 !important;
    }

    /* Playing Style Cluster Box */
    .cluster-box {
        background: linear-gradient(135deg, #0c1929 0%, #1a2d4a 50%, #243b5c 100%);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(12, 25, 41, 0.4);
        margin-bottom: 1rem;
    }

    .cluster-box-title {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }

    .cluster-box-name {
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        line-height: 1.2;
    }

    /* xG Cluster Stats */
    .xg-cluster-card {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }

    .xg-value {
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1;
    }

    .xg-for {
        color: #10b981;
    }

    .xg-against {
        color: #ef4444;
    }

    .xg-label {
        font-size: 0.7rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    .xg-matches {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    }

    /* Formation Stats */
    .formation-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .formation-primary {
        background: linear-gradient(135deg, #0c1929 0%, #1a2d4a 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 4px 12px rgba(12, 25, 41, 0.4);
    }

    .formation-primary .formation-pct {
        font-size: 1rem;
        opacity: 0.85;
        background: rgba(255,255,255,0.2);
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
    }

    .formation-secondary {
        background: linear-gradient(135deg, #64748b 0%, #475569 100%);
        color: white;
        padding: 0.6rem 1.2rem;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        box-shadow: 0 2px 8px rgba(71, 85, 105, 0.25);
    }

    .formation-secondary .formation-pct {
        font-size: 0.85rem;
        opacity: 0.85;
        background: rgba(255,255,255,0.2);
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
    }

    /* Formation Timeline */
    .formation-timeline {
        display: flex;
        flex-wrap: nowrap;
        gap: 4px;
        padding: 0.5rem 0;
        overflow-x: auto;
        scrollbar-width: thin;
        scrollbar-color: #cbd5e1 transparent;
    }

    .formation-timeline::-webkit-scrollbar {
        height: 6px;
    }

    .formation-timeline::-webkit-scrollbar-track {
        background: transparent;
    }

    .formation-timeline::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 3px;
    }

    .formation-match-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex-shrink: 0;
    }

    .formation-match {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 36px;
        min-width: 36px;
        height: 100px;
        padding: 10px 4px;
        border-radius: 8px;
        transition: all 0.15s ease;
        cursor: pointer;
    }

    .formation-match:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .formation-match-code {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1px;
        justify-content: center;
    }

    .formation-match-code span {
        font-weight: 800;
        font-size: 0.95rem;
        line-height: 1.1;
    }

    .formation-match-week {
        font-size: 0.65rem;
        color: #64748b;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Hide entire sidebar for cleaner experience */
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"],
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }

    /* ============================================
       SEGMENTED CONTROL (Filter buttons)
       ============================================ */
    /* Target all possible segmented control selectors */
    [data-baseweb="segmented-control"] button,
    [role="radiogroup"] button,
    .stSegmentedControl button,
    div[data-testid="stSegmentedControlContainer"] button,
    div[data-testid="stHorizontalBlock"] [role="radiogroup"] button {
        padding: 14px 28px !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        min-height: 50px !important;
        min-width: 130px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.02em !important;
    }

    /* ============================================
       PDF BUTTONS - SMALL FONT, ROUNDED
       Uses .st-key-{key} selector pattern (Streamlit 1.41+)
       ============================================ */

    /* 1. Vertical block inside card - minimal gap between rows */
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] {
        gap: 2px !important;
    }

    /* 2. Target PDF buttons and metric detail button using wildcard on st-key class */
    div[class*="st-key-pdf_btn"] .stButton button,
    div[class*="st-key-detail_btn"] .stButton button,
    div[class*="st-key-metric_btn"] .stButton button {
        font-size: 0.65rem !important;
        padding: 4px 10px !important;
        min-height: 24px !important;
        border-radius: 12px !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
    }

    /* 3. Target the p tag inside buttons (Streamlit renders text in p) */
    div[class*="st-key-pdf_btn"] .stButton button p,
    div[class*="st-key-detail_btn"] .stButton button p,
    div[class*="st-key-metric_btn"] .stButton button p {
        font-size: 0.65rem !important;
        line-height: 1.2 !important;
        margin: 0 !important;
    }

    /* 4. Horizontal block - clean */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* ============================================
       PLAYER PROFILE PAGE
       ============================================ */

    /* Player Header Container */
    .player-profile-header {
        display: flex;
        align-items: flex-start;
        gap: 2rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 16px;
        margin-bottom: 1.5rem;
    }

    /* Player Image */
    .player-image-container {
        flex-shrink: 0;
    }

    .player-image {
        width: 170px;
        height: 170px;
        border-radius: 14px;
        object-fit: cover;
        background: #e5e7eb;
        border: 4px solid white;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
    }

    .player-image-placeholder {
        width: 170px;
        height: 170px;
        border-radius: 14px;
        background: linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 4.5rem;
        color: #6b7280;
        border: 4px solid white;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
    }

    /* Player Info */
    .player-info {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .player-name {
        font-size: 2.4rem;
        font-weight: 800;
        color: #0c1929;
        margin: 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }

    .player-team {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 1.25rem;
        color: #374151;
        font-weight: 500;
    }

    .player-team img {
        width: 28px;
        height: 28px;
    }

    .player-position {
        font-size: 1.1rem;
        color: #6b7280;
        font-weight: 600;
    }

    .player-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: #0c1929;
        color: white;
        font-size: 1.2rem;
        font-weight: 700;
        border-radius: 8px;
        margin-top: 0.5rem;
    }

    /* Compact Stats - Two Rows */
    .player-stats-compact {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
        margin-top: 0.8rem;
        padding: 0.8rem 1.2rem;
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        border-radius: 12px;
        font-size: 1.05rem;
        color: #374151;
        max-width: fit-content;
        border: 1px solid #cbd5e1;
    }

    .stats-row {
        display: flex;
        gap: 1.5rem;
    }

    .stat-compact {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        white-space: nowrap;
    }

    .stat-compact strong {
        color: #0c1929;
        font-weight: 800;
        font-size: 1.15rem;
    }

    /* Usage Score Box */
    .usage-score-box {
        border-radius: 16px;
        padding: 1.5rem 2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        min-width: 200px;
    }

    .usage-score-box.score-low {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }

    .usage-score-box.score-medium {
        background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
    }

    .usage-score-box.score-high {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    }

    .usage-score-value {
        font-size: 4rem;
        font-weight: 800;
        color: white;
        line-height: 1;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .usage-score-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    .usage-score-subtitle {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }

    /* Season Chart - 38 Rounds */
    .season-chart-container {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1rem;
        margin: 1.5rem 0;
        overflow-x: auto;
    }

    .season-chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #0c1929;
        margin-bottom: 1rem;
    }

    .season-chart {
        display: flex;
        gap: 4px;
        padding: 0.5rem 0;
        min-width: max-content;
    }

    .round-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 22px;
        gap: 4px;
    }

    /* Rating Bar */
    .rating-bar {
        width: 16px;
        border-radius: 8px;
        transition: all 0.2s ease;
        position: relative;
    }

    .rating-bar:hover {
        transform: scale(1.15);
        z-index: 10;
    }

    .rating-bar-value {
        position: absolute;
        top: -18px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 9px;
        font-weight: 600;
        color: #374151;
        white-space: nowrap;
    }

    /* Minutes Bar */
    .minutes-bar {
        width: 16px;
        border-radius: 8px;
        max-height: 50px;
        transition: all 0.2s ease;
    }

    .minutes-bar:hover {
        transform: scale(1.15);
    }

    .minutes-bar-value {
        font-size: 8px;
        color: #6b7280;
        margin-top: 2px;
    }

    /* Not Played Bar */
    .bar-not-played {
        background: #e5e7eb !important;
    }

    /* Events Icons */
    .events-icons {
        display: flex;
        flex-direction: column;
        align-items: center;
        font-size: 11px;
        min-height: 18px;
        gap: 1px;
    }

    /* Round Label */
    .round-label {
        font-size: 9px;
        color: #9ca3af;
        margin-top: 2px;
    }

    /* Stats Summary */
    .stats-summary {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        background: #f8fafc;
        border-radius: 12px;
        padding: 1rem;
        margin: 1.5rem 0;
    }

    .stat-item {
        flex: 1;
        min-width: 90px;
        text-align: center;
        padding: 0.75rem 0.5rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0c1929;
        line-height: 1.2;
    }

    .stat-label {
        font-size: 0.7rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    /* StatsBomb Metrics Columns */
    .metrics-three-columns {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .metrics-column {
        border-radius: 12px;
        padding: 1rem;
    }

    .metrics-column-positive {
        background: #dcfce7;
        border: 2px solid #22c55e;
    }

    .metrics-column-neutral {
        background: #f3f4f6;
        border: 2px solid #9ca3af;
    }

    .metrics-column-negative {
        background: #fee2e2;
        border: 2px solid #ef4444;
    }

    .column-header {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .column-header-positive {
        color: #16a34a;
        border-bottom: 2px solid #22c55e;
    }

    .column-header-neutral {
        color: #6b7280;
        border-bottom: 2px solid #9ca3af;
    }

    .column-header-negative {
        color: #dc2626;
        border-bottom: 2px solid #ef4444;
    }

    .metric-row {
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(0, 0, 0, 0.08);
    }

    .metric-row:last-child {
        border-bottom: none;
    }

    .metric-name {
        font-size: 0.85rem;
        font-weight: 500;
        color: #374151;
    }

    .metric-value-percentile {
        font-size: 0.8rem;
        color: #6b7280;
        margin-top: 0.15rem;
    }

    .metric-category-header {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #4b5563;
        margin: 0.75rem 0 0.25rem 0;
        padding: 0.25rem 0.5rem;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 4px;
    }

    .metric-category-header:first-of-type {
        margin-top: 0;
    }

    /* Roster Dialog */
    .roster-group-title {
        font-size: 1rem;
        font-weight: 600;
        color: #0c1929;
        margin: 1rem 0 0.5rem 0;
        padding-bottom: 0.25rem;
        border-bottom: 2px solid #e5e7eb;
    }

    .roster-player-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem;
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.15s ease;
    }

    .roster-player-row:hover {
        background: #f3f4f6;
    }

    .roster-player-image {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        background: #e5e7eb;
    }

    .roster-player-info {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .roster-player-name {
        font-weight: 500;
        color: #0c1929;
        min-width: 150px;
    }

    .roster-player-stats {
        display: flex;
        gap: 1rem;
        font-size: 0.85rem;
        color: #6b7280;
    }

    .roster-stat {
        display: flex;
        gap: 0.25rem;
    }

    .roster-stat-label {
        color: #9ca3af;
    }

    .roster-stat-value {
        font-weight: 500;
        color: #374151;
    }

</style>
"""
