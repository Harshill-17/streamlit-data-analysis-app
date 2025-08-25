'''
To run this project :
    1. Run this command into your Project Terminal -> pip install -r requirements.txt
    2. To run your project -> streamlit run app.py (your project name)
'''
import io
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

# Page setup
st.set_page_config(page_title="Data Analytics Portal", page_icon="image.png", layout="wide")

# styling
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0b1020; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
h1,h2,h3,h4,h5 { color: #e6e8f0 !important; }
p, label, span, div { color: #c7cce1; }
.block-container { padding-top: 1.2rem; }
.card { background: #111735; border: 1px solid #2a335a; border-radius: 14px; padding: 14px; }
hr { border: 1px solid #20284a; }
.stButton>button, .stDownloadButton>button {
  background: linear-gradient(90deg, #7c3aed, #06b6d4);
  color: white; border: 0; border-radius: 10px; padding: .55rem .9rem;
}
.stTabs [role="tab"] { background: #0f1530; border-radius: 10px; margin-right: 6px; border: 1px solid #263059; }
.stTabs [aria-selected="true"] { background: #1a2250 !important; border-color: #3a4bb3 !important; }
.kpi { background: #0f1635; border: 1px solid #2a335a; border-radius: 14px; padding: 12px; }
.kpi .v { font-size: 22px; font-weight: 700; color: #e6e8f0 }
.kpi .l { font-size: 12px; color: #9aa4d1 }
</style>
""", unsafe_allow_html=True)

st.title("🌈 Data Analytics Portal — by Harshil")
st.subheader(":gray[Explore data with ease.]", divider="rainbow")

# Sidebar 
with st.sidebar:
    st.header("⚙️ Options")
    sample_if_big = st.toggle("Sample if > 100k rows", value=True)
    chart_theme = st.selectbox("Chart theme", ["plotly_white", "plotly_dark"], index=1)
    st.caption("Tip: Use sampling on very large files to keep it snappy.")

#  Helpers 
def read_any_file(upload) -> pd.DataFrame:
    if upload.name.lower().endswith(".csv"):
        # try common separators
        raw = upload.read()
        for sep in [",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=sep)
                if df.shape[1] > 1 or sep == ",":
                    return df
            except Exception:
                continue
        return pd.read_csv(io.BytesIO(raw))
    else:
        return pd.read_excel(upload)

def num_cat(df):
    num = df.select_dtypes(include=[np.number]).columns.tolist()
    cat = [c for c in df.columns if c not in num]
    return num, cat

def metric(label, value):
    st.markdown(f"""<div class="kpi">
        <div class="l">{label}</div>
        <div class="v">{value}</div>
    </div>""", unsafe_allow_html=True)

# Upload 
file = st.file_uploader("📤 Drop CSV or Excel file", type=["csv", "xlsx", "xls"])

if not file:
    st.info("Upload a file to begin.", icon="📥")
    st.stop()

data = read_any_file(file)

if sample_if_big and len(data) > 100_000:
    data = data.sample(100_000, random_state=42).reset_index(drop=True)

st.success("✅ File is successfully uploaded", icon="🚨")
st.dataframe(data.head(10), use_container_width=True)

# KPIs 
c1, c2, c3, c4 = st.columns(4)
with c1: metric("Rows", f"{len(data):,}")
with c2: metric("Columns", f"{data.shape[1]:,}")
with c3:
    missing_cells = int(data.isna().sum().sum())
    metric("Missing cells", f"{missing_cells:,}")
with c4:
    uniq = int(np.mean([data[c].nunique() for c in data.columns]))
    metric("Avg unique / col", f"{uniq:,}")

# Tabs 
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    " 📊 Overview ", " ⬆️⬇️ Top/Bottom ", " 🧹 Clean", " 🔢 Value Counts", " 📂 Groupby", " 🔗 Correlation"
])

# Overview 
with tab1:
    st.markdown("#### Basic information", help="Quick summary of shape, dtypes, and stats.")
    cA, cB = st.columns(2)
    with cA:
        st.markdown("**Dtypes**")
        st.dataframe(pd.DataFrame({"column": data.columns, "dtype": data.dtypes.astype(str)}),
                     use_container_width=True, height=280)
    with cB:
        num, cat = num_cat(data)
        st.markdown("**Descriptive statistics (numeric)**")
        st.dataframe(data[num].describe().T if num else pd.DataFrame({"note": ["no numeric columns"]}),
                     use_container_width=True, height=280)
    st.markdown("---")
    st.markdown("**Missing per column**")
    miss = data.isna().sum().sort_values(ascending=False).reset_index()
    miss.columns = ["column", "missing"]
    fig = px.bar(miss, x="column", y="missing", template='plotly_white')
    fig.update_layout(height=380, xaxis={"categoryorder": "total descending"})
    st.plotly_chart(fig, use_container_width=True)

# Top/Bottom 
with tab2:
    st.markdown("#### Peek at rows")
    topn = st.slider("Top rows", 1, min(1000, len(data)), 5, key="top_rows")
    st.dataframe(data.head(topn), use_container_width=True)
    st.markdown("---")
    botn = st.slider("Bottom rows", 1, min(1000, len(data)), 5, key="bottom_rows")
    st.dataframe(data.tail(botn), use_container_width=True)

# Clean
with tab3:
    st.markdown("#### Cleaning tools")
    st.caption("Simple, transparent cleaning — easy to explain in interviews.")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**Handle missing values**")
        clean_cols = st.multiselect("Columns", data.columns.tolist(), key="na_cols")
        strat = st.selectbox("Strategy", ["mean", "median", "mode", "drop rows", "fill constant"], key="na_strat")
        const_val = st.text_input("Constant (for fill constant)", key="na_const")
        if st.button("Apply missing handling"):
            if strat == "drop rows":
                data.dropna(subset=clean_cols if clean_cols else None, inplace=True)
            elif strat in ["mean", "median"]:
                for c in clean_cols:
                    if pd.api.types.is_numeric_dtype(data[c]):
                        val = getattr(data[c], strat)()
                        data[c] = data[c].fillna(val)
            elif strat == "mode":
                for c in clean_cols:
                    mode = data[c].mode()
                    if not mode.empty:
                        data[c] = data[c].fillna(mode.iloc[0])
            else:
                for c in clean_cols:
                    data[c] = data[c].fillna(const_val)
            st.success("Missing values handled.")

    with c2:
        st.markdown("**Remove duplicates**")
        if st.button("Drop duplicate rows"):
            before = len(data)
            data.drop_duplicates(inplace=True)
            st.success(f"Dropped {before - len(data)} duplicate rows.")

    with c3:
        st.markdown("**Convert types**")
        # Datetime conversion
        dt_candidates = [c for c in data.columns if data[c].dtype == "object"]
        dt_pick = st.multiselect("Convert to datetime", dt_candidates, key="to_dt")
        if st.button("Convert selected to datetime"):
            for c in dt_pick:
                data[c] = pd.to_datetime(data[c], errors="coerce")
            st.success("Converted to datetime (invalid parsed as NaT).")
        # Numeric conversion
        num_candidates = [c for c in data.columns if data[c].dtype == "object"]
        num_pick = st.multiselect("Convert to numeric", num_candidates, key="to_num")
        if st.button("Convert selected to numeric"):
            for c in num_pick:
                data[c] = pd.to_numeric(data[c].astype(str).str.replace(",", ""), errors="coerce")
            st.success("Converted to numeric (invalid parsed as NaN).")

    st.markdown("---")
    st.dataframe(data.head(8), use_container_width=True)
    st.download_button("⬇️ Download cleaned data (CSV)",
                       data=data.to_csv(index=False).encode("utf-8"),
                       file_name="dataset_cleaned.csv",
                       mime="text/csv")

# Value Counts
with tab4:
    st.markdown("#### Column value counts + quick charts")
    col = st.selectbox("Choose a column", options=data.columns.tolist())
    topk = st.number_input("Top N", 1, 100, 10)
    vc = data[col].value_counts(dropna=False).reset_index()
    vc.columns = [col, "count"]
    vc = vc.head(topk)

    st.dataframe(vc, use_container_width=True)

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        fig = px.bar(vc, x=col, y="count", text="count", template='plotly_white')
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.line(vc, x=col, y="count", markers=True, template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
    with c3:
        fig = px.pie(vc, names=col, values="count", template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)

# Groupby
with tab5:
    st.markdown("#### Groupby: summarize by categories")
    g1, g2, g3 = st.columns(3)
    with g1:
        group_cols = st.multiselect("Group by columns", options=data.columns.tolist())
    with g2:
        op_col = st.selectbox("Aggregate column", options=[None] + data.columns.tolist())
    with g3:
        op = st.selectbox("Operation", options=["sum", "mean", "median", "max", "min", "count", "nunique"])

    if group_cols and op_col:
        result = data.groupby(group_cols).agg(newcol=(op_col, op)).reset_index()
        st.dataframe(result, use_container_width=True, height=350)

        st.markdown("**Quick visualization**")
        chart = st.selectbox("Chart type", ["Bar", "Line", "Scatter", "Pie", "Sunburst"])
        if chart in ["Bar", "Line", "Scatter"]:
            x_axis = st.selectbox("X axis", options=result.columns.tolist(), key="gx")
            y_axis = st.selectbox("Y axis", options=result.columns.tolist(), key="gy")
            color = st.selectbox("Color", options=[None] + result.columns.tolist(), key="gc")
            if chart == "Bar":
                fig = px.bar(result, x=x_axis, y=y_axis, color=color, template='plotly_white', barmode="group")
            elif chart == "Line":
                fig = px.line(result, x=x_axis, y=y_axis, color=color, template='plotly_white')
            else:
                size = st.selectbox("Size", options=[None] + result.columns.tolist(), key="gs")
                fig = px.scatter(result, x=x_axis, y=y_axis, color=color, size=size, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        elif chart == "Pie":
            names = st.selectbox("Names", options=result.columns.tolist(), key="gpie_n")
            values = st.selectbox("Values", options=result.columns.tolist(), key="gpie_v")
            fig = px.pie(result, names=names, values=values, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            path = st.multiselect("Path", options=result.columns.tolist(), key="gsun")
            if path:
                fig = px.sunburst(result, path=path, values="newcol", template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)

# Correlation 
with tab6:
    st.markdown("#### Correlation heatmap (numeric columns)")
    num_cols, _ = num_cat(data)
    if len(num_cols) >= 2:
        corr = data[num_cols].corr(numeric_only=True)
        fig = px.imshow(corr, text_auto=True, aspect="auto", template='plotly_white',
                        color_continuous_scale="RdBu", origin="lower")
        fig.update_layout(height=520)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough numeric columns for correlation.", icon="ℹ️")