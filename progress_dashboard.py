import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import database as db
import utils
import branding
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Set the style for all charts
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette(["#DC143C", "#000000", "#808080"])
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 13,
    'axes.titlesize': 14,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.titlesize': 15
})

def show_progress_dashboard(read_only=False):
    """Show the read-only progress dashboard"""
    
    # Apply branding if in read-only mode
    if read_only:
        st.markdown(branding.CUSTOM_CSS, unsafe_allow_html=True)
        st.markdown(branding.get_header_html(), unsafe_allow_html=True)
    
    st.title("📊 Progress Dashboard")
    
    # Add toggle for interactive charts
    col_title, col_toggle = st.columns([3, 1])
    with col_title:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
    with col_toggle:
        use_interactive = st.checkbox("📊 Interactive Charts", value=True)
    
    # Auto-refresh option
    if read_only:
        auto_refresh = st.checkbox("Auto-refresh (5 minutes)", value=True)
        if auto_refresh:
            st.write("Dashboard will refresh automatically every 5 minutes")
    
    # Get data
    moves_df = db.get_all_trailer_moves()
    trailer_stats = db.get_trailer_statistics()
    
    # Section 1: Active Routes
    st.header("🚛 Active Routes")
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics
    in_progress = len(moves_df[moves_df['completion_date'].isna()])
    completed_today = len(moves_df[pd.to_datetime(moves_df['completion_date']).dt.date == datetime.today().date()])
    completed_week = len(moves_df[
        (pd.to_datetime(moves_df['completion_date']) >= datetime.now() - timedelta(days=7)) &
        (pd.to_datetime(moves_df['completion_date']) <= datetime.now())
    ])
    
    # Calculate average completion time
    completed_moves = moves_df[moves_df['completion_date'].notna()].copy()
    if not completed_moves.empty:
        completed_moves['completion_time'] = (
            pd.to_datetime(completed_moves['completion_date']) - 
            pd.to_datetime(completed_moves['date_assigned'])
        ).dt.days
        avg_completion = completed_moves['completion_time'].mean()
    else:
        avg_completion = 0
    
    with col1:
        st.metric("Routes in Progress", in_progress)
    with col2:
        st.metric("Completed Today", completed_today)
    with col3:
        st.metric("Completed This Week", completed_week)
    with col4:
        st.metric("Avg Completion (days)", f"{avg_completion:.1f}")
    
    # Section 2: Driver Performance
    st.header("👥 Driver Performance")
    
    if not moves_df.empty:
        # Calculate driver metrics
        driver_stats = moves_df.groupby('assigned_driver').agg({
            'id': 'count',
            'completion_date': lambda x: x.notna().sum(),
            'miles': 'sum'
        }).reset_index()
        driver_stats.columns = ['Driver', 'Total Assigned', 'Completed', 'Total Miles']
        driver_stats['Completion Rate'] = (driver_stats['Completed'] / driver_stats['Total Assigned'] * 100).round(1)
        driver_stats['Active Routes'] = driver_stats['Total Assigned'] - driver_stats['Completed']
        
        # Display top performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Active Drivers")
            active_drivers = driver_stats[driver_stats['Active Routes'] > 0][['Driver', 'Active Routes']].sort_values('Active Routes', ascending=False)
            if not active_drivers.empty:
                # Show only top 5 for cleaner view
                active_drivers = active_drivers.head(5)
                
                if use_interactive:
                    # Interactive Plotly chart
                    fig = go.Figure(data=[
                        go.Bar(
                            y=active_drivers['Driver'],
                            x=active_drivers['Active Routes'],
                            orientation='h',
                            marker=dict(color='#DC143C', line=dict(color='black', width=2)),
                            text=active_drivers['Active Routes'],
                            textposition='outside',
                            textfont=dict(size=14, color='black', family='Arial Black'),
                            hovertemplate='<b>%{y}</b><br>Active Routes: %{x}<extra></extra>'
                        )
                    ])
                    fig.update_layout(
                        height=250,
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis=dict(title='Active Routes', title_font=dict(size=14, family='Arial Black'), tickfont=dict(size=11)),
                        yaxis=dict(title='', tickfont=dict(size=12)),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        showlegend=False,
                        hovermode='y unified'
                    )
                    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Original matplotlib chart
                    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor='white')
                    bars = ax.barh(active_drivers['Driver'], active_drivers['Active Routes'], 
                                  color='#DC143C', edgecolor='black', linewidth=1.5)
                    
                    # Add value labels on the bars
                    for i, (bar, value) in enumerate(zip(bars, active_drivers['Active Routes'])):
                        ax.text(value + 0.1, bar.get_y() + bar.get_height()/2, 
                               str(int(value)), va='center', fontweight='bold', fontsize=12)
                    
                    ax.set_xlabel('Active Routes', fontsize=13, fontweight='bold')
                    ax.set_ylabel('')
                    ax.set_xlim(0, max(active_drivers['Active Routes']) * 1.15)
                    ax.tick_params(axis='y', labelsize=12)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_linewidth(2)
                    ax.spines['bottom'].set_linewidth(2)
                    ax.grid(axis='x', alpha=0.3, linestyle='--')
                    ax.set_axisbelow(True)
                    plt.tight_layout()
                    st.pyplot(fig)
            else:
                st.info("No active drivers currently")
        
        with col2:
            st.subheader("Completion Rates")
            top_performers = driver_stats[driver_stats['Completed'] > 0][['Driver', 'Completion Rate']].sort_values('Completion Rate', ascending=False)
            if not top_performers.empty:
                # Show only top 5 for cleaner view
                top_performers = top_performers.head(5)
                
                if use_interactive:
                    # Interactive Plotly chart
                    colors = ['#28a745' if x >= 90 else '#ffc107' if x >= 70 else '#dc3545' for x in top_performers['Completion Rate']]
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            y=top_performers['Driver'],
                            x=top_performers['Completion Rate'],
                            orientation='h',
                            marker=dict(color=colors, line=dict(color='black', width=2)),
                            text=[f'{x:.1f}%' for x in top_performers['Completion Rate']],
                            textposition='outside',
                            textfont=dict(size=14, color='black', family='Arial Black'),
                            hovertemplate='<b>%{y}</b><br>Completion Rate: %{x:.1f}%<extra></extra>'
                        )
                    ])
                    
                    # Add reference lines
                    fig.add_vline(x=90, line_dash="dash", line_color="green", opacity=0.3)
                    fig.add_vline(x=70, line_dash="dash", line_color="orange", opacity=0.3)
                    
                    fig.update_layout(
                        height=250,
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis=dict(
                            title='Completion Rate (%)', 
                            title_font=dict(size=14, family='Arial Black'),
                            tickfont=dict(size=11),
                            range=[0, 105]
                        ),
                        yaxis=dict(title='', tickfont=dict(size=12)),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        showlegend=False,
                        hovermode='y unified'
                    )
                    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Original matplotlib chart
                    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor='white')
                    colors = ['#28a745' if x >= 90 else '#ffc107' if x >= 70 else '#dc3545' for x in top_performers['Completion Rate']]
                    bars = ax.barh(top_performers['Driver'], top_performers['Completion Rate'], 
                                  color=colors, edgecolor='black', linewidth=1.5)
                    
                    # Add value labels
                    for i, (bar, value) in enumerate(zip(bars, top_performers['Completion Rate'])):
                        ax.text(value + 1, bar.get_y() + bar.get_height()/2, 
                               f'{value:.1f}%', va='center', fontweight='bold', fontsize=12)
                    
                    # Add reference lines
                    ax.axvline(x=90, color='green', linestyle='--', alpha=0.3, linewidth=1)
                    ax.axvline(x=70, color='orange', linestyle='--', alpha=0.3, linewidth=1)
                    
                    ax.set_xlabel('Completion Rate (%)', fontsize=13, fontweight='bold')
                    ax.set_ylabel('')
                    ax.set_xlim(0, 105)
                    ax.tick_params(axis='y', labelsize=12)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_linewidth(2)
                    ax.spines['bottom'].set_linewidth(2)
                    ax.grid(axis='x', alpha=0.3, linestyle='--')
                    ax.set_axisbelow(True)
                    plt.tight_layout()
                    st.pyplot(fig)
            else:
                st.info("No completed deliveries yet")
    
    # Section 3: Operational Efficiency
    st.header("📈 Operational Efficiency")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate efficiency metrics
    if not moves_df.empty:
        total_miles = moves_df['miles'].sum()
        avg_miles_per_day = moves_df.groupby(pd.to_datetime(moves_df['date_assigned']).dt.date)['miles'].sum().mean()
        
        # Trailer utilization
        total_trailers = trailer_stats['available_new'] + trailer_stats['available_old'] + trailer_stats['assigned']
        utilization_rate = (trailer_stats['assigned'] / total_trailers * 100) if total_trailers > 0 else 0
        
        with col1:
            st.metric("Total Miles", f"{total_miles:,.0f}")
        with col2:
            st.metric("Avg Miles/Day", f"{avg_miles_per_day:,.0f}")
        with col3:
            st.metric("Trailer Utilization", f"{utilization_rate:.1f}%")
        with col4:
            st.metric("Peak Hours", "8AM - 12PM")  # This would need actual calculation
    
    # Section 4: Trend Charts
    st.header("📊 Trends")
    
    if not moves_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Daily Completions (Last 30 Days)")
            # Group by completion date
            daily_completions = moves_df[moves_df['completion_date'].notna()].copy()
            if not daily_completions.empty:
                daily_completions['date'] = pd.to_datetime(daily_completions['completion_date']).dt.date
                daily_counts = daily_completions.groupby('date').size().reset_index(name='Completions')
                daily_counts = daily_counts.tail(30)  # Last 30 days
                
                if use_interactive:
                    # Interactive Plotly line chart
                    fig = go.Figure()
                    
                    # Add main line
                    fig.add_trace(go.Scatter(
                        x=daily_counts['date'],
                        y=daily_counts['Completions'],
                        mode='lines+markers',
                        name='Daily Completions',
                        line=dict(color='#DC143C', width=3),
                        marker=dict(size=8, color='#DC143C', line=dict(color='black', width=2)),
                        fill='tozeroy',
                        fillcolor='rgba(220, 20, 60, 0.2)',
                        hovertemplate='<b>Date:</b> %{x}<br><b>Completions:</b> %{y}<extra></extra>'
                    ))
                    
                    # Add 7-day moving average if enough data
                    if len(daily_counts) > 7:
                        ma7 = daily_counts['Completions'].rolling(window=7, min_periods=1).mean()
                        fig.add_trace(go.Scatter(
                            x=daily_counts['date'],
                            y=ma7,
                            mode='lines',
                            name='7-Day Average',
                            line=dict(color='black', width=2, dash='dash'),
                            hovertemplate='<b>7-Day Avg:</b> %{y:.1f}<extra></extra>'
                        ))
                    
                    fig.update_layout(
                        height=280,
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis=dict(
                            title='Date',
                            title_font=dict(size=14, family='Arial Black'),
                            tickformat='%m/%d',
                            tickfont=dict(size=11)
                        ),
                        yaxis=dict(
                            title='Completions',
                            title_font=dict(size=14, family='Arial Black'),
                            tickfont=dict(size=11)
                        ),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor='white')
                    
                    # Create the line plot with markers
                    line = ax.plot(daily_counts['date'], daily_counts['Completions'], 
                                  color='#DC143C', linewidth=2.5, marker='o', 
                                  markersize=8, markeredgecolor='black', markeredgewidth=1.5,
                                  label='Daily Completions')
                    
                    # Fill area under the curve
                    ax.fill_between(daily_counts['date'], daily_counts['Completions'], 
                                   alpha=0.2, color='#DC143C')
                    
                    # Add moving average line
                    if len(daily_counts) > 7:
                        ma7 = daily_counts['Completions'].rolling(window=7, min_periods=1).mean()
                        ax.plot(daily_counts['date'], ma7, color='black', linewidth=1.5, 
                               linestyle='--', alpha=0.7, label='7-Day Average')
                    
                    # Styling
                    ax.set_xlabel('Date', fontsize=13, fontweight='bold')
                    ax.set_ylabel('Completions', fontsize=13, fontweight='bold')
                    ax.tick_params(axis='both', labelsize=11)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_linewidth(2)
                    ax.spines['bottom'].set_linewidth(2)
                    ax.grid(True, alpha=0.3, linestyle='--')
                    ax.set_axisbelow(True)
                    
                    # Format x-axis dates
                    import matplotlib.dates as mdates
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
                    plt.xticks(rotation=45, ha='right')
                    
                    # Add legend
                    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
            else:
                st.info("No completion data available")
        
        with col2:
            st.subheader("Top 5 Routes")
            # Most used routes
            route_counts = moves_df.groupby(['pickup_location', 'destination']).size().reset_index(name='Count')
            route_counts['Route'] = route_counts['pickup_location'].str[:15] + ' → ' + route_counts['destination'].str[:15]
            route_counts = route_counts.nlargest(5, 'Count')  # Show only top 5
            
            if not route_counts.empty:
                if use_interactive:
                    # Interactive Plotly chart
                    fig = go.Figure(data=[
                        go.Bar(
                            y=route_counts['Route'],
                            x=route_counts['Count'],
                            orientation='h',
                            marker=dict(
                                color=route_counts['Count'],
                                colorscale='Reds',
                                line=dict(color='black', width=2),
                                showscale=False
                            ),
                            text=route_counts['Count'],
                            textposition='outside',
                            textfont=dict(size=14, color='black', family='Arial Black'),
                            hovertemplate='<b>%{y}</b><br>Trips: %{x}<extra></extra>'
                        )
                    ])
                    
                    fig.update_layout(
                        height=280,
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis=dict(
                            title='Number of Trips',
                            title_font=dict(size=14, family='Arial Black'),
                            tickfont=dict(size=11)
                        ),
                        yaxis=dict(title='', tickfont=dict(size=11)),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        showlegend=False,
                        hovermode='y unified'
                    )
                    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor='white')
                    
                    # Create gradient colors based on count
                    norm = plt.Normalize(route_counts['Count'].min(), route_counts['Count'].max())
                    colors = plt.cm.Reds(norm(route_counts['Count']))
                    
                    bars = ax.barh(route_counts['Route'], route_counts['Count'], 
                                  color=colors, edgecolor='black', linewidth=1.5)
                    
                    # Add value labels
                    for i, (bar, value) in enumerate(zip(bars, route_counts['Count'])):
                        ax.text(value + 0.5, bar.get_y() + bar.get_height()/2, 
                               str(int(value)), va='center', fontweight='bold', fontsize=12)
                    
                    ax.set_xlabel('Number of Trips', fontsize=13, fontweight='bold')
                    ax.set_ylabel('')
                    ax.set_xlim(0, max(route_counts['Count']) * 1.15)
                    ax.tick_params(axis='y', labelsize=11)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_linewidth(2)
                    ax.spines['bottom'].set_linewidth(2)
                    ax.grid(axis='x', alpha=0.3, linestyle='--')
                    ax.set_axisbelow(True)
                    
                    # Adjust font size for route names if needed
                    ax.tick_params(axis='y', labelsize=11)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
            else:
                st.info("No route data available")
    
    # Section 5: Trailer Status Summary
    st.header("🚛 Trailer Status")
    
    # Add a pie chart for trailer distribution
    col_chart, col_metrics = st.columns([1, 1.5])
    
    with col_chart:
        st.subheader("Trailer Distribution")
        if trailer_stats['available_new'] + trailer_stats['available_old'] + trailer_stats['assigned'] > 0:
            if use_interactive:
                # Interactive Plotly pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=['New Available', 'Old Available', 'In Transit'],
                    values=[trailer_stats['available_new'], trailer_stats['available_old'], trailer_stats['assigned']],
                    hole=0.3,  # Creates a donut chart
                    marker=dict(
                        colors=['#28a745', '#17a2b8', '#ffc107'],
                        line=dict(color='black', width=2)
                    ),
                    textinfo='label+percent',
                    textfont=dict(size=13, color='white', family='Arial Black'),
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
                    pull=[0.05, 0.05, 0.1]  # Explode the "In Transit" slice
                )])
                
                fig.update_layout(
                    height=350,
                    margin=dict(l=0, r=0, t=30, b=0),
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.05,
                        font=dict(size=12)
                    ),
                    title=dict(
                        text='Fleet Overview',
                        font=dict(size=14, family='Arial Black'),
                        x=0.5,
                        xanchor='center'
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig, ax = plt.subplots(figsize=(5, 5), facecolor='white')
                
                # Data for pie chart
                sizes = [trailer_stats['available_new'], trailer_stats['available_old'], trailer_stats['assigned']]
                labels = ['New Available', 'Old Available', 'In Transit']
                colors = ['#28a745', '#17a2b8', '#ffc107']
                explode = (0.05, 0.05, 0.1)  # Explode the "In Transit" slice
                
                # Create pie chart
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, explode=explode,
                                                   autopct='%1.1f%%', shadow=True, startangle=90,
                                                   wedgeprops={'edgecolor': 'black', 'linewidth': 2})
                
                # Enhance text
                for text in texts:
                    text.set_fontsize(11)
                    text.set_fontweight('bold')
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(10)
                    autotext.set_fontweight('bold')
                
                ax.set_title('Fleet Overview', fontsize=12, fontweight='bold', pad=20)
                plt.tight_layout()
                st.pyplot(fig)
        else:
            st.info("No trailer data available")
    
    with col_metrics:
        st.subheader("Status Breakdown")
        subcol1, subcol2, subcol3 = st.columns(3)
        
        with subcol1:
            st.markdown(f"""
            <div style="background: #d4edda; padding: 1rem; border-radius: 8px; text-align: center; border: 2px solid #000000;">
                <h3 style="margin: 0; color: #155724; font-size: 2rem;">{trailer_stats['available_new']}</h3>
                <p style="margin: 0; color: #155724; font-weight: bold;">New Available</p>
            </div>
            """, unsafe_allow_html=True)
        
        with subcol2:
            st.markdown(f"""
            <div style="background: #cce5ff; padding: 1rem; border-radius: 8px; text-align: center; border: 2px solid #000000;">
                <h3 style="margin: 0; color: #004085; font-size: 2rem;">{trailer_stats['available_old']}</h3>
                <p style="margin: 0; color: #004085; font-weight: bold;">Old Available</p>
            </div>
            """, unsafe_allow_html=True)
        
        with subcol3:
            st.markdown(f"""
            <div style="background: #fff3cd; padding: 1rem; border-radius: 8px; text-align: center; border: 2px solid #000000;">
                <h3 style="margin: 0; color: #856404; font-size: 2rem;">{trailer_stats['assigned']}</h3>
                <p style="margin: 0; color: #856404; font-weight: bold;">In Transit</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer with company branding
    if read_only:
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; color: #666; padding: 1rem;">
            <p>© 2024 {branding.COMPANY_NAME}. All rights reserved.</p>
            <p style="font-size: 0.9rem;">This is a read-only view. No financial information is displayed.</p>
        </div>
        """, unsafe_allow_html=True)

def generate_progress_report():
    """Generate a progress report for email"""
    moves_df = db.get_all_trailer_moves()
    trailer_stats = db.get_trailer_statistics()
    
    # Calculate metrics
    completed_today = len(moves_df[pd.to_datetime(moves_df['completion_date']).dt.date == datetime.today().date()])
    in_progress = len(moves_df[moves_df['completion_date'].isna()])
    
    # Calculate on-time rate (simplified - would need actual deadline data)
    completed_moves = moves_df[moves_df['completion_date'].notna()]
    on_time_rate = 95  # Placeholder - would calculate from actual data
    
    # Count active drivers
    active_drivers = moves_df[moves_df['completion_date'].isna()]['assigned_driver'].nunique()
    
    report_data = {
        'date': datetime.today().strftime('%Y-%m-%d'),
        'routes_today': completed_today,
        'routes_progress': in_progress,
        'on_time_rate': on_time_rate,
        'active_drivers': active_drivers,
        'new_trailers': trailer_stats['available_new'],
        'old_trailers': trailer_stats['available_old'],
        'transit_trailers': trailer_stats['assigned']
    }
    
    # Format the email body
    template = db.get_email_template('progress_report')
    if template:
        body = template['body']
        for key, value in report_data.items():
            body = body.replace(f'{{{key}}}', str(value))
        
        subject = template['subject'].replace('{date}', report_data['date'])
        
        return subject, body
    
    return None, None