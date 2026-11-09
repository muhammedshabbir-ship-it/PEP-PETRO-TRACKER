import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import D, N, X

st.set_page_config(page_title="PEP Petro Tracker", layout="wide", initial_sidebar_state="collapsed")

NAT = D["nat"]
CITIES = D["cities"]
CODES = [c["code"] for c in CITIES]
BLUE, RED, NAVY = "#1f6fd1", "#ff0000", "#0a1f5c"
WAVES = ["W9", "W10", "W11", "W12", "W13", "W14"]

st.markdown(
    f"""
<style>
.block-container{{padding:0.6rem 1rem 2rem 1rem;max-width:100%}}
header[data-testid="stHeader"]{{display:none}}
.title{{background:{NAVY};color:#fff;text-align:center;font-weight:800;font-size:26px;
 letter-spacing:.5px;padding:6px 0;border:2px solid #000;margin-bottom:10px}}
.sub{{text-align:center;color:#555;font-size:12px;margin:-6px 0 10px}}
.fp{{border:1.5px solid #000;margin-bottom:8px;background:#fff}}
.fp .h{{font-weight:700;font-size:12px;padding:2px 6px;border-bottom:1px solid #ccc;color:#000}}
.pill{{display:inline-block;background:#5b9bd5;color:#fff;border-radius:6px;font-size:11px;padding:1px 9px;margin:2px}}
.pill.off{{background:#c9c9c9;color:#444}}
table.t{{border-collapse:collapse;width:100%;font-size:12px;border:2px solid #000;background:#fff;color:#000}}
table.t th,table.t td{{padding:2px 6px;text-align:right;border-bottom:1px solid #d0d0d0;white-space:nowrap}}
table.t th:first-child,table.t td:first-child{{text-align:left;font-weight:600}}
table.t th{{font-weight:700;text-decoration:underline}}
.hd{{color:#fff;font-weight:700;text-align:center;padding:2px;font-size:13px;text-decoration:underline}}
.sep{{border-left:2px solid #000}}
.g{{color:#00a651;font-weight:600}} .r{{color:#e60000;font-weight:600}} .n{{color:#000}}
.natrow td{{background:#e8eef8;font-weight:700}}
.card{{border:1.5px solid #000;padding:4px;background:#fff;margin-bottom:8px}}
</style>
<div class="title">PEP PETRO TRACKER</div>
<div class="sub">Wave 14 · OCT-H2 vs wave 13 · OCT-H1 · 244 Petro audits · 9 cities · Source: PEP MA Wave-14 report</div>
""",
    unsafe_allow_html=True,
)


def idx_cell(v):
    if v is None:
        return "<td></td>"
    cls = "g" if v >= 103 else "r" if v <= 97 else "n"
    return f'<td class="{cls}">{v:.0f}%</td>'


HL = "background:#fff3b0;"


def table(title, color_l, color_r, left_heads, right_heads, rows, right_title, hl_left=None, hl_right=None):
    """rows: list of (label, [left values], [index values], is_national).
    hl_left / hl_right: column index (in lv / iv) to highlight."""
    nl, nr = len(left_heads), len(right_heads)
    h = f'<table class="t"><tr><td colspan="{nl+1}" class="hd" style="background:{color_l}">{title}</td>'
    h += f'<td colspan="{nr}" class="hd sep" style="background:{color_r}">{right_title}</td></tr>'
    h += "<tr><th>CITY</th>" + "".join(
        f'<th style="{HL if i == hl_left else ""}">{x}</th>' for i, x in enumerate(left_heads))
    h += "".join(
        f'<th class="{"sep" if i==0 else ""}" style="{HL if i == hl_right else ""}">{x}</th>'
        for i, x in enumerate(right_heads)) + "</tr>"
    for label, lv, iv, nat in rows:
        h += f'<tr class="{"natrow" if nat else ""}"><td>{label}</td>'
        h += "".join(f'<td style="{HL if i == hl_left else ""}">{v}</td>' for i, v in enumerate(lv))
        for i, v in enumerate(iv):
            c = idx_cell(v)
            st_ = ("border-left:2px solid #000;" if i == 0 else "") + (HL if i == hl_right else "")
            if st_:
                c = c.replace("<td", f'<td style="{st_}"', 1)
            h += c
        h += "</tr>"
    return h + "</table>"


def ix(a, b):
    return None if not b else a / b * 100


def pct(v):
    return f"{v:.1f}%"


left, mid, right = st.columns([1.0, 4.6, 2.5], gap="small")

# ---------------- LEFT FILTER PANEL ----------------
with left:
    st.markdown('<div class="fp"><div class="h">REGION</div></div>', unsafe_allow_html=True)
    sel = [c for c in CODES if st.checkbox(c, value=True, key=f"city_{c}")]
    st.markdown(
        '<div class="fp"><div class="h">CHANNEL</div><span class="pill">Petro</span></div>'
        '<div class="fp"><div class="h">WAVE</div></div>',
        unsafe_allow_html=True,
    )
    wave = st.radio("Wave", ["14 · OCT-H2 (latest)", "13 · OCT-H1"], label_visibility="collapsed")
    st.markdown('<div class="fp"><div class="h">KPI (tables + charts)</div></div>', unsafe_allow_html=True)
    metric = st.radio(
        "KPI",
        ["Availability", "Fullness", "Purity", "Utilization", "SOS"],
        index=4,
        label_visibility="collapsed",
    )

W14 = wave.startswith("14")
KEYS = ("av", "fu", "pu", "ut", "sos")
KLAB = {"Availability": "av", "Fullness": "fu", "Purity": "pu", "Utilization": "ut", "SOS": "sos"}
key = KLAB[metric]
kidx = KEYS.index(key)
WLAB = "WAVE 14" if W14 else "WAVE 13"


def cv(c, k):
    """City KPI value in the selected wave (wave 13 = wave 14 minus the change vs last period)."""
    return c[k] if W14 else c[k] - c["d" + k]


def nv(k):
    """National KPI value in the selected wave."""
    return NAT[k] if W14 else NAT["tr"][k][-2]


rows_c = [c for c in CITIES if c["code"] in sel] or CITIES
rows_c = sorted(rows_c, key=lambda c: -cv(c, "sos"))

# ---------------- MIDDLE TABLES ----------------
with mid:
    # 1. Cooler KPIs
    rows = [("National", [NAT["n"], *[pct(nv(k)) for k in KEYS]], [100] * 5, True)]
    for c in rows_c:
        rows.append((c["code"], [c["n"], *[pct(cv(c, k)) for k in KEYS]],
                     [ix(cv(c, k), nv(k)) for k in KEYS], False))
    st.markdown(
        table(f"COOLER KPIs ({WLAB})", "#0b5cab", "#2f7fd0",
              ["STORES", "AVAIL", "FULLNESS", "PURITY", "UTIL", "SOS"],
              ["AVAIL", "FULL", "PURITY", "UTIL", "SOS"], rows,
              "KPIs - INDEXING VS NATIONAL", hl_left=kidx + 1, hl_right=kidx),
        unsafe_allow_html=True)
    st.write("")

    # 2. Share of shelf
    rows = [("National", [pct(NAT[k]) for k in ("sos", "ko", "mbl", "gb", "oth")],
             [ix(NAT["sos"], NAT["ko"]), ix(NAT["sos"], NAT["mbl"]), ix(NAT["sos"], NAT["oth"])], True)]
    for c in rows_c:
        rows.append((c["code"], [pct(c[k]) for k in ("sos", "ko", "mbl", "gb", "oth")],
                     [ix(c["sos"], c["ko"]), ix(c["sos"], c["mbl"]), ix(c["sos"], c["oth"])], False))
    st.markdown(
        table("SHARE OF SHELF (SOS, ALL COOLERS)", "#1b3a8a", "#3a5fb8",
              ["PEP", "KO", "MBL", "GB", "OTHERS"], ["PEP vs KO", "PEP vs MBL", "PEP vs OTH"], rows,
              "SOS - INDEXING VS COMP"),
        unsafe_allow_html=True)
    st.write("")

    # 3. Brand duels
    def duel_vals(b):
        return ([f'{b["pepsi"]:.1f}%', f'{b["coke"]:.1f}%', f'{b["up"]:.1f}%', f'{b["sprite"]:.1f}%',
                 f'{b["mir"]:.1f}%', f'{b["fanta"]:.1f}%'],
                [ix(b["pepsi"], b["coke"]), ix(b["up"], b["sprite"]), ix(b["mir"], b["fanta"])])

    lv, iv = duel_vals(NAT["b"])
    rows = [("National", lv, iv, True)]
    for c in rows_c:
        lv, iv = duel_vals(c["b"])
        rows.append((c["code"], lv, iv, False))
    st.markdown(
        table("BRAND SHARE OF COOLER FACINGS", "#2e7d32", "#43a047",
              ["PEPSI", "COKE", "7UP", "SPRITE", "MIRINDA", "FANTA"],
              ["PEPSI vs COKE", "7UP vs SPRITE", "MIR vs FANTA"], rows,
              "BRAND - INDEXING VS COMP"),
        unsafe_allow_html=True)
    if not W14:
        st.info("Wave 13 values are rebuilt from wave 14 minus the change vs last period. "
                "The share-of-shelf and brand tables above only exist for wave 14 in the source data.")
    st.caption("Index = PEP figure ÷ comparator × 100. Green ≥ 103%, red ≤ 97%. "
               "Availability / Fullness / Purity / Utilization are measured only in stores with a PEP cooler; small bases (Sukkur, Islamabad, Faisalabad) are directional.")

# ---------------- RIGHT CHARTS ----------------
def layout(fig, title, h=250):
    fig.update_layout(title=dict(text=title, font=dict(size=13)), height=h, margin=dict(l=8, r=8, t=36, b=8),
                      legend=dict(orientation="h", y=-0.18, x=0), bargap=0.25, paper_bgcolor="white",
                      plot_bgcolor="white", font=dict(color="#222", size=10),
                      yaxis=dict(showgrid=False, showticklabels=False))
    return fig


with right:
    n_w = 6 if W14 else 5
    ser = NAT["tr"][key][:n_w]
    f1 = go.Figure(go.Bar(x=WAVES[:n_w], y=ser, marker_color=BLUE, name=f"PEP {metric}",
                          text=[f"{v:.1f}" for v in ser], textposition="outside"))
    f1.update_yaxes(range=[0, max(ser) * 1.15])
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.plotly_chart(layout(f1, f"{metric} - Trend up to {WLAB.title()} (National)"), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    vals_c = [cv(c, key) for c in rows_c]
    f2 = go.Figure(go.Bar(x=[c["code"][:3] for c in rows_c], y=vals_c, marker_color=BLUE,
                          name=f"PEP {metric}", text=[f"{v:.0f}" for v in vals_c], textposition="outside"))
    f2.add_trace(go.Scatter(x=[c["code"][:3] for c in rows_c], y=[nv(key)] * len(rows_c), mode="lines",
                            line=dict(color=RED, dash="dash"), name=f"National {nv(key):.1f}%"))
    f2.update_yaxes(range=[0, max(vals_c + [nv(key)]) * 1.15])
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.plotly_chart(layout(f2, f"{metric} by City - {WLAB.title()}"), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    f3 = go.Figure()
    f3.add_trace(go.Bar(x=[c["code"][:3] for c in rows_c], y=[c["b"]["pepsi"] for c in rows_c],
                        name="Pepsi", marker_color=BLUE))
    f3.add_trace(go.Bar(x=[c["code"][:3] for c in rows_c], y=[c["b"]["coke"] for c in rows_c],
                        name="Coke", marker_color=RED))
    f3.update_layout(barmode="group")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.plotly_chart(layout(f3, "Pepsi vs Coke - % of Cooler Facings by City"), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- DETAIL TABS ----------------
st.markdown("---")
t1, t2, t3, t4, t5, t6 = st.tabs(
    ["Summary", "City deep dive", "Issue deep dive", "Root cause & plan", "Outlets to fix first", "Next steps"])

with t1:
    for s in N["sum"]:
        st.markdown(f"- {s}", unsafe_allow_html=True)
    st.markdown("**Why the national numbers moved**")
    for s in N["why"]:
        st.markdown(f"- {s}")

with t2:
    city = st.selectbox("City", CODES, index=CODES.index("Lahore"))
    c = next(x for x in CITIES if x["code"] == city)
    nn = N["c"][city]
    st.subheader(f"{city} · {nn['tag']}")
    cols = st.columns(5)
    for col, (k, lab) in zip(cols, [("av", "Availability"), ("fu", "Fullness"), ("pu", "Purity"),
                                    ("ut", "Utilization"), ("sos", "SOS")]):
        col.metric(lab, pct(c[k]), f"{c['d'+k]:+.1f} pp")
    a, b = st.columns(2)
    with a:
        av, fu, pu = c["av"] / 100, c["fu"] / 100, c["pu"] / 100
        vals = {"Productive PEP cooler": av * fu * pu, "Purity loss": av * fu * (1 - pu),
                "Fullness loss": av * (1 - fu), "No PEP cooler": 1 - av}
        fig = go.Figure(go.Bar(y=list(vals), x=[v * 100 for v in vals.values()], orientation="h",
                               marker_color=["#2dd4a0", "#fbbf24", "#f97316", "#ff6b6b"],
                               text=[f"{v*100:.0f}%" for v in vals.values()], textposition="auto"))
        st.plotly_chart(layout(fig, "Cooler opportunity (out of 100 stores)", 260), use_container_width=True)
        fig = go.Figure(go.Bar(x=["PEP", "KO", "MBL", "GB", "Others"],
                               y=[c["sos"], c["ko"], c["mbl"], c["gb"], c["oth"]],
                               marker_color=[BLUE, RED, "#fbbf24", "#a78bfa", "#94a3b8"]))
        st.plotly_chart(layout(fig, "SOS split", 240), use_container_width=True)
    with b:
        st.markdown("**What is behind the numbers**")
        for w in nn["why"]:
            st.markdown(f"- {w}")
        st.markdown("**Outlet gaps (audits)**")
        gm = X["gm"][city]
        st.dataframe(pd.DataFrame({"Gap": list(gm), "Audits": list(gm.values())}),
                     hide_index=True, use_container_width=True)
        p = X["ps"][city]
        st.markdown("**Franchise panels**")
        st.dataframe(pd.DataFrame([["Bottler", *p[0]], ["Snapp", *p[1]]],
                                  columns=["Panel", "Audits", "Availability %", "SOS %"]),
                     hide_index=True, use_container_width=True)

with t3:
    gcols = st.columns(2)
    for i, s in enumerate(X["iss"]):
        with gcols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{i+1}. {s['t']}**")
                for e in s["ev"]:
                    st.markdown(f"- {e}")
                st.caption(f"Most affected: {s['w']}")
    st.markdown("**Where each gap sits (audits by primary gap)**")
    gdf = pd.DataFrame(X["gm"]).fillna(0).astype(int)
    gdf["Total"] = gdf.sum(axis=1)
    st.dataframe(gdf, use_container_width=True)

with t4:
    st.caption("Owners are roles (the data has no names). W15 = Nov-H1, W16 = Nov-H2, W17 = Dec-H1, W18 = Dec-H2.")
    for i, p in enumerate(X["plan"]):
        with st.expander(p["m"], expanded=(i == 0)):
            st.markdown(f"**Challenge:** {p['ch']}")
            st.markdown("**Root causes**")
            for w in p["why"]:
                st.markdown(f"- {w}")
            st.markdown("**Corrective actions**")
            st.dataframe(pd.DataFrame(p["act"], columns=["Action", "Owner (role)", "When"]),
                         hide_index=True, use_container_width=True)
            st.markdown("**Targets**")
            st.dataframe(pd.DataFrame(p["tg"], columns=["Metric", "Now", "Target", "By"]),
                         hide_index=True, use_container_width=True)
            st.caption(p["nt"])

with t5:
    st.caption("Lowest-SOS Petro priority outlets. Full lists are in PEPSI_Outlet_Gap_Lists_Wave14.xlsx.")
    oc = st.columns(3)
    for col, (city, lst) in zip(oc, X["top"].items()):
        with col:
            st.markdown(f"**{city}**")
            st.dataframe(pd.DataFrame(lst, columns=["Outlet", "Panel", "Gap", "SOS %"]),
                         hide_index=True, use_container_width=True)

with t6:
    st.markdown("""
- **Analysis:** ready now on wave 14 data.
- **Walkthrough (45 min):** 1) Petro root causes, 2) Faisalabad, Multan and Lahore plans, 3) owners and targets, 4) decisions: cooler budget for 23 coolers, Petro head-office cooler-use rule, audit fixes. Best held before W16 starts (16 Nov).
- **Needs:** named owners, the meeting slot, SKU-level MSL data.
""")