import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ────────────────────────────────
# 기본 설정
# ────────────────────────────────
st.set_page_config(
    page_title="북극 해빙 면적 변화 대시보드",
    page_icon="🧊",
    layout="wide"
)

DATA_FILE = "arctic_ice_extent_심화_.csv"  # main.py와 같은 폴더에 위치한 데이터 파일


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    df["year"] = df["year"].astype(int)
    df["extent"] = df["extent"].astype(float)
    df = df.sort_values("year").reset_index(drop=True)
    return df


df = load_data()

# ────────────────────────────────
# 사이드바
# ────────────────────────────────
st.sidebar.title("🧊 옵션 설정")
st.sidebar.markdown("데이터: NASA/NSIDC 북극 해빙 면적(단위: 백만 km²)")

year_min, year_max = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider(
    "연도 범위 선택",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
    step=1
)

show_trend = st.sidebar.checkbox("추세선(선형회귀) 표시", value=True)
show_ma = st.sidebar.checkbox("이동평균선 표시", value=False)
ma_window = st.sidebar.slider("이동평균 기간(년)", min_value=2, max_value=10, value=5, disabled=not show_ma)

st.sidebar.markdown("---")
st.sidebar.caption("만든이: Streamlit + Plotly 기반 인터랙티브 대시보드")

filtered = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])].reset_index(drop=True)

# ────────────────────────────────
# 헤더
# ────────────────────────────────
st.title("🧊 북극 해빙 면적(Arctic Sea Ice Extent) 변화 대시보드")
st.markdown(
    f"**{year_range[0]}년 ~ {year_range[1]}년** 동안의 북극 해빙 면적 변화를 인터랙티브하게 살펴봅니다."
)

# ────────────────────────────────
# 주요 지표 카드
# ────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

first_val = filtered.iloc[0]["extent"]
last_val = filtered.iloc[-1]["extent"]
change = last_val - first_val
change_pct = (change / first_val) * 100

min_row = filtered.loc[filtered["extent"].idxmin()]
max_row = filtered.loc[filtered["extent"].idxmax()]

col1.metric("최근 해빙 면적", f"{last_val:.3f} 백만 km²")
col2.metric(
    f"{year_range[0]}년 대비 변화",
    f"{change:.3f} 백만 km²",
    f"{change_pct:.1f}%",
    delta_color="inverse"
)
col3.metric("최저 기록", f"{min_row['extent']:.3f} 백만 km²", f"{int(min_row['year'])}년")
col4.metric("최고 기록", f"{max_row['extent']:.3f} 백만 km²", f"{int(max_row['year'])}년")

st.markdown("---")

# ────────────────────────────────
# 메인 인터랙티브 그래프 (Plotly)
# ────────────────────────────────
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=filtered["year"],
    y=filtered["extent"],
    mode="lines+markers",
    name="해빙 면적",
    line=dict(color="#1f77b4", width=3),
    marker=dict(size=7, color="#1f77b4", line=dict(width=1, color="white")),
    hovertemplate="<b>%{x}년</b><br>면적: %{y:.3f} 백만 km²<extra></extra>"
))

if show_trend and len(filtered) > 1:
    coeffs = np.polyfit(filtered["year"], filtered["extent"], 1)
    trend_y = np.polyval(coeffs, filtered["year"])
    yearly_change = coeffs[0]
    fig.add_trace(go.Scatter(
        x=filtered["year"],
        y=trend_y,
        mode="lines",
        name=f"추세선 (연 {yearly_change:.4f} 백만 km²)",
        line=dict(color="crimson", width=2, dash="dash"),
        hovertemplate="<b>%{x}년</b><br>추세값: %{y:.3f} 백만 km²<extra></extra>"
    ))

if show_ma:
    filtered["ma"] = filtered["extent"].rolling(window=ma_window, min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=filtered["year"],
        y=filtered["ma"],
        mode="lines",
        name=f"{ma_window}년 이동평균",
        line=dict(color="orange", width=2.5),
        hovertemplate="<b>%{x}년</b><br>이동평균: %{y:.3f} 백만 km²<extra></extra>"
    ))

fig.update_layout(
    title="연도별 북극 해빙 면적 변화",
    xaxis_title="연도",
    yaxis_title="해빙 면적 (백만 km²)",
    hovermode="x unified",
    template="plotly_white",
    height=550,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(rangeslider=dict(visible=True), type="linear"),
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ────────────────────────────────
# 연대별(Decade) 비교
# ────────────────────────────────
st.subheader("📊 연대별 평균 해빙 면적 비교")

decade_df = filtered.copy()
decade_df["decade"] = (decade_df["year"] // 10) * 10
decade_avg = decade_df.groupby("decade")["extent"].mean().reset_index()
decade_avg["decade_label"] = decade_avg["decade"].astype(str) + "년대"

fig_decade = px.bar(
    decade_avg,
    x="decade_label",
    y="extent",
    color="extent",
    color_continuous_scale="Blues_r",
    text=decade_avg["extent"].round(3),
    labels={"decade_label": "연대", "extent": "평균 해빙 면적 (백만 km²)"},
)
fig_decade.update_traces(
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>평균 면적: %{y:.3f} 백만 km²<extra></extra>"
)
fig_decade.update_layout(
    template="plotly_white",
    height=450,
    coloraxis_showscale=False
)
st.plotly_chart(fig_decade, use_container_width=True)

st.markdown("---")

# ────────────────────────────────
# 전년 대비 증감 (변화량)
# ────────────────────────────────
st.subheader("📉 전년 대비 증감량")

diff_df = filtered.copy()
diff_df["diff"] = diff_df["extent"].diff()
diff_df = diff_df.dropna()
diff_df["color"] = np.where(diff_df["diff"] >= 0, "증가", "감소")

fig_diff = px.bar(
    diff_df,
    x="year",
    y="diff",
    color="color",
    color_discrete_map={"증가": "#2ca02c", "감소": "#d62728"},
    labels={"year": "연도", "diff": "전년 대비 변화량 (백만 km²)", "color": "구분"},
)
fig_diff.update_traces(
    hovertemplate="<b>%{x}년</b><br>변화량: %{y:.3f} 백만 km²<extra></extra>"
)
fig_diff.update_layout(
    template="plotly_white",
    height=400,
    hovermode="x unified"
)
st.plotly_chart(fig_diff, use_container_width=True)

st.markdown("---")

# ────────────────────────────────
# 원본 데이터 및 다운로드
# ────────────────────────────────
with st.expander("📄 원본 데이터 보기"):
    st.dataframe(filtered[["year", "extent"]], use_container_width=True)
    csv = filtered[["year", "extent"]].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="필터링된 데이터 CSV 다운로드",
        data=csv,
        file_name="arctic_ice_extent_filtered.csv",
        mime="text/csv"
    )

st.caption("데이터 출처: 업로드된 arctic_ice_extent_심화_.csv 파일 기준")
