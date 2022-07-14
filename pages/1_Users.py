## Packages ##
from logging import PlaceHolder
from unittest import main
from xmlrpc.client import boolean
import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px

## Page Config ##
st.set_page_config(
    page_title="All Users",
    page_icon= "",
)

## Misc Functions and Variables ##
def connect_to_snowflake() -> object:    
    try:
        ctx = snowflake.connector.connect( # Connection
        user = "sergiomartelo",
        password = "Cojowa214356.",
        account = 'eia16549.us-east-1'
        )
    except:
        st.error("An error occurred logging in! Double check username and password.")
    else: 
        try:
            ## Setup
            cs = ctx.cursor()
            cs.execute("USE DATABASE CHIPPER")
            cs.execute("USE WAREHOUSE CHIPPER_DATA")
            cs.execute("USE SCHEMA PUBLIC")    
        except:
            st.error("An error occurred!")
        else:
            return ctx
        finally:
            cs.close()


def user_scores(user_id: str) -> object:
    ctx = connect_to_snowflake()
    ues_query = """
        SELECT USER_ENGAGEMENT_SCORE AS UES,
            USER_ENGAGEMENT_BUCKET AS "Bucket",
            UES_BASE AS "Base UES",
            BOOST_SCORE AS "Boost Score",
            PURCHASES_SCORE AS "Purchases Score",
            P2P_SCORE AS "P2P Score",
            INVESTMENTS_SCORE AS "Investments Score",
            DEPOSITS_SCORE AS "Deposits Score",
            UPDATED_AT AS "Date"
        FROM "CHIPPER"."UTILS"."USER_ENGAGEMENT_SCORE"
        WHERE USeR_ID = '""" + user_id + "' ORDER BY UPDATED_AT;"
    scores = pd.read_sql(ues_query, ctx)
    return scores


def latest_ues (user_id: str) -> int:
    ctx = connect_to_snowflake()

    latest_ues_query = """
    SELECT USER_ENGAGEMENT_SCORE, USER_ENGAGEMENT_BUCKET
    FROM "CHIPPER"."UTILS"."USER_ENGAGEMENT_SCORE"
    WHERE USER_ID = 'c5926ee0-14bf-11ec-aa61-531192780cb5'
    ORDER BY UPDATED_AT DESC
    LIMIT 1;"""
    
    latest_ues = pd.read_sql(latest_ues_query,ctx)

    return latest_ues


## Page ##

### Sidebar ###
sidebar = st.sidebar

sidebar.success("Select a page above.")



#### Login ####

#login = sidebar.empty()

# Login form
#with login:
#    form = st.form(key = 'snowflake_login', clear_on_submit= False)
#    form.markdown('## SnowFlake Login' )
#    username = form.text_input(label = 'Username:')
#    password = form.text_input(label = 'Password:', type = 'password')
#    submitted = form.form_submit_button('Login')
#    ctx = connect_to_snowflake(username, password, form, submitted)

### Main Content ###

# User Selection Headers
st.markdown("""# User Explorer
                Use the tool below to explore trends in scores for a given user.""")

header = st.container()

with header:
    txt_input, current_ues, current_bucket = header.columns([2,1,1])
    user_id = txt_input.text_input('Enter User ID:', placeholder = 'ID')
    searched = txt_input.button('Run')

    if searched:
        scores = user_scores(user_id).sort_values(by = ['Date'], ascending = False)
        ues_bucket = scores.iloc[0]

        current_ues.metric('Current UES:', value = round(ues_bucket.iloc[0], 4))
        current_bucket.metric('Current Bucket:', value= ues_bucket.iloc[1])

main = st.container()

with main:
    graph, metrics_1, metrics_2, table = main.empty(), main.empty(), main.empty(), main.empty()

    if searched:
        fig = px.line(scores.melt(id_vars = 'Date', value_vars = ['UES', 'Purchases Score', 'Deposits Score', 'P2P Score', 'Investments Score'],
                        value_name = 'Score'), 
                        x="Date", y="Score", color = "variable", 
                        title='UES Over Time')
        graph.plotly_chart(fig)
        table.dataframe(scores)

        with metrics_1:
            avg_ues, avg_boost, mf_bucket, n_scores = st.columns(4)
            avg_ues.metric('Average UES:', value = round(scores['UES'].mean(), 4))
            avg_boost.metric('Average Boost:', value = round(scores['Boost Score'].mean(),4))
            #mf_bucket.write(scores['Bucket'].mode().iloc[0])
            mf_bucket.metric('Most Frequent Bucket:', value = scores['Bucket'].mode().iloc[0])
            n_scores.metric('Number of Scores:', value = len(scores))

        with metrics_2:
            avg_purch_score, avg_p2p_score, avg_inv_score, avg_dep_score = st.columns(4)
            avg_purch_score.metric('Avg Purchases Score:', value = round(scores['Purchases Score'].mean(),4))
            avg_p2p_score.metric('Avg P2P Score:', value = round(scores['P2P Score'].mean(),4))
            avg_inv_score.metric('Avg Investments Score:', value = round(scores['Investments Score'].mean(),4))
            avg_dep_score.metric('Avg Deposits Score:', value = round(scores['Deposits Score'].mean(),4))
    else:
        st.info('Waiting for a user ID...')
        


