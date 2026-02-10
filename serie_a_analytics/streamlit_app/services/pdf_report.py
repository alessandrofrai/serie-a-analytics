"""
PDF Report Generation Service for Serie A Analytics.

Generates professional PDF reports using ReportLab.
Compatible with Streamlit Cloud deployment.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from pathlib import Path
import io
import base64
import logging

import pandas as pd

# Import name helpers for SofaScore display names
from utils.data_helpers import (
    get_sofascore_names_map,
    get_player_display_name,
    extract_surname
)

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String
from reportlab.graphics.charts.spider import SpiderChart
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

logger = logging.getLogger(__name__)

# Font defaults (fallback to core fonts if custom fonts are unavailable)
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
FONT_BOLD_ITALIC = "Helvetica-BoldOblique"
_FONTS_REGISTERED = False


def _register_fonts():
    """Register Unicode-capable fonts for PDF rendering."""
    global FONT_REGULAR, FONT_BOLD, FONT_ITALIC, FONT_BOLD_ITALIC, _FONTS_REGISTERED

    if _FONTS_REGISTERED:
        return

    font_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    regular_path = font_dir / "DejaVuSans.ttf"
    bold_path = font_dir / "DejaVuSans-Bold.ttf"
    italic_path = font_dir / "DejaVuSans-Oblique.ttf"
    bold_italic_path = font_dir / "DejaVuSans-BoldOblique.ttf"

    if regular_path.exists() and bold_path.exists() and italic_path.exists() and bold_italic_path.exists():
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", str(regular_path)))
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(bold_path)))
            pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", str(italic_path)))
            pdfmetrics.registerFont(TTFont("DejaVuSans-BoldOblique", str(bold_italic_path)))
            registerFontFamily(
                "DejaVuSans",
                normal="DejaVuSans",
                bold="DejaVuSans-Bold",
                italic="DejaVuSans-Oblique",
                boldItalic="DejaVuSans-BoldOblique"
            )

            FONT_REGULAR = "DejaVuSans"
            FONT_BOLD = "DejaVuSans-Bold"
            FONT_ITALIC = "DejaVuSans-Oblique"
            FONT_BOLD_ITALIC = "DejaVuSans-BoldOblique"
        except Exception:
            pass

    _FONTS_REGISTERED = True

# Game Phases constants (matching components/game_phases.py)
GAME_PHASES = [
    'direct_sp',
    'indirect_sp',
    'counter',
    'fast_attack',
    'cross',
    'long_range',
    'buildup_progressive',
    'buildup_direct',
]

PHASE_NAMES = {
    'direct_sp': 'Inattive Dirette',
    'indirect_sp': 'Inattive Indirette',
    'counter': 'Contropiede',
    'fast_attack': 'Attacco Rapido',
    'cross': 'Cross',
    'long_range': 'Tiro da Fuori',
    'buildup_progressive': 'Build-up Progressivo',
    'buildup_direct': 'Build-up Diretto',
}


# Design System Colors (matching the dashboard)
class PDFColors:
    # Brand
    PRIMARY = colors.HexColor('#0c1929')
    SECONDARY = colors.HexColor('#1a2d4a')

    # Strength (Green)
    STRENGTH_BG = colors.HexColor('#ecfdf5')
    STRENGTH_MAIN = colors.HexColor('#10b981')
    STRENGTH_DARK = colors.HexColor('#065f46')

    # Average (Orange) - for "Nella Media" metrics
    AVERAGE_BG = colors.HexColor('#fff7ed')
    AVERAGE_MAIN = colors.HexColor('#f59e0b')
    AVERAGE_DARK = colors.HexColor('#b45309')

    # Weakness (Red)
    WEAKNESS_BG = colors.HexColor('#fef2f2')
    WEAKNESS_MAIN = colors.HexColor('#ef4444')
    WEAKNESS_DARK = colors.HexColor('#991b1b')

    # Neutral
    NEUTRAL_50 = colors.HexColor('#fafafa')
    NEUTRAL_100 = colors.HexColor('#f5f5f5')
    NEUTRAL_200 = colors.HexColor('#e5e5e5')
    NEUTRAL_600 = colors.HexColor('#525252')
    NEUTRAL_800 = colors.HexColor('#262626')
    HIGHLIGHT = colors.HexColor('#fff3cd')
    WHITE = colors.white
    BLACK = colors.black

    # Performance Map colors
    CARD_BG = colors.HexColor('#1e293b')        # Sfondo card scuro
    CARD_BG_LIGHT = colors.HexColor('#334155')  # Sfondo card gradient end
    TEXT_MUTED = colors.HexColor('#94a3b8')     # Testo secondario
    TEXT_SUBTLE = colors.HexColor('#64748b')    # Testo terziario


def markdown_to_html(text: str) -> str:
    """
    Convert markdown formatting to ReportLab HTML tags.

    Converts:
    - **bold** -> <b>bold</b>
    - *italic* -> <i>italic</i>
    - Newlines -> <br/>

    Args:
        text: Text with markdown formatting

    Returns:
        Text with HTML tags for ReportLab
    """
    import re

    if not text:
        return text

    # Convert **bold** to <b>bold</b> (must be done before single *)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    # Convert *italic* to <i>italic</i>
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)

    # Convert newlines to <br/> for paragraph breaks
    text = text.replace('\n\n', '<br/><br/>')
    text = text.replace('\n', '<br/>')

    return text


@dataclass
class PDFReportConfig:
    """Configuration for PDF report generation."""
    team_id: int
    manager_id: int
    team_name: str
    manager_name: str
    matches_count: int
    formation: str
    cluster_name: str
    formation_stats: Optional[Dict[str, Any]]

    # Selected metrics (now includes average/nella media category)
    positive_metrics: List[str]  # Punti di Forza (green)
    average_metrics: List[str] = None  # Nella Media (orange) - optional, defaults to empty
    negative_metrics: List[str] = None  # Punti Deboli (red)

    # Detail contribution pages
    positive_detail_metrics: List[str] = None  # metrics with player contributions
    average_detail_metrics: List[str] = None  # metrics with player contributions
    negative_detail_metrics: List[str] = None  # metrics with player contributions

    def __post_init__(self):
        """Initialize optional lists to empty if None."""
        if self.average_metrics is None:
            self.average_metrics = []
        if self.negative_metrics is None:
            self.negative_metrics = []
        if self.positive_detail_metrics is None:
            self.positive_detail_metrics = []
        if self.average_detail_metrics is None:
            self.average_detail_metrics = []
        if self.negative_detail_metrics is None:
            self.negative_detail_metrics = []


class PDFReportError(Exception):
    """Base exception for PDF report generation errors."""
    pass


class DataNotAvailableError(PDFReportError):
    """Required data is not available."""
    pass


def validate_config(config: PDFReportConfig) -> List[str]:
    """Validate configuration before generation."""
    errors = []

    # Calculate total metrics selected across all categories
    total_metrics = (
        len(config.positive_metrics) +
        len(config.average_metrics) +
        len(config.negative_metrics)
    )

    # Note: 0 metrics is now allowed - the report will skip the metrics pages
    # This enables generating reports focused on tactical analysis only

    # Optional: warn if too many metrics (could make report very long)
    if total_metrics > 30:
        errors.append("Troppe metriche selezionate (max 30 consigliato)")

    return errors


def _create_styles():
    """Create custom paragraph styles for the PDF."""
    _register_fonts()
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = FONT_REGULAR

    # Team name (large, centered)
    styles.add(ParagraphStyle(
        'TeamName',
        parent=styles['Title'],
        fontSize=28,
        textColor=PDFColors.PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName=FONT_BOLD,
        leading=34
    ))

    # Manager info
    styles.add(ParagraphStyle(
        'ManagerInfo',
        parent=styles['Normal'],
        fontSize=14,
        textColor=PDFColors.NEUTRAL_600,
        alignment=TA_CENTER,
        spaceAfter=12
    ))

    # Section title
    styles.add(ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=PDFColors.PRIMARY,
        fontName=FONT_BOLD,
        spaceBefore=16,
        spaceAfter=8,
        borderPadding=(0, 0, 4, 0)
    ))

    # Subsection title (compact)
    styles.add(ParagraphStyle(
        'SubsectionTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=PDFColors.NEUTRAL_800,
        fontName=FONT_BOLD,
        spaceBefore=4,
        spaceAfter=4
    ))

    # Timeline cell (compact)
    styles.add(ParagraphStyle(
        'TimelineCell',
        parent=styles['Normal'],
        fontSize=7.0,
        textColor=PDFColors.NEUTRAL_800,
        alignment=TA_CENTER,
        leading=8
    ))

    styles.add(ParagraphStyle(
        'TimelineHeader',
        parent=styles['Normal'],
        fontSize=7.5,
        textColor=PDFColors.NEUTRAL_800,
        alignment=TA_CENTER,
        leading=9,
        fontName=FONT_BOLD
    ))

    # Cluster badge
    styles.add(ParagraphStyle(
        'ClusterBadge',
        parent=styles['Normal'],
        fontSize=12,
        textColor=PDFColors.WHITE,
        alignment=TA_CENTER,
        fontName=FONT_BOLD
    ))

    # Analysis text
    styles.add(ParagraphStyle(
        'AnalysisText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=PDFColors.NEUTRAL_600,
        alignment=TA_JUSTIFY,
        leading=11,
        spaceBefore=4,
        spaceAfter=4
    ))

    # Player card
    styles.add(ParagraphStyle(
        'PlayerName',
        parent=styles['Normal'],
        fontSize=10,
        textColor=PDFColors.NEUTRAL_800,
        fontName=FONT_BOLD
    ))

    styles.add(ParagraphStyle(
        'PlayerDescription',
        parent=styles['Normal'],
        fontSize=9,
        textColor=PDFColors.NEUTRAL_600,
        leading=12
    ))

    # Metric styles
    styles.add(ParagraphStyle(
        'MetricName',
        parent=styles['Normal'],
        fontSize=10,
        textColor=PDFColors.NEUTRAL_800
    ))

    styles.add(ParagraphStyle(
        'MetricValue',
        parent=styles['Normal'],
        fontSize=11,
        textColor=PDFColors.NEUTRAL_800,
        fontName=FONT_BOLD,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        'MetricCardName',
        parent=styles['Normal'],
        fontSize=11,
        textColor=PDFColors.NEUTRAL_800,
        fontName=FONT_BOLD
    ))

    styles.add(ParagraphStyle(
        'MetricRank',
        parent=styles['Normal'],
        fontSize=12,
        textColor=PDFColors.NEUTRAL_800,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        'MetricTitleLarge',
        parent=styles['Normal'],
        fontSize=20,
        textColor=PDFColors.PRIMARY,
        alignment=TA_CENTER,
        fontName=FONT_BOLD,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        'SectionSubtitleSmall',
        parent=styles['Normal'],
        fontSize=9,
        textColor=PDFColors.NEUTRAL_600,
        alignment=TA_CENTER
    ))

    return styles


class PDFReportGenerator:
    """Generate PDF reports for Serie A Analytics using ReportLab."""

    def __init__(
        self,
        config: PDFReportConfig,
        data: Dict[str, Any],
        team_metrics: pd.DataFrame,
        player_metrics: pd.DataFrame,
        logo_base64: Optional[str] = None,
        radar_base64: Optional[str] = None,
        pitch_base64: Optional[str] = None,
        team_analysis: Optional[str] = None,
        player_profiles: Optional[List[Dict]] = None,
        player_names: Optional[Dict[int, str]] = None,
        player_id_to_slot: Optional[Dict[int, int]] = None,
        player_faces: Optional[Dict[int, Any]] = None,
        player_ratings: Optional[Dict[int, float]] = None,
        performances_df: Optional[pd.DataFrame] = None,
        valid_pairs: Optional[set] = None
    ):
        self.config = config
        self.data = data
        self.team_metrics = team_metrics
        self.player_metrics = player_metrics
        self.logo_base64 = logo_base64
        self.radar_base64 = radar_base64
        self.pitch_base64 = pitch_base64
        self.team_analysis = team_analysis
        self.player_profiles = player_profiles or []
        self.player_names = player_names or {}
        self.player_id_to_slot = player_id_to_slot or {}
        self.player_faces = player_faces or {}
        self.player_ratings = player_ratings or {}
        self.performances_df = performances_df
        self.valid_pairs = valid_pairs or set()

        self.styles = _create_styles()
        self.width, self.height = A4
        self.margin = 1.5 * cm

    def generate(self) -> bytes:
        """Generate complete PDF report and return bytes."""
        errors = validate_config(self.config)
        if errors:
            raise DataNotAvailableError(f"Configurazione non valida: {', '.join(errors)}")

        try:
            buffer = io.BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=self.margin,
                rightMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )

            # Build story (list of flowables)
            story = []

            # Page 1: Team Header + Formation + Timeline
            story.extend(self._build_page1())
            story.append(PageBreak())

            # Page 2: Profilo Tattico + Analisi Tattica
            story.extend(self._build_page2())
            story.append(PageBreak())

            # Page 3: Fasi di Gioco (xG e Tiri)
            game_phases_section = self._build_game_phases_page()
            if game_phases_section:
                story.extend(game_phases_section)
                story.append(PageBreak())

            # Page 4: Metrics Summary (skipped if no metrics selected)
            total_metrics = (
                len(self.config.positive_metrics) +
                len(self.config.average_metrics) +
                len(self.config.negative_metrics)
            )
            if total_metrics > 0:
                story.extend(self._build_page3())

            # Positive Contributions (one metric per page)
            positive_pages = self._build_page4()
            if positive_pages:
                story.append(PageBreak())
                story.extend(positive_pages)

            # Average (Nella Media) Contributions (one metric per page)
            average_pages = self._build_page6()
            if average_pages:
                story.append(PageBreak())
                story.extend(average_pages)

            # Negative Contributions (one metric per page)
            negative_pages = self._build_page5()
            if negative_pages:
                story.append(PageBreak())
                story.extend(negative_pages)

            # Last Page: Player Profiles (Analisi Singoli Giocatori)
            player_profiles_section = self._build_player_profiles_section()
            if player_profiles_section:
                story.append(PageBreak())
                story.extend(player_profiles_section)

            doc.build(story)

            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except Exception as e:
            logger.exception("Error generating PDF")
            raise PDFReportError(f"Errore generazione PDF: {str(e)}")

    def _build_page1(self) -> List:
        """Build Page 1: Team Header + Radar + Formation."""
        elements = []

        # Team name
        elements.append(Paragraph(self.config.team_name, self.styles['TeamName']))

        # Logo
        if self.logo_base64:
            try:
                logo_img = self._base64_to_image(self.logo_base64, width=2.5*cm, height=2.5*cm)
                if logo_img:
                    elements.append(logo_img)
            except Exception:
                pass

        # Manager info
        manager_text = f"{self.config.manager_name} ({self.config.matches_count} partite)"
        elements.append(Paragraph(manager_text, self.styles['ManagerInfo']))

        # Cluster badge
        if self.config.cluster_name:
            cluster_table = Table(
                [[Paragraph(f"Stile di Gioco: {self.config.cluster_name}", self.styles['ClusterBadge'])]],
                colWidths=[10*cm]
            )
            cluster_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), PDFColors.PRIMARY),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 16),
                ('RIGHTPADDING', (0, 0), (-1, -1), 16),
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ]))
            elements.append(Spacer(1, 12))
            elements.append(cluster_table)

        elements.append(Spacer(1, 12))

        # Section: Top 3 Formazioni
        top_formations_table = self._build_top_formations_table()
        if top_formations_table:
            elements.append(Paragraph("Top 3 Formazioni", self.styles['SectionTitle']))
            elements.append(top_formations_table)
            elements.append(Spacer(1, 6))

            timeline_table = self._build_formation_timeline_table()
            if timeline_table:
                elements.append(Paragraph("Cronologia ultime 10 Formazioni", self.styles['SubsectionTitle']))
                elements.append(timeline_table)
                elements.append(Spacer(1, 8))

        # Section: Formazione
        elements.append(Paragraph(f"Formazione: {self.config.formation}", self.styles['SectionTitle']))

        # Pitch image (with volti + valori)
        if self.pitch_base64:
            try:
                pitch_img = self._base64_to_image_fit(self.pitch_base64, max_width=15*cm, max_height=10.5*cm)
                if pitch_img:
                    elements.append(pitch_img)
            except Exception:
                elements.append(Paragraph("Formazione non disponibile", self.styles['AnalysisText']))

        return elements

    def _build_formation_timeline_table(self, max_cols: int = 38) -> Optional[Table]:
        """Build a compact formation timeline with weeks on x-axis and formations vertical below."""
        if not self.config.formation_stats:
            return None

        timeline = self.config.formation_stats.get('timeline', [])
        if not timeline:
            return None

        try:
            timeline_sorted = sorted(timeline, key=lambda x: x.get('match_week', 0), reverse=True)
        except Exception:
            timeline_sorted = list(reversed(timeline))

        # Keep only the latest 10 formations (from most recent backwards)
        timeline_sorted = timeline_sorted[:10]

        # Show in chronological order (lowest to highest) for readability
        timeline_sorted = list(reversed(timeline_sorted))

        total_cols = min(max_cols, len(timeline_sorted))
        if total_cols <= 0:
            return None

        # Dynamic font sizing for very dense timelines
        if total_cols >= 30:
            header_size = 5.5
            cell_size = 5.2
            leading = 6
        elif total_cols >= 22:
            header_size = 6.2
            cell_size = 5.8
            leading = 7
        else:
            header_size = 7.0
            cell_size = 6.6
            leading = 8

        header_style = ParagraphStyle(
            'TimelineHeaderDense',
            parent=self.styles['TimelineHeader'],
            fontSize=header_size,
            leading=leading
        )
        cell_style = ParagraphStyle(
            'TimelineCellDense',
            parent=self.styles['TimelineCell'],
            fontSize=cell_size,
            leading=leading
        )

        week_cells = []
        formation_cells = []
        for item in timeline_sorted:
            week = item.get('match_week', '')
            formation = item.get('formation', '')
            week_cells.append(Paragraph(f"G{week}", header_style))
            if formation:
                vertical = "<br/>".join([p for p in formation.split('-') if p])
            else:
                vertical = ""
            formation_cells.append(Paragraph(vertical, cell_style))

        rows = []
        for i in range(0, len(week_cells), total_cols):
            header = week_cells[i:i + total_cols]
            values = formation_cells[i:i + total_cols]
            if len(header) < total_cols:
                header += [''] * (total_cols - len(header))
                values += [''] * (total_cols - len(values))
            rows.append(header)
            rows.append(values)

        if not rows:
            return None

        usable_width = self.width - (2 * self.margin)
        col_width = usable_width / total_cols
        table = Table(rows, colWidths=[col_width] * total_cols)
        style_cmds = [
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('GRID', (0, 0), (-1, -1), 0.4, PDFColors.NEUTRAL_200),
        ]

        # Zebra columns to improve readability
        for row_idx in range(0, len(rows), 2):
            for col_idx in range(total_cols):
                if col_idx % 2 == 0:
                    style_cmds.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx + 1), PDFColors.NEUTRAL_50))

        table.setStyle(TableStyle(style_cmds))

        return table

    def _build_top_formations_table(self) -> Optional[Table]:
        """Build a compact 3-column table for top formations."""
        stats = []
        if self.config.formation_stats:
            stats = (
                self.config.formation_stats.get('formations_all')
                or self.config.formation_stats.get('formations')
                or []
            )

        if not stats:
            return None

        top = stats[:3]
        cells = []
        for item in top:
            formation = item.get('formation', '')
            pct = item.get('percentage', 0)
            cell_text = f"<b>{formation}</b><br/>{pct}%"
            cells.append(Paragraph(cell_text, self.styles['MetricName']))

        while len(cells) < 3:
            cells.append('')

        table = Table([cells], colWidths=[5.2*cm, 5.2*cm, 5.2*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            ('BACKGROUND', (0, 0), (-1, 0), PDFColors.NEUTRAL_100),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.4, PDFColors.NEUTRAL_200),
        ]))

        return table

    def _build_performance_map(self) -> List:
        """Build the Performance Map section with score card and scatterplot."""
        elements = []

        # Check if performances data is available
        if self.performances_df is None or len(self.performances_df) == 0:
            return elements

        # Check required columns
        required_cols = {'team_id', 'manager_id', 'performance_score', 'xg_diff',
                         'field_tilt_diff', 'is_home', 'result'}
        if not required_cols.issubset(set(self.performances_df.columns)):
            return elements

        # Filter for current team+manager
        team_df = self.performances_df[
            (self.performances_df['team_id'] == self.config.team_id) &
            (self.performances_df['manager_id'] == self.config.manager_id)
        ]

        if len(team_df) < 3:
            return elements  # Need at least 3 matches

        # Section title
        elements.append(Paragraph("Mappa Prestazioni", self.styles['SectionTitle']))
        elements.append(Spacer(1, 8))

        # Build score card and scatterplot
        score_card = self._render_performance_score_card(team_df)
        scatter_img = self._render_performance_scatterplot(team_df)

        # Create two-column layout (ratio ~1:2)
        left_cell = score_card if score_card else Paragraph("Dati non disponibili", self.styles['AnalysisText'])
        right_cell = scatter_img if scatter_img else Paragraph("Grafico non disponibile", self.styles['AnalysisText'])

        layout_table = Table(
            [[left_cell, right_cell]],
            colWidths=[5.8*cm, 11.5*cm]
        )
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))

        elements.append(layout_table)

        return elements

    def _render_performance_score_card(self, team_df: pd.DataFrame) -> Optional[Table]:
        """Render the Performance Score Card as a ReportLab Table."""
        import numpy as np

        if len(team_df) == 0:
            return None

        # Calculate statistics (replicating performance_scatterplot.py logic)
        avg_score = team_df['performance_score'].mean()

        # Home/Away split
        home_df = team_df[team_df['is_home'] == True]
        away_df = team_df[team_df['is_home'] == False]
        home_score = home_df['performance_score'].mean() if len(home_df) > 0 else 0
        away_score = away_df['performance_score'].mean() if len(away_df) > 0 else 0

        # Calculate z-score vs valid_pairs
        if self.valid_pairs:
            valid_df = self.performances_df[
                self.performances_df.apply(
                    lambda r: (r['team_id'], r['manager_id']) in self.valid_pairs, axis=1
                )
            ]
        else:
            # Fallback: filter by MIN_MATCHES
            MIN_MATCHES = 5
            match_counts = self.performances_df.groupby(['team_id', 'manager_id']).size()
            valid_combinations = match_counts[match_counts >= MIN_MATCHES].index
            valid_df = self.performances_df[
                self.performances_df.set_index(['team_id', 'manager_id']).index.isin(valid_combinations)
            ]

        all_avgs = valid_df.groupby(['team_id', 'manager_id'])['performance_score'].mean()
        league_mean = all_avgs.mean()
        league_std = all_avgs.std()

        z_score = (avg_score - league_mean) / league_std if league_std > 0 else 0

        # Calculate ranking
        all_avgs_sorted = all_avgs.sort_values(ascending=False)
        total_managers = len(all_avgs_sorted)
        rank = 1
        for (t_id, m_id), _ in all_avgs_sorted.items():
            if t_id == self.config.team_id and m_id == self.config.manager_id:
                break
            rank += 1

        # Z-score color and label
        if z_score > 0.5:
            z_color = '#10b981'  # Green
            z_label = 'Sopra media'
        elif z_score < -0.5:
            z_color = '#ef4444'  # Red
            z_label = 'Sotto media'
        else:
            z_color = '#f59e0b'  # Orange
            z_label = 'Nella media'

        z_sign = '+' if z_score > 0 else ''

        # Results breakdown
        wins = len(team_df[team_df['result'] == 'W'])
        draws = len(team_df[team_df['result'] == 'D'])
        losses = len(team_df[team_df['result'] == 'L'])
        total = len(team_df)
        win_pct = (wins / total * 100) if total > 0 else 0

        # Key metrics
        avg_xg_diff = team_df['xg_diff'].mean()
        avg_tilt_diff = team_df['field_tilt_diff'].mean()

        xg_color = '#10b981' if avg_xg_diff > 0 else '#ef4444' if avg_xg_diff < 0 else '#9ca3af'
        xg_sign = '+' if avg_xg_diff > 0 else ''

        tilt_color = '#10b981' if avg_tilt_diff > 0 else '#ef4444' if avg_tilt_diff < 0 else '#9ca3af'
        tilt_sign = '+' if avg_tilt_diff > 0 else ''

        # Build card content as a table
        # Row 1: Main score
        score_text = Paragraph(
            f"<para align='center'><font size='24' color='white'><b>{avg_score:.1f}</b></font></para>",
            self.styles['Normal']
        )
        score_label = Paragraph(
            f"<para align='center'><font size='8' color='#94a3b8'>Performance Score</font></para>",
            self.styles['Normal']
        )

        # Row 2: Home/Away
        home_away_text = Paragraph(
            f"<para align='center'>"
            f"<font size='7' color='#94a3b8'>Casa</font><br/>"
            f"<font size='12' color='white'><b>{home_score:.1f}</b></font>"
            f"</para>",
            self.styles['Normal']
        )
        away_text = Paragraph(
            f"<para align='center'>"
            f"<font size='7' color='#94a3b8'>Trasferta</font><br/>"
            f"<font size='12' color='white'><b>{away_score:.1f}</b></font>"
            f"</para>",
            self.styles['Normal']
        )

        # Row 3: Comparative evaluation header
        comp_header = Paragraph(
            f"<para align='center'><font size='6' color='#64748b'>VALUTAZIONE COMPARATIVA</font></para>",
            self.styles['Normal']
        )

        # Row 4: Z-score and rank
        z_text = Paragraph(
            f"<para align='center'>"
            f"<font size='14' color='{z_color}'><b>{z_sign}{z_score:.2f}</b></font><br/>"
            f"<font size='6' color='#64748b'>{z_label}</font>"
            f"</para>",
            self.styles['Normal']
        )
        rank_text = Paragraph(
            f"<para align='center'>"
            f"<font size='14' color='white'><b>{rank}°</b></font><br/>"
            f"<font size='6' color='#64748b'>su {total_managers}</font>"
            f"</para>",
            self.styles['Normal']
        )

        # Row 5: Key metrics
        xg_metric = Paragraph(
            f"<para align='center'>"
            f"<font size='6' color='#64748b'>xG Diff</font><br/>"
            f"<font size='10' color='{xg_color}'><b>{xg_sign}{avg_xg_diff:.2f}</b></font>"
            f"</para>",
            self.styles['Normal']
        )
        tilt_metric = Paragraph(
            f"<para align='center'>"
            f"<font size='6' color='#64748b'>Tilt Diff</font><br/>"
            f"<font size='10' color='{tilt_color}'><b>{tilt_sign}{avg_tilt_diff:.1f}%</b></font>"
            f"</para>",
            self.styles['Normal']
        )
        win_metric = Paragraph(
            f"<para align='center'>"
            f"<font size='6' color='#64748b'>Win %</font><br/>"
            f"<font size='10' color='white'><b>{win_pct:.0f}%</b></font>"
            f"</para>",
            self.styles['Normal']
        )

        # Row 6: Results breakdown
        results_text = Paragraph(
            f"<para align='center'>"
            f"<font size='9' color='#10b981'><b>{wins}V</b></font> "
            f"<font size='9' color='#9ca3af'><b>{draws}N</b></font> "
            f"<font size='9' color='#ef4444'><b>{losses}P</b></font> "
            f"<font size='8' color='#64748b'>({total})</font>"
            f"</para>",
            self.styles['Normal']
        )

        # Build the table structure
        data = [
            [score_text],
            [score_label],
            [Table([[home_away_text, away_text]], colWidths=[2.6*cm, 2.6*cm])],
            [comp_header],
            [Table([[z_text, rank_text]], colWidths=[2.6*cm, 2.6*cm])],
            [Table([[xg_metric, tilt_metric, win_metric]], colWidths=[1.7*cm, 1.7*cm, 1.7*cm])],
            [results_text],
        ]

        card_table = Table(data, colWidths=[5.5*cm])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PDFColors.CARD_BG),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            # Top rounded corners simulation with border
            ('BOX', (0, 0), (-1, -1), 0.5, PDFColors.CARD_BG_LIGHT),
            # Divider lines
            ('LINEBELOW', (0, 2), (-1, 2), 0.5, colors.HexColor('#475569')),
            ('LINEBELOW', (0, 4), (-1, 4), 0.5, colors.HexColor('#475569')),
        ]))

        return card_table

    def _render_performance_scatterplot(
        self,
        team_df: pd.DataFrame,
        width: float = 11*cm,
        height: float = 7.5*cm
    ) -> Optional[Image]:
        """Render the Performance Scatterplot using Matplotlib."""
        try:
            import numpy as np
            import matplotlib.pyplot as plt
        except ImportError:
            return None

        if len(team_df) == 0:
            return None

        # Result colors
        RESULT_COLORS = {'W': '#10b981', 'D': '#9ca3af', 'L': '#ef4444'}
        RESULT_LABELS = {'W': 'Vittoria', 'D': 'Pareggio', 'L': 'Sconfitta'}

        # Calculate axis ranges
        x_vals = team_df['xg_diff'].values
        y_vals = team_df['field_tilt_diff'].values

        x_abs_max = max(abs(x_vals.min()), abs(x_vals.max()), 0.5) * 1.3
        y_abs_max = max(abs(y_vals.min()), abs(y_vals.max()), 5) * 1.3

        # Create figure
        width_in = width / 72  # points to inches
        height_in = height / 72
        fig, ax = plt.subplots(figsize=(width_in, height_in), facecolor='white')

        # Draw quadrant backgrounds
        # Q1: Top-right (green) - Prestazione Positiva
        ax.fill([0, x_abs_max, x_abs_max, 0], [0, 0, y_abs_max, y_abs_max],
                color='#10b981', alpha=0.15)
        # Q2: Top-left (yellow) - Dominio Sterile
        ax.fill([-x_abs_max, 0, 0, -x_abs_max], [0, 0, y_abs_max, y_abs_max],
                color='#fbbf24', alpha=0.15)
        # Q3: Bottom-left (red) - Prestazione Negativa
        ax.fill([-x_abs_max, 0, 0, -x_abs_max], [-y_abs_max, -y_abs_max, 0, 0],
                color='#ef4444', alpha=0.15)
        # Q4: Bottom-right (blue) - Pragmatismo
        ax.fill([0, x_abs_max, x_abs_max, 0], [-y_abs_max, -y_abs_max, 0, 0],
                color='#3b82f6', alpha=0.15)

        # Draw axis lines at 0
        ax.axhline(y=0, color='#6b7280', linestyle='--', linewidth=1, alpha=0.7)
        ax.axvline(x=0, color='#6b7280', linestyle='--', linewidth=1, alpha=0.7)

        # Plot scatter points for each result type
        for result in ['W', 'D', 'L']:
            result_df = team_df[team_df['result'] == result]
            if len(result_df) > 0:
                ax.scatter(
                    result_df['xg_diff'],
                    result_df['field_tilt_diff'],
                    c=RESULT_COLORS[result],
                    s=60,
                    edgecolors='white',
                    linewidths=1,
                    label=RESULT_LABELS[result],
                    zorder=3
                )

        # Add quadrant labels
        label_offset_x = x_abs_max * 0.65
        label_offset_y = y_abs_max * 0.85
        ax.text(label_offset_x, label_offset_y, 'Prestazione Positiva',
                fontsize=7, color='#6b7280', alpha=0.6, ha='center')
        ax.text(-label_offset_x, label_offset_y, 'Dominio Sterile',
                fontsize=7, color='#6b7280', alpha=0.6, ha='center')
        ax.text(-label_offset_x, -label_offset_y, 'Prestazione Negativa',
                fontsize=7, color='#6b7280', alpha=0.6, ha='center')
        ax.text(label_offset_x, -label_offset_y, 'Pragmatismo',
                fontsize=7, color='#6b7280', alpha=0.6, ha='center')

        # Set axis limits and labels
        ax.set_xlim(-x_abs_max, x_abs_max)
        ax.set_ylim(-y_abs_max, y_abs_max)
        ax.set_xlabel('xG - xGA', fontsize=9)
        ax.set_ylabel('Diff. Field Tilt', fontsize=9)

        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))

        # Add legend at top
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=3,
                  fontsize=8, frameon=False)

        # Grid
        ax.grid(True, alpha=0.2)
        ax.set_facecolor('white')

        # Tight layout
        plt.tight_layout()

        # Save to buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)

        return Image(buf, width=width, height=height)

    def _build_page2(self) -> List:
        """Build Page 2: Profilo Tattico + Analisi Tattica."""
        elements = []

        # Section: Profilo Tattico
        elements.append(Paragraph("Profilo Tattico Squadra", self.styles['SectionTitle']))
        if self.radar_base64:
            try:
                radar_img = self._base64_to_image(self.radar_base64, width=8*cm, height=8*cm)
                if radar_img:
                    elements.append(radar_img)
            except Exception:
                elements.append(Paragraph("Radar chart non disponibile", self.styles['AnalysisText']))

        elements.append(Spacer(1, 2))

        # Section: Analisi Tattica
        elements.append(Paragraph("Analisi Tattica Squadra", self.styles['SectionTitle']))

        analysis_text = self.team_analysis or "Analisi tattica non disponibile. Genera l'analisi dalla dashboard."
        # Convert markdown to HTML for ReportLab rendering
        analysis_html = markdown_to_html(analysis_text)
        elements.append(Paragraph(analysis_html, self.styles['AnalysisText']))

        # Section: Mappa Prestazioni
        performance_map_elements = self._build_performance_map()
        if performance_map_elements:
            elements.append(Spacer(1, 16))
            elements.extend(performance_map_elements)

        return elements

    def _build_game_phases_page(self) -> List:
        """Build Game Phases page with xG and Shots bar charts."""
        elements = []

        total_combinations = len(self.data.get('combinations', []))
        if total_combinations == 0:
            return elements

        # Page title
        elements.append(Paragraph("Fasi di Gioco", self.styles['SectionTitle']))
        elements.append(Spacer(1, 6))

        # Legend
        legend_text = (
            "<font color='#22c55e'>■</font> Top 25% · "
            "<font color='#9ca3af'>■</font> Media · "
            "<font color='#ef4444'>■</font> Bottom 25%"
        )
        elements.append(Paragraph(legend_text, self.styles['AnalysisText']))
        elements.append(Spacer(1, 12))

        # xG Section
        elements.append(Paragraph("<b>Expected Goals (xG)</b>", self.styles['SubsectionTitle']))
        elements.append(Spacer(1, 4))
        xg_table = self._build_game_phases_table("xg_", total_combinations)
        if xg_table:
            elements.append(xg_table)
        elements.append(Spacer(1, 16))

        # Shots Section
        elements.append(Paragraph("<b>Tiri</b>", self.styles['SubsectionTitle']))
        elements.append(Spacer(1, 4))
        shots_table = self._build_game_phases_table("shots_", total_combinations)
        if shots_table:
            elements.append(shots_table)
        elements.append(Spacer(1, 12))

        # Footer caption
        caption = f"Ranking su {total_combinations} squadre · Creati: rank alto = più creati · Subiti: rank alto = meno subiti"
        elements.append(Paragraph(caption, self.styles['AnalysisText']))

        return elements

    def _build_game_phases_table(self, prefix: str, total: int) -> Optional[Table]:
        """Build a table with horizontal bars for game phases."""
        # Header row
        data = [['Fase', 'Creati', '#', 'Subiti', '#']]

        for phase in GAME_PHASES:
            creation_metric = f"{prefix}{phase}"
            conceded_metric = f"{prefix}conceded_{phase}"

            creation_data = self._get_phase_metric_data(creation_metric, total)
            conceded_data = self._get_phase_metric_data(conceded_metric, total)

            # Create bar cells
            creation_bar = self._render_pdf_progress_bar(
                creation_data['bar_value'],
                creation_data['color'],
                width=4.5*cm
            )
            conceded_bar = self._render_pdf_progress_bar(
                conceded_data['bar_value'],
                conceded_data['color'],
                width=4.5*cm
            )

            creation_rank = Paragraph(
                f"<font color='{creation_data['color']}'><b>#{creation_data['rank']}</b></font>",
                self.styles['MetricRank']
            )
            conceded_rank = Paragraph(
                f"<font color='{conceded_data['color']}'><b>#{conceded_data['rank']}</b></font>",
                self.styles['MetricRank']
            )

            data.append([
                PHASE_NAMES.get(phase, phase),
                creation_bar,
                creation_rank,
                conceded_bar,
                conceded_rank,
            ])

        table = Table(data, colWidths=[3.5*cm, 5*cm, 1.5*cm, 5*cm, 1.5*cm])

        style_cmds = [
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), PDFColors.NEUTRAL_100),
            ('TEXTCOLOR', (0, 0), (-1, 0), PDFColors.NEUTRAL_800),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),

            # Alignment
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.4, PDFColors.NEUTRAL_200),

            # Vertical separator between Creati and Subiti
            ('LINEAFTER', (2, 0), (2, -1), 1.5, PDFColors.NEUTRAL_200),
        ]

        # Zebra rows
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), PDFColors.NEUTRAL_50))

        table.setStyle(TableStyle(style_cmds))
        return table

    def _get_phase_metric_data(self, metric_name: str, total: int) -> dict:
        """Get data for a single game phase metric."""
        metric_row = self.team_metrics[self.team_metrics['metric_name'] == metric_name]

        if len(metric_row) > 0:
            row = metric_row.iloc[0]
            rank = int(row.get('metric_rank', 0)) or total
            bar_value = (total - rank + 1) / total if total > 0 else 0
            return {
                'rank': rank,
                'bar_value': bar_value,
                'color': self._get_phase_color(rank, total),
                'value_p90': row.get('metric_value_p90', 0) or 0,
            }
        else:
            return {
                'rank': 0,
                'bar_value': 0,
                'color': '#9ca3af',
                'value_p90': 0,
            }

    def _get_phase_color(self, rank: int, total: int) -> str:
        """Determine bar color based on ranking percentile."""
        if total == 0 or rank == 0:
            return '#9ca3af'  # Grey

        percentile = (total - rank + 1) / total

        if percentile >= 0.75:
            return '#22c55e'  # Green - Top 25%
        elif percentile <= 0.25:
            return '#ef4444'  # Red - Bottom 25%
        else:
            return '#9ca3af'  # Grey - Average

    def _render_pdf_progress_bar(self, value: float, color: str, width: float = 4*cm) -> Drawing:
        """Render a horizontal progress bar as a ReportLab Drawing."""
        bar_height = 14
        drawing = Drawing(width, bar_height)

        # Background bar (grey)
        bg_rect = Rect(0, 0, width, bar_height, fillColor=PDFColors.NEUTRAL_200, strokeColor=None)
        drawing.add(bg_rect)

        # Progress bar (colored)
        bar_width = max(width * 0.05, width * value)  # Minimum 5% for visibility
        bar_rect = Rect(0, 0, bar_width, bar_height, fillColor=colors.HexColor(color), strokeColor=None)
        drawing.add(bar_rect)

        return drawing

    def _build_player_profiles_section(self) -> List:
        """Build player profiles section starting from page 3.

        Returns empty list if no player profiles are available,
        so the section is completely skipped in the PDF.
        """
        # Skip section entirely if no player profiles
        if not self.player_profiles:
            return []

        elements = []
        elements.append(Paragraph("Analisi Singoli Giocatori", self.styles['SectionTitle']))

        for profile in self.player_profiles:
            player_elements = self._build_player_card(profile)
            elements.append(KeepTogether(player_elements))
            elements.append(Spacer(1, 6))

        return elements

    def _build_player_card(self, profile: Dict) -> List:
        """Build a player profile card."""
        elements = []

        surname = profile.get('surname', 'Unknown')
        position = profile.get('position_it', '')
        archetype = profile.get('archetype', '')
        description = profile.get('description', '')

        # Header row: Name | Position | Archetype
        header_text = f"<b>{surname}</b>"
        if position:
            header_text += f" <font color='#6b7280'>({position})</font>"
        if archetype:
            header_text += f" - <i>{archetype}</i>"

        elements.append(Paragraph(header_text, self.styles['PlayerName']))

        if description:
            elements.append(Paragraph(description, self.styles['PlayerDescription']))

        return elements

    def _build_page3(self) -> List:
        """Build Page 3: Metrics Summary - includes Positive, Average (Nella Media), and Negative."""
        from components.metrics_panel import METRIC_NAMES

        elements = []

        elements.append(Paragraph("Metriche Chiave", self.styles['SectionTitle']))
        elements.append(Spacer(1, 8))

        total_combinations = len(self.data.get('combinations', []))

        # Prepare data for all three categories
        positive_data = self._prepare_metrics_data(self.config.positive_metrics, METRIC_NAMES, True)
        average_data = self._prepare_metrics_data(self.config.average_metrics, METRIC_NAMES, True)
        negative_data = self._prepare_metrics_data(self.config.negative_metrics, METRIC_NAMES, False)

        # Positive metrics cards (green)
        if positive_data:
            elements.append(Paragraph("<font color='#065f46'><b>Punti di Forza</b></font>", self.styles['MetricName']))
            elements.append(Spacer(1, 6))
            elements.extend(self._build_metric_cards(positive_data, total_combinations, metric_type="positive"))
            elements.append(Spacer(1, 12))

        # Average metrics cards (orange) - "Nella Media"
        if average_data:
            elements.append(Paragraph("<font color='#b45309'><b>Nella Media</b></font>", self.styles['MetricName']))
            elements.append(Spacer(1, 6))
            elements.extend(self._build_metric_cards(average_data, total_combinations, metric_type="average"))
            elements.append(Spacer(1, 12))

        # Negative metrics cards (red)
        if negative_data:
            elements.append(Paragraph("<font color='#991b1b'><b>Punti Deboli</b></font>", self.styles['MetricName']))
            elements.append(Spacer(1, 6))
            elements.extend(self._build_metric_cards(negative_data, total_combinations, metric_type="negative"))

        return elements

    def _build_metric_cards(self, metrics_data: List[Dict], total: int, metric_type: str = "positive") -> List:
        """Build metric cards with distribution charts.

        Args:
            metric_type: "positive" (green), "average" (orange), or "negative" (red)
        """
        elements = []
        for metric in metrics_data:
            card = self._build_metric_card(metric, total, metric_type)
            elements.append(card)
            elements.append(Spacer(1, 6))
        return elements

    def _build_metric_card(self, metric: Dict, total: int, metric_type: str = "positive") -> Table:
        """Build a single metric card row.

        Args:
            metric_type: "positive" (green), "average" (orange), or "negative" (red)
        """
        metric_key = metric.get('metric_key', '')
        name = metric.get('name', '')
        value = metric.get('value', 0)
        rank = metric.get('rank', 0)

        # Color selection based on metric type
        if metric_type == "positive":
            color_main = PDFColors.STRENGTH_MAIN
            color_fill = PDFColors.STRENGTH_BG
        elif metric_type == "average":
            color_main = PDFColors.AVERAGE_MAIN
            color_fill = PDFColors.AVERAGE_BG
        else:  # negative
            color_main = PDFColors.WEAKNESS_MAIN
            color_fill = PDFColors.WEAKNESS_BG

        name_par = Paragraph(name, self.styles['MetricCardName'])

        # Distribution chart
        distribution_values = self._get_metric_distribution(metric_key)
        lower_is_better = self._is_lower_better(metric_key)
        chart_img = self._render_metric_distribution_image(
            distribution_values,
            selected_value=value,
            color=color_main,
            lower_is_better=lower_is_better,
            width=6.0*cm,
            height=1.4*cm,
            seed_key=metric_key
        )

        chart_cell = chart_img if chart_img else ''

        value_par = Paragraph(
            f"<para align='center'><font size='11' color='white'><b>{value:.2f}</b></font><br/>"
            f"<font size='7' color='white'>p90</font></para>",
            self.styles['MetricValue']
        )

        rank_par = Paragraph(
            f"<para align='center'><font size='12'><b>#{rank}</b></font>"
            f"<font size='8' color='#6b7280'>/{total}</font></para>",
            self.styles['MetricRank']
        )

        data = [[name_par, chart_cell, value_par, rank_par]]
        table = Table(data, colWidths=[5.5*cm, 6.5*cm, 2.2*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (3, 0), 'CENTER'),

            ('BACKGROUND', (0, 0), (-1, -1), PDFColors.WHITE),
            ('BOX', (0, 0), (-1, -1), 0.6, PDFColors.NEUTRAL_200),

            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

            ('BACKGROUND', (2, 0), (2, 0), color_main),
            ('TEXTCOLOR', (2, 0), (2, 0), PDFColors.WHITE),
        ]))

        return table

    def _build_metrics_table(self, metrics_data: List[Dict], total: int, is_positive: bool) -> Table:
        """Build a styled metrics table."""
        # Header
        data = [['Metrica', 'Valore', 'Rank']]

        for m in metrics_data:
            rank_str = f"#{m['rank']}/{total}"
            data.append([
                m['name'],
                f"{m['value']:.2f}",
                rank_str
            ])

        table = Table(data, colWidths=[9*cm, 3.5*cm, 3.5*cm])

        # Styling
        bg_color = PDFColors.STRENGTH_BG if is_positive else PDFColors.WEAKNESS_BG
        border_color = PDFColors.STRENGTH_MAIN if is_positive else PDFColors.WEAKNESS_MAIN
        text_color = PDFColors.STRENGTH_DARK if is_positive else PDFColors.WEAKNESS_DARK

        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), PDFColors.NEUTRAL_100),
            ('TEXTCOLOR', (0, 0), (-1, 0), PDFColors.NEUTRAL_800),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), bg_color),
            ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),

            # Alignment
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Left border accent
            ('LINEBEFOREBCOLOR', (0, 1), (0, -1), border_color),
            ('LINEBEFOREBWIDTH', (0, 1), (0, -1), 3),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, PDFColors.NEUTRAL_200),
        ]))

        return table

    def _build_page4(self) -> List:
        """Build Positive Contributions pages (one metric per page)."""
        return self._build_contribution_pages(
            self.config.positive_detail_metrics,
            metric_type="positive",
            section_title="Dettaglio Contributi - Punti di Forza"
        )

    def _build_page5(self) -> List:
        """Build Negative Contributions pages (one metric per page)."""
        return self._build_contribution_pages(
            self.config.negative_detail_metrics,
            metric_type="negative",
            section_title="Dettaglio Contributi - Punti Deboli"
        )

    def _build_page6(self) -> List:
        """Build Average (Nella Media) Contributions pages (one metric per page)."""
        return self._build_contribution_pages(
            self.config.average_detail_metrics,
            metric_type="average",
            section_title="Dettaglio Contributi - Nella Media"
        )

    def _build_contribution_pages(
        self,
        metric_names: List[str],
        metric_type: str = "positive",
        section_title: str = ""
    ) -> List:
        """Build contribution pages (one metric per page).

        Args:
            metric_type: "positive" (green), "average" (orange), or "negative" (red)
        """
        from components.metrics_panel import METRIC_NAMES

        elements = []

        if not metric_names:
            return elements

        contributions = self._prepare_contributions_data(metric_names, METRIC_NAMES)

        if not contributions:
            return elements

        for idx, contrib in enumerate(contributions):
            elements.extend(self._build_contribution_metric_page(contrib, metric_type, section_title))
            if idx < len(contributions) - 1:
                elements.append(PageBreak())

        return elements

    def _build_contribution_metric_page(self, contrib: Dict, metric_type: str, section_title: str) -> List:
        """Build a single metric contribution page."""
        elements = []

        # Small section subtitle to preserve context
        elements.append(Paragraph(section_title, self.styles['SectionSubtitleSmall']))

        # Large centered metric title with normalization
        norm_label = self._get_metric_normalization_label(contrib['metric_key'])
        title_html = (
            f"<b>{contrib['metric_name']}</b> "
            f"<font size='12' color='#6b7280'>({norm_label})</font>"
        )
        elements.append(Paragraph(title_html, self.styles['MetricTitleLarge']))
        elements.append(Spacer(1, 6))

        # Tables row: Team ranking | Player contributions
        team_table = self._build_team_ranking_table(contrib['metric_key'], max_rows=17)
        players_table = self._build_players_contribution_table(contrib['players'], max_rows=17)

        left_cell = team_table or Paragraph("Classifica non disponibile.", self.styles['AnalysisText'])
        right_cell = players_table or Paragraph("Contributi non disponibili.", self.styles['AnalysisText'])

        tables_layout = Table(
            [[left_cell, right_cell]],
            colWidths=[8.7*cm, 8.7*cm]
        )
        tables_layout.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(tables_layout)
        elements.append(Spacer(1, 8))

        # Pitch title
        elements.append(Paragraph("Mappa Contributi sul Campo", self.styles['SubsectionTitle']))
        elements.append(Spacer(1, 2))

        # Large pitch, centered
        pitch_img = None
        pitch_base64 = self._build_metric_pitch_base64(contrib['metric_key'], width=900, height=650)
        if pitch_base64:
            pitch_img = self._base64_to_image_fit(pitch_base64, max_width=17.5*cm, max_height=10.5*cm)

        if pitch_img:
            pitch_table = Table([[pitch_img]], colWidths=[self.width - 2*self.margin])
            pitch_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(pitch_table)
        else:
            elements.append(Paragraph("Campo non disponibile.", self.styles['AnalysisText']))

        return elements

    def _build_contribution_metric_block(self, contrib: Dict, is_positive: bool) -> List:
        """Build a compact block with team ranking, player ranking, and pitch."""
        elements = []

        color = '#065f46' if is_positive else '#991b1b'
        elements.append(Paragraph(
            f"<font color='{color}'><b>{contrib['metric_name']}</b></font>",
            self.styles['MetricName']
        ))
        elements.append(Spacer(1, 4))

        left_flowables = []
        left_flowables.append(Paragraph("Classifica Squadra + Allenatore", self.styles['SubsectionTitle']))
        team_table = self._build_team_ranking_table(contrib['metric_key'])
        if team_table:
            left_flowables.append(team_table)
        else:
            left_flowables.append(Paragraph("Classifica non disponibile.", self.styles['AnalysisText']))

        left_flowables.append(Spacer(1, 6))
        left_flowables.append(Paragraph("Contributo Giocatori", self.styles['SubsectionTitle']))
        players_table = self._build_contributions_table(
            contrib['players'],
            is_positive,
            col_widths=[1.2*cm, 6.2*cm, 2.0*cm],
            font_size=8
        )
        left_flowables.append(players_table)

        left_block = left_flowables

        pitch_img = None
        pitch_base64 = self._build_metric_pitch_base64(contrib['metric_key'])
        if pitch_base64:
            pitch_img = self._base64_to_image_fit(pitch_base64, max_width=8.2*cm, max_height=6.6*cm)

        right_block = pitch_img or Paragraph("Campo non disponibile.", self.styles['AnalysisText'])

        layout_table = Table(
            [[left_block, right_block]],
            colWidths=[9.2*cm, 8.4*cm]
        )
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(layout_table)
        return elements

    def _build_team_ranking_table(self, metric_name: str, max_rows: int = 17) -> Optional[Table]:
        """Build a compact team+manager ranking table for a metric."""
        ranking_rows = self._prepare_team_ranking_data(metric_name, max_rows=max_rows)
        if not ranking_rows:
            return None

        data = [['#', 'Squadra (Allenatore)', 'Valore']]
        for row in ranking_rows:
            data.append([
                str(row['rank']),
                row['label'],
                f"{row['value']:.2f}"
            ])

        table = Table(data, colWidths=[1.1*cm, 5.4*cm, 2.0*cm])

        style_commands = [
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            ('BACKGROUND', (0, 0), (-1, 0), PDFColors.NEUTRAL_100),
            ('TEXTCOLOR', (0, 0), (-1, 0), PDFColors.NEUTRAL_800),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('TOPPADDING', (0, 0), (-1, 0), 4),

            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 1),
            ('TOPPADDING', (0, 1), (-1, -1), 1),

            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            ('GRID', (0, 0), (-1, -1), 0.4, PDFColors.NEUTRAL_200),
        ]

        for i, row in enumerate(ranking_rows, start=1):
            row_bg = PDFColors.NEUTRAL_50 if i % 2 == 0 else PDFColors.WHITE
            style_commands.append(('BACKGROUND', (0, i), (-1, i), row_bg))
            if row.get('is_current'):
                style_commands.append(('BACKGROUND', (0, i), (-1, i), PDFColors.HIGHLIGHT))
                style_commands.append(('FONTNAME', (0, i), (-1, i), FONT_BOLD))

        table.setStyle(TableStyle(style_commands))
        return table

    def _build_players_contribution_table(self, players: List[Dict], max_rows: int = 17) -> Optional[Table]:
        """Build player contributions table with site-like color scale."""
        if not players:
            return None

        players = players[:max_rows]
        max_contribution = max((p.get('contribution', 0) for p in players), default=1)

        data = [['#', 'Giocatore', 'Contributo']]
        for p in players:
            data.append([
                str(p.get('rank', '')),
                p.get('surname', ''),
                f"{p.get('contribution', 0):.1f}%"
            ])

        table = Table(data, colWidths=[1.1*cm, 5.2*cm, 2.2*cm])

        style_cmds = [
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            ('BACKGROUND', (0, 0), (-1, 0), PDFColors.NEUTRAL_100),
            ('TEXTCOLOR', (0, 0), (-1, 0), PDFColors.NEUTRAL_800),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('TOPPADDING', (0, 0), (-1, 0), 4),

            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 1),
            ('TOPPADDING', (0, 1), (-1, -1), 1),

            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.4, PDFColors.NEUTRAL_200),
        ]

        for i, p in enumerate(players, start=1):
            contribution = p.get('contribution', 0)
            ratio = contribution / max_contribution if max_contribution > 0 else 0

            # Gradient: red (high) -> blue (low)
            r = int(220 - (220 - 13) * (1 - ratio))
            g = int(53 + (110 - 53) * (1 - ratio))
            b = int(69 + (253 - 69) * (1 - ratio))

            # Light background tint
            bg_r = int(r + (255 - r) * 0.85)
            bg_g = int(g + (255 - g) * 0.85)
            bg_b = int(b + (255 - b) * 0.85)

            bg_color = colors.Color(bg_r / 255, bg_g / 255, bg_b / 255)
            accent_color = colors.Color(r / 255, g / 255, b / 255)

            style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg_color))
            style_cmds.append(('LINEBEFORE', (0, i), (0, i), 3, accent_color))

        table.setStyle(TableStyle(style_cmds))
        return table

    def _prepare_team_ranking_data(self, metric_name: str, max_rows: int = 8) -> List[Dict]:
        """Prepare team+manager ranking rows for a metric."""
        all_team_metrics = self.data.get('team_metrics')
        if all_team_metrics is None or len(all_team_metrics) == 0:
            return []

        metric_data = all_team_metrics[all_team_metrics['metric_name'] == metric_name].copy()
        if len(metric_data) == 0:
            return []

        if 'metric_rank' in metric_data.columns:
            metric_data = metric_data.sort_values('metric_rank')
        else:
            metric_data = metric_data.sort_values('metric_value_p90', ascending=False)

        # Build label map from combinations
        labels = {}
        combinations = self.data.get('combinations')
        if combinations is not None and len(combinations) > 0:
            try:
                from utils.data_helpers import extract_surname
            except Exception:
                extract_surname = None
            for _, row in combinations.iterrows():
                manager_name = row.get('manager_name', '')
                if extract_surname:
                    manager_label = extract_surname(manager_name)
                else:
                    manager_label = manager_name.split()[-1] if manager_name else ""
                label = row.get('team_name', f"Team {row.get('team_id')}")
                if manager_label:
                    label = f"{label} ({manager_label})"
                labels[(row.get('team_id'), row.get('manager_id'))] = label

        rows = []
        current_key = (self.config.team_id, self.config.manager_id)
        for idx, (_, row) in enumerate(metric_data.iterrows(), 1):
            team_id = row.get('team_id')
            manager_id = row.get('manager_id')
            label = labels.get((team_id, manager_id), f"Team {team_id} ({manager_id})")
            rank_val = row.get('metric_rank', idx)
            try:
                rank = int(rank_val)
            except Exception:
                rank = idx
            value = row.get('metric_value_p90', 0) or 0
            rows.append({
                'rank': rank,
                'label': label,
                'value': value,
                'is_current': (team_id, manager_id) == current_key
            })

        top_rows = rows[:max_rows]
        if not any(r['is_current'] for r in top_rows):
            current_row = next((r for r in rows if r['is_current']), None)
            if current_row:
                if len(top_rows) >= max_rows:
                    top_rows[-1] = current_row
                else:
                    top_rows.append(current_row)

        return top_rows

    def _build_metric_pitch_base64(
        self,
        metric_name: str,
        width: int = 520,
        height: int = 400
    ) -> Optional[str]:
        """Render formation pitch with contribution values for a specific metric."""
        if not self.player_id_to_slot:
            return None

        metric_players = self.player_metrics[
            (self.player_metrics['team_id'] == self.config.team_id) &
            (self.player_metrics['manager_id'] == self.config.manager_id) &
            (self.player_metrics['metric_name'] == metric_name)
        ]

        if len(metric_players) == 0:
            return None

        slot_values = {}
        for _, row in metric_players.iterrows():
            player_id = row.get('player_id')
            slot = self.player_id_to_slot.get(player_id)
            if slot is not None:
                slot_values[slot] = row.get('contribution_percentage', 0)

        if not slot_values:
            return None

        try:
            from components.pitch import render_formation_to_base64
            return render_formation_to_base64(
                self.config.formation,
                player_names=self.player_names,
                player_values=slot_values,
                player_faces=self.player_faces,
                show_ratings=False,
                width=width,
                height=height
            )
        except Exception:
            return None

    def _build_contributions_table(
        self,
        players: List[Dict],
        is_positive: bool,
        col_widths: Optional[List[float]] = None,
        font_size: int = 9
    ) -> Table:
        """Build a player contributions table."""
        data = [['#', 'Giocatore', 'Contributo']]

        for p in players:
            data.append([
                str(p['rank']),
                p['surname'],
                f"{p['contribution']:.1f}%"
            ])

        table = Table(data, colWidths=col_widths or [1.5*cm, 9*cm, 3*cm])

        bg_color = PDFColors.STRENGTH_BG if is_positive else PDFColors.WEAKNESS_BG
        text_color = PDFColors.STRENGTH_DARK if is_positive else PDFColors.WEAKNESS_DARK

        style_commands = [
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), PDFColors.NEUTRAL_100),
            ('TEXTCOLOR', (0, 0), (-1, 0), PDFColors.NEUTRAL_800),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), font_size),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),

            # Data
            ('FONTSIZE', (0, 1), (-1, -1), font_size),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),

            # Alignment
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, PDFColors.NEUTRAL_200),
        ]

        # Alternate row colors
        for i in range(1, len(data)):
            row_bg = bg_color if i % 2 == 1 else PDFColors.WHITE
            style_commands.append(('BACKGROUND', (0, i), (-1, i), row_bg))
            style_commands.append(('TEXTCOLOR', (0, i), (-1, i), text_color))

        table.setStyle(TableStyle(style_commands))

        return table

    def _get_metric_distribution(self, metric_name: str) -> List[float]:
        """Get distribution values for a metric across all team+manager combinations."""
        all_team_metrics = self.data.get('team_metrics')
        if all_team_metrics is None or len(all_team_metrics) == 0:
            return []
        metric_rows = all_team_metrics[all_team_metrics['metric_name'] == metric_name]
        if len(metric_rows) == 0:
            return []
        values = metric_rows['metric_value_p90'].dropna().tolist()
        return values

    def _get_metric_normalization_label(self, metric_name: str) -> str:
        """Return normalization label for metric (without parentheses)."""
        metric_normalizations = {
            # Percentage metrics
            'goal_conversion_rate': '%',
            'goal_conversion_sot': '%',
            'big_chances_conversion': '%',
            'possession_percentage': '%',
            'buildup_progressive_ratio': '%',
            'buildup_success_rate': '%',
            'pressing_success_rate': '%',

            # Per 100 opponent passes in defensive third
            'tackles': 'per 100 pass. avv. in dif.',
            'interceptions': 'per 100 pass. avv. in dif.',
            'clearances': 'per 100 pass. avv. in dif.',
            'blocks': 'per 100 pass. avv. in dif.',
            'ground_duels_defensive': 'per 100 pass. avv. in dif.',
            'opp_passes_def_third': 'per 90 min',

            # Per 100 long passes (aerial duels)
            'aerial_duels_offensive': 'per 100 lanci nostri',
            'aerial_duels_defensive': 'per 100 lanci avv.',
            'aerial_duels_open_play': 'per 90 min',
            'aerial_duels_set_pieces': 'per 90 min',

            # Per 100 lost balls
            'ground_duels_offensive': 'per 100 palle perse',

            # Per corners/set pieces
            'sot_per_100_corners': 'per 100 corner',
            'sot_per_100_indirect_sp': 'per 100 palle inattive',

            # PPDA (ratio)
            'ppda': 'tasso',

            # Per touch
            'turnovers_per_touch': 'per tocco',
            'shots_per_box_touch': 'per tocco in area',

            # xA per key pass
            'xa_per_key_pass': 'per pass. chiave',
            'goals_per_xa': 'gol per xA',

            # Difference metrics
            'xg_goals_difference': 'differenza',
            'xga_difference': 'differenza',
        }

        norm = metric_normalizations.get(metric_name, 'per 90 min')
        if norm == '%':
            return '%'
        return norm

    def _is_lower_better(self, metric_name: str) -> bool:
        """Check if lower values are better for a metric."""
        from utils.constants import LOWER_IS_BETTER_METRICS
        return metric_name in LOWER_IS_BETTER_METRICS

    def _render_metric_distribution_image(
        self,
        values: List[float],
        selected_value: Optional[float],
        color: colors.Color,
        lower_is_better: bool,
        width: float,
        height: float,
        seed_key: str = ""
    ) -> Optional[Image]:
        """Render a compact scatter + half-violin distribution chart."""
        if not values:
            return None

        try:
            import numpy as np
            import matplotlib.pyplot as plt
        except Exception:
            return None

        values_np = np.array(values, dtype=float)
        if values_np.size == 0:
            return None

        vmin = float(np.min(values_np))
        vmax = float(np.max(values_np))
        span = max(vmax - vmin, 1e-6)
        pad = span * 0.08

        # Simple KDE without SciPy
        grid = np.linspace(vmin - pad, vmax + pad, 120)
        std = float(np.std(values_np)) if values_np.size > 1 else span
        bw = max(std * 0.35, span / 12, 1e-6)

        diff = grid[:, None] - values_np[None, :]
        density = np.exp(-0.5 * (diff / bw) ** 2).sum(axis=1)
        density = density / (values_np.size * bw * np.sqrt(2 * np.pi))
        if density.max() > 0:
            density = density / density.max()
        density = density * 0.32

        # Convert ReportLab color to hex (strip 0x if present)
        color_hex = color.hexval()
        if color_hex.startswith(('0x', '0X')):
            color_hex = color_hex[2:]
        if not color_hex.startswith('#'):
            color_hex = f"#{color_hex}"
        fill_hex = self._lighten_hex(color_hex, 0.75)

        width_in = width / 72
        height_in = height / 72
        fig = plt.figure(figsize=(width_in, height_in))
        ax = fig.add_axes([0, 0, 1, 1])

        ax.fill_between(grid, 0, density, color=fill_hex, alpha=0.6)
        ax.plot(grid, density, color=color_hex, linewidth=1.2)

        # Scatter points with deterministic jitter
        seed = abs(hash(seed_key)) % (2**32)
        rng = np.random.default_rng(seed)
        jitter = rng.normal(0, 0.02, size=values_np.size)
        ax.scatter(values_np, jitter, s=8, color="#6b7280", alpha=0.8)

        if selected_value is not None:
            ax.scatter([selected_value], [0], s=60, color=color_hex, edgecolors="white", linewidths=1.2, zorder=5)

        # Axis limits and orientation
        if lower_is_better:
            ax.set_xlim(vmax + pad, vmin - pad)
        else:
            ax.set_xlim(vmin - pad, vmax + pad)
        ax.set_ylim(-0.08, 0.4)
        ax.axis('off')

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=200, facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)

        return Image(buf, width=width, height=height)

    def _lighten_hex(self, hex_color: str, amount: float = 0.6) -> str:
        """Lighten a hex color by mixing with white."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r + (255 - r) * amount)
        g = int(g + (255 - g) * amount)
        b = int(b + (255 - b) * amount)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _prepare_metrics_data(
        self,
        metric_names: List[str],
        display_names: Dict[str, str],
        sort_ascending: bool = True
    ) -> List[Dict]:
        """Prepare metric data for template."""
        metrics_data = []

        for metric_name in metric_names:
            metric_row = self.team_metrics[
                self.team_metrics['metric_name'] == metric_name
            ]

            if len(metric_row) > 0:
                m = metric_row.iloc[0]
                metrics_data.append({
                    'metric_key': metric_name,
                    'name': display_names.get(metric_name, metric_name.replace('_', ' ').title()),
                    'value': m.get('metric_value_p90', 0),
                    'rank': int(m.get('metric_rank', 0)),
                    'percentile': m.get('percentile', 50),
                })

        metrics_data.sort(key=lambda x: x['rank'], reverse=not sort_ascending)
        return metrics_data

    def _prepare_contributions_data(
        self,
        metric_names: List[str],
        display_names: Dict[str, str],
        max_players: int = 17
    ) -> List[Dict]:
        """Prepare player contribution data with SofaScore names when available."""
        contributions = []

        player_metrics_filtered = self.player_metrics[
            (self.player_metrics['team_id'] == self.config.team_id) &
            (self.player_metrics['manager_id'] == self.config.manager_id)
        ]

        # Load SofaScore names mapping for better display names
        sofascore_map = get_sofascore_names_map()

        for metric_name in metric_names:
            metric_players = player_metrics_filtered[
                player_metrics_filtered['metric_name'] == metric_name
            ].copy()

            if len(metric_players) == 0:
                continue

            metric_players = metric_players.sort_values('contribution_percentage', ascending=False)

            players_list = []
            for rank, (_, row) in enumerate(metric_players.head(max_players).iterrows(), 1):
                player_id = row.get('player_id')
                statsbomb_name = row.get('player_name', 'Unknown')

                # Use SofaScore name if available, otherwise StatsBomb name
                display_name = get_player_display_name(int(player_id), statsbomb_name, sofascore_map) if player_id else statsbomb_name
                surname = extract_surname(display_name) if display_name else 'Unknown'

                players_list.append({
                    'rank': rank,
                    'surname': surname,
                    'contribution': row.get('contribution_percentage', 0),
                })

            contributions.append({
                'metric_key': metric_name,
                'metric_name': display_names.get(metric_name, metric_name.replace('_', ' ').title()),
                'players': players_list,
            })

        return contributions

    def _base64_to_image(self, base64_str: str, width: float, height: float) -> Optional[Image]:
        """Convert base64 string to ReportLab Image."""
        try:
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]

            img_data = base64.b64decode(base64_str)
            img_buffer = io.BytesIO(img_data)

            return Image(img_buffer, width=width, height=height)
        except Exception as e:
            logger.warning(f"Failed to convert base64 to image: {e}")
            return None

    def _base64_to_image_fit(self, base64_str: str, max_width: float, max_height: float) -> Optional[Image]:
        """Convert base64 to Image while preserving aspect ratio within bounds."""
        try:
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]

            img_data = base64.b64decode(base64_str)
            size_reader = ImageReader(io.BytesIO(img_data))
            iw, ih = size_reader.getSize()
            if not iw or not ih:
                return None

            scale = min(max_width / iw, max_height / ih)
            draw_w = iw * scale
            draw_h = ih * scale

            img_buffer = io.BytesIO(img_data)
            return Image(img_buffer, width=draw_w, height=draw_h)
        except Exception as e:
            logger.warning(f"Failed to convert base64 to image (fit): {e}")
            return None


# Helper functions (unchanged)
def get_metrics_with_contributions(
    player_metrics: pd.DataFrame,
    team_id: int,
    manager_id: int,
    metric_names: List[str]
) -> List[str]:
    """Filter metrics to only those that have player contributions."""
    player_metrics_filtered = player_metrics[
        (player_metrics['team_id'] == team_id) &
        (player_metrics['manager_id'] == manager_id)
    ]

    metrics_with_contributions = []
    for metric_name in metric_names:
        metric_players = player_metrics_filtered[
            player_metrics_filtered['metric_name'] == metric_name
        ]
        if len(metric_players) > 0:
            metrics_with_contributions.append(metric_name)

    return metrics_with_contributions


def get_strength_metrics(
    team_metrics: pd.DataFrame,
    total_combinations: int,
    top_percentile: float = 0.25
) -> List[str]:
    """Get metrics where team ranks in top percentile (strengths)."""
    threshold = int(total_combinations * top_percentile)
    strength_metrics = team_metrics[team_metrics['metric_rank'] <= threshold].copy()
    strength_metrics = strength_metrics.sort_values('metric_rank')
    return strength_metrics['metric_name'].tolist()


def get_weakness_metrics(
    team_metrics: pd.DataFrame,
    total_combinations: int,
    bottom_percentile: float = 0.25
) -> List[str]:
    """Get metrics where team ranks in bottom percentile (weaknesses)."""
    threshold = int(total_combinations * (1 - bottom_percentile))
    weakness_metrics = team_metrics[team_metrics['metric_rank'] > threshold].copy()
    weakness_metrics = weakness_metrics.sort_values('metric_rank', ascending=False)
    return weakness_metrics['metric_name'].tolist()
