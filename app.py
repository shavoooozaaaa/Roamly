import os
import base64
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Roamly",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Home"


@st.cache_data(show_spinner=False)
def get_farray_font_face() -> str:
    """Loads and caches the HOTEL FARRAY (FARRAY.otf) font as base64."""
    local_font_path = "FARRAY.otf"
    font_urls = [
        "https://static.wfonts.com/data/2015/02/26/farray/FARRAY.otf",
        "https://files.fontsme.com/f/793/2793/file/farray.regular.otf",
    ]

    if not os.path.exists(local_font_path):
        headers = {"User-Agent": "Mozilla/5.0"}
        for url in font_urls:
            try:
                r = requests.get(url, headers=headers, timeout=6)
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(local_font_path, "wb") as f:
                        f.write(r.content)
                    break
            except Exception:
                continue

    if os.path.exists(local_font_path):
        with open(local_font_path, "rb") as f:
            b64_font = base64.b64encode(f.read()).decode("utf-8")
        return f"""
        @font-face {{
            font-family: 'FARRAY';
            src: local('FARRAY'), local('FARRAY-Regular'), local('Farray'),
                 url('data:font/opentype;base64,{b64_font}') format('opentype');
            font-weight: normal;
            font-style: normal;
            font-display: swap;
        }}
        """

    return """
    @font-face {
        font-family: 'FARRAY';
        src: local('FARRAY'), local('FARRAY-Regular'), local('Farray'),
             url('https://static.wfonts.com/data/2015/02/26/farray/FARRAY.otf') format('opentype');
        font-weight: normal;
        font-style: normal;
        font-display: swap;
    }
    """


farray_font_css = get_farray_font_face()

# =====================================================================
# 1. WATERY CIRCULAR CURSOR RIPPLES + SPARKLING WARP PARTICLES CANVAS
# =====================================================================
components.html(
    """
    <script>
    (function() {
        const parentWin = window.parent;
        const parentDoc = parentWin.document;

        // Remove any previous ribbon canvas or animation loop
        ['roamly-reactive-bg', 'roamly-silk-canvas'].forEach(id => {
            const el = parentDoc.getElementById(id);
            if (el) el.remove();
        });

        let canvas = parentDoc.getElementById('roamly-water-canvas');
        if (!canvas) {
            if (parentWin._roamlyAnimFrame) {
                parentWin.cancelAnimationFrame(parentWin._roamlyAnimFrame);
            }

            canvas = parentDoc.createElement('canvas');
            canvas.id = 'roamly-water-canvas';
            canvas.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                pointer-events: none;
                z-index: 1;
                mix-blend-mode: normal;
            `;
            parentDoc.body.appendChild(canvas);

            const ctx = canvas.getContext('2d');
            let width = canvas.width = parentWin.innerWidth;
            let height = canvas.height = parentWin.innerHeight;

            parentWin.addEventListener('resize', () => {
                width = canvas.width = parentWin.innerWidth;
                height = canvas.height = parentWin.innerHeight;
            });

            let mouse = {
                x: width * 0.5,
                y: height * 0.42,
                smoothX: width * 0.5,
                smoothY: height * 0.42,
                lastRippleX: width * 0.5,
                lastRippleY: height * 0.42,
                lastSpawnTime: 0
            };

            // Active circular water waves around the cursor (kept small in count: max 4)
            const ripples = [];

            function spawnWaterRipple(x, y, maxRadius = 135, initialAlpha = 0.42) {
                if (ripples.length >= 4) {
                    ripples.shift();
                }
                ripples.push({
                    x: x,
                    y: y,
                    radius: 8,
                    maxRadius: maxRadius,
                    alpha: initialAlpha,
                    phase: Math.random() * Math.PI * 2
                });
            }

            parentDoc.addEventListener('mousemove', (e) => {
                mouse.x = e.clientX;
                mouse.y = e.clientY;

                const now = performance.now();
                const movedDist = Math.hypot(mouse.x - mouse.lastRippleX, mouse.y - mouse.lastRippleY);

                // Spawn a gentle circular water wave when cursor glides
                if (movedDist > 16 && (now - mouse.lastSpawnTime) > 50) {
                    spawnWaterRipple(mouse.x, mouse.y, 125 + Math.min(movedDist * 0.35, 45), 0.38);
                    mouse.lastRippleX = mouse.x;
                    mouse.lastRippleY = mouse.y;
                    mouse.lastSpawnTime = now;
                }
            });

            parentDoc.addEventListener('mousedown', (e) => {
                spawnWaterRipple(e.clientX, e.clientY, 175, 0.55);
            });

            // Sparkling purple/lilac/white micro-particles floating on the water surface
            const NUM_PARTICLES = 2000;
            const particles = [];
            const palette = ['#ffffff', '#f3e8ff', '#e9d5ff', '#d8b4fe', '#c084fc', '#a855f7'];
            for (let i = 0; i < NUM_PARTICLES; i++) {
                particles.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    vx: (Math.random() - 0.5) * 0.3,
                    vy: (Math.random() - 0.5) * 0.3,
                    size: Math.random() * 1.8 + 0.6,
                    color: palette[Math.floor(Math.random() * palette.length)],
                    phase: Math.random() * Math.PI * 2,
                    speed: Math.random() * 0.035 + 0.015
                });
            }

            function drawOrganicWaterRing(cx, cy, radius, phase, tick, lineWidth, strokeStyle, shadowBlur) {
                const SEGMENTS = 56;
                ctx.save();
                ctx.beginPath();
                for (let i = 0; i <= SEGMENTS; i++) {
                    const theta = (i / SEGMENTS) * Math.PI * 2;
                    // Subtle liquid surface undulation so the circle feels like real water
                    const waveWobble =
                        Math.sin(theta * 5 + tick * 2.2 + phase) * 2.2 +
                        Math.cos(theta * 3 - tick * 1.8 + phase) * 1.6;
                    const r = Math.max(1, radius + waveWobble);
                    const px = cx + Math.cos(theta) * r;
                    const py = cy + Math.sin(theta) * r;
                    if (i === 0) {
                        ctx.moveTo(px, py);
                    } else {
                        ctx.lineTo(px, py);
                    }
                }
                ctx.closePath();
                ctx.strokeStyle = strokeStyle;
                ctx.lineWidth = lineWidth;
                ctx.shadowColor = '#c084fc';
                ctx.shadowBlur = shadowBlur;
                ctx.stroke();
                ctx.restore();
            }

            let tick = 0;
            function render() {
                tick += 0.03;
                ctx.clearRect(0, 0, width, height);

                // Smoothly interpolate cursor aura center
                mouse.smoothX += (mouse.x - mouse.smoothX) * 0.75;
                mouse.smoothY += (mouse.y - mouse.smoothY) * 0.75;

                // 1. Ambient glowy purple water pool under the cursor
                const poolGlow = ctx.createRadialGradient(
                    mouse.smoothX, mouse.smoothY, 4,
                    mouse.smoothX, mouse.smoothY, 270
                );
                poolGlow.addColorStop(0, 'rgba(216, 180, 254, 0.24)');
                poolGlow.addColorStop(0.32, 'rgba(168, 85, 247, 0.15)');
                poolGlow.addColorStop(0.65, 'rgba(88, 28, 135, 0.06)');
                poolGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
                ctx.fillStyle = poolGlow;
                ctx.beginPath();
                ctx.arc(mouse.smoothX, mouse.smoothY, 270, 0, Math.PI * 2);
                ctx.fill();

                // 2. Update & draw circular water ripples around the mouse
                for (let i = ripples.length - 1; i >= 0; i--) {
                    const rp = ripples[i];
                    // Ease-out expansion like a real water wave
                    rp.radius += (rp.maxRadius - rp.radius) * 0.055 + 0.9;
                    const progress = rp.radius / rp.maxRadius;
                    const currentAlpha = rp.alpha * Math.pow(1 - progress, 1.55);

                    if (currentAlpha <= 0.01 || rp.radius >= rp.maxRadius) {
                        ripples.splice(i, 1);
                        continue;
                    }

                    // Primary outer water wave crest
                    drawOrganicWaterRing(
                        rp.x,
                        rp.y,
                        rp.radius,
                        rp.phase,
                        tick,
                        1.7 * (1 - progress * 0.4),
                        `rgba(233, 213, 255, ${currentAlpha.toFixed(3)})`,
                        14
                    );

                    // Subtle secondary inner harmonic ring for liquid depth
                    if (rp.radius > 24) {
                        drawOrganicWaterRing(
                            rp.x,
                            rp.y,
                            rp.radius * 0.72,
                            rp.phase + 1.2,
                            tick,
                            1.0,
                            `rgba(168, 85, 247, ${(currentAlpha * 0.55).toFixed(3)})`,
                            8
                        );
                    }
                }

                // 3. Update & draw sparkling particles that warp with cursor & water rings
                for (let i = 0; i < NUM_PARTICLES; i++) {
                    const pt = particles[i];
                    pt.phase += pt.speed;

                    const dx = mouse.smoothX - pt.x;
                    const dy = mouse.smoothY - pt.y;
                    const dist = Math.hypot(dx, dy) + 0.001;

                    // Gentle swirl around the cursor
                    if (dist < 240) {
                        const force = (1 - dist / 240);
                        const nx = dx / dist;
                        const ny = dy / dist;
                        pt.vx += (-ny * 0.32 + nx * 0.45) * force;
                        pt.vy += (nx * 0.32 + ny * 0.45) * force;
                    }

                    // Gentle radial push from passing circular water waves
                    for (let r = 0; r < ripples.length; r++) {
                        const rp = ripples[r];
                        const rdx = pt.x - rp.x;
                        const rdy = pt.y - rp.y;
                        const rDist = Math.hypot(rdx, rdy) + 0.001;
                        const bandDiff = Math.abs(rDist - rp.radius);
                        if (bandDiff < 24) {
                            const push = (1 - bandDiff / 24) * 0.22;
                            pt.vx += (rdx / rDist) * push;
                            pt.vy += (rdy / rDist) * push;
                        }
                    }

                    pt.vx *= 0.94;
                    pt.vy *= 0.94;
                    pt.x += pt.vx + Math.sin(pt.phase) * 0.16;
                    pt.y += pt.vy + Math.cos(pt.phase) * 0.16;

                    if (pt.x < 0) pt.x = width;
                    if (pt.x > width) pt.x = 0;
                    if (pt.y < 0) pt.y = height;
                    if (pt.y > height) pt.y = 0;

                    const proximityBoost = dist < 240 ? (1 - dist / 240) * 0.6 : 0;
                    const alpha = Math.min(1, (0.20 + (Math.sin(pt.phase) + 1) * 0.24) + proximityBoost);
                    const radius = pt.size + (dist < 180 ? (1 - dist / 180) * 1.1 : 0);

                    ctx.save();
                    ctx.globalAlpha = alpha;
                    ctx.fillStyle = pt.color;
                    ctx.shadowColor = '#d8b4fe';
                    ctx.shadowBlur = dist < 200 ? 10 : 4;
                    ctx.beginPath();
                    ctx.arc(pt.x, pt.y, radius, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();
                }

                parentWin._roamlyAnimFrame = parentWin.requestAnimationFrame(render);
            }
            parentWin._roamlyAnimFrame = parentWin.requestAnimationFrame(render);
        }
    })();
    </script>
    """,
    height=0,
    width=0,
)

# =====================================================================
# 2. CSS: ALIGNED NAVBAR, INSTANT UNDERLINE HOVER, EQUAL HERO SPACING
# =====================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
    {farray_font_css}

    [data-testid="stSidebar"], [data-testid="collapsedControl"], footer, #MainMenu {{
        display: none !important;
    }}
    [data-testid="stHeader"] {{
        background: transparent !important;
        height: 0px !important;
    }}
    iframe[title="streamlit_components_v1.html_v1"] {{
        display: none !important;
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #f5f3ff !important;
        -webkit-font-smoothing: antialiased;
    }}

    [data-testid="stAppViewContainer"] {{
        background-color: #000000 !important;
    }}
    [data-testid="stMain"] {{
        background: transparent !important;
    }}
    .block-container {{
        position: relative;
        z-index: 2;
        padding-top: 1.2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1120px !important;
    }}

    /* TARGET ONLY THE TOP NAVBAR HORIZONTAL BLOCK */
    div[data-testid="stHorizontalBlock"]:has(.nav-wordmark) {{
        background: rgba(255, 255, 255, 0.025) !important;
        backdrop-filter: blur(30px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(30px) saturate(180%) !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.20) !important;
        border-radius: 16px !important;
        padding: 10px 28px !important;
        box-shadow: 0 12px 34px rgba(0, 0, 0, 0.65) !important;
        align-items: center !important;
        margin-bottom: 1.6rem !important;
    }}

    /* Force vertical centering on every column inside the navbar */
    div[data-testid="stHorizontalBlock"]:has(.nav-wordmark) > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"]:has(.nav-wordmark) [data-testid="stMarkdownContainer"] {{
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    .nav-wordmark {{
        font-family: 'FARRAY', 'Inter', sans-serif !important;
        font-size: 1.4rem !important;
        font-weight: 400 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        color: #ffffff !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
        transform: translateY(-2px) !important;
    }}

    /* INSTANT REACTIVE UNDERLINE BUTTONS (NO OPAQUE BOX) */
    .stButton > button {{
        background: transparent !important;
        backdrop-filter: none !important;
        color: rgba(243, 232, 255, 0.85) !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0px !important;
        padding: 8px 6px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.98rem !important;
        font-weight: 400 !important;
        letter-spacing: -0.01em !important;
        white-space: nowrap !important;
        box-shadow: none !important;
        transition: color 0.04s linear, border-color 0.04s linear, text-shadow 0.04s linear !important;
    }}
    .stButton > button:hover,
    .stButton > button:focus,
    .stButton > button:active {{
        background: transparent !important;
        color: #ffffff !important;
        border: none !important;
        border-bottom: 2px solid #d8b4fe !important;
        box-shadow: 0 6px 14px -6px rgba(192, 132, 252, 0.85) !important;
        text-shadow: 0 0 14px rgba(216, 180, 254, 0.65) !important;
        transform: none !important;
    }}

    /* CENTERED HOME HERO WITH EQUAL VERTICAL SPACING */
    .home-stage {{
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        padding: 2.0rem 1rem 2.2rem 1rem !important;
        gap: 2.2rem !important;
        width: 100% !important;
    }}
    .home-eyebrow {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.74rem !important;
        font-weight: 400 !important;
        letter-spacing: 0.24em !important;
        text-transform: uppercase !important;
        color: #c084fc !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        text-align: center !important;
        width: 100% !important;
    }}
    .home-brand-center {{
        font-family: 'FARRAY', sans-serif !important;
        font-size: clamp(6.8rem, 14.5vw, 11rem) !important;
        font-weight: 400 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        line-height: 0.86 !important;
        margin: 0 !important;
        padding: 0 !important;
        color: #ffffff !important;
        text-align: center !important;
        width: 100% !important;
    }}
    .home-tagline {{
        font-family: 'Inter', sans-serif !important;
        font-size: 1.02rem !important;
        font-weight: 300 !important;
        color: #a1a1aa !important;
        max-width: 520px !important;
        margin: 0 auto !important;
        padding: 0 !important;
        line-height: 1.6 !important;
        letter-spacing: -0.01em !important;
        text-align: center !important;
    }}

    /* Minimalist Architectural Spec Footer on Home */
    .home-spec-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        margin-top: 5.5rem;
        padding-top: 1.6rem;
        gap: 2rem;
    }}
    .spec-index {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        color: #a855f7;
        letter-spacing: 0.12em;
        margin-bottom: 0.35rem;
    }}
    .spec-title {{
        font-size: 0.85rem;
        font-weight: 500;
        color: #f4f4f5;
        margin-bottom: 0.2rem;
    }}
    .spec-desc {{
        font-size: 0.78rem;
        font-weight: 300;
        color: #71717a;
        line-height: 1.5;
    }}

    /* Configurator Styling */
    .cfg-header {{
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 1.2rem;
        margin-bottom: 2rem;
    }}
    .cfg-eyebrow {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #c084fc;
        margin-bottom: 0.3rem;
    }}
    .cfg-title {{
        font-size: 2rem;
        font-weight: 300;
        letter-spacing: -0.04em;
        color: #ffffff;
        margin: 0;
    }}

    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {{
        background-color: rgba(255, 255, 255, 0.025) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 10px !important;
        color: #f4f4f5 !important;
    }}
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {{
        border-color: rgba(192, 132, 252, 0.55) !important;
    }}
    span[data-baseweb="tag"] {{
        background: rgba(168, 85, 247, 0.16) !important;
        border: 1px solid rgba(192, 132, 252, 0.32) !important;
        color: #f3e8ff !important;
        border-radius: 6px !important;
    }}
    label[data-testid="stWidgetLabel"] p {{
        font-family: 'JetBrains Mono', monospace !important;
        color: #a1a1aa !important;
        font-weight: 400 !important;
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
    }}

    .metric-strip {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding: 1.1rem 0;
        margin: 2.2rem 0 1.8rem 0;
    }}
    .metric-cell {{
        padding: 0 1rem;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }}
    .metric-cell:last-child {{
        border-right: none;
    }}
    .metric-k {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #71717a;
    }}
    .metric-v {{
        font-size: 1.25rem;
        font-weight: 300;
        letter-spacing: -0.03em;
        color: #ffffff;
        margin-top: 0.2rem;
    }}

    .section-label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #c084fc;
        margin: 2.2rem 0 0.75rem 0;
    }}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_road_geometry(coords_tuple):
    """Fetch real turn-by-turn street geometry from OpenStreetMap OSRM so routes follow roads."""
    if len(coords_tuple) < 2:
        return [list(c) for c in coords_tuple]

    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords_tuple])
    osrm_endpoints = [
        f"https://routing.openstreetmap.de/routed-foot/route/v1/driving/{coord_str}?overview=full&geometries=geojson",
        f"https://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson"
    ]
    headers = {"User-Agent": "RoamlyMinimalStudio/3.3"}

    for url in osrm_endpoints:
        try:
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                routes = resp.json().get("routes", [])
                if routes:
                    geojson_pts = routes[0]["geometry"]["coordinates"]
                    return [[pt[1], pt[0]] for pt in geojson_pts]
        except Exception:
            continue

    return [list(c) for c in coords_tuple]


def generate_trip(dest, days, interests, pace, budget, crew, transit):
    resp = requests.post(
        f"{API_URL}/generate-itinerary",
        json={
            "destination": dest,
            "days": days,
            "interests": interests,
            "pace": pace
        },
        timeout=25
    )
    if resp.status_code == 200:
        data = resp.json()
        data["budget"] = budget
        data["crew"] = crew
        data["transit"] = transit
        st.session_state["current_itinerary"] = data
        st.session_state["active_dest"] = dest
    else:
        st.error(resp.json().get("detail", "Could not generate itinerary."))


# =====================================================================
# 3. CLEAR LIQUID GLASS NAVBAR (LEFT-CENTERED LOGO & WIDER TABS)
# =====================================================================
nav_brand_col, nav_space_col, nav_home_col, nav_cfg_col = st.columns([2.4, 3.2, 1.0, 1.9])

with nav_brand_col:
    st.markdown('<div class="nav-wordmark">ROAMLY</div>', unsafe_allow_html=True)

with nav_home_col:
    if st.button("Home", key="nav_home", use_container_width=True):
        st.session_state["nav_page"] = "Home"
        st.rerun()

with nav_cfg_col:
    if st.button("Trip Configurator", key="nav_cfg", use_container_width=True):
        st.session_state["nav_page"] = "Configurator"
        st.rerun()


# =====================================================================
# 4. PAGE 1: HOME (EQUAL SPACING + CENTERED SUBTITLE + WATER RIPPLES)
# =====================================================================
if st.session_state["nav_page"] == "Home":
    st.markdown("""
    <div class="home-stage">
        <div class="home-eyebrow">Spatial Itinerary Architecture</div>
        <div class="home-brand-center">ROAMLY</div>
        <div class="home-tagline">
            Bespoke holiday itineraries organized by KMeans spatial clustering and real street-grid routing.
        </div>
    </div>
    """, unsafe_allow_html=True)

    btn_l, btn_c, btn_r = st.columns([2.2, 1.4, 2.2])
    with btn_c:
        if st.button("Trip Configurator  →", key="home_cta", use_container_width=True):
            st.session_state["nav_page"] = "Configurator"
            st.rerun()

    st.markdown("""
    <div class="home-spec-grid">
        <div>
            <div class="spec-index">01 / CLUSTERING</div>
            <div class="spec-title">Scikit-Learn KMeans</div>
            <div class="spec-desc">Partitions city coordinates into compact daily geographic zones.</div>
        </div>
        <div>
            <div class="spec-index">02 / ROUTING</div>
            <div class="spec-title">Geopy &amp; OSRM Street Grid</div>
            <div class="spec-desc">Sequences stops by nearest-neighbor geodesic distance along real roads.</div>
        </div>
        <div>
            <div class="spec-index">03 / DATA ENGINE</div>
            <div class="spec-title">FastAPI, Pandas &amp; SQLite</div>
            <div class="spec-desc">Cleans live attraction telemetry into interactive schedules.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================================
# 5. PAGE 2: DEDICATED TRIP CONFIGURATOR
# =====================================================================
elif st.session_state["nav_page"] == "Configurator":
    st.markdown("""
    <div class="cfg-header">
        <div class="cfg-eyebrow">01 / Parameters</div>
        <h2 class="cfg-title">Trip Configurator</h2>
    </div>
    """, unsafe_allow_html=True)

    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns([1.8, 0.9, 1.1, 1.1])
    with r1_c1:
        destination = st.text_input(
            "Destination City",
            value=st.session_state.get("active_dest", "Paris, France"),
            placeholder="Paris, Tokyo, Rome, London..."
        )
    with r1_c2:
        days = st.slider("Duration (Days)", min_value=1, max_value=7, value=3)
    with r1_c3:
        pace = st.select_slider("Daily Pace", options=["Relaxed", "Moderate", "Packed"], value="Moderate")
    with r1_c4:
        crew = st.selectbox("Travel Party", ["Solo", "Couple", "Friends", "Family"])

    r2_c1, r2_c2, r2_c3 = st.columns([2.2, 1.1, 1.1])
    with r2_c1:
        interests = st.multiselect(
            "Curated Interests",
            ["Culture & History", "Architecture", "Food & Cafes", "Nature & Parks", "Entertainment & Shopping"],
            default=["Culture & History", "Architecture", "Food & Cafes"]
        )
    with r2_c2:
        budget = st.selectbox("Budget Tier", ["Essential ($)", "Comfort ($$)", "Luxury ($$$)"], index=1)
    with r2_c3:
        transit = st.selectbox("Transit Mode", ["Walking & Metro", "Chauffeur / Cab", "Scenic Walk"])

    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
    g1, g2, g3 = st.columns([1.6, 1.2, 1.6])
    with g2:
        generate_btn = st.button("Generate Itinerary  →", key="cfg_generate", use_container_width=True)

    if generate_btn:
        if not destination.strip():
            st.error("Enter a valid destination city.")
        elif not interests:
            st.error("Select at least one interest category.")
        else:
            with st.spinner("Computing KMeans clusters & street geometry..."):
                try:
                    generate_trip(destination, days, interests, pace, budget, crew, transit)
                except Exception:
                    st.error("FastAPI backend offline. Run `uvicorn backend:app --reload --port 8000` in Terminal 1.")

    if "current_itinerary" not in st.session_state:
        try:
            generate_trip(destination, days, interests, pace, budget, crew, transit)
        except Exception:
            pass

    if "current_itinerary" in st.session_state:
        data = st.session_state["current_itinerary"]
        itinerary = data["itinerary"]
        all_stops = [s for d in itinerary for s in d["stops"]]
        total_km = round(sum(d["total_distance_km"] for d in itinerary), 2)

        st.markdown(f"""
        <div class="metric-strip">
            <div class="metric-cell">
                <div class="metric-k">Destination</div>
                <div class="metric-v">{data['destination']}</div>
            </div>
            <div class="metric-cell">
                <div class="metric-k">KMeans Clusters</div>
                <div class="metric-v">{data['days']} Days · {data['pace']}</div>
            </div>
            <div class="metric-cell">
                <div class="metric-k">Curated Stops</div>
                <div class="metric-v">{len(all_stops)} Landmarks</div>
            </div>
            <div class="metric-cell">
                <div class="metric-k">Total Street Distance</div>
                <div class="metric-v">{total_km} km</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        day_filter = st.radio(
            "Filter Day",
            options=["All Days"] + [f"Day {d['day']}" for d in itinerary],
            horizontal=True,
            label_visibility="collapsed"
        )

        # -----------------------------------------------------------------
        # OUTPUT 1: STREET-SNAPPED FOLIUM MAP DIRECTLY BELOW GENERATE
        # -----------------------------------------------------------------
        st.markdown('<div class="section-label">02 / Street-Snapped Spatial Map (Folium + OSRM)</div>', unsafe_allow_html=True)

        fmap = folium.Map(
            location=[data["center"]["lat"], data["center"]["lon"]],
            zoom_start=13,
            tiles="OpenStreetMap"
        )

        fmap.get_root().header.add_child(folium.Element("""
            <style>
                .leaflet-tile-pane {
                    filter: invert(100%) hue-rotate(180deg) brightness(85%) contrast(95%);
                }
                .leaflet-container {
                    background: #000000 !important;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                }
            </style>
        """))

        marker_colors = ["purple", "darkpurple", "pink", "cadetblue", "blue"]
        line_colors = ["#c084fc", "#a855f7", "#e879f9", "#818cf8", "#d8b4fe"]
        visible_pts = []

        for idx, day_obj in enumerate(itinerary):
            d_label = f"Day {day_obj['day']}"
            if day_filter != "All Days" and day_filter != d_label:
                continue

            m_col = marker_colors[idx % len(marker_colors)]
            l_col = line_colors[idx % len(line_colors)]
            day_coords = []

            for stop_idx, stop in enumerate(day_obj["stops"], start=1):
                pt = (float(stop["lat"]), float(stop["lon"]))
                day_coords.append(pt)
                visible_pts.append(pt)

                folium.Marker(
                    location=[pt[0], pt[1]],
                    tooltip=f"Day {day_obj['day']} · {stop['slot']} — {stop['name']}",
                    icon=folium.Icon(color=m_col, icon="info-sign")
                ).add_to(fmap)

            if len(day_coords) > 1:
                road_geometry = get_road_geometry(tuple(day_coords))
                folium.PolyLine(
                    road_geometry,
                    color=l_col,
                    weight=4,
                    opacity=0.9,
                    tooltip=f"Day {day_obj['day']} Street Path ({day_obj['total_distance_km']} km)"
                ).add_to(fmap)

        if len(visible_pts) > 1:
            fmap.fit_bounds(visible_pts, padding=(28, 28))

        st_folium(fmap, width=None, height=450, returned_objects=[])

        # -----------------------------------------------------------------
        # OUTPUT 2: INTERACTIVE DAY-BY-DAY SCHEDULE TABLE BELOW THE MAP
        # -----------------------------------------------------------------
        st.markdown(
            f'<div class="section-label">03 / Interactive Day-by-Day Events ({data["days"]} Days)</div>',
            unsafe_allow_html=True
        )

        cost_tier = {"Essential ($)": 15, "Comfort ($$)": 32, "Luxury ($$$)": 75}.get(
            data.get("budget", "Comfort ($$)"), 32
        )

        rows = []
        for day_obj in itinerary:
            d_label = f"Day {day_obj['day']}"
            if day_filter != "All Days" and day_filter != d_label:
                continue
            for stop_idx, stop in enumerate(day_obj["stops"], start=1):
                rows.append({
                    "Done": False,
                    "Day": d_label,
                    "Order": f"0{stop_idx}",
                    "Time": stop["slot"],
                    "Attraction": stop["name"],
                    "Category": stop["category"],
                    "Rating": float(stop["rating"]),
                    "Leg Distance": float(stop["distance_from_prev_km"]),
                    "Est. Budget": int(cost_tier + (hash(stop["name"]) % 14)),
                    "Navigation": f"https://www.google.com/maps/search/?api=1&query={stop['lat']},{stop['lon']}"
                })

        edited_df = st.data_editor(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Done": st.column_config.CheckboxColumn("✓"),
                "Order": st.column_config.TextColumn("#"),
                "Attraction": st.column_config.TextColumn("Event / Landmark", width="large"),
                "Rating": st.column_config.NumberColumn("Rating", format="%.1f ★"),
                "Leg Distance": st.column_config.NumberColumn("Distance", format="%.2f km"),
                "Est. Budget": st.column_config.NumberColumn("Est. Cost", format="$%d"),
                "Navigation": st.column_config.LinkColumn("Map", display_text="Open ↗")
            }
        )

        exp_col1, exp_col2 = st.columns([1, 2])
        with exp_col1:
            st.download_button(
                "Export Schedule (CSV)",
                data=edited_df.to_csv(index=False).encode("utf-8"),
                file_name=f"roamly_{data['destination'].lower().replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with st.expander("04 / KMeans Spatial Centroids & Distance Analytics (Matplotlib)"):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.2))
            fig.patch.set_facecolor("#000000")

            for idx, day_obj in enumerate(itinerary):
                c_hex = line_colors[idx % len(line_colors)]
                lons = [s["lon"] for s in day_obj["stops"]]
                lats = [s["lat"] for s in day_obj["stops"]]
                ax1.scatter(lons, lats, color=c_hex, s=65, label=f"Day {day_obj['day']}", edgecolors="white")
            ax1.set_facecolor("#08040f")
            ax1.set_title("KMeans Cluster Distribution", color="#e9d5ff", fontsize=9.5)
            ax1.tick_params(colors="#71717a", labelsize=8)
            ax1.legend(facecolor="#000000", edgecolor="#2e1065", labelcolor="white", fontsize=8)
            for spine in ax1.spines.values():
                spine.set_color("#1e1035")

            ax2.bar(
                [f"Day {d['day']}" for d in itinerary],
                [d["total_distance_km"] for d in itinerary],
                color="#c084fc",
                width=0.42
            )
            ax2.set_facecolor("#08040f")
            ax2.set_title("Daily Geodesic Distance (km)", color="#e9d5ff", fontsize=9.5)
            ax2.tick_params(colors="#71717a", labelsize=8)
            for spine in ax2.spines.values():
                spine.set_color("#1e1035")

            plt.tight_layout()
            st.pyplot(fig)