import streamlit as st
import pandas as pd
import plotly.express as px
import os  # For file cleanup

st.set_page_config(page_title="Insurance Claims Dashboard", layout="wide")
st.title("Insurance Claims Analysis and Visualization Dashboard")

# File uploader
uploaded_file = st.file_uploader("Upload File", type=["csv", "xls", "xlsx", "xlsm"])

if uploaded_file:
    try:
        # Load data
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

        # Basic validation: Check for required columns
        required_cols = ['Date_of_Service', 'Submitted_Amount', 'Payer_Name', 'Doctor_Name']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}. Please check your file.")
            st.stop()

        # Data cleaning
        df.columns = df.columns.str.strip()
        df['Date_of_Service'] = pd.to_datetime(df['Date_of_Service'], errors='coerce')
        df = df.dropna(subset=['Date_of_Service'])

        # Amount columns (with validation)
        amount_cols = ['Submitted_Amount', 'Resubmitted_Amount_1', 'Resubmitted_Amount2',
                       'Paid_Amount', 'Resubmission_Paid_Amount_1', 'Resubmission_Paid_Amount2',
                       'Denied_Amount', 'Resubmission_Denied_Amount_Remittance_1', 'Resubmission_Denied_Amount_Remittance_2']
        df[amount_cols] = df[amount_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Derived columns
        df['Year'] = df['Date_of_Service'].dt.year
        df['Month'] = df['Date_of_Service'].dt.strftime('%b')
        df['Quarter'] = df['Date_of_Service'].dt.quarter

        # Simplified calculations (adjust logic as needed for accuracy)
        df['Total Submitted Amount'] = round(df['Submitted_Amount'] + df['Resubmitted_Amount_1'] + df['Resubmitted_Amount2'],2)

        df['Total Paid Amount'] = round(df['Paid_Amount'] + df['Resubmission_Paid_Amount_1'] + df['Resubmission_Paid_Amount2'],2)

        df['Total Denied Amount'] = round((df['Denied_Amount'] - df['Resubmitted_Amount_1']) + (df['Resubmission_Denied_Amount_Remittance_1'] - df['Resubmitted_Amount2']) + df['Resubmission_Denied_Amount_Remittance_2'],2)

        df['Total Pending Amount'] = round(df['Submitted_Amount'] - (df['Total Paid Amount'] + df['Total Denied Amount']),2)

        # Sidebar filters for interactivity
        st.sidebar.header("Filters")

        # Options for doctors with "ALL" added
        doctor_options = ["ALL"] + list(df['Doctor_Name'].unique())
        selected_doctor = st.sidebar.multiselect("Select Doctor(s)", options=doctor_options, default=["ALL"])

        # Options for years with "ALL" added
        year_options = ["ALL"] + sorted(df['Year'].unique())
        selected_year = st.sidebar.multiselect("Select Year(s)", options=year_options, default=["ALL"])

        # Options for insurance with "ALL" added
        insurance_options = ["ALL"] + list(df['Payer_Name'].unique())
        selected_insurance = st.sidebar.multiselect("Select Insurance(s)", options=insurance_options, default=["ALL"])

        # Determine effective selections: if "ALL" is selected, use all options; otherwise, use selected ones
        effective_doctor = df['Doctor_Name'].unique() if "ALL" in selected_doctor else [d for d in selected_doctor if d != "ALL"]
        effective_year = df['Year'].unique() if "ALL" in selected_year else [y for y in selected_year if y != "ALL"]
        effective_insurance = df['Payer_Name'].unique() if "ALL" in selected_insurance else [i for i in selected_insurance if i != "ALL"]

        # Apply filters to raw df
        filtered_df = df[
            (df['Doctor_Name'].isin(effective_doctor)) &
            (df['Year'].isin(effective_year)) &
            (df['Payer_Name'].isin(effective_insurance))
        ]

        # Grouped Summary Table (filtered)
        grouped_summary = filtered_df.groupby(['Year', 'Payer_Name']).agg(
            Claimed_Amount=('Total Submitted Amount', 'sum'),
            Received_Amount=('Total Paid Amount', 'sum'),
            Denied_Amount=('Total Denied Amount', 'sum'),
            Pending_Amount=('Total Pending Amount', 'sum')
        ).reset_index().sort_values(by='Year')

        # Submitted per Month Table (filtered)
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        grouped_submitted = filtered_df.groupby(['Year', 'Payer_Name', 'Month'])['Submitted_Amount'].sum().unstack().fillna(0)
        grouped_submitted = grouped_submitted.reindex(columns=month_order, fill_value=0).reset_index()

        # Doctor + Insurance + Month Table (Pivot, filtered)
        doctor_insurance_month = filtered_df.groupby(['Year', 'Doctor_Name', 'Payer_Name', 'Month']).agg(
            Claimed_Amount=('Total Submitted Amount', 'sum'),
            Received_Amount=('Total Paid Amount', 'sum'),
            Denied_Amount=('Total Denied Amount', 'sum'),
            Pending_Amount=('Total Pending Amount', 'sum')
        ).reset_index()
        doctor_insurance_month['Month'] = pd.Categorical(doctor_insurance_month['Month'], categories=month_order, ordered=True)
        doctor_insurance_month = doctor_insurance_month.sort_values(['Year', 'Doctor_Name', 'Payer_Name', 'Month'])
        pivot_table = doctor_insurance_month.pivot_table(
            index=['Year', 'Doctor_Name', 'Payer_Name'],
            columns='Month',
            values=['Claimed_Amount', 'Received_Amount', 'Denied_Amount', 'Pending_Amount'],
            fill_value=0
        )
        pivot_table.columns = [f'{month}_{metric.upper()}' for metric, month in pivot_table.columns]
        doctor_insurance_month = pivot_table.reset_index()

        # Display Tables
        st.subheader("Summary Table: Claimed, Received, Denied, Pending (Filtered)")
        st.dataframe(grouped_summary)
        st.subheader("Submitted Amount Per Month (Insurance/TPA wise, Filtered)")
        st.dataframe(grouped_submitted)
        st.subheader("Doctor-wise | Insurance-wise | Monthly Summary Table (Filtered)")
        st.dataframe(doctor_insurance_month)


        # Charts
        st.subheader("Data Visualizations (Filtered Data)")

        # Aggregate by Doctor for bar chart (sum across all filtered data)
        doctor_summary = filtered_df.groupby('Doctor_Name').agg(
            Claimed_Amount=('Total Submitted Amount', 'sum'),
            Received_Amount=('Total Paid Amount', 'sum'),
            Denied_Amount=('Total Denied Amount', 'sum'),
            Pending_Amount=('Total Pending Amount', 'sum')
        ).reset_index()

        # Consolidated Bar Chart: By Doctor (Amounts)
        bar_chart = px.bar(doctor_summary, x='Doctor_Name', y=['Claimed_Amount', 'Received_Amount', 'Denied_Amount', 'Pending_Amount'],
                           title="Claim vs Received vs Denied vs Pending by Doctor",
                           labels={'value': 'Amount', 'variable': 'Category'}, barmode='group')
        st.plotly_chart(bar_chart)

        # Consolidated Bar Chart: Total claims (count of rows) by doctor
        doctor_claims_count = filtered_df.groupby('Doctor_Name').agg(Claimed_Amount=('Doctor_Name', 'size')).reset_index()
        bar_chart = px.bar(doctor_claims_count, x='Doctor_Name', y='Claimed_Amount',
                           color_discrete_sequence=px.colors.qualitative.Set2,
                           title="Total Claimed Amount (Count of Claims) per Doctor",
                           labels={'Claimed_Amount': 'Number of Claims', 'Doctor_Name': 'Doctor Name'})
        st.plotly_chart(bar_chart)

        # Scatter: Doctor Performance (Claims Count vs. Paid Amount)
        doctor_performance = filtered_df.groupby('Doctor_Name').agg(
            Total_Claims=('Doctor_Name', 'size'),
            Total_Paid=('Total Paid Amount', 'sum')
        ).reset_index()
        scatter_chart = px.scatter(doctor_performance, x='Total_Claims', y='Total_Paid',
                                   color='Doctor_Name', size='Total_Claims',
                                   title="Doctor Performance: Claims Count vs. Paid Amount",
                                   labels={'Total_Claims': 'Number of Claims', 'Total_Paid': 'Total Paid Amount'})
        st.plotly_chart(scatter_chart)

        # Bar: By Year
        bar_chart_year = px.bar(grouped_summary, x='Year', y=['Claimed_Amount', 'Received_Amount', 'Denied_Amount'],
                                title="Total Claimed vs Paid vs Denied Amount by Year",
                                labels={'value': 'Amount', 'variable': 'Category'}, barmode='group')
        st.plotly_chart(bar_chart_year)

        # Consolidated Bar: Claimed vs Paid by Insurance
        insurance_summary = grouped_summary.groupby('Payer_Name').agg(
            Claimed_Amount=('Claimed_Amount', 'sum'),
            Received_Amount=('Received_Amount', 'sum')
        ).reset_index()
        bar_insurance = px.bar(insurance_summary, x='Payer_Name', y=['Claimed_Amount', 'Received_Amount'],
                               title="Claimed vs Paid Amounts by Insurance Provider",
                               labels={'value': 'Amount', 'variable': 'Category'}, barmode='group')
        st.plotly_chart(bar_insurance)

        # Histogram: Monthly Claims
        hist_chart = px.histogram(filtered_df, x='Month', y='Submitted_Amount', color='Year',
                                  title="Monthly Claim Distribution", barmode='group',
                                  category_orders={'Month': month_order})
        st.plotly_chart(hist_chart)

        # Export to Excel (filtered data)
        output_file = "Insurance_Claims_Report.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            grouped_summary.to_excel(writer, sheet_name="Summary", index=False)
            grouped_submitted.to_excel(writer, sheet_name="Submitted Claims Per Month", index=False)
            doctor_insurance_month.to_excel(writer, sheet_name="Doctor_Insurance_Monthly", index=False)
            filtered_df.to_excel(writer, sheet_name="All Claims Raw (Filtered)", index=False)

        # Download Button
        with open(output_file, "rb") as file:
            st.download_button("Download Full Insurance Claims Excel Report (Filtered)",
                               file, file_name="Insurance_Claims_Report.xlsx")
        # Cleanup (optional, for local runs)
        os.remove(output_file)

    except Exception as e:
        st.error(f"Error processing file: {e}. Please check your data format and try again.")
