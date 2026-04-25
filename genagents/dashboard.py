"""GenAgents Dashboard — Day 7: heatmap + propagation + memory stats."""
import re
from pathlib import Path

import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="GenAgents Dashboard", layout="wide")
st.title("Generative Agents Dashboard")
st.caption("Day 6 multi-day simulation results")

report_path = Path("reports/day6_report.md")
if not report_path.exists():
    st.warning(f"未找到报告: {report_path}")
    st.stop()

text = report_path.read_text(encoding="utf-8")


def parse_propagation(t: str):
    pat = re.compile(
        r"\|\s*(Isabella|Maria|Klaus)\s*\|\s*\*\*(\w+)\*\*\s*\|\s*L(\d)\s*\|\s*([^|]+)\s*\|"
    )
    return [
        {"agent": m.group(1), "yes_no": m.group(2),
         "level": int(m.group(3)), "known_fields": m.group(4).strip()}
        for m in pat.finditer(t)
    ]


def parse_relationships(t: str):
    pat = re.compile(
        r"### (\w+) → (\w+).*?反思次数[^:]*:\s*(\d+).*?关注度[^:]*:\s*([\d.]+)",
        re.DOTALL,
    )
    return [
        {"from": m.group(1), "to": m.group(2),
         "count": int(m.group(3)), "attention": float(m.group(4))}
        for m in pat.finditer(t)
    ]


def parse_memory_stats(t: str):
    section = t.split("Memory stream 统计")[-1] if "Memory stream 统计" in t else t
    pat = re.compile(
        r"\|\s*(Isabella|Maria|Klaus)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|"
    )
    return [
        {"agent": m.group(1), "total": int(m.group(2)),
         "observation": int(m.group(3)), "reflection": int(m.group(4))}
        for m in pat.finditer(section)
    ]


prop_data = parse_propagation(text)
edges = parse_relationships(text)
mem_data = parse_memory_stats(text)

# === Top metrics ===
if prop_data:
    yes_rate = sum(1 for p in prop_data if p["yes_no"] == "yes") / len(prop_data) * 100
    l3_rate = sum(1 for p in prop_data if p["level"] >= 3) / len(prop_data) * 100
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Agent 数", len(prop_data))
    mc2.metric("Paper-faithful 覆盖率", f"{yes_rate:.0f}%")
    mc3.metric("L3 完整覆盖率", f"{l3_rate:.0f}%")
    st.divider()

# === Two columns: propagation chart + heatmap ===
col1, col2 = st.columns(2)

with col1:
    st.subheader("📡 Seed 事件传播 (per agent)")
    if prop_data:
        df_prop = pd.DataFrame(prop_data)
        bars = alt.Chart(df_prop).mark_bar().encode(
            x=alt.X("agent:N", title="Agent", sort=None),
            y=alt.Y("level:Q", title="Level (L0-L3)",
                    scale=alt.Scale(domain=[0, 3.5])),
            color=alt.Color("level:Q",
                            scale=alt.Scale(scheme="greens", domain=[0, 3]),
                            legend=None),
            tooltip=["agent", "level", "yes_no", "known_fields"],
        ).properties(height=300)
        labels = alt.Chart(df_prop).mark_text(
            fontSize=20, fontWeight="bold", dy=-12,
        ).encode(
            x="agent:N", y="level:Q",
            text=alt.Text("level:Q", format="d"),
        )
        st.altair_chart(bars + labels, use_container_width=True)
        st.caption("L0-L3:agent 知道 seed event 的字段数等级")

with col2:
    st.subheader("🔥 关系矩阵热力图")
    if edges:
        df = pd.DataFrame(edges)
        rect = alt.Chart(df).mark_rect().encode(
            x=alt.X("to:N", title="对象 (→)", sort=None),
            y=alt.Y("from:N", title="主体", sort=None),
            color=alt.Color("attention:Q",
                            scale=alt.Scale(scheme="reds"),
                            legend=alt.Legend(title="attention")),
            tooltip=["from", "to", "count", "attention"],
        ).properties(height=300)
        overlay = alt.Chart(df).mark_text(
            fontSize=14, fontWeight="bold",
        ).encode(
            x="to:N", y="from:N",
            text=alt.Text("attention:Q", format=".0f"),
            color=alt.condition("datum.attention > 150",
                                alt.value("white"), alt.value("black")),
        )
        st.altair_chart(rect + overlay, use_container_width=True)
        st.caption("数字 = attention(Σ importance)")

st.divider()

# === Memory stream distribution ===
if mem_data:
    st.subheader("🧠 Memory stream 分布")
    df_mem = pd.DataFrame(mem_data)
    df_long = df_mem.melt(
        id_vars="agent", value_vars=["observation", "reflection"],
        var_name="type", value_name="count",
    )
    chart = alt.Chart(df_long).mark_bar().encode(
        x=alt.X("agent:N", title="Agent", sort=None),
        y=alt.Y("count:Q", title="Memory 条数"),
        color=alt.Color("type:N",
                        scale=alt.Scale(
                            domain=["observation", "reflection"],
                            range=["#3b82f6", "#f59e0b"])),
        tooltip=["agent", "type", "count"],
    ).properties(height=250)
    st.altair_chart(chart, use_container_width=True)
    st.caption("Observation = 直接观察;Reflection = 高层抽象")

st.divider()

with st.expander("📄 完整报告 (markdown)"):
    st.markdown(text)
