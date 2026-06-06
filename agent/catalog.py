"""Curated deep-sky and double-star targets suited to an 80 mm refractor.

Coordinates are J2000, RA in degrees (= hours * 15), Dec in degrees.
`difficulty`: easy | moderate | challenge  (challenge targets are dropped when
a bright Moon is up). `what` is a short human description used in the message.

Planets, the Moon and the Sun are handled live in sky.py from the ephemeris;
they are not in this list.
"""

# name, ra_deg, dec_deg, mag, kind, difficulty, what
_ROWS = [
    # --- Showpiece nebulae & clusters (easy) ---
    ("M42 Orion Nebula",        83.85,  -5.45, 4.0, "nebula",   "easy",      "the great winter nebula"),
    ("M45 Pleiades",            56.75,  24.12, 1.6, "cluster",  "easy",      "the Seven Sisters"),
    ("M44 Beehive",            130.03,  19.98, 3.7, "cluster",  "easy",      "big open cluster in Cancer"),
    ("Double Cluster (NGC869/884)", 35.00, 57.13, 4.3, "cluster", "easy",   "twin clusters in Perseus"),
    ("M31 Andromeda Galaxy",    10.68,  41.27, 3.4, "galaxy",   "easy",      "nearest big galaxy"),
    ("M8 Lagoon Nebula",       270.95, -24.38, 6.0, "nebula",   "moderate",  "summer nebula, low in the south"),
    ("M11 Wild Duck Cluster",  282.78,  -6.27, 5.8, "cluster",  "easy",      "rich open cluster in Scutum"),
    # --- Globular clusters ---
    ("M13 Hercules Cluster",   250.42,  36.46, 5.8, "globular", "easy",      "best northern globular"),
    ("M92 Hercules Globular",  259.28,  43.14, 6.4, "globular", "moderate",  "fine globular near M13"),
    ("M22 Sagittarius Globular",279.10,-23.90, 5.1, "globular", "moderate",  "bright but low globular"),
    ("M3 Globular",            205.55,  28.38, 6.2, "globular", "moderate",  "showpiece spring globular"),
    ("M5 Globular",            229.65,   2.08, 5.6, "globular", "moderate",  "one of the finest globulars"),
    ("M15 Pegasus Globular",   322.50,  12.17, 6.2, "globular", "moderate",  "compact autumn globular"),
    ("M2 Aquarius Globular",   323.36,  -0.82, 6.5, "globular", "moderate",  "rich autumn globular"),
    # --- Open clusters ---
    ("M35 Gemini Cluster",      92.23,  24.33, 5.1, "cluster",  "easy",      "large cluster at Gemini's feet"),
    ("M36 Auriga Cluster",      84.04,  34.13, 6.0, "cluster",  "moderate",  "open cluster in Auriga"),
    ("M37 Auriga Cluster",      88.07,  32.55, 5.6, "cluster",  "moderate",  "richest of the Auriga trio"),
    ("M38 Auriga Cluster",      82.17,  35.83, 6.4, "cluster",  "moderate",  "open cluster in Auriga"),
    ("M41 Canis Major Cluster",101.50, -20.75, 4.5, "cluster",  "easy",      "bright cluster below Sirius"),
    ("M34 Perseus Cluster",     40.50,  42.78, 5.5, "cluster",  "easy",      "loose cluster in Perseus"),
    ("M39 Cygnus Cluster",     323.05,  48.43, 4.6, "cluster",  "easy",      "big sparse cluster in Cygnus"),
    ("M52 Cassiopeia Cluster", 351.05,  61.58, 6.9, "cluster",  "moderate",  "rich cluster in Cassiopeia"),
    # --- Planetary nebulae ---
    ("M27 Dumbbell Nebula",    299.90,  22.72, 7.4, "planetary","moderate",  "bright planetary nebula"),
    ("M57 Ring Nebula",        283.40,  33.03, 8.8, "planetary","challenge", "the Ring, small but iconic"),
    # --- Brighter galaxies (challenge for 80 mm) ---
    ("M81 Bode's Galaxy",      148.90,  69.07, 6.9, "galaxy",   "challenge", "bright spiral near the Pole"),
    ("M82 Cigar Galaxy",       148.97,  69.68, 8.4, "galaxy",   "challenge", "edge-on starburst by M81"),
    ("M51 Whirlpool Galaxy",   202.47,  47.20, 8.4, "galaxy",   "challenge", "face-on spiral in Canes Venatici"),
    ("M104 Sombrero Galaxy",   190.00, -11.62, 8.0, "galaxy",   "challenge", "edge-on with dust lane"),
    # --- Double stars / asterisms (use STAR_MAG_LIMIT) ---
    ("Albireo (Beta Cygni)",   292.68,  27.97, 3.1, "double",   "easy",      "gold & blue double star"),
    ("Mizar & Alcor",          200.98,  54.92, 2.3, "double",   "easy",      "classic naked-eye + scope double"),
    ("Almach (Gamma And)",      30.97,  42.33, 2.3, "double",   "easy",      "colourful double in Andromeda"),
    ("Cor Caroli",             194.00,  38.32, 2.9, "double",   "easy",      "wide bright double"),
    ("Castor (Alpha Gem)",     113.65,  31.89, 1.6, "double",   "moderate",  "tight bright double"),
    ("Algieba (Gamma Leo)",    155.00,  19.83, 2.0, "double",   "moderate",  "golden double in Leo"),
    ("Polaris",                 37.95,  89.26, 2.0, "double",   "moderate",  "the Pole Star, faint companion"),
    ("Double-Double (Eps Lyr)",281.18,  39.67, 4.6, "double",   "challenge", "four stars at high power"),
]

CATALOG = [
    {
        "id": row[0].split(" ")[0].lower().strip("()"),  # slug-ish stable key
        "name": row[0],
        "ra_deg": row[1],
        "dec_deg": row[2],
        "mag": row[3],
        "kind": row[4],
        "difficulty": row[5],
        "what": row[6],
    }
    for row in _ROWS
]
