# ... [existing code above] ...

def build_seasonality_chart(agg_df, brand, value_col='Spend'):
    agg_df['Month'] = agg_df['Date'].dt.month
    fig = px.box(
        agg_df, 
        x='Month', 
        y=value_col, 
        color='Media Partner',
        title=f"{brand}: Seasonality of {value_col} by Month"
    )
    return fig

def build_partner_mix_pie_chart(agg_df, brand, value_col='Spend', time_period='Monthly'):
    fig = px.pie(
        agg_df,
        names='Media Partner',
        values=value_col,
        title=f"{brand}: Media Mix by Partner ({time_period})",
        hole=0.3
    )
    return fig

# ... [existing code above] ...
brand_data = {...}  # or brand_data = some_function()
for brand, data in brand_data.items():
    spend_df = data['spend']
    # Guess columns
    date_col = next((col for col in spend_df.columns if 'date' in col.lower()), spend_df.columns[0])
    partner_col = next((col for col in spend_df.columns if 'partner' in col.lower()), spend_df.columns[1])
    value_col = next((col for col in spend_df.columns if 'spend' in col.lower()), spend_df.columns[2])
    spend_df.rename(columns={date_col: 'Date', partner_col: 'Media Partner', value_col: 'Spend'}, inplace=True)
    # Aggregate for selected period
    agg = aggregate_data(spend_df, 'Date', 'Spend', group_cols=['Media Partner'], freq=freq)
    agg['Brand'] = brand
    all_brands_agg_list.append(agg)
    # Partner mix bar chart
    if st.checkbox(f"Show {brand}: Partner Spend Mix Chart"):
        fig_mix = build_partner_mix_chart(agg, brand, value_col='Spend', time_period=time_period_label)
        st.plotly_chart(fig_mix, use_container_width=True)
        selected_charts[f"{brand} Partner Mix"] = fig_mix
    # Partner mix pie chart
    if st.checkbox(f"Show {brand}: Partner Media Mix Pie Chart"):
        fig_pie = build_partner_mix_pie_chart(agg, brand, value_col='Spend', time_period=time_period_label)
        st.plotly_chart(fig_pie, use_container_width=True)
        selected_charts[f"{brand} Partner Mix Pie"] = fig_pie
    # Trend chart
    if st.checkbox(f"Show {brand}: Spend Trend Chart"):
        agg_trend = aggregate_data(spend_df, 'Date', 'Spend', group_cols=['Media Partner'], freq=freq)
        agg_trend.rename(columns={f'Date': 'Date'}, inplace=True)
        fig_trend = build_trend_chart(agg_trend, brand, value_col='Spend', time_period=time_period_label)
        st.plotly_chart(fig_trend, use_container_width=True)
        selected_charts[f"{brand} Spend Trend"] = fig_trend
    # ... [rest of code] ...
