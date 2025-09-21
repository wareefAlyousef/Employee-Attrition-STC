#--------------------------------------------------------------
# Employee Attrition Dashboard using Dash and Plotly
#--------------------------------------------------------------


#--------------------------------------------------------------
# Import necessary libraries
#--------------------------------------------------------------
import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime
import plotly.figure_factory as ff

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Employee Attrition Dashboard"


#--------------------------------------------------------------
# styling CSS
#--------------------------------------------------------------
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }
            .navbar {
                background: linear-gradient(135deg, #4F008C 0%, #7B3FE4 100%);
                padding: 15px 30px;
                color: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .navbar-brand {
                font-size: 24px;
                font-weight: bold;
                margin-right: 30px;
            }
            .nav-link {
                color: white !important;
                margin: 0 15px;
                padding: 10px 15px;
                border-radius: 5px;
                transition: background-color 0.3s;
            }
            .nav-link:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            .nav-link.active {
                background-color: rgba(255, 255, 255, 0.2);
                font-weight: bold;
            }
            .card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            .filter-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 20px;
                margin-bottom: 30px;
            }
            .btn-primary {
                background: linear-gradient(135deg, #4F008C 0%, #7B3FE4 100%);
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
                transition: all 0.3s;
            }
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(79, 0, 140, 0.3);
            }
            .btn-success {
                background: linear-gradient(135deg, #4F008C 0%, #7B3FE4 100%);
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
                transition: all 0.3s;
            }
            .btn-success:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(79, 0, 140, 0.3);
            }
            .form-control {
                border-radius: 5px;
                border: 1px solid #ddd;
                padding: 10px;
                margin-bottom: 15px;
                width: 95%;
            }
            .dropdown {
                margin-bottom: 15px;
            }
            .chart-container {
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 15px;
                margin-bottom: 20px;
            }
            .stats-card {
                background: linear-gradient(135deg, #4F008C 0%, #7B3FE4 100%);
                color: white;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                margin-bottom: 20px;
            }
            .stats-number {
                font-size: 32px;
                font-weight: bold;
                margin: 10px 0;
            }
            .stats-label {
                font-size: 14px;
                opacity: 0.8;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

#--------------------------------------------------------------
# Database connection and data loading
#--------------------------------------------------------------
# Connect to database
def get_db_connection():
    try:
        conn = sqlite3.connect('db/employee_database.db')
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Load data from database
def load_data_from_db():
    conn = get_db_connection()
    if conn:
        try:
            # query join tables
            query = """
            SELECT 
                e.*,
                d.DepartmentName,
                j.JobRole,
                j.JobLevel,
                ef.FieldName as EducationField
            FROM Employees e
            LEFT JOIN Departments d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN Jobs j ON e.JobID = j.JobID
            LEFT JOIN EducationFields ef ON e.EducationFieldID = ef.EducationFieldID
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            print("Successfully loaded data from database")
            print(f"Data shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            return df
        except sqlite3.Error as e:
            print(f"Error reading from database: {e}")
            conn.close()
            return pd.DataFrame()
    return pd.DataFrame()

# load data
df = load_data_from_db()

# calculat some statistic for the dashboard
if not df.empty:
    total_employees = len(df)
    attrition_rate = (df['Attrition'] == 'Yes').mean() * 100
    avg_income = df['MonthlyIncome'].mean()
    avg_satisfaction = df[['JobSatisfaction', 'EnvironmentSatisfaction']].mean().mean()
else:
    total_employees = 0
    attrition_rate = 0
    avg_income = 0
    avg_satisfaction = 0

# --------------------------------------------------------------
# App Layout and Callbacks
#--------------------------------------------------------------

# app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # navigation Bar
    html.Div([
        html.Div([
            html.Span('Employee Attrition Dashboard', className='navbar-brand'),
            dcc.Link('Overview', href='/', className='nav-link'),
            dcc.Link('Employee Management', href='/employee-management', className='nav-link'),
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], className='navbar'),
    
    # page content
    html.Div(id='page-content', style={'padding': '30px'})
])

# page layout
overview_layout = html.Div([
    html.H2('Statistical Overview of Employee Attrition', style={'marginBottom': '30px'}),
    # cards
    html.Div([
        html.Div([
            html.Div([
                html.Div(f"{total_employees:,}", className='stats-number'),
                html.Div('Total Employees', className='stats-label')
            ], className='stats-card'),
        ], style={'width': '23.5%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Div([
                html.Div(f"{attrition_rate:.1f}%", className='stats-number'),
                html.Div('Attrition Rate', className='stats-label')
            ], className='stats-card'),
        ], style={'width': '23.5%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Div([
                html.Div(f"${avg_income:,.0f}", className='stats-number'),
                html.Div('Avg. Monthly Income', className='stats-label')
            ], className='stats-card'),
        ], style={'width': '23.5%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Div([
                html.Div(f"{avg_satisfaction:.1f}/5", className='stats-number'),
                html.Div('Avg. Satisfaction', className='stats-label')
            ], className='stats-card'),
        ], style={'width': '23.5%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'marginBottom': '30px'}),

    # Visualizations overall data (before filter)
    html.Div([
        html.H3('Overall Company Trends', style={'marginBottom': '20px', 'marginTop': '30px'}),
        html.Div([
            html.Div([
                html.H4('Job Role Attrition Rate', className='chart-title'),
                html.Div([
                    html.P("This chart shows the attrition rate by job role for the overall company." \
                " It helps identify which job roles have higher attrition rates.", className='chart-description'),
                    dcc.Graph(id='overall-jobrole-chart'),
                    html.P("Sales Representative Attrition Rate is 40 %, making it the highest among all job roles. flowing it Laboratory Technician with 24% and Human Resources with 23%.", className='chart-description'),
                ], className='chart-container'),
            ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%', 'verticalAlign': 'top'}),
            
            html.Div([
                html.H4('Attrition Income Distribution', className='chart-title'),
                html.Div([
                    html.P("This chart shows the income distribution by attrition status for the overall company." \
                " It helps identify whether having higher income levels affects attrition rates.", className='chart-description'),
                    dcc.Graph(id='overall-income-chart'),
                    html.P("This graph outlines lower income levels slightly impact attrition rates.", className='chart-description'),
                    html.Br(),
                ], className='chart-container'),
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ]),
    ]),
    
    # filter
    html.Div([
        html.H3('Filters', style={'marginBottom': '20px'}),
        html.Div([
            html.Div([
                html.Label("Select Department:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='dept-filter',
                    options=[{'label': dept, 'value': dept} for dept in df['DepartmentName'].unique()] if 'DepartmentName' in df.columns else [],
                    value=df['DepartmentName'].unique()[0] if 'DepartmentName' in df.columns and len(df['DepartmentName'].unique()) > 0 else '',
                    className='dropdown'
                ),
            ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'})
        ]),
    ], className='filter-card'),


    # Visualizations
    html.Div([
        # first row 
        html.Div([
            html.H4('Job Role Attrition Rate', className='chart-title'),
            html.Div([
                html.P("This chart shows the attrition rate by job role for the selected department. It helps identify which job roles have higher attrition rates, and the order of attrition by job role.", className='chart-description'),
                dcc.Graph(id='jobrole-chart'),
                html.Br(),
                html.Br(),
                html.Br(),
            ], className='chart-container'),
        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%', 'verticalAlign': 'top'}),
        
        html.Div([
            html.H4('Overtime Attrition Rate', className='chart-title'),
            html.Div([
                html.P("This chart shows the attrition rate by overtime status for the selected department. It helps identify whether employees who work overtime have higher attrition rates.", className='chart-description'),
                dcc.Graph(id='overtime-chart'),
                html.P("This graph outlines that employees who work overtime tend to have higher attrition rates across all departments.", className='chart-description'),
            ], className='chart-container'),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ]),
    
    # 2 row 
    html.Div([
        html.Div([
            html.H4('Marital Status Attrition Rate', className='chart-title'),
            html.Div([
                html.P("This chart shows the attrition rate by marital status for the selected department. It helps identify whether marital status affects attrition rates.", className='chart-description'),
                dcc.Graph(id='maritalstatus-chart'),
                html.P("This graph outlines that single employees tend to have higher attrition rates across all departments, except the HR department, where divorced employees have a higher rate.", className='chart-description'),
            ], className='chart-container'),
        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%', 'verticalAlign': 'top'}),
        
        html.Div([
            html.H4('Business Travel Attrition Rate', className='chart-title'),
            html.Div([
                html.P("This chart shows the attrition rate by business travel frequency for the selected department. It helps identify whether frequent business travel affects attrition rates.", className='chart-description'),
                dcc.Graph(id='businesstravel-chart'),
                html.P("This graph outlines that employees who travel frequently for business tend to have higher attrition rates across all departments.", className='chart-description'),
            ], className='chart-container'),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ]),
    
    # 3 row 
    html.Div([
        html.Div([
            html.H4('Income Distribution by Attrition Status', className='chart-title'),
            html.Div([
                html.Br(),
                html.Br(),
                html.P("This chart shows the income distribution by attrition status for the selected department. It helps identify whether having higher income levels affects attrition rates.", className='chart-description'),
                html.Br(),
                html.Br(),
                dcc.Graph(id='income-chart'),
                html.Br(),
                html.Br(),
                html.P("This graph outlines that employees across all departments with lower monthly income tend to leave more frequently. But the correlation with attrition rates is not straightforward.", className='chart-description'),
                html.Br(),
                html.Br(),
                html.Br(),
            ], className='chart-container'),
        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%', 'verticalAlign': 'top'}),
        
        html.Div([
            html.H4('Correlation Heatmap of Key Features', className='chart-title'),
            html.Div([
                html.P("This heatmap shows the correlation between key numerical features and attrition. It helps identify which factors are most strongly associated with employees leaving the company.", className='chart-description'),
                dcc.Graph(id='correlation-heatmap'),
                html.P("", className='chart-description'),
                html.P("Job level, Total Working Years, and Age have strong positive correlations among each other, indicating that employees with higher job levels tend to have more years of experience and be older. And all three have a slightly negative correlation with attrition, meaning that as these factors increase, the likelihood of attrition decreases.", className='chart-description'),
            ], className='chart-container'),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ]),
])

# Employee Management page
employee_management_layout = html.Div([
    html.H2('Employee Management', style={'marginBottom': '30px'}),
    
    # add employee 
    html.Div([
        html.H3('Add New Employee', style={'marginBottom': '20px'}),
        html.Div([
            html.Div([
                html.Label("Department", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='new-dept',
                    options=[{'label': dept, 'value': dept} for dept in df['DepartmentName'].unique()] if 'DepartmentName' in df.columns else [],
                    className='form-control'
                ),
                
                html.Label("Job Role", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Input(id='new-jobrole', type='text', placeholder='Enter job role', className='form-control'),
                
                html.Label("Monthly Income", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Input(id='new-income', type='number', placeholder='Enter monthly income', className='form-control'),
                
                html.Label("OverTime", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='new-overtime',
                    options=[{'label': 'Yes', 'value': 'Yes'}, {'label': 'No', 'value': 'No'}],
                    className='form-control'
                ),
                
                html.Button('Add Employee', id='add-employee-btn', n_clicks=0, className='btn-success', style={'marginTop': '10px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '20px'}),
            
            # update employee
            html.Div([
                html.H3('Update Employee Income', style={'marginBottom': '20px'}),
                html.Label("Employee ID", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Input(id='employee-id', type='number', placeholder='Enter employee ID', className='form-control'),
                
                html.Label("New Monthly Income", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Input(id='update-income', type='number', placeholder='Enter new monthly income', className='form-control'),
                
                html.Button('Update Income', id='update-income-btn', n_clicks=0, className='btn-primary', style={'marginTop': '10px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ]),
        
        html.Div(id='form-output', style={'marginTop': '20px', 'padding': '15px', 'borderRadius': '5px', 'backgroundColor': '#f8f9fa'})
    ], className='card'),
    
    # Employee List
    html.Div([
        html.H3('Employee List', style={'marginBottom': '20px'}),
        html.Div(id='employee-table-container')
    ], className='card', style={'marginTop': '30px'}),
])

# switch between pages
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/employee-management':
        return employee_management_layout
    else:
        return overview_layout

# callbacks for visualization
@app.callback(
    [Output('jobrole-chart', 'figure'),
     Output('overtime-chart', 'figure'),
     Output('maritalstatus-chart', 'figure'),
     Output('businesstravel-chart', 'figure'),
     Output('income-chart', 'figure'),
     Output('correlation-heatmap', 'figure'),
     Output('overall-jobrole-chart', 'figure'),
     Output('overall-income-chart', 'figure')],
    [Input('dept-filter', 'value')]
)

#--------------------------------------------------------------
# function to update charts based on filter
#--------------------------------------------------------------
def update_charts(selected_dept):
    # filter department
    if selected_dept and 'DepartmentName' in df.columns:
        filtered_df = df[df['DepartmentName'] == selected_dept]
    else:
        filtered_df = df
    
    # job role
    if 'JobRole' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        jobrole_attrition = filtered_df.groupby('JobRole')['Attrition'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        jobrole_attrition.columns = ['JobRole', 'AttritionRate']
        jobrole_fig = px.bar(jobrole_attrition, x='JobRole', y='AttritionRate', 
                             title='Attrition Rate by Job Role',
                             labels={'AttritionRate': 'Attrition Rate (%)', 'JobRole': 'Job Role'},
                             color='AttritionRate',
                             color_continuous_scale=['#E6D7F2', '#C9AFE5', '#AC87D8', '#8F5FCB', '#7237BE', '#550FA1', '#4F008C'])
        jobrole_fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    else:
        jobrole_fig = go.Figure()
        jobrole_fig.add_annotation(text="JobRole or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # overtime 
    if 'OverTime' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        overtime_attrition = filtered_df.groupby('OverTime')['Attrition'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        overtime_attrition.columns = ['OverTime', 'AttritionRate']
        overtime_fig = px.bar(overtime_attrition, x='OverTime', y='AttritionRate', 
                              title='Attrition Rate by Overtime',
                              labels={'AttritionRate': 'Attrition Rate (%)', 'OverTime': 'Overtime'},
                              color='OverTime',
                              color_discrete_map={'Yes': '#FF375E', 'No': '#4F008C'})
        overtime_fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    else:
        overtime_fig = go.Figure()
        overtime_fig.add_annotation(text="OverTime or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # mearital states 
    if 'MaritalStatus' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        marital_attrition = filtered_df.groupby('MaritalStatus')['Attrition'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        marital_attrition.columns = ['MaritalStatus', 'AttritionRate']
        marital_fig = px.bar(marital_attrition, x='MaritalStatus', y='AttritionRate', 
                             title='Attrition Rate by Marital Status',
                             labels={'AttritionRate': 'Attrition Rate (%)', 'MaritalStatus': 'Marital Status'},
                             color='MaritalStatus',
                             color_discrete_map={'Single': '#FF375E', 'Married': '#4F008C', 'Divorced': '#AC87D8'})
        marital_fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    else:
        marital_fig = go.Figure()
        marital_fig.add_annotation(text="MaritalStatus or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # business travel 
    if 'BusinessTravel' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        travel_attrition = filtered_df.groupby('BusinessTravel')['Attrition'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        travel_attrition.columns = ['BusinessTravel', 'AttritionRate']
        travel_fig = px.bar(travel_attrition, x='BusinessTravel', y='AttritionRate', 
                            title='Attrition Rate by Business Travel',
                            labels={'AttritionRate': 'Attrition Rate (%)', 'BusinessTravel': 'Business Travel'},
                            color='BusinessTravel',
                            color_discrete_map={'Travel_Frequently': '#FF375E', 'Travel_Rarely': '#4F008C', 'Non-Travel': '#AC87D8'})
        travel_fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    else:
        travel_fig = go.Figure()
        travel_fig.add_annotation(text="BusinessTravel or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # income distributionn 
    if 'MonthlyIncome' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        income_fig = px.violin(filtered_df, x='Attrition', y='MonthlyIncome', 
                               title='Income Distribution by Attrition Status',
                               color='Attrition',
                               color_discrete_map={'Yes': '#FF375E', 'No': '#4F008C'})
        income_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    else:
        income_fig = go.Figure()
        income_fig.add_annotation(text="MonthlyIncome or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # Corr heatmap 
    numeric_columns = ['Age', 'MonthlyIncome', 'TotalWorkingYears', 'JobLevel', 
                    'JobSatisfaction', 'EnvironmentSatisfaction', 'DailyRate']

    if all(col in df.columns for col in numeric_columns + ['Attrition']):
        df_numeric = df[numeric_columns + ['Attrition']].copy()
        df_numeric['Attrition'] = df_numeric['Attrition'].map({'Yes': 1, 'No': 0})
        corr_matrix = df_numeric.corr()
        
        heatmap_fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            colorscale=['#E6D7F2', '#C9AFE5', '#AC87D8', '#8F5FCB', '#7237BE', '#550FA1', '#4F008C'],
            zmin=-1,
            zmax=1,
            hoverongaps=False,
        ))
        
        heatmap_fig.update_layout(
            title='Correlation Matrix of Key Features',
            xaxis_title="Features",
            yaxis_title="Features",
            width=600,
            height=600,
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)'
        )
        annotations = []
        for i, row in enumerate(corr_matrix.values):
            for j, value in enumerate(row):
                annotations.append(
                    dict(
                        x=corr_matrix.columns[j],
                        y=corr_matrix.index[i],
                        text=str(round(value, 2)),
                        showarrow=False,
                        font=dict(color='white' if abs(value) > 0.5 else 'black')
                    )
                )
        heatmap_fig.update_layout(annotations=annotations)
        
    else:
        heatmap_fig = go.Figure()
        heatmap_fig.add_annotation(text="Required data not available for correlation matrix", x=0.5, y=0.5, showarrow=False)
    
    #  job role  (before filter)
    if 'JobRole' in df.columns and 'Attrition' in df.columns:
        overall_jobrole_attrition = df.groupby('JobRole')['Attrition'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        overall_jobrole_attrition.columns = ['JobRole', 'AttritionRate']
        overall_jobrole_fig = px.bar(overall_jobrole_attrition, x='JobRole', y='AttritionRate', 
                                     title='Overall Attrition Rate by Job Role (Company-wide)',
                                     labels={'AttritionRate': 'Attrition Rate (%)', 'JobRole': 'Job Role'},
                                     color='AttritionRate',
                                     color_continuous_scale=['#FFD1D9', '#FFA3B0', '#FF7587', '#FF375E', '#E62E4D', '#CC263D', '#B31D2C'])
        overall_jobrole_fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    else:
        overall_jobrole_fig = go.Figure()
        overall_jobrole_fig.add_annotation(text="JobRole or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # income distribution (before filter)
    if 'MonthlyIncome' in df.columns and 'Attrition' in df.columns:
        overall_income_fig = px.violin(df, x='Attrition', y='MonthlyIncome', 
                                       title='Overall Income Distribution by Attrition Status (Company-wide)',
                                       color='Attrition',
                                       color_discrete_map={'Yes': '#FF375E', 'No': '#4F008C'})
        overall_income_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    else:
        overall_income_fig = go.Figure()
        overall_income_fig.add_annotation(text="MonthlyIncome or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    return (jobrole_fig, overtime_fig, marital_fig, travel_fig, income_fig, 
            heatmap_fig, overall_jobrole_fig, overall_income_fig)

# callback submit
@app.callback(
    [Output('form-output', 'children'),
     Output('employee-table-container', 'children')],
    [Input('add-employee-btn', 'n_clicks'),
     Input('update-income-btn', 'n_clicks')],
    [State('new-dept', 'value'),
     State('new-jobrole', 'value'),
     State('new-income', 'value'),
     State('new-overtime', 'value'),
     State('employee-id', 'value'),
     State('update-income', 'value')]
)

#--------------------------------------------------------------
# function to handle form submissions
#--------------------------------------------------------------
def handle_form_submissions(add_clicks, update_clicks, new_dept, new_jobrole, new_income, new_overtime, emp_id, update_income):
    ctx = callback_context
    if not ctx.triggered:
        return "", get_employee_table()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'add-employee-btn' and add_clicks > 0:
        # vlidate input
        if not all([new_dept, new_jobrole, new_income, new_overtime]):
            return html.Div("Please fill all fields", style={'color': 'red'}), get_employee_table()
        
        # add to database
        try:
            conn = get_db_connection()
            if conn:
                c = conn.cursor()
                
                c.execute("SELECT DepartmentID FROM Departments WHERE DepartmentName = ?", (new_dept,))
                dept_result = c.fetchone()
                if not dept_result:
                    return html.Div("Department not found in database", style={'color': 'red'}), get_employee_table()
                department_id = dept_result[0]
                
                c.execute("SELECT JobID FROM Jobs WHERE JobRole = ?", (new_jobrole,))
                job_result = c.fetchone()
                if job_result:
                    job_id = job_result[0]
                else:
                    c.execute("INSERT INTO Jobs (JobRole, JobLevel) VALUES (?, 1)", (new_jobrole,))
                    job_id = c.lastrowid

                c.execute('''INSERT INTO Employees (DepartmentID, JobID, MonthlyIncome, OverTime) 
                             VALUES (?, ?, ?, ?)''', 
                         (department_id, job_id, new_income, new_overtime))
                
                conn.commit()
                conn.close()
                
                return html.Div("Employee added successfully!", style={'color': 'green'}), get_employee_table()
            else:
                return html.Div("Database connection failed", style={'color': 'red'}), get_employee_table()
        except Exception as e:
            return html.Div(f"Error: {str(e)}", style={'color': 'red'}), get_employee_table()
    
    elif button_id == 'update-income-btn' and update_clicks > 0:

        if not all([emp_id, update_income]):
            return html.Div("Please provide both Employee ID and new income", style={'color': 'red'}), get_employee_table()
        
        try:
            conn = get_db_connection()
            if conn:
                c = conn.cursor()
                
                # check if employee exists
                c.execute('SELECT EmployeeID FROM Employees WHERE EmployeeID = ?', (emp_id,))
                if not c.fetchone():
                    return html.Div("Employee ID not found", style={'color': 'red'}), get_employee_table()

                # update income
                c.execute('''UPDATE Employees SET MonthlyIncome = ? 
                             WHERE EmployeeID = ?''', (update_income, emp_id))
                
                conn.commit()
                conn.close()
                
                return html.Div("Income updated successfully!", style={'color': 'green'}), get_employee_table()
            else:
                return html.Div("Database connection failed", style={'color': 'red'}), get_employee_table()
        except Exception as e:
            return html.Div(f"Error: {str(e)}", style={'color': 'red'}), get_employee_table()
    
    return "", get_employee_table()


#--------------------------------------------------------------
# Helper function to create employee table
#--------------------------------------------------------------
# def get employee table
def get_employee_table():
    conn = get_db_connection()
    if conn:
        try:
            query = """
            SELECT 
                e.EmployeeID,
                e.Age,
                e.Gender,
                e.MaritalStatus,
                d.DepartmentName,
                j.JobRole,
                e.MonthlyIncome,
                e.OverTime,
                e.Attrition
            FROM Employees e
            LEFT JOIN Departments d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN Jobs j ON e.JobID = j.JobID
            LIMIT 50
            """
            employees_df = pd.read_sql_query(query, conn)
            conn.close()
            
            if employees_df.empty:
                return html.Div("No employees found in database")
            
            return dash_table.DataTable(
                id='employee-table',
                columns=[{"name": i, "id": i} for i in employees_df.columns],
                data=employees_df.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_header={
                    'backgroundColor': '#4F008C',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'minWidth': '100px'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    }
                ]
            )
        except Exception as e:
            return html.Div(f"Error loading employee data: {str(e)}")
    return html.Div("Database connection failed")

# run app
if __name__ == '__main__':
    app.run(debug=True)