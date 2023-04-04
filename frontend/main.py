import pandas as pd
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import base64
import streamlit_authenticator as stauth
import yaml
import matplotlib.pyplot as plt
import seaborn as sns


# Fetching data from API
api_key = "supersecret"
headers = {"X-API-KEY": api_key}
api_base_url = "http://127.0.0.1:3010/api/"

def fetch_data(endpoint, method="GET", payload=None):
    api_url = f"http://127.0.0.1:3010/api/{endpoint}"
    if method == "GET":
        response = requests.get(api_url, headers=headers)
    elif method == "POST":
        response = requests.post(api_url, json=payload, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            if 'data' in data and 'columns' in data:
                data_dicts = [dict(zip(data['columns'], row)) for row in data['data']]
                return pd.DataFrame(data_dicts)
            else:
                return data
        except Exception as e:
            print("Error parsing JSON data:", e)
            return pd.DataFrame()
    else:
        print(f"Error fetching data from API, status code: {response.status_code}, response content: {response.content}")
        return pd.DataFrame()


articles_df = fetch_data("articles")
customers_df = fetch_data("customers")
transactions_df = fetch_data("transactions")


yaml_config = f'''
credentials:
  usernames: 
    jsmith:
      name: John Smith
      password: {"abc"}
    rbriggs:
      name: Rebecca Briggs
      password: {"def"}
cookie:
  expiry_days: 30
  key: blabla # Must be string
  name: cookie
preauthorized:
  emails:
  - melsby@gmail.com
'''

config = yaml.load(yaml_config, Loader=yaml.SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = ""

def set_authenticated(username):
    st.session_state.authenticated = True
    st.session_state.user = username

def is_authenticated():
    return st.session_state.authenticated

def get_authenticated_user():
    return st.session_state.user

def clear_authentication():
    st.session_state.authenticated = False
    st.session_state.user = ""

if "account_created" not in st.session_state:
    st.session_state.account_created = False


if not is_authenticated():

    # Converting the image to base64
    def img_to_base64(img_path: str) -> str:
        with open(img_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

    # Formatting
    logo = "logo.png"
    encoded_logo = img_to_base64(logo)

    st.markdown(f"<p style='text-align: center;'><img src='data:image/png;base64,{encoded_logo}' width=200></p>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>H&M Data - Dashboard</h1>", unsafe_allow_html=True)

    username = st.text_input("Username", key="login_username_input1")
    password = st.text_input("Password", type="password", key="login_password_input1")
    login_button = st.button("Login", key="login_button1")


    if login_button:
        payload = {"username": username, "password": password}
        response = fetch_data("users/login", method="POST", payload=payload)

        if "access_token" in response:
            st.success("Logged in successfully!")
            name = username
            set_authenticated(name)
            st.experimental_rerun()
        else:
            st.sidebar.error("Username/password is incorrect")


    def signup():
        with st.sidebar:
            st.subheader("Sign up")
            new_username = st.text_input("New username", key="signup_username_input")
            new_password = st.text_input("New password", type="password", key="signup_password_input")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm_password_input")
            signup_button = st.button("Sign up")

            if signup_button:
                if new_password == confirm_password:
                    payload = {"username": new_username, "password": new_password}
                    response = fetch_data("users/signup", method="POST", payload=payload)

                    if "error" not in response:
                        st.success("Account created successfully!")
                        st.session_state.account_created = True
                        st.experimental_rerun()
                    else:
                        st.error("Username already exists. Please choose a different one.")
                else:
                    st.error("Passwords do not match. Please try again.")


    signup()

    if st.session_state.account_created:
        st.sidebar.info("Your account has been created successfully. Please log in.")
        st.session_state.account_created = False


if is_authenticated():

    name = get_authenticated_user()

    st.sidebar.header(f"Welcome back {name}!")

    logout_button = st.sidebar.button("Logout")

    if logout_button:
        clear_authentication()
        st.experimental_rerun()


    st.sidebar.image('logo.png', width=130)

    
    st.write('<h1 style="text-align: center;">H&M Dashboard Demo</h1>', unsafe_allow_html=True)
    st.markdown('<h6 style="text-align: center;">This dashboard provides an overview of different article, customer and transaction KPIs for H&M</h6>', unsafe_allow_html=True)

    st.sidebar.write("")

    page = st.sidebar.radio("Select page:", ('Articles', 'Customers', 'Transactions'))
    st.sidebar.write("")
    st.sidebar.write("")


    if page == 'Articles':
        
        df = articles_df

        # Sidebar filters
        product_types = sorted(df['product_type_name'].unique())
        selected_product_types = st.sidebar.selectbox('Product Types', [''] + product_types, index=0)

        # Additional filters
        selected_department = st.sidebar.selectbox('Department', [''] + sorted(df['department_name'].unique()), index=0)
        selected_section = st.sidebar.selectbox('Section', [''] + sorted(df['section_name'].unique()), index=0)
        selected_colour_group = st.sidebar.selectbox('Colour Group', [''] + sorted(df['colour_group_name'].unique()), index=0)

        # Apply filters to dataframe
        filtered_df = df.copy()

        if selected_product_types != "":
            filtered_df = filtered_df[filtered_df['product_type_name'] == selected_product_types]
        if selected_department != "":
            filtered_df = filtered_df[filtered_df['department_name'] == selected_department]
        if selected_section != "":
            filtered_df = filtered_df[filtered_df['section_name'] == selected_section]
        if selected_colour_group != "":
            filtered_df = filtered_df[filtered_df['colour_group_name'] == selected_colour_group]


        # Remove unnecessary columns from the displayed dataframe
        columns_to_keep = ['article_id', 'product_type_name', 'product_group_name', 'graphical_appearance_name', 'colour_group_name', 'perceived_colour_value_name', 'perceived_colour_master_name', 'department_name', 'section_name']
        filtered_df1 = filtered_df[columns_to_keep]

        # Display filtered dataframe
        st.write(filtered_df1)

        # Display KPIs
        kpi1, kpi2 = st.columns(2)

        kpi1.metric(
            label = "Total Articles",
            value = len(filtered_df)
        )

        kpi2.metric(
            label="Number of Unique Products",
            value=len(filtered_df['product_type_name'].unique())    
        )

        with sns.color_palette(["#373F51", "#F9A03F", "#4E8A8B", "#F13C20", "#F8E9A1", "#6A8A82"]):

            # Defining a custom color scale
            color_scale = px.colors.qualitative.Plotly

            # Histogram
            fig1 = px.histogram(filtered_df, x="product_group_name", color="colour_group_name", barmode="group", nbins=10, color_discrete_sequence=color_scale)
            fig1.layout.xaxis.title = "<b>Product Group Name</b>"
            fig1.layout.yaxis.title = "<b>Count</b>"
            fig1.layout.title = {
                'text': "<b>Histogram of Product Group Names and Colour Group Names</b>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            }
            fig1.update_traces(showlegend=True)

            # Add some spacing
            st.write("")
            st.write("")
            st.write("")
            st.write("")

            # Pie chart
            fig2 = px.pie(filtered_df, values='article_id', names='graphical_appearance_name', hole=.5, color_discrete_sequence=px.colors.qualitative.Plotly)
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.layout.title = {
                'text': "<b>Graphical Appearance Distribution</b>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            }
            fig2.layout.legend.title = "<b>Graphical Appearance Name</b>"
            fig2.layout.legend.x = 0.85
            fig2.layout.legend.y = 0.5
            fig2.layout.legend.traceorder = "normal"
            fig2.layout.legend.font.family = "sans-serif"
            fig2.layout.legend.font.size = 12
            fig2.layout.legend.font.color = "black"
            fig2.layout.legend.bordercolor = "#FFFFFF"
            fig2.layout.legend.borderwidth = 2
            fig2.layout.legend.bgcolor = "#f5f5f5"
            fig2.layout.legend.orientation = "v"

            # Add some spacing
            st.write("")
            st.write("")
            st.write("")
            st.write("")

            # Scatter plot
            fig4 = px.scatter(filtered_df, x='perceived_colour_master_name', y='product_group_name', color='graphical_appearance_name')
            fig4.layout.xaxis.title = "<b>Perceived Colour Master Name</b>"
            fig4.layout.yaxis.title = "<b>Product Group Name</b>"
            fig4.layout.title = {
                'text': "<b>Perceived Colour Master Name vs Product Group Name</b>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            }

            # Add some spacing
            st.write("")
            st.write("")
            st.write("")
            st.write("")

            # Box plot
            fig5 = px.box(filtered_df, x='department_name', y='perceived_colour_value_id', color='product_group_name')
            fig5.layout.xaxis.title = "<b>Department Name</b>"
            fig5.layout.yaxis.title = "<b>Perceived Colour Value ID</b>"
            fig5.layout.title = {
                'text': "<b>Department Name vs Perceived Colour Value ID</b>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            }

            # Updating chart size
            for fig in [fig1, fig2, fig4, fig5]:
                fig.update_xaxes(showgrid=False, zeroline=False)
                fig.update_yaxes(showgrid=False, zeroline=False)
                fig.update_layout(
                    width=1000,
                    height=800,
                    margin=dict(l=50, r=50, b=100, t=100, pad=4)
                )

                # Centering chart title
                fig.layout.title.x = 0.5

            st.plotly_chart(fig1)
            st.plotly_chart(fig2)
            st.plotly_chart(fig4)
            st.plotly_chart(fig5)

        # Print out filtered dataframe
        print(filtered_df.head())

        # KPIs affected by filters
        total_articles = len(filtered_df)
        unique_product_types = len(filtered_df['product_type_name'].unique())

    elif page == 'Customers':

        df = customers_df

        # Sidebar filters
        age_lst = df["age"].to_list()

        age_filtered_lst = st.sidebar.slider(
            'Select a range of ages',
            0, 100, (20, 80))

        st.sidebar.write('Ages range selected:', age_filtered_lst)

        # Customers KPIs
        customer_df = customers_df.loc[
            (customers_df['age'] >= age_filtered_lst[0]) &
            (customers_df['age'] <= age_filtered_lst[1])
        ]

        status_lst = customer_df["club_member_status"].unique().tolist()

        status_filtered_lst = st.sidebar.multiselect(
            'Select club member status',
            status_lst, default=["ACTIVE"]
        )

        if status_filtered_lst:
            customer_df = customer_df.loc[customer_df['club_member_status'].isin(status_filtered_lst)]

        news_customers = customer_df.loc[customer_df['fashion_news_frequency'].notnull()].shape[0]

        news_filtered_lst = st.sidebar.multiselect(
            'Select fashion news frequency',
            customer_df.loc[customer_df['fashion_news_frequency'].notnull(), 'fashion_news_frequency'].unique().tolist()
        )

        if news_filtered_lst:
            customer_df = customer_df.loc[customer_df['fashion_news_frequency'].isin(news_filtered_lst)]

        # Display dataframe
        customer_df_new = customer_df.drop(columns=['postal_code', 'FN', 'Active', 'club_member_status', 'index'])
        st.dataframe(customer_df_new)


        num_customers = len(customer_df)
        avg_age = customer_df["age"].mean()

        kpi4, kpi5 = st.columns(2)

        st.write("")
        st.write("")
        st.write("")

        kpi4.metric(
            label = "Number of Customers",
            value = num_customers
        )

        kpi5.metric(
            label="Average Age",
            value=avg_age   
        )

        st.write("")

        # Set H&M's brand colors
        hm_red = "#D62828"
        hm_gray = "#222222"
        hm_black = "#222222"
        hm_purple = "#800080"


        # Histogram for Age Distribution
        fig1 = px.histogram(customer_df, x="age", nbins=20, color_discrete_sequence=[hm_red], opacity=0.7)
        fig1.update_layout(title=dict(text="<b>Age Distribution</b>", font=dict(size=24, color=hm_black), x=0.5),
                        xaxis_title=dict(text="<b>Age</b>", font=dict(size=16, color=hm_black)),
                        yaxis_title=dict(text="<b>Count</b>", font=dict(size=16, color=hm_black)),
                        font=dict(color=hm_black),
                        plot_bgcolor='rgba(0,0,0,0)')
        fig1.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(size=14, color=hm_gray))
        fig1.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(size=14, color=hm_gray))
        st.plotly_chart(fig1)


        st.write("")
        st.write("")
        st.write("")

        # Bar chart for Fashion News Frequency
        news_counts = customer_df['fashion_news_frequency'].value_counts()
        news_labels = [f"{label} ({percent:.1f}%)" for label, percent in zip(news_counts.index, news_counts.values/news_counts.sum()*100) if percent > 0]
        news_counts = [count for count in news_counts.values if count > 0]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=news_labels, y=news_counts, marker_color=hm_black, opacity=0.7))
        fig2.update_layout(title=dict(text="<b>Fashion News Frequency</b>", font=dict(size=24, color=hm_black), x=0.5),
                        xaxis_title=dict(text="<b>Frequency</b>", font=dict(size=16, color=hm_black)),
                        yaxis_title=dict(text="<b>Count</b>", font=dict(size=16, color=hm_black)),
                        font=dict(color=hm_black),
                        plot_bgcolor='rgba(0,0,0,0)')
        fig2.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(size=14, color=hm_gray))
        fig2.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(size=14, color=hm_gray))
        st.plotly_chart(fig2)

    elif page == 'Transactions':

        df = transactions_df

        # Convert t_dat column to datetime
        df['t_dat'] = pd.to_datetime(df['t_dat'], errors='coerce')

        # Define sidebar filters
        year_month_min = df["t_dat"].min().to_pydatetime().replace(day=1)
        year_month_max = df["t_dat"].max().to_pydatetime().replace(day=pd.Timestamp(df["t_dat"].max().year, df["t_dat"].max().month, 1).days_in_month)

        filter_date = st.sidebar.slider("Select a range of dates", year_month_min, year_month_max, (year_month_min, year_month_max))
        price_range = st.sidebar.slider('Select Price Range', df['price'].min(), df['price'].max(), (df['price'].min(), df['price'].max()))

        sales_channel_id_map = {'Online': 1, 'Offline': 2}
        sales_channel_filtered_lst = st.sidebar.multiselect('Select sales channel', ['Online', 'Offline'], default=['Online', 'Offline'])

        # # Filter data
        # filtered_df = df[(df['t_dat'].dt.strftime('%Y-%m') >= filter_date[0].strftime('%Y-%m')) & (df['t_dat'].dt.strftime('%Y-%m') <= filter_date[1].strftime('%Y-%m'))]
        # filtered_df = filtered_df[(filtered_df['price'] >= price_range[0]) & (filtered_df['price'] <= price_range[1])]

        # Filter data
        filtered_df = df[(df['t_dat'] >= filter_date[0]) & (df['t_dat'] <= filter_date[1])]
        filtered_df = filtered_df[(filtered_df['price'] >= price_range[0]) & (filtered_df['price'] <= price_range[1])]

        if sales_channel_filtered_lst:
            sales_channel_ids = [sales_channel_id_map[channel_name] for channel_name in sales_channel_filtered_lst]
            filtered_df = filtered_df[filtered_df['sales_channel_id'].isin(sales_channel_ids)]

        # Remove unnecessary columns from the displayed dataframe
        columns_to_keep = ['t_dat', 'customer_id', 'article_id', 'price', 'sales_channel_id']
        filtered_df_display = filtered_df[columns_to_keep]

        # Display filtered data in a table
        st.dataframe(filtered_df_display)

        def calculate_kpis(df):
            sales_channel_filtered_df = df[df['sales_channel_id'].isin([sales_channel_id_map[channel_name] for channel_name in sales_channel_filtered_lst])]

            price_sum = sales_channel_filtered_df['price'].sum()
            transaction_count = sales_channel_filtered_df.shape[0]

            return price_sum, transaction_count

        price_sum, transaction_count = calculate_kpis(filtered_df)

        st.write("")
        st.write("")

        kpi4, kpi5 = st.columns(2)

        st.write("")
        st.write("")
        st.write("")

        kpi4.metric(
            label="Total Sales Revenue",
            value=round(price_sum, 2),
            delta=-10 + price_sum,
        )

        kpi5.metric(
            label="Number of Transactions",
            value=transaction_count,
            delta=int(transaction_count),
        )

        st.write("")
        st.write("")
        st.write("")

        st.markdown("""
        <style>
            .stColumn > div > div > div {
                display: flex;
                justify-content: center;
            }
        </style>
        """, unsafe_allow_html=True)


        # Set H&M's brand colors
        hm_red = "#D62828"
        hm_gray = "#222222"
        hm_black = "#222222"

        plt.rcParams['text.color'] = hm_gray
        plt.rcParams['axes.labelcolor'] = hm_gray
        plt.rcParams['xtick.color'] = hm_gray
        plt.rcParams['ytick.color'] = hm_gray

        # Sales Channel-wise Sales Revenue Chart
        sales_channel_revenue = df.groupby('sales_channel_id')['price'].sum().reset_index()
        sales_channel_revenue['percentage'] = round((sales_channel_revenue['price'] / sales_channel_revenue['price'].sum()) * 100, 1)
        sales_channel_revenue.index = ['Online', 'Offline']

        fig1 = px.pie(sales_channel_revenue, values='price', names=sales_channel_revenue.index, color=sales_channel_revenue.index, color_discrete_sequence=[hm_black, hm_red], hole=0.5)
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        fig1.layout.title = {
            'text': "<b>Sales Channel-wise Sales Revenue</b>",
            'font': {'size': 24}
        }

        # Sales Channel-wise Sales Count Chart
        sales_channel_count = df['sales_channel_id'].value_counts().reset_index()
        sales_channel_count.columns = ['sales_channel_id', 'count']
        sales_channel_count['percentage'] = round((sales_channel_count['count'] / sales_channel_count['count'].sum()) * 100, 1)
        sales_channel_count.index = ['Online', 'Offline']

        fig2 = px.pie(sales_channel_count, values='count', names=sales_channel_count.index, color=sales_channel_count.index, color_discrete_sequence=[hm_black, hm_red], hole=0.5)
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        fig2.layout.title = {
            'text': "<b>Sales Channel-wise Sales Count</b>",
            'font': {'size': 24}
        }

        # Create columns for the Sales Channel charts
        col1, col2, col3 = st.columns([2, 2, 2])

        # Display the charts
        col1.plotly_chart(fig1)
        col3.plotly_chart(fig2)

        # Sales Revenue by Date Chart
        transactions_by_date = filtered_df.groupby('t_dat')['price'].sum().reset_index()
        transactions_by_date['date'] = transactions_by_date['t_dat'].dt.date.astype(str)

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=transactions_by_date['date'], y=transactions_by_date['price'], mode='markers+lines', marker=dict(size=7.5, color=hm_red), line=dict(color=hm_red, width=2.5)))
        fig3.update_layout(
            width=1000,
            height=800,
            margin=dict(l=50, r=50, b=100, t=100, pad=4),
            xaxis_title="<b>Date</b>",
            yaxis_title="<b>Sales Revenue</b>",
            showlegend=False
        )
        fig3.layout.title = {
            'text': "<b>Sales Revenue by Date</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24}
        }
        fig3.update_xaxes(showgrid=False, zeroline=False, tickangle=45)
        fig3.update_yaxes(showgrid=False, zeroline=False)

        st.plotly_chart(fig3)
        # Add some spacing
        st.write("")
        st.write("")

        # Distribution of sales revenue by customer
        customer_revenue = filtered_df.groupby('customer_id')['price'].sum().reset_index()

        fig4 = px.histogram(customer_revenue, x="price", nbins=50, color_discrete_sequence=['#f94144'])
        fig4.update_traces(marker=dict(line=dict(width=1, color='black')))
        fig4.layout.title = {
            'text': "<b>Distribution of Sales Revenue by Customer</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24}
        }
        fig4.layout.xaxis.title = "<b>Sales Revenue</b>"
        fig4.layout.yaxis.title = "<b>Count</b>"
        fig4.update_xaxes(showgrid=False, zeroline=False)
        fig4.update_yaxes(showgrid=False, zeroline=False)
        fig4.update_layout(
            width=1000,
            height=800,
            margin=dict(l=50, r=50, b=100, t=100, pad=4)
        )

        st.plotly_chart(fig4)
                    
