"""
generate_weather_svg.py
Fetches current weather from wttr.in (no API key needed) and generates an
animated SVG "weather card" reflecting current conditions (sun pulsing,
clouds drifting, rain falling, snow falling, lightning flashing).

Run by the weather-svg.yml GitHub Action on a schedule. Output is written to
dist/weather-card.svg, which the workflow pushes to the "weather-output" branch.
The README embeds the raw SVG URL directly, so it always shows the latest card
without needing a commit to main on every refresh.
"""

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Change this to your city. Format: "City" or "City,CountryCode"
CITY = "Bangalore"

OUTPUT_PATH = "dist/weather-card.svg"


def fetch_weather(city: str) -> dict:
    url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def classify(desc: str) -> str:
    d = desc.lower()
    if "thunder" in d:
        return "storm"
    if "snow" in d or "sleet" in d or "ice" in d:
        return "snow"
    if "rain" in d or "drizzle" in d or "shower" in d:
        return "rain"
    if "fog" in d or "mist" in d or "haze" in d:
        return "fog"
    if "cloud" in d or "overcast" in d:
        return "cloud"
    return "clear"


def icon_svg(kind: str) -> str:
    """Returns the animated icon group, centered at (70, 70)."""
    if kind == "clear":
        return """
        <g transform="translate(70,70)">
          <circle r="22" fill="#FFC93C">
            <animate attributeName="r" values="22;25;22" dur="3s" repeatCount="indefinite"/>
          </circle>
          <g stroke="#FFC93C" stroke-width="3" stroke-linecap="round">
            <g>
              <line x1="0" y1="-32" x2="0" y2="-40"/>
              <line x1="0" y1="32" x2="0" y2="40"/>
              <line x1="-32" y1="0" x2="-40" y2="0"/>
              <line x1="32" y1="0" x2="40" y2="0"/>
              <line x1="-23" y1="-23" x2="-29" y2="-29"/>
              <line x1="23" y1="23" x2="29" y2="29"/>
              <line x1="-23" y1="23" x2="-29" y2="29"/>
              <line x1="23" y1="-23" x2="29" y2="-29"/>
              <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="20s" repeatCount="indefinite"/>
            </g>
          </g>
        </g>"""
    if kind == "cloud":
        return """
        <g>
          <g transform="translate(60,65)">
            <ellipse cx="0" cy="0" rx="30" ry="16" fill="#B0BEC5"/>
            <ellipse cx="20" cy="-6" rx="18" ry="14" fill="#CFD8DC"/>
            <ellipse cx="-18" cy="-4" rx="16" ry="12" fill="#CFD8DC"/>
            <animateTransform attributeName="transform" type="translate" values="50,65;70,65;50,65" dur="6s" repeatCount="indefinite"/>
          </g>
        </g>"""
    if kind in ("rain", "storm"):
        drops = ""
        for i, dx in enumerate([-24, -8, 8, 24]):
            delay = i * 0.3
            drops += f"""
          <line x1="{dx}" y1="18" x2="{dx-4}" y2="30" stroke="#4FC3F7" stroke-width="3" stroke-linecap="round" opacity="0.9">
            <animate attributeName="y1" values="10;40" dur="1s" begin="{delay}s" repeatCount="indefinite"/>
            <animate attributeName="y2" values="22;52" dur="1s" begin="{delay}s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="0.9;0" dur="1s" begin="{delay}s" repeatCount="indefinite"/>
          </line>"""
        bolt = ""
        if kind == "storm":
            bolt = """
          <polygon points="0,15 -6,32 0,32 -5,50 12,25 4,25 9,15" fill="#FFEB3B" opacity="0">
            <animate attributeName="opacity" values="0;1;0;0;0;1;0" dur="2.5s" repeatCount="indefinite"/>
          </polygon>"""
        return f"""
        <g transform="translate(60,55)">
          <ellipse cx="0" cy="0" rx="30" ry="16" fill="#78909C"/>
          <ellipse cx="20" cy="-6" rx="18" ry="14" fill="#90A4AE"/>
          <ellipse cx="-18" cy="-4" rx="16" ry="12" fill="#90A4AE"/>
          {drops}
          {bolt}
        </g>"""
    if kind == "snow":
        flakes = ""
        for i, dx in enumerate([-24, -8, 8, 24]):
            delay = i * 0.5
            flakes += f"""
          <circle cx="{dx}" cy="18" r="2.5" fill="#FFFFFF">
            <animate attributeName="cy" values="10;45" dur="2.5s" begin="{delay}s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="1;0" dur="2.5s" begin="{delay}s" repeatCount="indefinite"/>
          </circle>"""
        return f"""
        <g transform="translate(60,55)">
          <ellipse cx="0" cy="0" rx="30" ry="16" fill="#90A4AE"/>
          <ellipse cx="20" cy="-6" rx="18" ry="14" fill="#B0BEC5"/>
          <ellipse cx="-18" cy="-4" rx="16" ry="12" fill="#B0BEC5"/>
          {flakes}
        </g>"""
    if kind == "fog":
        lines = ""
        for i, y in enumerate([50, 62, 74]):
            delay = i * 0.7
            lines += f"""
          <line x1="20" y1="{y}" x2="100" y2="{y}" stroke="#CFD8DC" stroke-width="4" stroke-linecap="round" opacity="0.7">
            <animate attributeName="opacity" values="0.3;0.8;0.3" dur="3s" begin="{delay}s" repeatCount="indefinite"/>
          </line>"""
        return f'<g transform="translate(10,10)">{lines}</g>'
    return ""


def build_svg(city: str, data: dict) -> str:
    current = data["current_condition"][0]
    today = data["weather"][0]

    temp_c = current["temp_C"]
    feels_like = current["FeelsLikeC"]
    desc = current["weatherDesc"][0]["value"]
    humidity = current["humidity"]
    wind_kmph = current["windspeedKmph"]
    max_temp = today["maxtempC"]
    min_temp = today["mintempC"]
    kind = classify(desc)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    icon = icon_svg(kind)

    return f"""<svg width="440" height="150" viewBox="0 0 440 150" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1b2735"/>
      <stop offset="100%" stop-color="#0d1b2a"/>
    </linearGradient>
  </defs>
  <rect width="440" height="150" rx="14" fill="url(#bg)"/>

  {icon}

  <text x="130" y="45" fill="#ECEFF1" font-family="Verdana, sans-serif" font-size="20" font-weight="bold">{city}</text>
  <text x="130" y="70" fill="#B0BEC5" font-family="Verdana, sans-serif" font-size="13">{desc}</text>

  <text x="130" y="100" fill="#FFC93C" font-family="Verdana, sans-serif" font-size="26" font-weight="bold">{temp_c}&#176;C</text>
  <text x="200" y="100" fill="#78909C" font-family="Verdana, sans-serif" font-size="12">feels {feels_like}&#176;C</text>

  <text x="130" y="122" fill="#90A4AE" font-family="Verdana, sans-serif" font-size="11">Humidity {humidity}%  |  Wind {wind_kmph} km/h  |  H:{max_temp}&#176; L:{min_temp}&#176;</text>

  <text x="130" y="140" fill="#546E7A" font-family="Verdana, sans-serif" font-size="9">Updated {updated}</text>
</svg>"""


if __name__ == "__main__":
    data = fetch_weather(CITY)
    svg = build_svg(CITY, data)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUTPUT_PATH}")
