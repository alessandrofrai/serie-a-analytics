"""
Serie A Analytics - AI Insights Service

This module provides AI-generated tactical profiles using OpenRouter API.
Instead of simple bullet points, it generates rich narrative descriptions
that identify:
- Player archetype (e.g., "Regista", "Box-to-Box", "Falso 9")
- Tactical role and how the player interprets it
- Key characteristics and playing style
- Strengths and limitations in context

API: OpenRouter (https://openrouter.ai)
Default Model: mistralai/mistral-small-3.1-24b-instruct:free
"""

import os
import sys
import json
import logging
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

# Add parent path for config imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import OPENROUTER_API_KEY, OPENROUTER_MODEL

logger = logging.getLogger(__name__)

# Try to import httpx, fallback to requests
try:
    import httpx
    HTTP_CLIENT = "httpx"
except ImportError:
    try:
        import requests
        HTTP_CLIENT = "requests"
    except ImportError:
        HTTP_CLIENT = None
        logger.warning("Neither httpx nor requests available for AI insights")


@dataclass
class PlayerTacticalProfile:
    """AI-generated tactical profile for a player."""
    player_name: str
    role_name_it: str
    archetype: str  # e.g., "Regista", "Box-to-Box", "Finalizzatore"
    description: str  # 2-3 sentence tactical description
    cached: bool = False


@dataclass
class TeamTacticalProfile:
    """AI-generated tactical profile for a team+manager."""
    team_name: str
    manager_name: str
    style_name: str  # From clustering (e.g., "Possesso Dominante")
    analysis: str  # 100-word analysis
    cached: bool = False


# Legacy class for backwards compatibility
@dataclass
class PlayerInsights:
    """AI-generated insights for a player (legacy)."""
    player_name: str
    role_name_it: str
    strength_insights: List[str]
    weakness_insights: List[str]
    cached: bool = False


class OpenRouterClient:
    """
    Client for OpenRouter API to generate tactical insights.

    Model is configurable via OPENROUTER_MODEL environment variable.
    Default: mistralai/mistral-small-3.1-24b-instruct:free
    """

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the client.

        Args:
            api_key: OpenRouter API key. If not provided, uses config.settings.
            model: Model to use. If not provided, uses config.settings.
        """
        self.api_key = api_key or OPENROUTER_API_KEY
        self.model = model or OPENROUTER_MODEL or self.DEFAULT_MODEL
        self._cache: Dict[str, PlayerInsights] = {}

    @property
    def is_available(self) -> bool:
        """Check if the client is properly configured."""
        return bool(self.api_key) and HTTP_CLIENT is not None

    def _get_cache_key(self, player_name: str, role: str, strengths: str, weaknesses: str) -> str:
        """Generate a cache key for the request."""
        content = f"{player_name}|{role}|{strengths}|{weaknesses}"
        return hashlib.md5(content.encode()).hexdigest()

    def generate_insights(
        self,
        player_name: str,
        role_name_it: str,
        strengths: List[Dict],
        weaknesses: List[Dict],
        timeout: int = 30
    ) -> Optional[PlayerInsights]:
        """
        Generate tactical insights for a player.

        Args:
            player_name: Player's name
            role_name_it: Role in Italian (e.g., "Attaccante")
            strengths: List of strength dicts with keys: metric_name_it, z_score, player_value, role_mean
            weaknesses: List of weakness dicts with keys: metric_name_it, z_score, player_value, role_mean
            timeout: Request timeout in seconds

        Returns:
            PlayerInsights or None if generation failed
        """
        if not self.is_available:
            logger.warning("OpenRouter client not available (no API key or HTTP client)")
            return None

        # Format strengths and weaknesses for the prompt
        strengths_text = self._format_metrics(strengths, is_strength=True)
        weaknesses_text = self._format_metrics(weaknesses, is_strength=False)

        # Check cache
        cache_key = self._get_cache_key(player_name, role_name_it, strengths_text, weaknesses_text)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            cached.cached = True
            return cached

        # Build the prompt
        prompt = self._build_prompt(player_name, role_name_it, strengths_text, weaknesses_text)

        try:
            response = self._call_api(prompt, timeout)
            if response is None:
                return None

            # Parse the response
            insights = self._parse_response(response, player_name, role_name_it)

            # Cache the result
            if insights:
                self._cache[cache_key] = insights

            return insights

        except Exception as e:
            logger.error(f"Error generating insights for {player_name}: {e}")
            return None

    def _format_metrics(self, metrics: List[Dict], is_strength: bool) -> str:
        """Format metrics for the prompt."""
        if not metrics:
            return "Nessuna" if is_strength else "Nessuna"

        lines = []
        for m in metrics:
            name = m.get('metric_name_it', m.get('metric_name', 'Unknown'))
            z = m.get('z_score', 0)
            value = m.get('player_value', 0)
            mean = m.get('role_mean', 0)

            if is_strength:
                direction = "sopra" if z > 0 else "sotto"
            else:
                direction = "sotto" if z < 0 else "sopra"

            # Format z-score interpretation
            z_abs = abs(z)
            if z_abs >= 2.0:
                level = "eccezionale" if is_strength else "critico"
            elif z_abs >= 1.5:
                level = "eccellente" if is_strength else "molto debole"
            elif z_abs >= 1.0:
                level = "molto buono" if is_strength else "debole"
            else:
                level = "buono" if is_strength else "sotto la media"

            lines.append(
                f"- {name}: {value:.2f} p90 (media ruolo: {mean:.2f}, z-score: {z:+.2f}, livello: {level})"
            )

        return "\n".join(lines)

    def _build_prompt(
        self,
        player_name: str,
        role_name_it: str,
        strengths_text: str,
        weaknesses_text: str
    ) -> str:
        """Build the prompt for the AI model (legacy format)."""
        return f"""Sei un analista tattico di calcio. Analizza il seguente giocatore e fornisci insights tattici CONCISI in italiano.

GIOCATORE: {player_name}
RUOLO: {role_name_it}

PUNTI DI FORZA (rispetto ai {role_name_it} della Serie A):
{strengths_text}

PUNTI DEBOLI (rispetto ai {role_name_it} della Serie A):
{weaknesses_text}

ISTRUZIONI:
1. Per i PUNTI DI FORZA: Scrivi massimo 3 bullet points brevi (max 15 parole ciascuno) su come sfruttare tatticamente questi punti di forza.
2. Per i PUNTI DEBOLI: Scrivi massimo 3 bullet points brevi (max 15 parole ciascuno) su come le squadre avversarie potrebbero sfruttare questi punti deboli.

IMPORTANTE:
- Ogni bullet point deve essere TATTICO e PRATICO, non descrittivo
- Usa un linguaggio diretto e specifico
- Se non ci sono punti di forza o debolezza significativi, scrivi "Nessun insight significativo"

FORMATO RISPOSTA (JSON):
{{
  "strengths": ["insight 1", "insight 2", "insight 3"],
  "weaknesses": ["insight 1", "insight 2", "insight 3"]
}}

Rispondi SOLO con il JSON, nient'altro."""

    def _build_profile_prompt(
        self,
        player_name: str,
        role_name_it: str,
        all_metrics_text: str,
        team_style: Optional[str] = None
    ) -> str:
        """Build the prompt for tactical profile generation."""
        # Add team style context if available
        team_context = ""
        if team_style:
            team_context = f"""
STILE DI GIOCO DELLA SQUADRA: {team_style}
IMPORTANTE: Questo giocatore fa parte di una squadra con stile "{team_style}".
- Se la squadra ha "Possesso Dominante": è NORMALE che tutti abbiano buoni passaggi progressivi. NON significa che siano "costruttori".
- Per essere un vero "Difensore Costruttore" deve avere metriche ECCEZIONALI (z > 1.5) in passaggi progressivi/filtranti.
- In una squadra di possesso, concentrati sulle metriche DIFENSIVE per distinguere i difensori (duelli aerei, contrasti, intercetti).
"""

        return f"""Sei un analista tattico professionista della Serie A. Analizza i dati statistici di questo giocatore e produci un profilo tattico accurato.

GIOCATORE: {player_name}
RUOLO IN FORMAZIONE: {role_name_it}
{team_context}
DATI STATISTICI (confronto con tutti i giocatori dello stesso ruolo in Serie A 2015-16):
{all_metrics_text}

NOTA IMPORTANTE: Le metriche di VOLUME dei passaggi (passaggi totali, corti, medi, lunghi) sono state ESCLUSE perché inflazionate dallo stile di gioco della squadra.

INTERPRETAZIONE Z-SCORE:
- z > +1.5 = eccellenza assoluta (top 5-10% del ruolo)
- z tra +0.5 e +1.5 = sopra la media
- z tra -0.5 e +0.5 = nella norma
- z tra -1.5 e -0.5 = sotto la media
- z < -1.5 = carenza significativa

COMPITO:
Analizza le COMBINAZIONI di metriche per determinare:
1. L'ARCHETIPO del giocatore (es. "Regista", "Incursore", "Stopper", "Finalizzatore", etc.)
2. Una DESCRIZIONE professionale di max 50 parole

LOGICA DI ANALISI PER RUOLO:

DIFENSORI CENTRALI:
- La maggior parte dei difensori sono STOPPER (difesa aggressiva). È il default.
- "Difensore Costruttore" SOLO se ha metriche QUALITATIVE ECCEZIONALI (z > 1.5): passaggi progressivi, filtranti, conduzioni progressive.
- I duelli aerei, contrasti, intercetti sono le metriche PRIMARIE per un difensore.
- Se un difensore ha buoni duelli aerei o contrasti → Stopper, anche se ha passaggi progressivi sopra media.

CENTROCAMPISTI:
- Regista = alti passaggi progressivi/chiave + BASSI contrasti (gestisce, non corre)
- Incursore/Box-to-Box = alti contrasti + alte conduzioni/inserimenti
- Mediano Difensivo = alti contrasti/intercetti + bassi passaggi creativi

ATTACCANTI:
- Finalizzatore = alto xG, tiri, conversione
- Falso Nove = basso xG ma alta creatività (xA, passaggi chiave)

NON usare archetipi generici come "Completo" o "Equilibrato" - trova la caratteristica DOMINANTE.

STILE DESCRIZIONE:
- Linguaggio professionale da analista (non poetico o enfatico)
- Basato sui dati, non su impressioni
- Indica il punto forte principale e il limite principale
- Max 50 parole

FORMATO JSON:
{{
  "archetype": "Nome Archetipo",
  "description": "Descrizione concisa e professionale."
}}

Solo JSON, nient'altro."""

    # Volume metrics that are inflated by team possession style
    # These should be EXCLUDED from AI analysis as they don't reflect individual ability
    TEAM_DEPENDENT_VOLUME_METRICS = {
        'passes_total', 'passes_short', 'passes_medium', 'passes_long',
        'ball_recoveries', 'touches_in_box', 'touches_total'
    }

    def generate_tactical_profile(
        self,
        player_name: str,
        role_name_it: str,
        all_z_scores: Dict,
        team_style: Optional[str] = None,
        timeout: int = 30
    ) -> Optional[PlayerTacticalProfile]:
        """
        Generate a tactical profile for a player.

        Args:
            player_name: Player's name
            role_name_it: Role in Italian (e.g., "Attaccante")
            all_z_scores: Dict of metric_name -> PlayerMetricZScore objects
            team_style: Team's playing style from clustering (e.g., "Possesso Dominante")
            timeout: Request timeout in seconds

        Returns:
            PlayerTacticalProfile or None if generation failed
        """
        if not self.is_available:
            logger.warning("OpenRouter client not available")
            return None

        # Format metrics for the prompt, EXCLUDING team-dependent volume metrics
        metrics_list = []
        for metric_name, zs in all_z_scores.items():
            # Skip team-dependent volume metrics - they're inflated by possession
            if metric_name in self.TEAM_DEPENDENT_VOLUME_METRICS:
                continue

            z = zs.z_score
            value = zs.player_value
            mean = zs.role_mean
            name_it = zs.metric_name_it

            # Interpret z-score
            if z >= 1.5:
                level = "ECCELLENTE"
            elif z >= 0.75:
                level = "sopra media"
            elif z >= -0.75:
                level = "nella media"
            elif z >= -1.5:
                level = "sotto media"
            else:
                level = "MOLTO BASSO"

            metrics_list.append({
                'name': name_it,
                'metric_name': metric_name,
                'z': z,
                'text': f"- {name_it}: {value:.2f} p90 (media: {mean:.2f}, z: {z:+.2f}) → {level}"
            })

        # Sort by absolute z-score (most distinctive first)
        metrics_list.sort(key=lambda x: abs(x['z']), reverse=True)
        metrics_text = "\n".join([m['text'] for m in metrics_list[:15]])  # Top 15 most distinctive

        # Check cache (include team_style in cache key)
        style_key = team_style or "unknown"
        cache_key = self._get_cache_key(player_name, role_name_it, metrics_text, f"profile_{style_key}")
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if isinstance(cached, PlayerTacticalProfile):
                cached.cached = True
                return cached

        # Build and call
        prompt = self._build_profile_prompt(player_name, role_name_it, metrics_text, team_style)

        try:
            response = self._call_api(prompt, timeout)
            if response is None:
                return None

            # Parse the response
            profile = self._parse_profile_response(response, player_name, role_name_it)

            # Cache the result
            if profile:
                self._cache[cache_key] = profile

            return profile

        except Exception as e:
            logger.error(f"Error generating profile for {player_name}: {e}")
            return None

    def _build_team_profile_prompt(
        self,
        team_name: str,
        manager_name: str,
        cluster_name: str,
        radar_values: Dict[str, float],
        metrics_by_category: Dict[str, str]
    ) -> str:
        """Build the prompt for team tactical profile generation."""
        # Format radar summary
        radar_summary = "\n".join([
            f"- {cat}: {val:.0f}° percentile" for cat, val in radar_values.items()
        ])

        # Format detailed metrics by category
        detailed_metrics = "\n\n".join([
            f"**{cat}**:\n{metrics}" for cat, metrics in metrics_by_category.items()
        ])

        return f"""Sei un analista tattico professionista della Serie A. Scrivi un'analisi tattica strutturata per questa squadra.

SQUADRA: {team_name}
ALLENATORE: {manager_name}
STILE DI GIOCO (da clustering): {cluster_name}

PERFORMANCE PER AREA (percentile rispetto alle altre 29 combinazioni squadra+allenatore della Serie A 2015-16):
{radar_summary}

METRICHE DETTAGLIATE PER CATEGORIA:
{detailed_metrics}

INTERPRETAZIONE PERCENTILI:
- 90-100: Elite (top 10%)
- 75-89: Molto forte
- 50-74: Sopra la media
- 25-49: Sotto la media
- 0-24: Punto debole

COMPITO:
Scrivi un'ANALISI TATTICA con questa STRUTTURA ESATTA:

1. PREAMBOLO (~30 parole): Un'introduzione discorsiva che contestualizza l'approccio tattico della gestione tecnica. Questo sarà mostrato in corsivo.

2. PUNTI DI FORZA (~45 parole): Descrivi i 2 principali punti di forza tattici basandoti sui dati, in modo discorsivo e piacevole da leggere. Inizia con "**Punti di forza:**" seguito dal testo.

3. PUNTI DEBOLI (~45 parole): Descrivi le aree di miglioramento basandoti sui dati, in modo discorsivo e piacevole da leggere. Inizia con "**Punti deboli:**" seguito dal testo.

STILE OBBLIGATORIO:
- Tono ESTREMAMENTE PROFESSIONALE da analista tecnico
- MAI usare parole troppo forti o enfatiche (evita: "eccezionale", "straordinario", "dominante", "impressionante")
- Preferisci termini misurati: "solido", "efficace", "strutturato", "metodico", "costante"
- Linguaggio oggettivo e basato sui dati
- Terminologia tattica specifica
- Totale circa 120 parole

FORMATO JSON (rispetta esattamente questa struttura con newline \\n):
{{
  "analysis": "*Preambolo di circa 30 parole in corsivo.*\\n\\n**Punti di forza:** Testo di circa 45 parole.\\n\\n**Punti deboli:** Testo di circa 45 parole."
}}

Solo JSON, nient'altro."""

    def generate_team_tactical_profile(
        self,
        team_name: str,
        manager_name: str,
        cluster_name: str,
        radar_values: Dict[str, float],
        metrics_by_category: Dict[str, str],
        timeout: int = 30
    ) -> Optional[TeamTacticalProfile]:
        """
        Generate a tactical profile for a team+manager.

        Args:
            team_name: Team name
            manager_name: Manager name
            cluster_name: Playing style from clustering
            radar_values: Dict of category -> percentile values
            metrics_by_category: Dict of category -> formatted metrics string
            timeout: Request timeout in seconds

        Returns:
            TeamTacticalProfile or None if generation failed
        """
        if not self.is_available:
            logger.warning("OpenRouter client not available")
            return None

        # Check cache
        cache_key = self._get_cache_key(team_name, manager_name, cluster_name, "team_profile")
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if isinstance(cached, TeamTacticalProfile):
                cached.cached = True
                return cached

        # Build prompt
        prompt = self._build_team_profile_prompt(
            team_name, manager_name, cluster_name, radar_values, metrics_by_category
        )

        try:
            response = self._call_api(prompt, timeout)
            if response is None:
                return None

            # Parse response
            profile = self._parse_team_profile_response(
                response, team_name, manager_name, cluster_name
            )

            if profile:
                self._cache[cache_key] = profile

            return profile

        except Exception as e:
            logger.error(f"Error generating team profile for {team_name}: {e}")
            return None

    def _parse_team_profile_response(
        self,
        response: str,
        team_name: str,
        manager_name: str,
        cluster_name: str
    ) -> Optional[TeamTacticalProfile]:
        """Parse the AI response into TeamTacticalProfile."""
        try:
            response = response.strip()
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                logger.warning("No JSON found in team profile response")
                return None

            json_str = response[start:end]
            data = json.loads(json_str)

            analysis = data.get("analysis", "").strip()

            if not analysis:
                return None

            return TeamTacticalProfile(
                team_name=team_name,
                manager_name=manager_name,
                style_name=cluster_name,
                analysis=analysis,
                cached=False
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse team profile JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing team profile response: {e}")
            return None

    def _parse_profile_response(
        self,
        response: str,
        player_name: str,
        role_name_it: str
    ) -> Optional[PlayerTacticalProfile]:
        """Parse the AI response into PlayerTacticalProfile."""
        try:
            response = response.strip()
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                logger.warning(f"No JSON found in profile response")
                return None

            json_str = response[start:end]
            data = json.loads(json_str)

            archetype = data.get("archetype", "").strip()
            description = data.get("description", "").strip()

            if not archetype or not description:
                return None

            return PlayerTacticalProfile(
                player_name=player_name,
                role_name_it=role_name_it,
                archetype=archetype,
                description=description,
                cached=False
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse profile JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing profile response: {e}")
            return None

    def _call_api(self, prompt: str, timeout: int) -> Optional[str]:
        """Make the API call to OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://serie-a-analytics.app",
            "X-Title": "Serie A Analytics Dashboard"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        if HTTP_CLIENT == "httpx":
            import httpx
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
        elif HTTP_CLIENT == "requests":
            import requests
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
        else:
            return None

        # Extract the content
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]

        return None

    def _parse_response(
        self,
        response: str,
        player_name: str,
        role_name_it: str
    ) -> Optional[PlayerInsights]:
        """Parse the AI response into PlayerInsights."""
        try:
            # Try to extract JSON from response
            # Sometimes the model includes extra text
            response = response.strip()

            # Find JSON object
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                logger.warning(f"No JSON found in response: {response[:100]}")
                return None

            json_str = response[start:end]
            data = json.loads(json_str)

            strengths = data.get("strengths", [])
            weaknesses = data.get("weaknesses", [])

            # Validate and clean
            strengths = [s for s in strengths if s and isinstance(s, str) and len(s) > 5][:3]
            weaknesses = [w for w in weaknesses if w and isinstance(w, str) and len(w) > 5][:3]

            return PlayerInsights(
                player_name=player_name,
                role_name_it=role_name_it,
                strength_insights=strengths,
                weakness_insights=weaknesses,
                cached=False
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return None

    def clear_cache(self):
        """Clear the insights cache."""
        self._cache.clear()


# Global client instance (lazy initialization)
_client: Optional[OpenRouterClient] = None


def get_client() -> OpenRouterClient:
    """Get or create the global OpenRouter client."""
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client


def generate_player_insights(
    player_name: str,
    role_name_it: str,
    strengths: List[Dict],
    weaknesses: List[Dict],
    api_key: Optional[str] = None
) -> Optional[PlayerInsights]:
    """
    Generate tactical insights for a player.

    This is a convenience function that uses the global client.

    Args:
        player_name: Player's name
        role_name_it: Role in Italian
        strengths: List of strength dicts
        weaknesses: List of weakness dicts
        api_key: Optional API key (uses env var if not provided)

    Returns:
        PlayerInsights or None
    """
    client = get_client()

    # Update API key if provided
    if api_key:
        client.api_key = api_key

    return client.generate_insights(
        player_name=player_name,
        role_name_it=role_name_it,
        strengths=strengths,
        weaknesses=weaknesses
    )


def generate_fallback_insights(
    player_name: str,
    role_name_it: str,
    strengths: List[Dict],
    weaknesses: List[Dict]
) -> PlayerInsights:
    """
    Generate rule-based fallback insights when AI is not available.

    This provides basic tactical insights based on the metrics without
    using the AI model.

    Args:
        player_name: Player's name
        role_name_it: Role in Italian
        strengths: List of strength dicts
        weaknesses: List of weakness dicts

    Returns:
        PlayerInsights with rule-based insights
    """
    strength_insights = []
    weakness_insights = []

    # Generate strength insights based on metric types
    for s in strengths[:3]:
        metric = s.get('metric_name', '')
        metric_it = s.get('metric_name_it', metric)

        if 'xg' in metric.lower() or 'shots' in metric.lower():
            strength_insights.append(f"Cerca spesso la conclusione, {metric_it} sopra la media")
        elif 'pass' in metric.lower() or 'through' in metric.lower():
            strength_insights.append(f"Coinvolgilo nel gioco, eccelle in {metric_it}")
        elif 'dribbl' in metric.lower() or 'carry' in metric.lower():
            strength_insights.append(f"Dagli spazio per condurre palla, {metric_it} elevato")
        elif 'tackle' in metric.lower() or 'intercept' in metric.lower():
            strength_insights.append(f"Affidabile in fase difensiva, {metric_it} sopra la media")
        elif 'aerial' in metric.lower() or 'clear' in metric.lower():
            strength_insights.append(f"Dominante nel gioco aereo, {metric_it} eccellente")
        elif 'cross' in metric.lower():
            strength_insights.append(f"Pericoloso sui cross, sfruttare la fascia")
        elif 'key' in metric.lower() or 'xa' in metric.lower():
            strength_insights.append(f"Creativo nell'ultimo passaggio, {metric_it} elevato")
        else:
            strength_insights.append(f"Punto di forza: {metric_it}")

    # Generate weakness insights based on metric types
    for w in weaknesses[:3]:
        metric = w.get('metric_name', '')
        metric_it = w.get('metric_name_it', metric)

        if 'xg' in metric.lower() or 'shots' in metric.lower():
            weakness_insights.append(f"Poco incisivo sotto porta, pressare quando ha palla in area")
        elif 'pass' in metric.lower():
            weakness_insights.append(f"Errori in costruzione, pressare per forzare passaggi sbagliati")
        elif 'dribbl' in metric.lower() or 'carry' in metric.lower():
            weakness_insights.append(f"Non ama condurre palla, chiudergli gli spazi")
        elif 'tackle' in metric.lower() or 'intercept' in metric.lower():
            weakness_insights.append(f"Vulnerabile in fase difensiva, attaccare la sua zona")
        elif 'aerial' in metric.lower():
            weakness_insights.append(f"Debole nel gioco aereo, cercare cross e lanci alti")
        elif 'cross' in metric.lower():
            weakness_insights.append(f"Cross imprecisi, concedere la fascia per forzare errori")
        elif 'key' in metric.lower() or 'xa' in metric.lower():
            weakness_insights.append(f"Poco creativo, raddoppiare su chi riceve da lui")
        else:
            weakness_insights.append(f"Punto debole: {metric_it}")

    return PlayerInsights(
        player_name=player_name,
        role_name_it=role_name_it,
        strength_insights=strength_insights,
        weakness_insights=weakness_insights,
        cached=False
    )


def generate_tactical_profile(
    player_name: str,
    role_name_it: str,
    all_z_scores: Dict,
    team_style: Optional[str] = None,
    api_key: Optional[str] = None
) -> Optional[PlayerTacticalProfile]:
    """
    Generate a tactical profile for a player.

    This is a convenience function that uses the global client.

    Args:
        player_name: Player's name
        role_name_it: Role in Italian
        all_z_scores: Dict of metric_name -> PlayerMetricZScore objects
        team_style: Team's playing style from clustering (e.g., "Possesso Dominante")
        api_key: Optional API key (uses env var if not provided)

    Returns:
        PlayerTacticalProfile or None
    """
    client = get_client()

    # Update API key if provided
    if api_key:
        client.api_key = api_key

    return client.generate_tactical_profile(
        player_name=player_name,
        role_name_it=role_name_it,
        all_z_scores=all_z_scores,
        team_style=team_style
    )


def generate_fallback_profile(
    player_name: str,
    role_name_it: str,
    strengths: List,
    weaknesses: List,
    all_z_scores: Dict
) -> PlayerTacticalProfile:
    """
    Generate a simple fallback tactical profile when AI is not available.
    Keeps it minimal - just returns the role with top strength/weakness.
    """
    # Team-dependent metrics to filter out
    TEAM_DEPENDENT = {
        'passes_total', 'passes_short', 'passes_medium', 'passes_long',
        'ball_recoveries', 'touches_in_box'
    }

    # Filter to individual metrics only
    filtered_strengths = [s for s in strengths if s.metric_name not in TEAM_DEPENDENT]
    filtered_weaknesses = [w for w in weaknesses if w.metric_name not in TEAM_DEPENDENT]

    # Simple archetype based on role
    archetype = role_name_it

    # Simple description based on top metrics
    if filtered_strengths:
        top_str = filtered_strengths[0].metric_name_it
        description = f"Si distingue in {top_str.lower()}."
        if filtered_weaknesses:
            top_weak = filtered_weaknesses[0].metric_name_it
            description += f" Margini di crescita in {top_weak.lower()}."
    else:
        description = f"Profilo nella norma per il ruolo di {role_name_it.lower()}."

    return PlayerTacticalProfile(
        player_name=player_name,
        role_name_it=role_name_it,
        archetype=archetype,
        description=description,
        cached=False
    )


def generate_team_tactical_profile(
    team_name: str,
    manager_name: str,
    cluster_name: str,
    radar_values: Dict[str, float],
    metrics_by_category: Dict[str, str],
    api_key: Optional[str] = None
) -> Optional[TeamTacticalProfile]:
    """
    Generate a tactical profile for a team+manager.

    This is a convenience function that uses the global client.

    Args:
        team_name: Team name
        manager_name: Manager name
        cluster_name: Playing style from clustering
        radar_values: Dict of category -> percentile values
        metrics_by_category: Dict of category -> formatted metrics string
        api_key: Optional API key (uses env var if not provided)

    Returns:
        TeamTacticalProfile or None
    """
    client = get_client()

    if api_key:
        client.api_key = api_key

    return client.generate_team_tactical_profile(
        team_name=team_name,
        manager_name=manager_name,
        cluster_name=cluster_name,
        radar_values=radar_values,
        metrics_by_category=metrics_by_category
    )


def generate_fallback_team_profile(
    team_name: str,
    manager_name: str,
    cluster_name: str,
    radar_values: Dict[str, float]
) -> TeamTacticalProfile:
    """
    Generate a simple fallback team tactical profile when AI is not available.
    Uses the same structured format as AI-generated profiles.
    """
    # Find strongest and weakest areas
    sorted_areas = sorted(radar_values.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_areas[0] if sorted_areas else ("", 50)
    second_strongest = sorted_areas[1] if len(sorted_areas) > 1 else ("", 50)
    weakest = sorted_areas[-1] if sorted_areas else ("", 50)

    # Preambolo in corsivo (~30 parole)
    preambolo = (
        f"*La gestione tecnica di {manager_name} si caratterizza per un approccio tattico riconducibile "
        f"allo stile '{cluster_name.lower()}', con un profilo prestazionale ben definito nel contesto "
        f"competitivo della Serie A 2015-16.*"
    )

    # Punti di forza (~45 parole)
    punti_forza = (
        f"**Punti di forza:** L'area {strongest[0].lower()} rappresenta il principale punto di eccellenza "
        f"della squadra, collocandosi al {strongest[1]:.0f}° percentile rispetto alle altre gestioni tecniche del campionato. "
        f"A supporto di questo primato, si registrano prestazioni solide anche nell'area {second_strongest[0].lower()} "
        f"({second_strongest[1]:.0f}° percentile), confermando una struttura tattica coerente."
    )

    # Punti deboli (~45 parole)
    punti_deboli = (
        f"**Punti deboli:** L'area {weakest[0].lower()} evidenzia margini di crescita significativi, "
        f"attestandosi al {weakest[1]:.0f}° percentile. Questo aspetto rappresenta l'ambito su cui concentrare "
        f"il lavoro per consolidare ulteriormente il profilo tattico della squadra e compiere un salto di qualità complessivo."
    )

    analysis = f"{preambolo}\n\n{punti_forza}\n\n{punti_deboli}"

    return TeamTacticalProfile(
        team_name=team_name,
        manager_name=manager_name,
        style_name=cluster_name,
        analysis=analysis,
        cached=False
    )


