import os
import tempfile

import pandas as pd
import streamlit as st
import altair as alt

from analytics.financial_assistant import ask_financial_assistant
from analytics.database import fetch_dataframe


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Mittelstand AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_REPORTING_DATE = pd.Timestamp("2026-10-27")


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
        .stApp { background: #0B1120; color: #E5E7EB; }
        [data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid #263244;
        }
        [data-testid="stMetric"] {
            background: #172235;
            border: 1px solid #263B55;
            padding: 16px;
            border-radius: 12px;
        }
        [data-testid="stMetricLabel"] { color: #9CA3AF; }
        [data-testid="stMetricValue"] { color: #F9FAFB; }
        h1, h2, h3 { color: #F9FAFB; }
        .block-container { padding-top: 1.8rem; padding-bottom: 3rem; }
        div[data-testid="stDataFrame"] {
            border: 1px solid #263244;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADING AND VALIDATION
# ============================================================

SUPPLIER_COLUMNS = [
    "invoice_id", "supplier", "country", "category",
    "invoice_date", "due_date", "amount_eur", "status",
]

CUSTOMER_COLUMNS = [
    "invoice_id", "customer", "country", "category",
    "invoice_date", "due_date", "amount_eur", "status",
    "payment_date",
]


def money(value):
    return f"€{float(value):,.2f}"


def load_supplier_invoices(uploaded_file=None):
    """Load supplier invoices from an uploaded CSV or PostgreSQL."""

    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        source = "Uploaded CSV"
    else:
        data = fetch_dataframe(
            "SELECT * FROM invoices ORDER BY invoice_id"
        )
        source = "PostgreSQL database"

    missing = [
        column for column in SUPPLIER_COLUMNS
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Missing supplier invoice columns: {missing}"
        )

    if data.empty:
        raise ValueError(
            "Supplier invoice data contains no records."
        )

    data = data.copy()

    data["invoice_id"] = data["invoice_id"].astype(str).str.strip()
    data["supplier"] = data["supplier"].astype(str).str.strip()
    data["status"] = data["status"].astype(str).str.strip().str.title()

    data["amount_eur"] = pd.to_numeric(
        data["amount_eur"], errors="coerce"
    )

    data["invoice_date"] = pd.to_datetime(
        data["invoice_date"], errors="coerce"
    )

    data["due_date"] = pd.to_datetime(
        data["due_date"], errors="coerce"
    )

    if data[
        ["invoice_id", "supplier", "invoice_date", "due_date"]
    ].isna().any().any():
        raise ValueError(
            "Supplier data contains missing IDs, suppliers or dates."
        )

    if data["amount_eur"].isna().any() or (
        data["amount_eur"] <= 0
    ).any():
        raise ValueError(
            "All supplier invoice amounts must be positive numbers."
        )

    if not data["status"].isin(["Paid", "Unpaid"]).all():
        raise ValueError(
            "Supplier payment status must be Paid or Unpaid."
        )

    if (data["due_date"] < data["invoice_date"]).any():
        raise ValueError(
            "Some supplier due dates are earlier than invoice dates."
        )

    return data, source


def load_customer_invoices():
    """Load and validate customer invoices from PostgreSQL."""

    try:
        data = fetch_dataframe(
            "SELECT * FROM customer_invoices ORDER BY invoice_id"
        )

        missing = [
            column for column in CUSTOMER_COLUMNS
            if column not in data.columns
        ]

        if missing:
            return None, f"Missing customer invoice columns: {missing}"

        if data.empty:
            return None, "Customer invoice data contains no records."

        data = data.copy()

        data["invoice_id"] = data["invoice_id"].astype(str).str.strip()
        data["customer"] = data["customer"].astype(str).str.strip()
        data["status"] = data["status"].astype(str).str.strip().str.title()

        data["amount_eur"] = pd.to_numeric(
            data["amount_eur"], errors="coerce"
        )

        for column in ["invoice_date", "due_date", "payment_date"]:
            data[column] = pd.to_datetime(
                data[column], errors="coerce"
            )

        if data["amount_eur"].isna().any() or (
            data["amount_eur"] <= 0
        ).any():
            return None, "Customer invoice amounts must be positive numbers."

        if not data["status"].isin(["Paid", "Unpaid"]).all():
            return None, "Customer payment status must be Paid or Unpaid."

        if data["invoice_id"].duplicated().any():
            return None, "Duplicate customer invoice IDs detected."

        if (
            data["invoice_date"].isna().any()
            or data["due_date"].isna().any()
        ):
            return None, "Customer invoice dates contain invalid values."

        if (data["due_date"] < data["invoice_date"]).any():
            return None, "A customer due date is earlier than its invoice date."

        return data, None

    except Exception as exc:
        return None, f"Unable to load customer data from PostgreSQL: {exc}"


def get_overdue_invoices(data, reporting_date):
    work = data.copy()
    work["due_date"] = pd.to_datetime(
        work["due_date"], errors="coerce"
    )

    return work[
        (work["status"].str.lower() == "unpaid")
        & (work["due_date"] < reporting_date)
    ].copy()


# ============================================================
# FINANCIAL INTELLIGENCE ENGINE
# ============================================================

def build_supplier_risk(data, reporting_date):
    """Create explainable prototype supplier risk scores and actions."""

    work = data.copy()
    work["due_date"] = pd.to_datetime(
        work["due_date"], errors="coerce"
    )

    unpaid = work[
        work["status"].str.lower() == "unpaid"
    ].copy()

    unpaid["days_overdue"] = (
        reporting_date - unpaid["due_date"]
    ).dt.days

    overdue = unpaid[
        unpaid["days_overdue"] > 0
    ].copy()

    unpaid_exposure = (
        unpaid.groupby("supplier")["amount_eur"]
        .sum()
        .rename("unpaid_exposure")
    )

    overdue_exposure = (
        overdue.groupby("supplier")["amount_eur"]
        .sum()
        .rename("overdue_exposure")
    )

    overdue_count = (
        overdue.groupby("supplier")["invoice_id"]
        .count()
        .rename("overdue_invoice_count")
    )

    max_days = (
        overdue.groupby("supplier")["days_overdue"]
        .max()
        .rename("max_days_overdue")
    )

    risk = pd.concat(
        [
            unpaid_exposure,
            overdue_exposure,
            overdue_count,
            max_days,
        ],
        axis=1,
    ).fillna(0).reset_index()

    def calculate_score(row):
        score = 0

        if row["overdue_exposure"] > 0:
            score += 10

        if row["overdue_exposure"] > 500:
            score += 10

        if row["overdue_exposure"] > 1000:
            score += 10

        if row["overdue_invoice_count"] >= 2:
            score += 20

        if row["max_days_overdue"] >= 15:
            score += 20

        if row["max_days_overdue"] > 30:
            score += 10

        if row["unpaid_exposure"] > 3000:
            score += 20

        return min(int(score), 100)

    risk["risk_score"] = risk.apply(
        calculate_score, axis=1
    )

    def classify(score):
        if score >= 50:
            return "High"
        if score >= 25:
            return "Medium"
        return "Low"

    risk["risk_level"] = risk["risk_score"].apply(classify)

    def recommend(row):
        if (
            row["overdue_exposure"] > 0
            and row["risk_level"] == "High"
        ):
            return (
                "Prioritise this supplier: review overdue invoices, contact "
                "the accounts payable team and agree a settlement date."
            )

        if row["overdue_exposure"] > 0:
            return (
                "Send a payment reminder, confirm the expected settlement date "
                "and monitor the overdue balance."
            )

        if row["unpaid_exposure"] > 0:
            return (
                "Monitor open invoices and confirm payments are scheduled "
                "before their due dates."
            )

        return (
            "No outstanding supplier payment action is currently required."
        )

    risk["recommended_action"] = risk.apply(
        recommend, axis=1
    )

    return risk.sort_values(
        ["risk_score", "overdue_exposure", "unpaid_exposure"],
        ascending=False,
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Mittelstand AI")
st.sidebar.caption("SME Financial Intelligence Platform")

uploaded_csv = st.sidebar.file_uploader(
    "Upload supplier invoice CSV",
    type=["csv"],
    help=(
        "If no CSV is uploaded, supplier invoices are loaded "
        "from PostgreSQL."
    ),
)

reporting_date = pd.Timestamp(
    st.sidebar.date_input(
        "Reporting date",
        value=DEFAULT_REPORTING_DATE.date(),
    )
)

try:
    invoices, data_source = load_supplier_invoices(uploaded_csv)

except Exception as exc:
    st.error(f"Supplier data could not be loaded: {exc}")
    st.stop()

st.sidebar.success(
    f"Loaded {len(invoices)} supplier invoices"
)

st.sidebar.caption(
    f"Source: {data_source}"
)

customers, customer_error = load_customer_invoices()

if customers is not None:
    st.sidebar.success(
        f"Loaded {len(customers)} customer invoices"
    )
else:
    st.sidebar.warning(
        "Customer receivables unavailable"
    )

st.sidebar.divider()
st.sidebar.subheader("Dashboard filters")

supplier_options = [
    "All"
] + sorted(invoices["supplier"].unique().tolist())

selected_supplier = st.sidebar.selectbox(
    "Supplier",
    supplier_options,
)

selected_status = st.sidebar.selectbox(
    "Payment status",
    ["All", "Paid", "Unpaid"],
)

filtered = invoices.copy()

if selected_supplier != "All":
    filtered = filtered[
        filtered["supplier"] == selected_supplier
    ]

if selected_status != "All":
    filtered = filtered[
        filtered["status"] == selected_status
    ]


# ============================================================
# SHARED CALCULATIONS
# ============================================================

risk_results = build_supplier_risk(
    invoices, reporting_date
)

overdue_all = get_overdue_invoices(
    invoices, reporting_date
)

filtered_overdue = get_overdue_invoices(
    filtered, reporting_date
)

paid_filtered = filtered[
    filtered["status"] == "Paid"
]

unpaid_filtered = filtered[
    filtered["status"] == "Unpaid"
]

total_value = filtered["amount_eur"].sum()
paid_value = paid_filtered["amount_eur"].sum()
unpaid_value = unpaid_filtered["amount_eur"].sum()
overdue_value = filtered_overdue["amount_eur"].sum()

total_paid = invoices.loc[
    invoices["status"] == "Paid", "amount_eur"
].sum()

total_unpaid = invoices.loc[
    invoices["status"] == "Unpaid", "amount_eur"
].sum()

total_overdue = overdue_all["amount_eur"].sum()


# ============================================================
# HEADER AND FINANCIAL OVERVIEW
# ============================================================

st.title("📊 Mittelstand AI")

st.caption(
    "AI-powered financial operations and business intelligence for SMEs"
)

st.caption(
    f"Reporting date: {reporting_date.strftime('%d %B %Y')}  ·  "
    f"Data source: {data_source}"
)

st.divider()
st.header("📊 Financial Overview")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Invoices", f"{len(filtered):,}")
k2.metric("Invoice value", money(total_value))
k3.metric("Paid value", money(paid_value))
k4.metric("Unpaid value", money(unpaid_value))

k5, k6, k7 = st.columns(3)

k5.metric(
    "Overdue invoices",
    f"{len(filtered_overdue):,}",
)

k6.metric(
    "Overdue exposure",
    money(overdue_value),
)

k7.metric(
    "Overdue share of unpaid",
    (
        f"{overdue_value / unpaid_value * 100:.1f}%"
        if unpaid_value else "0.0%"
    ),
)

left, right = st.columns(2)

with left:
    st.subheader("Invoice value by supplier")

    spend = (
        filtered.groupby("supplier")["amount_eur"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(spend)

with right:
    st.subheader("Paid vs unpaid")

    payment_mix = (
        filtered.groupby("status")["amount_eur"]
        .sum()
        .reindex(["Paid", "Unpaid"], fill_value=0)
    )

    st.bar_chart(payment_mix)

st.subheader("Monthly invoice value")

monthly = (
    filtered.assign(
        month=filtered["invoice_date"].dt.to_period("M").astype(str)
    )
    .groupby("month", as_index=False)["amount_eur"]
    .sum()
    .sort_values("month")
)

if not monthly.empty:
    st.line_chart(
        monthly.set_index("month")["amount_eur"]
    )
else:
    st.info(
        "No monthly invoice data available for these filters."
    )


# ============================================================
# SUPPLIER ANALYTICS AND AGING
# ============================================================

st.divider()
st.header("🏢 Supplier Analytics")

supplier_summary = (
    filtered.groupby("supplier")
    .agg(
        invoice_count=("invoice_id", "count"),
        total_value=("amount_eur", "sum"),
    )
    .sort_values("total_value", ascending=False)
)

st.dataframe(
    supplier_summary,
    use_container_width=True,
)

st.subheader("Unpaid invoice aging")

aging = unpaid_filtered.copy()

aging["days_overdue"] = (
    reporting_date - aging["due_date"]
).dt.days


def aging_bucket(days):
    if days <= 0:
        return "Not yet due"

    if days <= 30:
        return "1–30 days"

    if days <= 60:
        return "31–60 days"

    return "60+ days"


aging["aging_category"] = aging["days_overdue"].apply(
    aging_bucket
)

aging_order = [
    "Not yet due",
    "1–30 days",
    "31–60 days",
    "60+ days",
]

aging_summary = (
    aging.groupby("aging_category")["amount_eur"]
    .sum()
    .reindex(aging_order, fill_value=0)
)

st.bar_chart(aging_summary)

st.subheader("Overdue supplier invoices")

if filtered_overdue.empty:
    st.success(
        "No overdue unpaid supplier invoices in this filtered view."
    )

else:
    overdue_display = filtered_overdue[
        ["invoice_id", "supplier", "amount_eur", "due_date"]
    ].copy()

    overdue_display["days_overdue"] = (
        reporting_date - overdue_display["due_date"]
    ).dt.days

    st.dataframe(
        overdue_display,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# SUPPLIER RISK AND EXECUTIVE FINANCIAL INTELLIGENCE
# ============================================================

st.divider()
st.header("⚠️ Supplier Risk & Financial Intelligence")

st.caption(
    "Transparent prototype rules, not validated credit ratings or predictions. "
    "Review the underlying invoices before taking payment action."
)

displayed_risk = risk_results.copy()

if selected_supplier != "All":
    displayed_risk = displayed_risk[
        displayed_risk["supplier"] == selected_supplier
    ]

if displayed_risk.empty:
    st.info(
        "No supplier risk information for this selection."
    )

else:
    r1, r2, r3 = st.columns(3)

    r1.metric(
        "High-risk suppliers",
        int((displayed_risk["risk_level"] == "High").sum()),
    )

    r2.metric(
        "Medium-risk suppliers",
        int((displayed_risk["risk_level"] == "Medium").sum()),
    )

    r3.metric(
        "Low-risk suppliers",
        int((displayed_risk["risk_level"] == "Low").sum()),
    )

    st.subheader("Supplier risk ranking")

    st.dataframe(
        displayed_risk[
            [
                "supplier",
                "unpaid_exposure",
                "overdue_exposure",
                "overdue_invoice_count",
                "max_days_overdue",
                "risk_score",
                "risk_level",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Risk score by supplier")

    risk_chart = displayed_risk[
        ["supplier", "risk_score"]
    ].copy()

    risk_chart["risk_score"] = pd.to_numeric(
        risk_chart["risk_score"],
        errors="coerce",
    )

    risk_chart = risk_chart.dropna(
        subset=["risk_score"]
    ).sort_values(
        "risk_score",
        ascending=True,
    )

    if not risk_chart.empty:
        risk_bars = (
            alt.Chart(risk_chart)
            .mark_bar(cornerRadiusEnd=5)
            .encode(
                x=alt.X(
                    "risk_score:Q",
                    title="Risk score (0–100)",
                    scale=alt.Scale(domain=[0, 100]),
                ),
                y=alt.Y(
                    "supplier:N",
                    title="Supplier",
                    sort=alt.SortField(
                        field="risk_score",
                        order="ascending",
                    ),
                    axis=alt.Axis(
                        labelLimit=260,
                        labelOverlap=False,
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "supplier:N",
                        title="Supplier",
                    ),
                    alt.Tooltip(
                        "risk_score:Q",
                        title="Risk score",
                        format=".0f",
                    ),
                ],
            )
            .properties(
                height=max(220, 55 * len(risk_chart)),
            )
        )

        st.altair_chart(
            risk_bars,
            use_container_width=True,
        )

    else:
        st.info(
            "No supplier risk scores are available for this selection."
        )

    st.subheader("Recommended supplier actions")

    st.dataframe(
        displayed_risk[
            [
                "supplier",
                "risk_level",
                "recommended_action",
                "overdue_exposure",
                "unpaid_exposure",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    top_risk = displayed_risk.iloc[0]

    st.info(
        f"**Priority supplier:** {top_risk['supplier']} — "
        f"{top_risk['risk_level']} risk "
        f"(score {int(top_risk['risk_score'])}/100). "
        f"{top_risk['recommended_action']}"
    )

st.subheader("Executive Financial Summary")

s1, s2, s3, s4 = st.columns(4)

s1.metric(
    "Total invoices analysed",
    f"{len(invoices):,}",
)

s2.metric(
    "Paid amount",
    money(total_paid),
)

s3.metric(
    "Unpaid amount",
    money(total_unpaid),
)

s4.metric(
    "Overdue amount",
    money(total_overdue),
)

if not risk_results.empty:
    highest_risk = risk_results.iloc[0]

    st.markdown(
        f"""
        **Financial position:** {len(overdue_all)} supplier invoices are overdue,
        representing **{money(total_overdue)}**.

        **Highest-risk supplier:** {highest_risk['supplier']} with a prototype
        risk score of **{int(highest_risk['risk_score'])}/100
        ({highest_risk['risk_level']})**.

        **Recommended focus:** Review overdue invoices, contact suppliers where
        settlement is outstanding, and monitor upcoming payment deadlines.
        """
    )

st.download_button(
    "⬇️ Download supplier risk and recommendations report",
    data=risk_results.to_csv(index=False).encode("utf-8"),
    file_name="mittelstand_supplier_risk_report.csv",
    mime="text/csv",
)

st.download_button(
    "⬇️ Download overdue supplier invoice report",
    data=overdue_all.to_csv(index=False).encode("utf-8"),
    file_name="mittelstand_overdue_report.csv",
    mime="text/csv",
)


# ============================================================
# CUSTOMER RECEIVABLES
# ============================================================

st.divider()
st.header("💰 Customer Receivables")

if customers is None:
    st.warning(
        customer_error or "Customer receivables are unavailable."
    )

else:
    customer_paid = customers[
        customers["status"] == "Paid"
    ]

    customer_unpaid = customers[
        customers["status"] == "Unpaid"
    ]

    customer_overdue = customers[
        (customers["status"] == "Unpaid")
        & (customers["due_date"] < reporting_date)
    ].copy()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Customer invoices",
        f"{len(customers):,}",
    )

    c2.metric(
        "Collected",
        money(customer_paid["amount_eur"].sum()),
    )

    c3.metric(
        "Outstanding",
        money(customer_unpaid["amount_eur"].sum()),
    )

    c4.metric(
        "Overdue receivables",
        money(customer_overdue["amount_eur"].sum()),
    )

    st.subheader("Outstanding amount by customer")

    outstanding_by_customer = (
        customer_unpaid.groupby("customer")["amount_eur"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(outstanding_by_customer)

    st.subheader("Overdue customer invoices")

    if customer_overdue.empty:
        st.success(
            "No overdue customer invoices."
        )

    else:
        customer_overdue["days_overdue"] = (
            reporting_date - customer_overdue["due_date"]
        ).dt.days

        st.dataframe(
            customer_overdue[
                [
                    "invoice_id",
                    "customer",
                    "due_date",
                    "amount_eur",
                    "days_overdue",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.download_button(
        "⬇️ Download customer receivables report",
        data=customers.to_csv(index=False).encode("utf-8"),
        file_name="mittelstand_customer_receivables.csv",
        mime="text/csv",
    )


# ============================================================
# CASH FLOW FORECAST
# ============================================================

st.divider()
st.header("📈 30-Day Net Cash Flow Forecast")

opening_cash = st.sidebar.number_input(
    "Demo opening cash balance (€)",
    min_value=0.0,
    value=20000.0,
    step=1000.0,
)

forecast_end = reporting_date + pd.Timedelta(days=30)

forecast_dates = pd.date_range(
    reporting_date,
    forecast_end,
    freq="D",
)

supplier_unpaid = invoices[
    invoices["status"] == "Unpaid"
].copy()

supplier_unpaid["forecast_date"] = (
    supplier_unpaid["due_date"].clip(
        lower=reporting_date
    )
)

supplier_due = supplier_unpaid[
    supplier_unpaid["due_date"] <= forecast_end
]

if customers is not None:
    customer_unpaid = customers[
        customers["status"] == "Unpaid"
    ].copy()

    customer_unpaid["forecast_date"] = (
        customer_unpaid["due_date"].clip(
            lower=reporting_date
        )
    )

    customer_due = customer_unpaid[
        customer_unpaid["due_date"] <= forecast_end
    ]

else:
    customer_due = pd.DataFrame(
        columns=["forecast_date", "amount_eur"]
    )

incoming = (
    customer_due.groupby("forecast_date")["amount_eur"]
    .sum()
    .reindex(forecast_dates, fill_value=0)
)

outgoing = (
    supplier_due.groupby("forecast_date")["amount_eur"]
    .sum()
    .reindex(forecast_dates, fill_value=0)
)

cash_flow = pd.DataFrame(
    index=forecast_dates
)

cash_flow.index.name = "date"

cash_flow["expected_collections_eur"] = incoming

cash_flow["expected_supplier_payments_eur"] = outgoing

cash_flow["net_cash_flow_eur"] = (
    incoming - outgoing
)

cash_flow["projected_cash_balance_eur"] = (
    opening_cash
    + cash_flow["net_cash_flow_eur"].cumsum()
)

total_incoming = cash_flow[
    "expected_collections_eur"
].sum()

total_outgoing = cash_flow[
    "expected_supplier_payments_eur"
].sum()

closing_cash = (
    opening_cash + total_incoming - total_outgoing
)

f1, f2, f3, f4 = st.columns(4)

f1.metric(
    "Opening cash",
    money(opening_cash),
)

f2.metric(
    "Expected collections",
    money(total_incoming),
)

f3.metric(
    "Supplier payments",
    money(total_outgoing),
)

f4.metric(
    "Projected closing cash",
    money(closing_cash),
)

st.caption(
    "Illustrative forecast only. It assumes unpaid customer invoices are collected "
    "and unpaid supplier invoices are paid on their due dates; overdue invoices "
    "are scheduled at the reporting date. It excludes payroll, tax, rent, operating "
    "expenses, financing and payment delays."
)

cash_flow_chart = cash_flow.reset_index()

st.line_chart(
    cash_flow_chart,
    x="date",
    y="projected_cash_balance_eur",
    x_label="Forecast date",
    y_label="Projected cash balance (€)",
    height=360,
)

with st.expander("View daily forecast details"):
    st.dataframe(
        cash_flow_chart,
        use_container_width=True,
        hide_index=True,
    )

if (
    cash_flow["projected_cash_balance_eur"] < 0
).any():
    st.error(
        "The illustrative forecast shows a negative cash balance."
    )

else:
    st.success(
        "No negative cash balance appears in this illustrative forecast."
    )

st.download_button(
    "⬇️ Download 30-day cash flow forecast",
    data=cash_flow.to_csv().encode("utf-8"),
    file_name="mittelstand_cash_flow_forecast.csv",
    mime="text/csv",
)


# ============================================================
# INVOICE RECORDS AND EXPORT
# ============================================================

st.divider()
st.header("📑 Supplier Invoice Records")

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "⬇️ Download filtered supplier invoices",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="mittelstand_supplier_invoices.csv",
    mime="text/csv",
)


# ============================================================
# PDF INVOICE EXTRACTION AND DATABASE IMPORT
# ============================================================

st.divider()
st.header("📄 PDF Invoice Extraction")

uploaded_pdf = st.file_uploader(
    "Upload a PDF invoice for extraction",
    type=["pdf"],
    key="supplier_pdf_uploader",
)

if uploaded_pdf is not None:
    try:
        from analytics.pdf_extractor import (
            extract_text_from_pdf,
            extract_invoice_details,
            validate_invoice_details,
        )

        from analytics.invoice_importer import (
            check_duplicate_invoice,
            save_invoice,
        )

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf",
            ) as temp_file:
                temp_file.write(
                    uploaded_pdf.getvalue()
                )
                temp_path = temp_file.name

            extracted_text = extract_text_from_pdf(
                temp_path
            )

            details = extract_invoice_details(
                extracted_text
            )

            errors = validate_invoice_details(
                details
            )

            st.subheader("Extracted invoice details")
            st.json(details)

            if errors:
                st.warning(
                    "Invoice needs manual review."
                )

                for error in errors:
                    st.write(f"- {error}")

            else:
                st.success(
                    "Required invoice fields passed validation."
                )

                duplicate_status = check_duplicate_invoice(
                    details
                )

                if duplicate_status == "DUPLICATE":
                    st.error(
                        "Exact duplicate invoice ID detected."
                    )

                elif duplicate_status == "POTENTIAL_DUPLICATE":
                    st.warning(
                        "Potential duplicate detected. Review the existing record "
                        "before deciding whether to import."
                    )

                else:
                    st.info(
                        "No duplicate match detected."
                    )

                    if st.button(
                        "Save extracted invoice to database"
                    ):
                        result = save_invoice(details)

                        if result == "SAVED":
                            st.success(
                                "Invoice saved. Refresh the app to load the new record."
                            )

                        else:
                            st.warning(
                                f"Invoice was not saved: {result}"
                            )

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as exc:
        st.error(
            f"PDF extraction failed: {exc}"
        )


# ============================================================
# ANOMALY DETECTION
# ============================================================

st.divider()
st.header("🧪 Invoice Anomaly Detection")

try:
    from analytics.anomaly_detector import detect_invoice_anomalies

    anomalies = detect_invoice_anomalies()

    a1, a2 = st.columns(2)

    a1.metric(
        "Detected anomalies",
        len(anomalies),
    )

    high_severity = (
        int((anomalies["severity"] == "High").sum())
        if not anomalies.empty and "severity" in anomalies.columns
        else 0
    )

    a2.metric(
        "High-severity anomalies",
        high_severity,
    )

    if anomalies.empty:
        st.success(
            "No invoice anomalies detected in the database."
        )

    else:
        st.warning(
            "Potential invoice anomalies require review."
        )

        st.dataframe(
            anomalies,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download anomaly report",
            data=anomalies.to_csv(index=False).encode("utf-8"),
            file_name="mittelstand_invoice_anomalies.csv",
            mime="text/csv",
        )

except Exception as exc:
    st.warning(
        f"Anomaly detection is unavailable: {exc}"
    )


# ============================================================
# MITTELSTAND AI FINANCIAL CHAT ASSISTANT
# ============================================================

st.divider()
st.header("🤖 Ask Mittelstand AI")

st.caption(
    "Ask questions about supplier invoices, overdue payments and financial "
    "exposure. Figures are calculated from the current project dataset; "
    "other questions are answered by the local Ollama model."
)

if "financial_chat_history" not in st.session_state:
    st.session_state.financial_chat_history = []

with st.expander("Try these example questions"):
    st.markdown(
        "- Which supplier has the highest unpaid exposure?\n"
        "- Why does Berlin Components GmbH need attention?\n"
        "- What is the total overdue supplier exposure?\n"
        "- How much unpaid supplier debt is not yet due?\n"
        "- What is the total supplier invoice value?"
    )

for chat_message in st.session_state.financial_chat_history:
    with st.chat_message(chat_message["role"]):
        st.markdown(
            chat_message["content"]
        )

user_question = st.chat_input(
    "Ask a question about your financial data...",
    key="mittelstand_financial_chat_input",
)

if user_question:
    st.session_state.financial_chat_history.append(
        {
            "role": "user",
            "content": user_question,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner(
            "Analysing your financial data..."
        ):
            try:
                assistant_answer = ask_financial_assistant(
                    user_question
                )

                if (
                    not isinstance(assistant_answer, str)
                    or not assistant_answer.strip()
                ):
                    assistant_answer = (
                        "I couldn't generate an answer. Please try rephrasing "
                        "your question."
                    )

            except Exception as exc:
                assistant_answer = (
                    "The financial assistant encountered an error. "
                    f"Details: {exc}"
                )

        st.markdown(assistant_answer)

    st.session_state.financial_chat_history.append(
        {
            "role": "assistant",
            "content": assistant_answer,
        }
    )

if st.session_state.financial_chat_history:
    if st.button(
        "Clear chat history",
        key="clear_financial_chat",
    ):
        st.session_state.financial_chat_history = []
        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Mittelstand AI | Portfolio prototype using synthetic invoice data. "
    "Risk scores and forecasts are illustrative decision-support outputs, "
    "not audited financial advice."
)