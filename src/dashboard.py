import streamlit as st
import pandas as pd
import plotly.express as px
import os  # For file cleanup

st.set_page_config(page_title="Insurance Claims Dashboard", layout="wide")
st.title("Insurance Claims Analysis and Visualization Dashboard")

# File uploader with size warning
uploaded_file = st.file_uploader("Upload Excel/CSV File (Max 50MB recommended)", type=["csv", "xls", "xlsx", "xlsm"])

if uploaded_file:
    try:
        # Load data
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

        # Basic validation: Check for required columns
        required_cols = ['Remittance_Date', 'Payer_Name', 'Paid_Amount']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}. Please check your file.")
            st.stop()

        # Data cleaning
        df.columns = df.columns.str.strip()

        # Convert amount columns to numeric (expanded for robustness)
        amount_cols = ['Paid_Amount', 'Resubmission_Paid_Amount_1', 'Resubmission_Paid_Amount2',
                       'Submitted_Amount', 'Resubmitted_Amount_1', 'Resubmitted_Amount2',
                       'Denied_Amount', 'Resubmission_Denied_Amount_Remittance_1', 'Resubmission_Denied_Amount_Remittance_2']

        df[amount_cols] = df[amount_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Convert 'Remittance_Date' column to datetime
        df['Remittance_Date'] = pd.to_datetime(df['Remittance_Date'], errors='coerce')
        df = df.dropna(subset=['Remittance_Date'])

        # Extract year, month, and quarter
        df['Remittance_Year'] = df['Remittance_Date'].dt.year
        df['Remittance_Month'] = df['Remittance_Date'].dt.strftime('%b')
        df['Quarter'] = df['Remittance_Date'].dt.quarter

        # Simplified calculations (adjust logic as needed for accuracy)
        df['Total Submitted Amount'] = round(df['Submitted_Amount'] + df['Resubmitted_Amount_1'] + df['Resubmitted_Amount2'], 2)
        df['Total Paid Amount'] = round(df['Paid_Amount'] + df['Resubmission_Paid_Amount_1'] + df['Resubmission_Paid_Amount2'], 2)
        df['Total Denied Amount'] = round((df['Denied_Amount'] - df['Resubmitted_Amount_1']) + (df['Resubmission_Denied_Amount_Remittance_1'] - df['Resubmitted_Amount2']) + df['Resubmission_Denied_Amount_Remittance_2'], 2)
        df['Total Pending Amount'] = round(df['Submitted_Amount'] - (df['Total Paid Amount'] + df['Total Denied Amount']), 2)

        # Sidebar filters for interactivity
        st.sidebar.header("Filters")

        # Options for years with "ALL" added
        year_options = ["ALL"] + sorted(df['Remittance_Year'].unique())
        selected_year = st.sidebar.multiselect("Select Year(s)", options=year_options, default=["ALL"])

        # Options for insurance with "ALL" added
        insurance_options = ["ALL"] + list(df['Payer_Name'].unique())
        selected_insurance = st.sidebar.multiselect("Select Insurance(s)", options=insurance_options, default=["ALL"])

        # Determine effective selections: if "ALL" is selected, use all options; otherwise, use selected ones
        effective_year = df['Remittance_Year'].unique() if "ALL" in selected_year else [y for y in selected_year if y != "ALL"]
        effective_insurance = df['Payer_Name'].unique() if "ALL" in selected_insurance else [i for i in selected_insurance if i != "ALL"]

        # Apply filters using the effective selections
        filtered_df = df[
            (df['Remittance_Year'].isin(effective_year)) &
            (df['Payer_Name'].isin(effective_insurance))
        ]

        # Group by year, insurance provider, and month (filtered)
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        grouped_paid = filtered_df.groupby(['Remittance_Year', 'Payer_Name', 'Remittance_Month'])['Total Paid Amount'].sum().unstack(fill_value=0)
        grouped_paid = grouped_paid.reindex(columns=month_order, fill_value=0).reset_index().sort_values(by='Remittance_Year')

        # Additional summary table (new for completeness)
        summary_table = filtered_df.groupby(['Remittance_Year', 'Payer_Name']).agg(
            Total_Submitted=('Total Submitted Amount', 'sum'),
            Total_Paid=('Total Paid Amount', 'sum'),
            Total_Denied=('Total Denied Amount', 'sum'),
            Total_Pending=('Total Pending Amount', 'sum')
        ).reset_index().sort_values(by='Remittance_Year')

        # Display Tables
        st.subheader("Paid Amount Per Month (Filtered)")
        st.dataframe(grouped_paid)
        st.subheader("Summary Table: Submitted, Paid, Denied by Year and Insurance (Filtered)")
        st.dataframe(summary_table)

        # Charts Section
        st.subheader("Data Visualizations (Filtered Data)")
        if filtered_df.empty:
            st.warning("No data available for the selected filters. Please adjust your selections.")
        else:
            # Existing/Enhanced Charts
            st.markdown("### Trends and Comparisons")

            # Enhanced Bar Chart: Total Paid Amount per Year (added color by quarter for more insight)
            yearly_paid = filtered_df.groupby(['Remittance_Year', 'Quarter'])['Total Paid Amount'].sum().reset_index()
            bar_fig = px.bar(yearly_paid, x='Remittance_Year', y='Total Paid Amount', color='Quarter',
                             title="Yearly Paid Amount by Quarter", labels={'Total Paid Amount': "Total Paid ($)"},
                             color_discrete_sequence=px.colors.qualitative.Set1)
            st.plotly_chart(bar_fig)

            # Enhanced Bar Chart: Paid Amount by Insurance Provider (horizontal for readability)
            insurance_paid = filtered_df.groupby('Payer_Name')['Total Paid Amount'].sum().reset_index()
            bar_insurance = px.bar(insurance_paid, x='Total Paid Amount', y='Payer_Name', orientation='h',
                                   title="Paid Amount by Insurance Provider",
                                   labels={'Total Paid Amount': "Total Paid ($)"}, color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(bar_insurance)

            # Enhanced Histogram: Distribution of Paid Amounts (added marginal rug plot)
            hist_fig = px.histogram(filtered_df, x='Total Paid Amount', nbins=50,
                                    title="Distribution of Paid Amounts", labels={'Total Paid Amount': "Paid Amount ($)"},
                                    marginal="rug", color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(hist_fig)

            # Enhanced Scatter Chart: Paid vs. Submitted by Insurance (added trendline)
            scatter_data = filtered_df.groupby('Payer_Name').agg(
                Total_Submitted=('Total Submitted Amount', 'sum'),
                Total_Paid=('Total Paid Amount', 'sum')
            ).reset_index()
            scatter_fig = px.scatter(scatter_data, x='Total_Submitted', y='Total_Paid', color='Payer_Name',
                                     size='Total_Paid', title="Insurance Performance: Submitted vs. Paid Amounts",
                                     labels={'Total_Submitted': 'Total Submitted ($)', 'Total_Paid': 'Total Paid ($)'},
                                     trendline="ols")
            st.plotly_chart(scatter_fig)


            st.markdown("### Time-Series and Trends")

            # Line Chart: Paid Amount Trends Over Time
            time_trend = filtered_df.groupby(['Remittance_Year', 'Remittance_Month'])['Total Paid Amount'].sum().reset_index()
            time_trend['Month-Year'] = time_trend['Remittance_Month'] + '-' + time_trend['Remittance_Year'].astype(str)
            line_fig = px.line(time_trend, x='Month-Year', y='Total Paid Amount',
                               title="Monthly Paid Amount Trends", labels={'Total Paid Amount': "Total Paid ($)"},
                               color_discrete_sequence=['#ff7f0e'])
            st.plotly_chart(line_fig)

            # Area Chart: Cumulative Paid Amounts by Insurance
            area_data = filtered_df.groupby('Payer_Name')['Total Paid Amount'].sum().reset_index().sort_values('Total Paid Amount', ascending=False)
            area_fig = px.area(area_data, x='Payer_Name', y='Total Paid Amount',
                               title="Cumulative Paid Amounts by Insurance Provider",
                               labels={'Total Paid Amount': "Total Paid ($)"}, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(area_fig)

            st.markdown("### Proportions and Distributions")

            # Pie Chart: Paid vs. Denied Proportions by Insurance
            pie_data = filtered_df.groupby('Payer_Name').agg(
                Total_Paid=('Total Paid Amount', 'sum'),
                Total_Denied=('Total Denied Amount', 'sum')
            ).reset_index()
            pie_data_melted = pie_data.melt(id_vars='Payer_Name', value_vars=['Total_Paid', 'Total_Denied'],
                                             var_name='Status', value_name='Amount')
            pie_fig = px.pie(pie_data_melted, values='Amount', names='Status', color='Status',
                             title="Paid vs. Denied Amounts by Insurance Provider",
                             labels={'Amount': 'Amount ($)'}, color_discrete_map={'Total_Paid': '00F7FF', 'Total_Denied': 'red'})
            st.plotly_chart(pie_fig)

            # Box Plot: Paid Amount Distribution by Insurance
            box_fig = px.box(filtered_df, x='Payer_Name', y='Total Paid Amount',
                             title="Paid Amount Distribution by Insurance Provider",
                             labels={'Total Paid Amount': "Paid Amount ($)"}, color='Payer_Name')
            st.plotly_chart(box_fig)

            st.markdown("### Advanced Insights")

            # Heatmap: Monthly Paid Amounts by Year and Insurance
            heatmap_data = filtered_df.groupby(['Remittance_Year', 'Remittance_Month', 'Payer_Name'])['Total Paid Amount'].sum().reset_index()
            heatmap_pivot = heatmap_data.pivot_table(values='Total Paid Amount', index=['Remittance_Year', 'Payer_Name'], columns='Remittance_Month', fill_value=0)
            heatmap_pivot = heatmap_pivot.reindex(columns=month_order, fill_value=0)
            heatmap_fig = px.imshow(heatmap_pivot, text_auto=True, aspect="auto",
                                    title="Heatmap of Monthly Paid Amounts by Year and Insurance",
                                    labels=dict(x="Month", y="Year & Insurance", color="Paid Amount ($)"))
            st.plotly_chart(heatmap_fig)

            # Scatter Plot: Paid vs. Denied by Insurance
            scatter_denied = filtered_df.groupby('Payer_Name').agg(
                Total_Paid=('Total Paid Amount', 'sum'),
                Total_Denied=('Total Denied Amount', 'sum')
            ).reset_index()
            scatter_denied_fig = px.scatter(scatter_denied, x='Total_Denied', y='Total_Paid', color='Payer_Name',
                                            size='Total_Paid', title="Paid vs. Denied Amounts by Insurance",
                                            labels={'Total_Denied': 'Total Denied ($)', 'Total_Paid': 'Total Paid ($)'})
            st.plotly_chart(scatter_denied_fig)

            # Stacked Bar Chart: Multi-Metric Breakdown by Year
            stacked_data = filtered_df.groupby('Remittance_Year').agg(
                Total_Submitted=('Total Submitted Amount', 'sum'),
                Total_Paid=('Total Paid Amount', 'sum'),
                Total_Denied=('Total Denied Amount', 'sum'),
                Total_Pending=('Total Pending Amount', 'sum')
            ).reset_index()
            stacked_fig = px.bar(stacked_data, x='Remittance_Year', y=['Total_Submitted', 'Total_Paid', 'Total_Denied', 'Total_Pending'],
                                 title="Submitted, Paid, Denied, and Pending Amounts by Year",
                                 labels={'value': 'Amount ($)', 'variable': 'Metric'}, barmode='stack')
            st.plotly_chart(stacked_fig)

            # Faceted Histogram: Paid Amounts by Quarter
            facet_hist_fig = px.histogram(filtered_df, x='Total Paid Amount', facet_col='Quarter', nbins=30,
                                          title="Distribution of Paid Amounts by Quarter",
                                          labels={'Total Paid Amount': "Paid Amount ($)"})
            st.plotly_chart(facet_hist_fig)

        # Export to Excel (filtered data, multiple sheets)
        output_file = "Insurance_Claims_Report.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            grouped_paid.to_excel(writer, sheet_name="Paid Claims Per Month", index=False)
            summary_table.to_excel(writer, sheet_name="Summary", index=False)
            filtered_df.to_excel(writer, sheet_name="All Claims Raw (Filtered)", index=False)

        # Download button for the Excel file
        with open(output_file, "rb") as file:
            st.download_button("Download Insurance Claims Report (Filtered)", file, file_name="Insurance_Claims_Report.xlsx")
        # Cleanup
        os.remove(output_file)

    except Exception as e:
        st.error(f"Error processing file: {e}. Please check your data format and try again.")
