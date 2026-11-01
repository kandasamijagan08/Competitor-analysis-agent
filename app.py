
import re
import io
import time
from collections import Counter
from datetime import datetime
from urllib.parse import urlparse, urljoin
import json
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------

st.set_page_config(
    page_title="MarketLens AI",
    page_icon="🧭",
    layout="wide"
)

# -----------------------------------------
# PREMIUM UI DESIGN
# -----------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

.stApp {
    background:
    radial-gradient(circle at 10% 0%, #1b2850 0%, transparent 35%),
    linear-gradient(135deg, #080c19, #10162b, #090d18);
    color: #edf3ff;
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1500px;
    padding-top: 2rem;
}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif;
}

[data-testid="stSidebar"] {
    background: #0c1426;
    border-right: 1px solid #263858;
}

[data-testid="stMetric"] {
    background: linear-gradient(140deg, #1c2c4b, #111b30);
    border: 1px solid #354969;
    padding: 18px;
    border-radius: 16px;
}

[data-testid="stMetricValue"] {
    color: #62edff;
}

.stButton button {
    background: linear-gradient(100deg, #087eaa, #6941c6);
    color: white;
    border: 1px solid #6488bc;
    border-radius: 10px;
    font-weight: 700;
    min-height: 43px;
}

.stButton button:hover {
    border-color: #4deaff;
    box-shadow: 0 0 18px #4deaff55;
}

.stDownloadButton button {
    background: #172d49;
    color: white;
    border: 1px solid #42628a;
    border-radius: 10px;
}

div[data-testid="stTabs"] button {
    color: #a9bbd9;
    font-weight: 700;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #4deaff;
    border-bottom: 2px solid #4deaff;
}

.ml-hero {
    padding: 30px;
    border-radius: 22px;
    background: linear-gradient(110deg, #152b4e, #292052, #401e50);
    border: 1px solid #52648c;
    margin-bottom: 24px;
}

.ml-hero p {
    color: #c2d1ec;
}

.panel {
    background: linear-gradient(145deg, #182641, #101a2d);
    border: 1px solid #304465;
    padding: 20px;
    border-radius: 17px;
    margin-bottom: 15px;
}

.muted {
    color: #9eafcc;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------------------
# SESSION STATE
# -----------------------------------------

DEFAULT_COMPETITORS = [
    {
        "name": "AI Skill Up Academy",
        "url": "https://www.aiskillup.in/",
        "type": "Direct / adjacent"
    },
    {
        "name": "AIRA Global Tech",
        "url": "https://www.airaglobaltech.com/",
        "type": "Direct / adjacent"
    },
    {
        "name": "CRUD Academy",
        "url": "https://www.crud.academy/",
        "type": "Adjacent"
    },
    {
        "name": "RootAxis",
        "url": "https://www.rootaxis.in/",
        "type": "Adjacent"
    },
    {
        "name": "SearchX Academy",
        "url": "https://www.searchxacademy.com/",
        "type": "Direct"
    },
    {
        "name": "Dazzle Tech Academy",
        "url": "https://dazzletechacademy.com/",
        "type": "Direct"
    },
    {
        "name": "upGrad Coimbatore",
        "url": "https://upgradcoimbatore.in/",
        "type": "Adjacent"
    },
    {
        "name": "Zeta Nextmind",
        "url": "https://www.zetanextmind.com/",
        "type": "Adjacent"
    }
]

if "competitors" not in st.session_state:
    st.session_state.competitors = DEFAULT_COMPETITORS.copy()

if "results" not in st.session_state:
    st.session_state.results = {}

if "target_result" not in st.session_state:
    st.session_state.target_result = None


# -----------------------------------------
# WEBSITE VALIDATION
# -----------------------------------------

def validate_url(url):

    url = str(url).strip()

    if not url:
        return None

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    if not parsed.netloc or "." not in parsed.netloc:
        return None

    return url


# -----------------------------------------
# WEBSITE AUDIT ENGINE
# -----------------------------------------

def website_audit(url):

    result = {
        "url": url,
        "status": None,
        "title": "",
        "description": "",
        "h1": [],
        "h2": [],
        "canonical": "",
        "words": 0,
        "text": "",
        "load_time": None,
        "https": url.startswith("https://"),
        "schema": False,
        "images": 0,
        "missing_alt": 0,
        "error": None
    }

    try:

        start = time.time()

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 MarketLensAI/2.0"
            },
            timeout=18
        )

        result["load_time"] = round(
            (time.time() - start) * 1000
        )

        result["status"] = response.status_code

        if "html" not in response.headers.get(
            "content-type", ""
        ).lower():

            result["error"] = "Website did not return HTML."
            return result

        soup = BeautifulSoup(
            response.text[:2500000],
            "html.parser"
        )

        if soup.title:
            result["title"] = soup.title.get_text(
                " ", strip=True
            )

        meta = soup.find(
            "meta",
            attrs={"name": re.compile("^description$", re.I)}
        )

        if meta:
            result["description"] = (
                meta.get("content") or ""
            ).strip()

        result["h1"] = [
            x.get_text(" ", strip=True)
            for x in soup.find_all("h1")
        ][:10]

        result["h2"] = [
            x.get_text(" ", strip=True)
            for x in soup.find_all("h2")
        ][:20]

        canonical = soup.find(
            "link",
            rel=lambda value: value and "canonical" in value
        )

        if canonical:
            result["canonical"] = canonical.get("href", "")

        result["schema"] = bool(
            soup.find(
                "script",
                type=re.compile("ld\\+json", re.I)
            )
        )

        images = soup.find_all("img")

        result["images"] = len(images)

        result["missing_alt"] = sum(
            1 for image in images
            if not (image.get("alt") or "").strip()
        )

        for tag in soup([
            "script", "style", "noscript",
            "svg", "nav", "footer"
        ]):
            tag.decompose()

        text = re.sub(
            r"\s+",
            " ",
            soup.get_text(" ", strip=True)
        )

        result["text"] = text[:60000]
        result["words"] = len(text.split())

    except requests.exceptions.Timeout:
        result["error"] = "Website request timed out."

    except requests.exceptions.RequestException as error:
        result["error"] = str(error)[:180]

    except Exception as error:
        result["error"] = str(error)[:180]

    return result


# -----------------------------------------
# SEO CHECKLIST SCORE
# -----------------------------------------

def calculate_score(data):

    checks = {
        "HTTP success": (
            data.get("status") is not None
            and 200 <= data["status"] < 400
        ),
        "SEO title": bool(data.get("title")),
        "Meta description": bool(data.get("description")),
        "H1 heading": bool(data.get("h1")),
        "H2 headings": bool(data.get("h2")),
        "Content 100+ words": data.get("words", 0) >= 100,
        "Canonical tag": bool(data.get("canonical")),
        "HTTPS": bool(data.get("https")),
        "Structured data": bool(data.get("schema"))
    }

    score = round(
        sum(checks.values()) / len(checks) * 100
    )

    return score, checks


# -----------------------------------------
# KEYWORD EXTRACTION
# -----------------------------------------

def extract_keywords(text, limit=30):

    stopwords = set("""
    the and for with from your our are you this that
    have has was were will can all not but into about
    their they them its how what when where who why
    more most very also than then each use using used
    learn course courses training institute academy
    home contact about coimbatore india
    """.split())

    words = re.findall(
        r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}",
        (text or "").lower()
    )

    words = [
        word for word in words
        if word not in stopwords
    ]

    return Counter(words).most_common(limit)


# -----------------------------------------
# REPORT DATA
# -----------------------------------------

def build_report():

    rows = []

    for name, data in st.session_state.results.items():

        score = None

        if not data.get("error"):
            score, _ = calculate_score(data)

        keywords = extract_keywords(
            data.get("text", ""),
            8
        )

        rows.append({
            "Competitor": name,
            "Website": data.get("url"),
            "HTTP": data.get("status"),
            "SEO Checklist Score": score,
            "Page Title": data.get("title"),
            "Meta Description": data.get("description"),
            "H1": " | ".join(data.get("h1", [])),
            "Word Count": data.get("words", 0),
            "Load Time ms": data.get("load_time"),
            "Top Page Terms": ", ".join(
                word for word, count in keywords
            ),
            "Audit Status": (
                "Error" if data.get("error") else "Audited"
            )
        })

    return pd.DataFrame(rows)


def get_gaps():

    target = st.session_state.target_result

    if not target:
        return []

    target_terms = {
        word for word, count in extract_keywords(
            target.get("text", ""), 150
        )
    }

    competitor_counter = Counter()

    for data in st.session_state.results.values():

        if data.get("error"):
            continue

        competitor_counter.update(
            word for word, count in extract_keywords(
                data.get("text", ""), 150
            )
        )

    gaps = [
        (word, count)
        for word, count in competitor_counter.items()
        if word not in target_terms and count >= 2
    ]

    return sorted(
        gaps,
        key=lambda x: x[1],
        reverse=True
    )[:30]


# -----------------------------------------
# SIDEBAR
# -----------------------------------------

with st.sidebar:

    st.markdown("# 🧭 MarketLens AI")
    st.caption("COMPETITOR INTELLIGENCE V2")

    st.divider()

    st.markdown("### 🎯 Target Business")

    company = st.text_input(
        "Company name",
        "Brand Monk Academy"
    )

    target_url = st.text_input(
        "Target website URL",
        ""
    )

    location = st.text_input(
        "Market location",
        "Coimbatore, Tamil Nadu"
    )

    st.divider()

    competitor_count = st.slider(
        "Competitors to analyze",
        5,
        15,
        min(8, max(5, len(st.session_state.competitors)))
    )

    st.caption(
        "Candidate websites must be verified before using their results."
    )

    st.divider()

    st.markdown("### ⚙ Research settings")

    timeout = st.select_slider(
        "Request timeout",
        options=[8, 12, 18, 25],
        value=18
    )

    st.caption("This MVP audits public homepage HTML only.")


# -----------------------------------------
# HEADER
# -----------------------------------------

st.markdown(f"""
<div class="ml-hero">
    <div style="color:#64EFFF;font-weight:800;letter-spacing:2px;font-size:11px">
        MARKET INTELLIGENCE / RESEARCH WORKSPACE
    </div>
    <h1 style="color:white;margin:8px 0">
        MarketLens <span style="color:#64EFFF">AI</span>
    </h1>
    <p>
        Understand your competition. Discover website gaps.
        Make smarter marketing decisions for <b>{company}</b>.
    </p>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------
# NAVIGATION
# -----------------------------------------

tabs = st.tabs([
    "⚡ Overview",
    "🏁 Competitors",
    "🔍 SEO Audit",
    "🔑 Keywords",
    "🧠 AI Strategy",
    "📊 Reports"
])


# -----------------------------------------
# OVERVIEW
# -----------------------------------------

with tabs[0]:

    df = build_report()

    successful = (
        int((df["Audit Status"] == "Audited").sum())
        if not df.empty else 0
    )

    average = (
        round(df["SEO Checklist Score"].dropna().mean())
        if not df.empty
        and df["SEO Checklist Score"].notna().any()
        else None
    )

    target_score = None

    if st.session_state.target_result:
        target_score, _ = calculate_score(
            st.session_state.target_result
        )

    a, b, c, d = st.columns(4)

    a.metric(
        "Competitor Set",
        len(st.session_state.competitors)
    )

    b.metric(
        "Successful Audits",
        successful
    )

    c.metric(
        "Average SEO Checklist",
        f"{average}/100" if average is not None else "—"
    )

    d.metric(
        "Target SEO Checklist",
        f"{target_score}/100" if target_score is not None else "Pending"
    )

    st.markdown("### 📡 Competitor Intelligence")

    if not df.empty and df["SEO Checklist Score"].notna().any():

        chart_data = df.dropna(
            subset=["SEO Checklist Score"]
        ).sort_values("SEO Checklist Score")

        fig = px.bar(
            chart_data,
            x="SEO Checklist Score",
            y="Competitor",
            orientation="h",
            text="SEO Checklist Score",
            color="SEO Checklist Score",
            color_continuous_scale=[
                "#F472B6",
                "#A78BFA",
                "#4DEBFF"
            ]
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
            height=400,
            xaxis_title="Homepage checklist score",
            yaxis_title=""
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.markdown("""
        <div class="panel">
            <h3>🚀 Ready to discover your competition?</h3>
            <p class="muted">
                Add your target website, approve competitor URLs,
                and launch your first research run.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.info(
        "This checklist score is not a Google ranking or full competitive-strength score."
    )


# -----------------------------------------
# COMPETITOR MANAGEMENT
# -----------------------------------------

with tabs[1]:

    st.markdown("### 🏁 Competitor Lab")

    st.caption(
        "Edit the candidate list. These are suggested leads, not verified direct competitors."
    )

    competitor_df = pd.DataFrame(
        st.session_state.competitors
    )

    edited = st.data_editor(
        competitor_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "type": st.column_config.SelectboxColumn(
                "Type",
                options=[
                    "Direct",
                    "Direct / adjacent",
                    "Adjacent",
                    "Indirect",
                    "Irrelevant"
                ]
            )
        },
        key="competitor_table"
    )

    if st.button(
        "💾 SAVE COMPETITOR LIST",
        use_container_width=True
    ):

        clean = []

        for row in edited.fillna("").to_dict("records"):

            name = str(row.get("name", "")).strip()
            url = validate_url(row.get("url", ""))

            if name and url:

                clean.append({
                    "name": name,
                    "url": url,
                    "type": row.get("type", "Unclassified")
                })

        if not 5 <= len(clean) <= 15:

            st.error(
                "Please keep between 5 and 15 valid competitors."
            )

        elif len({
            x["name"].lower() for x in clean
        }) != len(clean):

            st.error("Competitor names must be unique.")

        else:

            st.session_state.competitors = clean
            st.success("Competitor list saved.")

    st.divider()

    st.markdown("### 🚀 Launch Analysis")

    if st.button(
        "START COMPETITOR ANALYSIS",
        type="primary",
        use_container_width=True
    ):

        target = validate_url(target_url)

        if not target:

            st.error(
                "Enter a valid target website URL in the sidebar."
            )

        elif len(st.session_state.competitors) < 5:

            st.error(
                "Add at least five competitors before starting."
            )

        else:

            progress = st.progress(0)
            status = st.empty()

            status.info(
                "Research Agent 1: Auditing target website..."
            )

            st.session_state.target_result = website_audit(
                target
            )

            results = {}

            selected = st.session_state.competitors[
                :competitor_count
            ]

            for i, competitor in enumerate(selected):

                status.info(
                    f"Research Agent 2: Auditing {competitor['name']}..."
                )

                results[competitor["name"]] = website_audit(
                    competitor["url"]
                )

                progress.progress(
                    int((i + 1) / len(selected) * 100)
                )

            st.session_state.results = results

            status.success(
                "Research completed. Your dashboard is updated."
            )

            st.rerun()

    if st.session_state.results:

        st.markdown("### Latest Research Results")

        st.dataframe(
            build_report(),
            hide_index=True,
            use_container_width=True
        )


# -----------------------------------------
# SEO AUDIT
# -----------------------------------------

with tabs[2]:

    st.markdown("### 🔍 Website SEO Inspector")

    target = st.session_state.target_result

    if not target:

        st.warning(
            "Run competitor analysis to see the target website audit."
        )

    else:

        score, checks = calculate_score(target)

        a, b, c = st.columns(3)

        a.metric("Checklist Score", f"{score}/100")
        b.metric("Page Word Count", target["words"])
        c.metric(
            "Response Time",
            f"{target['load_time']} ms"
            if target["load_time"] is not None
            else "Unavailable"
        )

        st.markdown("#### Page metadata")

        st.markdown(
            f"""
            <div class="panel">
                <b>SEO Title</b>
                <p>{target['title'] or 'Not detected'}</p>
                <hr>
                <b>Meta Description</b>
                <p>{target['description'] or 'Not detected'}</p>
                <hr>
                <b>Canonical URL</b>
                <p>{target['canonical'] or 'Not detected'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        left, right = st.columns(2)

        with left:

            st.markdown("#### H1 headings")
            st.write(target["h1"] or ["Not detected"])

            st.markdown("#### H2 headings")
            st.write(target["h2"] or ["Not detected"])

        with right:

            st.markdown("#### SEO checklist")

            check_df = pd.DataFrame([
                {
                    "SEO Check": name,
                    "Result": "PASS" if value else "REVIEW"
                }
                for name, value in checks.items()
            ])

            st.dataframe(
                check_df,
                hide_index=True,
                use_container_width=True
            )

            st.write(
                "HTTPS:",
                "Enabled" if target["https"] else "Not detected"
            )

            st.write(
                "Structured data:",
                "Detected" if target["schema"] else "Not detected"
            )

        if target["error"]:
            st.error(target["error"])

    if st.session_state.results:

        st.markdown("#### Competitor SEO comparison")

        st.dataframe(
            build_report(),
            hide_index=True,
            use_container_width=True
        )


# -----------------------------------------
# KEYWORD GAP ANALYSIS
# -----------------------------------------

with tabs[3]:

    st.markdown("### 🔑 Keyword Gap Explorer")

    if not st.session_state.target_result or not st.session_state.results:

        st.info(
            "Complete a competitor analysis to discover keyword gaps."
        )

    else:

        target_terms = {
            word
            for word, count in extract_keywords(
                st.session_state.target_result["text"],
                150
            )
        }

        competitor_terms = Counter()

        for data in st.session_state.results.values():

            if not data["error"]:

                competitor_terms.update([
                    word
                    for word, count in extract_keywords(
                        data["text"],
                        150
                    )
                ])

        gaps = [
            (word, count)
            for word, count in competitor_terms.items()
            if word not in target_terms and count >= 2
        ]

        gaps = sorted(
            gaps,
            key=lambda item: item[1],
            reverse=True
        )[:30]

        left, right = st.columns(2)

        with left:

            st.markdown("#### Your homepage terms")

            st.dataframe(
                pd.DataFrame(
                    extract_keywords(
                        st.session_state.target_result["text"],
                        20
                    ),
                    columns=["Keyword", "Frequency"]
                ),
                hide_index=True,
                use_container_width=True
            )

        with right:

            st.markdown("#### Potential keyword gaps")

            st.dataframe(
                pd.DataFrame(
                    gaps,
                    columns=[
                        "Keyword",
                        "Competitor page frequency"
                    ]
                ),
                hide_index=True,
                use_container_width=True
            )

        if gaps:

            chart_df = pd.DataFrame(
                gaps[:15],
                columns=["Keyword", "Frequency"]
            )

            fig = px.bar(
                chart_df.sort_values("Frequency"),
                x="Frequency",
                y="Keyword",
                orientation="h",
                color="Frequency",
                color_continuous_scale=[
                    "#A78BFA",
                    "#4DEBFF"
                ]
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.caption(
            "These are terms found in homepage text, not Google search volume or ranking data."
        )


# -----------------------------------------
# STRATEGY RECOMMENDATIONS
# -----------------------------------------

with tabs[4]:

    st.markdown("### 🧠 Strategy Studio")

    target = st.session_state.target_result

    if not target:

        st.info(
            "Run an audit to generate recommendations."
        )

    else:

        score, checks = calculate_score(target)

        recommendations = []

        if not checks["SEO title"]:

            recommendations.append((
                "CRITICAL",
                "Create an SEO title",
                "Add a unique title describing the academy and its primary courses."
            ))

        if not checks["Meta description"]:

            recommendations.append((
                "HIGH",
                "Write a meta description",
                "Explain the main training offer in a clear, useful summary."
            ))

        if not checks["H1 heading"]:

            recommendations.append((
                "HIGH",
                "Improve the primary heading",
                "Add a clear H1 that explains the main service or course offering."
            ))

        if target["words"] < 350:

            recommendations.append((
                "MEDIUM",
                "Expand homepage content",
                "Add curriculum, trainer details, student projects, course duration and FAQs."
            ))

        if target["missing_alt"] > 0:

            recommendations.append((
                "MEDIUM",
                "Improve image accessibility",
                f"{target['missing_alt']} detected images have no alt text."
            ))

        if not checks["Structured data"]:

            recommendations.append((
                "MEDIUM",
                "Review structured data",
                "Consider appropriate Organization, LocalBusiness or Course schema."
            ))

        recommendations.append((
            "HIGH",
            "Create focused course landing pages",
            "Build dedicated pages for Agentic AI, Generative AI, Python and digital marketing."
        ))

        recommendations.append((
            "MEDIUM",
            "Build useful local content",
            "Publish original guides for learners comparing training options in your target market."
        ))

        colors = {
            "CRITICAL": "#FB7185",
            "HIGH": "#FBBF24",
            "MEDIUM": "#A78BFA"
        }

        for priority, title, description in recommendations:

            st.markdown(
                f"""
                <div class="panel">
                    <span style="color:{colors[priority]};font-weight:800">
                        {priority} PRIORITY
                    </span>
                    <h4>{title}</h4>
                    <p class="muted">{description}</p>
                </div>
                """,
                unsafe_allow_html=True
            )


# -----------------------------------------
# REPORT EXPORTS
# -----------------------------------------

with tabs[5]:

    st.markdown("### 📊 Report Center")

    if not st.session_state.results:

        st.info(
            "Complete an analysis to unlock report exports."
        )

    else:

        report_df = build_report()

        st.download_button(
            "⬇ DOWNLOAD COMPETITOR CSV",
            report_df.to_csv(index=False).encode("utf-8-sig"),
            "marketlens_competitor_report.csv",
            "text/csv",
            use_container_width=True
        )

        if st.session_state.target_result:

            report = {
                "company": company,
                "location": location,
                "generated_at": datetime.now().isoformat(),
                "target_audit": {
                    k: v for k, v in
                    st.session_state.target_result.items()
                    if k != "text"
                },
                "competitor_audits": {
                    name: {
                        k: v for k, v in data.items()
                        if k != "text"
                    }
                    for name, data in
                    st.session_state.results.items()
                },
                "limitations": (
                    "Homepage-only public HTML audit. "
                    "No Google rankings, search volume, Meta ads "
                    "or backlink metrics are collected."
                )
            }

            st.download_button(
                "⬇ DOWNLOAD JSON RESEARCH DATA",
                json.dumps(
                    report,
                    indent=2,
                    ensure_ascii=False
                ).encode("utf-8"),
                "marketlens_research.json",
                "application/json",
                use_container_width=True
            )

            try:

                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import (
                    SimpleDocTemplate,
                    Paragraph,
                    Spacer,
                    Table,
                    TableStyle
                )
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib import colors

                buffer = io.BytesIO()

                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=A4
                )

                styles = getSampleStyleSheet()

                elements = [
                    Paragraph(
                        "MarketLens AI Competitor Report",
                        styles["Title"]
                    ),
                    Paragraph(
                        f"Business: {company} | Location: {location}",
                        styles["Normal"]
                    ),
                    Spacer(1, 18)
                ]

                table_data = [
                    [
                        "Competitor",
                        "SEO Checklist",
                        "Status"
                    ]
                ]

                for _, row in report_df.iterrows():

                    table_data.append([
                        str(row["Competitor"])[:30],
                        str(row["SEO Checklist Score"]),
                        str(row["Audit Status"])
                    ])

                table = Table(table_data)

                table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0),
                         colors.HexColor("#263858")),
                        ("TEXTCOLOR", (0, 0), (-1, 0),
                         colors.white),
                        ("GRID", (0, 0), (-1, -1), .4,
                         colors.grey),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                         [colors.white, colors.HexColor("#EAF0F8")])
                    ])
                )

                elements.append(table)

                elements.append(Spacer(1, 18))

                elements.append(
                    Paragraph(
                        "Note: Scores are homepage SEO checklist proxies, "
                        "not Google rankings or total competitor strength.",
                        styles["BodyText"]
                    )
                )

                doc.build(elements)

                st.download_button(
                    "⬇ DOWNLOAD PDF REPORT",
                    buffer.getvalue(),
                    "marketlens_competitor_report.pdf",
                    "application/pdf",
                    use_container_width=True
                )

            except Exception as error:

                st.warning(
                    f"PDF export unavailable: {error}"
                )


# -----------------------------------------
# FOOTER
# -----------------------------------------

st.divider()

st.markdown(
    """
    <div style="text-align:center;color:#8194B6;font-size:12px">
        MARKETLENS AI · COMPETITOR INTELLIGENCE · V2.0
        <br>
        Evidence first. Strategy second.
    </div>
    """,
    unsafe_allow_html=True
)
