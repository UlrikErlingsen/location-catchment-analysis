from html import escape

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from reachsignal import __version__, model, portable as io
from reachsignal.ui import signal_theme as sig
from reachsignal.ui.keys import NS, k
from reachsignal.ui.workspace import Workspace

MAP_POINTS = 3_000    # more customer areas than this are aggregated into a grid on the map
TABLE_ROWS = 10_000   # rows shown on screen per table; exports hold every row


def ready(w,candidate=None):
    if not w.reviewed:
        st.info("Check the sources and model assumptions in Edit & review before calculating location scenarios.")
        return False
    count,missing=w.cached(f"missing:{candidate}",lambda: model.readiness_summary(w.d,candidate,12))
    if count:
        more=f"; and {count-len(missing):,} more" if count>len(missing) else ""
        st.warning("Missing model inputs: "+"; ".join(missing)+more)
        return False
    return True


def show_table(frame,what,digits,by=None):
    """Show a result table; very long tables show their largest rows and say so."""
    shown=frame
    if len(frame)>TABLE_ROWS:
        shown=frame.nlargest(TABLE_ROWS,by) if by else frame.head(TABLE_ROWS)
    st.dataframe(shown.round(digits),hide_index=True,width="stretch")
    if len(frame)>TABLE_ROWS:
        order=f" with the most {by}" if by else ""
        st.caption(f"Showing {TABLE_ROWS:,} of {len(frame):,} {what}{order}. The Excel and ZIP exports hold every row.")


def coordinate_map(w,result,candidate,metric):
    sites=model.active_sites(w.d,candidate)
    areas=w.d["areas"]
    rows=areas+sites
    if any(r["latitude"] is None for r in rows):
        st.info("Add coordinates to show the map. The supplied travel-time matrix can still support the tables below.")
        return
    x,y=w.cached(f"xy:{candidate}",lambda: model.local_xy(rows))
    n=len(areas)
    frame=result["areas"]
    field,title={"Modeled own share":("own_share","Modeled own share (%)"),"Outside share":("outside_share","Outside share (%)"),"Distance to nearest site":("nearest_any","Nearest site distance")}[metric]
    values=frame[field].to_numpy(dtype=float)*(100 if "share" in field else 1)
    demand=frame["demand"].to_numpy(dtype=float)
    if n>MAP_POINTS:
        grid,size=model.grid_aggregate(x[:n],y[:n],demand,values)
        sizes=6+24*np.sqrt(grid.weight/max(1.0,float(grid.weight.max())))
        hover=[f"{a:,} areas<br>Demand: {dem:,.0f}<br>{title}: {v:.2f}" for a,dem,v in zip(grid.areas,grid.weight,grid.value)]
        fig=go.Figure(go.Scatter(x=grid.x,y=grid.y,mode="markers",marker={"size":sizes,"color":grid.value,"colorscale":"Viridis","showscale":True,"colorbar":{"title":title}},
                                 hovertext=hover,hoverinfo="text",name="Customer areas (grid)"))
        note=(f"{n:,} customer areas are combined into {len(grid):,} grid cells of about {size:,.1f} km for display; colours are "
              "demand-weighted averages. Totals and tables use every area.")
    else:
        sizes=14+30*np.sqrt(demand/max(1,float(demand.max())))
        fig=go.Figure(go.Scatter(x=x[:n],y=y[:n],mode="markers+text",text=[escape(a["name"]) for a in areas],textposition="top center",
                                 marker={"size":sizes,"color":values,"colorscale":"Viridis","showscale":True,"colorbar":{"title":title}},
                                 hovertext=[escape(a["name"])+f"<br>Demand: {a['demand']:,.0f}<br>{title}: {v:.2f}" for a,v in zip(areas,values)],hoverinfo="text",name="Customer areas"))
        note=None
    colors={"own":"#326384","competitor":"#aa5d83","candidate":"#56633f"}
    symbols={"own":"square","competitor":"diamond","candidate":"star"}
    for role in colors:
        indices=[i for i,s in enumerate(sites) if s["role"]==role]
        if indices:
            fig.add_scatter(x=[x[n+i] for i in indices],y=[y[n+i] for i in indices],mode="markers+text" if len(sites)<=60 else "markers",
                            text=[escape(sites[i]["id"]) for i in indices],
                            textposition="bottom center",marker={"size":17,"color":colors[role],"symbol":symbols[role],"line":{"color":"white","width":1}},
                            hovertext=[escape(sites[i]["name"]) for i in indices],hoverinfo="text",name=role.title()+" sites")
    fig.update_layout(height=530,xaxis_title="East / west · local km",yaxis_title="North / south · local km",legend={"orientation":"h","y":1.12},margin={"t":45})
    fig.update_yaxes(scaleanchor="x",scaleratio=1)
    sig.chart(NS,fig,key=k("map"))
    st.caption("Offline coordinate map, north up, drawn locally without map tiles. Marker sizes use relative demand; colors use the selected model output. This schematic contains no streets or travel routes.")
    if note:
        st.caption(note)
    if max(float(np.ptp(x)),float(np.ptp(y)))>500:
        st.warning("This is a broad geographic extent. The local coordinate sketch distorts geometry; use the distance tables for interpretation.")


def export_tables(p):
    """Input and result tables for the Excel and ZIP exports (runs when a download is clicked, outside the script)."""
    d=p["data"]
    tables={name:pd.DataFrame(d[name]) for name in model.TITLES}
    if io.reviewed(p) and not model.readiness_summary(d,limit=0)[0]:
        tables.update({"baseline_"+name:v for name,v in model.allocate(d).items() if isinstance(v,pd.DataFrame)})
        tables["candidate_comparison"]=model.compare(d)
    return tables


def render():
    sig.apply(NS)
    w=Workspace(NS,model)
    sig.sidebar_brand(NS,"Explore location access and catchment choices.")
    pages=["Overview","1 · Add your data","2 · Edit & review","3 · Catchment map","4 · Candidate comparison","5 · Export","Research & limits"]
    with st.sidebar:
        page=st.radio("Navigate",pages,label_visibility="collapsed",key=k("page"))
        st.caption("EXCEL · CSV · MANUAL · OPTIONAL AI")
        if st.button("Reset fictional demo",key=k("reset")):
            w.reset()
            st.rerun()
    sig.masthead(NS,["Location scenarios","Visible assumptions","Offline maps"])
    w.status()
    try:
        if page==pages[0]:
            sig.hero(NS,eyebrow="LOCATION & CATCHMENT PLANNING",title="See where you reach.",em="Compare the next location.",
                     body="Bring customer areas, site evidence and distance assumptions together. Explore accessibility and the modeled effect of alternative locations.",
                     pills=["Huff choice model","Distance or travel time","Candidate comparisons"])
            w.welcome()
            sig.cards([("01 / DEFINE","Put the market on the map","Declare a demand unit, period and customer areas. Mark existing own, competitor and candidate sites."),
                       ("02 / QUESTION","Keep the outside option visible","Define site attractiveness, distance decay and alternatives beyond the listed locations."),
                       ("03 / COMPARE","Test one location at a time","Compare access, site allocations and changes in your own portfolio under explicit assumptions.")])
            cols=st.columns(4)
            missing=w.cached("missing_count",lambda: model.readiness_summary(w.d,limit=0)[0])
            for c,label,value in zip(cols,["Customer areas","Existing sites","Candidate locations","Missing baseline inputs"],
                                      [len(w.d["areas"]),sum(s["role"]!="candidate" for s in w.d["sites"]),sum(s["role"]=="candidate" for s in w.d["sites"]),missing]):
                c.metric(label,f"{value:,}")
            st.write("The fictional Oslo-area case offers two café-location alternatives. Coordinates, demand and site attraction are invented for demonstration.")
        elif page==pages[1]:
            sig.header("UPLOAD, ENTER OR USE AI","Your data, your way.","Upload customer areas and locations, enter them yourself, or use your AI to help structure the research.")
            w.inputs()
        elif page==pages[2]:
            sig.header("AREAS → SITES → DISTANCE","Review the model's geographic inputs.","Straight-line mode computes km from coordinates. Travel-time mode requires the complete area-to-site matrix in minutes.")
            w.edit(model.TITLES)
        elif page==pages[3]:
            sig.header("ACCESS & MODELED CHOICE","Explore the catchment.")
            candidates={s["id"]:s["name"] for s in w.d["sites"] if s["role"]=="candidate"}
            selected=st.selectbox("Scenario",["Baseline"]+list(candidates),format_func=lambda x:candidates.get(x,x),key=k("scenario"))
            candidate=None if selected=="Baseline" else selected
            if ready(w,candidate):
                result=w.cached(f"allocate:{candidate}",lambda: model.allocate(w.d,candidate))
                p=w.d["parameters"][0]
                unit="km straight line" if p["distance_mode"]=="straight_km" else "travel minutes"
                st.text(w.d["context"][0]["demand_unit"]+" · "+w.d["context"][0]["period"])
                c1,c2,c3=st.columns(3)
                c1.metric("Allocated to own portfolio",f"{result['own_demand']:,.1f}")
                c2.metric("Allocated outside listed sites",f"{result['outside_demand']:,.1f}")
                c3.metric("Demand beyond access threshold",f"{result['beyond_access_demand']:,.1f}")
                st.caption(f"Access threshold: {p['access_threshold']:g} {unit} to the nearest listed site, including competitors. It is a user-defined criterion.")
                metric=st.radio("Map color",["Modeled own share","Outside share","Distance to nearest site"],horizontal=True,key=k("map_metric"))
                coordinate_map(w,result,candidate,metric)
                st.subheader("Area access and modeled choice")
                show_table(result["areas"],"customer areas",4,by="demand")
                st.subheader("Where the supplied demand is allocated")
                show_table(result["sites"],"locations",2)
                if any(a["outside_weight"]==0 for a in w.d["areas"]):
                    st.warning("At least one area has outside weight zero: its entire demand is forced to the listed locations. This is a closed-choice-set assumption.")
                if result["floored_pairs"]:
                    st.info(f"The minimum-distance rule applies to {result['floored_pairs']:,} area–site pairs. Inspect raw and adjusted distances below.")
                with st.expander("Inspect every distance and allocation"):
                    show_table(result["allocation"],"area–site rows",5)
                    if result["allocation_areas"]<result["area_count"]:
                        st.caption(f"This pair-level table covers the first {result['allocation_areas']:,} of {result['area_count']:,} customer areas "
                                   f"(at most {model.DETAIL_LIMIT:,} rows). Every total and share above uses all areas.")
        elif page==pages[4]:
            sig.header("ALTERNATIVE LOCATIONS","Compare what each candidate changes.","Each row adds one candidate to the same baseline. Total demand is held fixed.")
            if ready(w):
                comparison=w.cached("compare",lambda: model.compare(w.d))
                if comparison.empty:
                    st.info("Add sites with role candidate in Edit & review to compare locations.")
                else:
                    st.dataframe(comparison.round(2),hide_index=True,width="stretch")
                    complete=comparison[comparison.status.eq("Complete")]
                    if not complete.empty:
                        fig=go.Figure()
                        for field,label in [("candidate_demand","New site allocation"),("own_portfolio_change","Own portfolio increase")]:
                            fig.add_bar(x=[escape(s) for s in complete.candidate],y=complete[field],name=label)
                        fig.update_layout(barmode="group",height=360,yaxis_title="Supplied demand units",legend={"orientation":"h","y":1.15})
                        fig.update_yaxes(rangemode="tozero")
                        sig.chart(NS,fig,key=k("candidates_chart"))
                    st.caption("Existing-own, competitor and outside changes show how fixed demand is reassigned. A lower access-gap value means less demand lies beyond your distance threshold. These are not measured sales effects.")
                    st.subheader("Does the comparison depend on distance decay?")
                    sensitivity=w.cached("sensitivity",lambda: model.sensitivity(w.d))
                    frame=sensitivity[sensitivity.status.eq("Complete")]
                    if not frame.empty:
                        fig=go.Figure()
                        for name, group in frame.groupby("candidate"):
                            fig.add_scatter(x=group.distance_decay,y=group.own_portfolio_change,mode="lines+markers",name=escape(name))
                        fig.update_layout(height=350,xaxis_title="Distance-decay exponent β",yaxis_title="Own portfolio increase",legend={"orientation":"h","y":1.15})
                        sig.chart(NS,fig,key=k("sensitivity"))
                    st.caption("This varies β while keeping attractiveness, outside weights and demand fixed. It is an assumption check, not a fitted confidence interval or automatic site recommendation.")
        elif page==pages[5]:
            sig.header("SAVE & SHARE","Export the case.","Excel, project JSON, a printable brief and an evidence ZIP. Nothing is stored for you.")
            w.export(model.printable,export_tables)
        else:
            w.research()
    except io.DataProblem as exc:
        st.error(str(exc))
    sig.footer(NS,__version__,"Geographic scenarios with transparent assumptions")
