import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Employee Attrition Dashboard"

# Load data from your CSV file
try:
    df = pd.read_csv('data/cleanData.csv')
    print("Successfully loaded data from data/cleanData.csv")
except FileNotFoundError:
    print("CSV file not found. Creating sample data for demonstration.")
    # Fallback to sample data if CSV not found
    def generate_sample_data():
        n = 100
        data = {
            'JobRole': np.random.choice(['Sales Representative', 'Research Scientist', 'Laboratory Technician', 
                                        'Manufacturing Director', 'Healthcare Representative', 'Manager', 
                                        'Sales Executive', 'Research Director', 'Human Resources'], n),
            'OverTime': np.random.choice(['Yes', 'No'], n, p=[0.3, 0.7]),
            'MaritalStatus': np.random.choice(['Single', 'Married', 'Divorced'], n, p=[0.3, 0.5, 0.2]),
            'BusinessTravel': np.random.choice(['Travel_Frequently', 'Travel_Rarely', 'Non-Travel'], n, p=[0.2, 0.5, 0.3]),
            'EducationField': np.random.choice(['Human Resources', 'Life Sciences', 'Medical', 'Marketing', 
                                               'Technical Degree', 'Other'], n),
            'JobLevel': np.random.randint(1, 6, n),
            'MonthlyIncome': np.random.normal(5000, 2000, n).astype(int),
            'TotalWorkingYears': np.random.randint(0, 40, n),
            'JobSatisfaction': np.random.randint(1, 5, n),
            'EnvironmentSatisfaction': np.random.randint(1, 5, n),
            'DailyRate': np.random.randint(100, 1000, n),
            'Department': np.random.choice(['Sales', 'R&D', 'HR'], n, p=[0.4, 0.4, 0.2]),
            'Attrition': np.random.choice(['Yes', 'No'], n, p=[0.2, 0.8])
        }
        return pd.DataFrame(data)
    
    df = generate_sample_data()

# Connect to SQLite database
def get_db_connection():
    try:
        conn = sqlite3.connect('db/employee_database.db')
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to get employee data from database
def get_employees_from_db():
    conn = get_db_connection()
    if conn:
        try:
            employees_df = pd.read_sql_query("SELECT * FROM employees", conn)
            conn.close()
            return employees_df
        except sqlite3.Error as e:
            print(f"Error reading from database: {e}")
            conn.close()
            return pd.DataFrame()
    return pd.DataFrame()

# Function to get column names from database
def get_db_columns():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(employees)")
            columns = [column[1] for column in cursor.fetchall()]
            conn.close()
            return columns
        except sqlite3.Error as e:
            print(f"Error getting column names: {e}")
            conn.close()
            return []
    return []

# App layout
app.layout = html.Div([
    html.H1("Employee Attrition Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    # Filters
    html.Div([
        html.Label("Select Department:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Dropdown(
            id='dept-filter',
            options=[{'label': dept, 'value': dept} for dept in df['Department'].unique()],
            value=df['Department'].unique()[0] if len(df['Department'].unique()) > 0 else '',
            style={'width': '200px', 'display': 'inline-block', 'marginRight': '30px'}
        ),
        
        html.Label("Sort By:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Dropdown(
            id='sort-filter',
            options=[
                {'label': 'Attrition Rate', 'value': 'Attrition'},
                {'label': 'Monthly Income', 'value': 'MonthlyIncome'},
                {'label': 'Job Level', 'value': 'JobLevel'}
            ],
            value='Attrition',
            style={'width': '200px', 'display': 'inline-block'}
        )
    ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px', 'marginBottom': '20px'}),
    
    # Visualizations
    html.Div([
        # First row of charts
        html.Div([
            dcc.Graph(id='jobrole-chart', style={'width': '50%', 'display': 'inline-block'}),
            dcc.Graph(id='overtime-chart', style={'width': '50%', 'display': 'inline-block'})
        ]),
        
        # Second row of charts
        html.Div([
            dcc.Graph(id='maritalstatus-chart', style={'width': '50%', 'display': 'inline-block'}),
            dcc.Graph(id='businesstravel-chart', style={'width': '50%', 'display': 'inline-block'})
        ]),
        
        # Third row of charts
        html.Div([
            dcc.Graph(id='income-chart', style={'width': '50%', 'display': 'inline-block'}),
            dcc.Graph(id='satisfaction-chart', style={'width': '50%', 'display': 'inline-block'})
        ])
    ]),
    
    # Forms section
    html.Div([
        html.H2("Employee Management", style={'borderBottom': '2px solid #2c3e50', 'paddingBottom': '10px'}),
        
        # Add new employee form
        html.Div([
            html.H3("Add New Employee"),
            html.Div([
                html.Label("Department"),
                dcc.Dropdown(
                    id='new-dept',
                    options=[{'label': dept, 'value': dept} for dept in df['Department'].unique()],
                    style={'width': '100%', 'marginBottom': '10px'}
                ),
                
                html.Label("Job Role"),
                dcc.Input(id='new-jobrole', type='text', placeholder='Enter job role', style={'width': '100%', 'marginBottom': '10px'}),
                
                html.Label("Monthly Income"),
                dcc.Input(id='new-income', type='number', placeholder='Enter monthly income', style={'width': '100%', 'marginBottom': '10px'}),
                
                html.Label("OverTime"),
                dcc.Dropdown(
                    id='new-overtime',
                    options=[{'label': 'Yes', 'value': 'Yes'}, {'label': 'No', 'value': 'No'}],
                    style={'width': '100%', 'marginBottom': '10px'}
                ),
                
                html.Button('Add Employee', id='add-employee-btn', n_clicks=0, style={
                    'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
                    'padding': '10px 20px', 'borderRadius': '5px', 'cursor': 'pointer'
                })
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '20px'}),
            
            # Update employee income form
            html.Div([
                html.H3("Update Employee Income"),
                html.Label("Employee ID"),
                dcc.Input(id='employee-id', type='number', placeholder='Enter employee ID', style={'width': '100%', 'marginBottom': '10px'}),
                
                html.Label("New Monthly Income"),
                dcc.Input(id='update-income', type='number', placeholder='Enter new monthly income', style={'width': '100%', 'marginBottom': '10px'}),
                
                html.Button('Update Income', id='update-income-btn', n_clicks=0, style={
                    'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 
                    'padding': '10px 20px', 'borderRadius': '5px', 'cursor': 'pointer'
                })
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ]),
        
        html.Div(id='form-output', style={'marginTop': '20px', 'padding': '10px', 'borderRadius': '5px'})
    ], style={'marginTop': '40px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
])

# Callbacks for visualizations
@app.callback(
    [Output('jobrole-chart', 'figure'),
     Output('overtime-chart', 'figure'),
     Output('maritalstatus-chart', 'figure'),
     Output('businesstravel-chart', 'figure'),
     Output('income-chart', 'figure'),
     Output('satisfaction-chart', 'figure')],
    [Input('dept-filter', 'value'),
     Input('sort-filter', 'value')]
)
def update_charts(selected_dept, sort_by):
    # Filter data based on department
    if selected_dept and 'Department' in df.columns:
        filtered_df = df[df['Department'] == selected_dept]
    else:
        filtered_df = df
    
    # Job Role chart
    if 'JobRole' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        jobrole_attrition = filtered_df.groupby('JobRole')['Attrition'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        jobrole_attrition.columns = ['JobRole', 'AttritionRate']
        jobrole_fig = px.bar(jobrole_attrition, x='JobRole', y='AttritionRate', 
                             title='Attrition Rate by Job Role',
                             labels={'AttritionRate': 'Attrition Rate (%)', 'JobRole': 'Job Role'})
        jobrole_fig.update_layout(showlegend=False)
    else:
        jobrole_fig = go.Figure()
        jobrole_fig.add_annotation(text="JobRole or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # Overtime chart
    if 'OverTime' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        overtime_attrition = filtered_df.groupby('OverTime')['Attrition'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        overtime_attrition.columns = ['OverTime', 'AttritionRate']
        overtime_fig = px.bar(overtime_attrition, x='OverTime', y='AttritionRate', 
                              title='Attrition Rate by Overtime',
                              labels={'AttritionRate': 'Attrition Rate (%)', 'OverTime': 'Overtime'})
        overtime_fig.update_layout(showlegend=False)
    else:
        overtime_fig = go.Figure()
        overtime_fig.add_annotation(text="OverTime or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # Marital Status chart
    if 'MaritalStatus' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        marital_attrition = filtered_df.groupby('MaritalStatus')['Attrition'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        marital_attrition.columns = ['MaritalStatus', 'AttritionRate']
        marital_fig = px.bar(marital_attrition, x='MaritalStatus', y='AttritionRate', 
                             title='Attrition Rate by Marital Status',
                             labels={'AttritionRate': 'Attrition Rate (%)', 'MaritalStatus': 'Marital Status'})
        marital_fig.update_layout(showlegend=False)
    else:
        marital_fig = go.Figure()
        marital_fig.add_annotation(text="MaritalStatus or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # Business Travel chart
    if 'BusinessTravel' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        travel_attrition = filtered_df.groupby('BusinessTravel')['Attrition'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        travel_attrition.columns = ['BusinessTravel', 'AttritionRate']
        travel_fig = px.bar(travel_attrition, x='BusinessTravel', y='AttritionRate', 
                            title='Attrition Rate by Business Travel',
                            labels={'AttritionRate': 'Attrition Rate (%)', 'BusinessTravel': 'Business Travel'})
        travel_fig.update_layout(showlegend=False)
    else:
        travel_fig = go.Figure()
        travel_fig.add_annotation(text="BusinessTravel or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # Income distribution chart
    if 'MonthlyIncome' in filtered_df.columns and 'Attrition' in filtered_df.columns:
        income_fig = px.violin(filtered_df, x='Attrition', y='MonthlyIncome', 
                               title='Income Distribution by Attrition Status')
    else:
        income_fig = go.Figure()
        income_fig.add_annotation(text="MonthlyIncome or Attrition data not available", x=0.5, y=0.5, showarrow=False)
    
    # Satisfaction chart
    if all(col in filtered_df.columns for col in ['JobSatisfaction', 'EnvironmentSatisfaction', 'Attrition']):
        satisfaction_data = filtered_df[filtered_df['Attrition'] == 'Yes']
        satisfaction_fig = go.Figure()
        satisfaction_fig.add_trace(go.Box(y=satisfaction_data['JobSatisfaction'], name='Job Satisfaction', boxpoints='all'))
        satisfaction_fig.add_trace(go.Box(y=satisfaction_data['EnvironmentSatisfaction'], name='Environment Satisfaction', boxpoints='all'))
        satisfaction_fig.update_layout(title='Satisfaction Scores for Employees with Attrition')
    else:
        satisfaction_fig = go.Figure()
        satisfaction_fig.add_annotation(text="Satisfaction data not available", x=0.5, y=0.5, showarrow=False)
    
    return jobrole_fig, overtime_fig, marital_fig, travel_fig, income_fig, satisfaction_fig

# Callback for form submissions
@app.callback(
    Output('form-output', 'children'),
    [Input('add-employee-btn', 'n_clicks'),
     Input('update-income-btn', 'n_clicks')],
    [State('new-dept', 'value'),
     State('new-jobrole', 'value'),
     State('new-income', 'value'),
     State('new-overtime', 'value'),
     State('employee-id', 'value'),
     State('update-income', 'value')]
)
def handle_form_submissions(add_clicks, update_clicks, new_dept, new_jobrole, new_income, new_overtime, emp_id, update_income):
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'add-employee-btn' and add_clicks > 0:
        # Validate inputs
        if not all([new_dept, new_jobrole, new_income, new_overtime]):
            return html.Div("Please fill all fields", style={'color': 'red'})
        
        # Add to database
        try:
            conn = get_db_connection()
            if conn:
                c = conn.cursor()
                
                # Get column names to construct proper INSERT statement
                columns = get_db_columns()
                if columns:
                    # Create placeholders for the columns we're inserting
                    placeholders = ', '.join(['?' for _ in range(4)])
                    column_names = 'Department, JobRole, MonthlyIncome, OverTime'
                    
                    c.execute(f'''INSERT INTO employees ({column_names}) 
                                 VALUES ({placeholders})''', 
                             (new_dept, new_jobrole, new_income, new_overtime))
                
                conn.commit()
                conn.close()
                
                return html.Div("Employee added successfully!", style={'color': 'green'})
            else:
                return html.Div("Database connection failed", style={'color': 'red'})
        except Exception as e:
            return html.Div(f"Error: {str(e)}", style={'color': 'red'})
    
    elif button_id == 'update-income-btn' and update_clicks > 0:
        # Validate inputs
        if not all([emp_id, update_income]):
            return html.Div("Please provide both Employee ID and new income", style={'color': 'red'})
        
        # Update database
        try:
            conn = get_db_connection()
            if conn:
                c = conn.cursor()
                
                # Check if employee exists
                c.execute('SELECT id FROM employees WHERE id = ?', (emp_id,))
                if not c.fetchone():
                    return html.Div("Employee ID not found", style={'color': 'red'})
                
                # Update income
                c.execute('''UPDATE employees SET MonthlyIncome = ?, updated_at = CURRENT_TIMESTAMP 
                             WHERE id = ?''', (update_income, emp_id))
                
                conn.commit()
                conn.close()
                
                return html.Div("Income updated successfully!", style={'color': 'green'})
            else:
                return html.Div("Database connection failed", style={'color': 'red'})
        except Exception as e:
            return html.Div(f"Error: {str(e)}", style={'color': 'red'})
    
    return ""

if __name__ == '__main__':
    app.run(debug=True)