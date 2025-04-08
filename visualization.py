import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional

def create_gauge_chart(current_value: float, min_value: float, max_value: float, 
                     threshold: float, title: str, is_percent: bool = False) -> go.Figure:
    """
    Create a gauge chart for visualizing a metric against a threshold
    
    Args:
        current_value: The current value to display
        min_value: Minimum value on the gauge
        max_value: Maximum value on the gauge
        threshold: Threshold value for color coding
        title: Title for the gauge
        is_percent: Whether the value is a percentage
    
    Returns:
        Plotly figure object
    """
    # Set up colors based on threshold
    if current_value >= threshold:
        color = "green"
    elif current_value >= threshold * 0.7:
        color = "orange"
    else:
        color = "red"
    
    # Format the display value
    if is_percent:
        display_value = f"{current_value:.1f}%"
    else:
        display_value = f"{current_value:.1f}"
    
    # Create the gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_value,
        title={"text": title},
        number={"suffix": "%" if is_percent else ""},
        gauge={
            "axis": {"range": [min_value, max_value]},
            "bar": {"color": color},
            "steps": [
                {"range": [min_value, threshold * 0.7], "color": "rgba(255, 0, 0, 0.2)"},
                {"range": [threshold * 0.7, threshold], "color": "rgba(255, 165, 0, 0.3)"},
                {"range": [threshold, max_value], "color": "rgba(0, 128, 0, 0.2)"}
            ],
            "threshold": {
                "line": {"color": "black", "width": 2},
                "thickness": 0.75,
                "value": threshold
            }
        }
    ))
    
    # Set chart height
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=20))
    
    return fig

def create_trend_chart(data: List[Dict[str, Any]], x_key: str, y_key: str, 
                     title: str, color: str) -> go.Figure:
    """
    Create a line chart for visualizing trends over time
    
    Args:
        data: List of dictionaries containing the data
        x_key: Key for the x-axis values in the data dictionaries
        y_key: Key for the y-axis values in the data dictionaries
        title: Chart title
        color: Line color
    
    Returns:
        Plotly figure object
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Create line chart
    fig = px.line(
        df,
        x=x_key,
        y=y_key,
        title=title,
        markers=True
    )
    
    # Update line color
    fig.update_traces(line_color=color)
    
    # Update layout
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=30),
        hovermode="x unified"
    )
    
    return fig

def create_pie_chart(data: List[Dict[str, Any]], labels_key: str, values_key: str, 
                   title: str) -> go.Figure:
    """
    Create a pie chart for visualizing distributions
    
    Args:
        data: List of dictionaries containing the data
        labels_key: Key for the sector labels in the data dictionaries
        values_key: Key for the sector values in the data dictionaries
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Create pie chart
    fig = px.pie(
        df,
        names=labels_key,
        values=values_key,
        title=title
    )
    
    # Update layout
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=30)
    )
    
    # Update trace
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def create_bar_chart(data: List[Dict[str, Any]], x_key: str, y_key: str, 
                   title: str, color_key: Optional[str] = None) -> go.Figure:
    """
    Create a bar chart for visualizing categorical data
    
    Args:
        data: List of dictionaries containing the data
        x_key: Key for the x-axis values in the data dictionaries
        y_key: Key for the y-axis values in the data dictionaries
        title: Chart title
        color_key: Optional key for color coding the bars
    
    Returns:
        Plotly figure object
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Create bar chart
    if color_key and color_key in df.columns:
        fig = px.bar(
            df,
            x=x_key,
            y=y_key,
            title=title,
            color=color_key
        )
    else:
        fig = px.bar(
            df,
            x=x_key,
            y=y_key,
            title=title
        )
    
    # Update layout
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=30)
    )
    
    return fig

def create_comparison_chart(categories: List[str], budget_values: List[float], 
                          actual_values: List[float], title: str) -> go.Figure:
    """
    Create a grouped bar chart for budget vs. actual comparison
    
    Args:
        categories: List of category names
        budget_values: List of budget values
        actual_values: List of actual values
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    # Create figure
    fig = go.Figure()
    
    # Add budget bars
    fig.add_trace(go.Bar(
        x=categories,
        y=budget_values,
        name='Budget',
        marker_color='rgb(26, 118, 255)'
    ))
    
    # Add actual bars
    fig.add_trace(go.Bar(
        x=categories,
        y=actual_values,
        name='Actual',
        marker_color='rgb(55, 83, 109)'
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        barmode='group',
        xaxis_tickangle=-45,
        height=400,
        margin=dict(l=20, r=20, t=50, b=100)
    )
    
    return fig
