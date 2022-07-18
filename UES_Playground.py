## Packages ##
from tkinter import W
import streamlit as st
import time 
import pandas as pd
import UES_Playground_Utils as utils

## VARIABLES ##

ACTIVITIES = {
    "Deposited into Chipper": "Deposits", 
    "Purchased through Chipper": "Purchases",
    "Transfered funds P2P": "P2P",
    "Invested through Chipper": "Investments"
}

USER_DETAILS = {
    "ACCOUNT_AGE_IN_DAYS": 0,
    "DAYS_SINCE_LAST_DEPOSITS": -1,
    "DEPOSITS_TRANSACTION_VALUE_IN_USD": 0.0,
    "DEPOSITS_TRANSACTION_COUNT": 0,
    "DAYS_SINCE_LAST_PURCHASES": -1,
    "PURCHASES_TRANSACTION_VALUE_IN_USD": 0.0,
    "PURCHASES_TRANSACTION_COUNT": 0,
    "DAYS_SINCE_LAST_P2P": -1,
    "P2P_TRANSACTION_VALUE_IN_USD": 0.0,
    "P2P_TRANSACTION_COUNT": 0,
    "DAYS_SINCE_LAST_INVESTMENTS": -1,
    "INVESTMENTS_TRANSACTION_VALUE_IN_USD": 0.0,
    "INVESTMENTS_TRANSACTION_COUNT": 0,
    "INVESTMENTS_AMP_COUNT": 0
}

UES_INFO = [
    0.00, # UES
    "INACTIVE" # Bucket
]

## Page Config ##
st.set_page_config(
    page_title="UES Playground",
    page_icon='🛠️',
)

## Page ##

### Sidebar ###
st.sidebar.success("Select a page above.")

### Content ###

#### Introduction ####
"""
# UES Playground

Use the playground below to get a better understanding on how user engagement scores are calculated and what user behavior affects it.
"""


#### Raw Features to UES ####

raw_features_to_ues = st.container()

with raw_features_to_ues:
    """
    ## Placeholder

    placeholder
    """
    user_activities = []
    transacted = "No"

    USER_DETAILS['ACCOUNT_AGE_IN_DAYS'] = st.number_input(
        label = "How old is the user's account in days?",
        value = 0,
        help = 'Please only input whole numbers.',
        step = 1,
        min_value = 0
        )
    
    if USER_DETAILS['ACCOUNT_AGE_IN_DAYS'] != 0:
        transacted = st.radio(
            label = "Has the user transacted in the last 90 days?",
            options = ["No", "Yes"],
            horizontal = True
        )

    if transacted == "Yes":
        user_activities = st.multiselect(
            label = 'What actions has the user taken in the past 90 days?',
            options = ACTIVITIES.keys()
        )
        
    if len(user_activities) > 0:
        """
        Fill in the details on user activity below.
        """
    
    for act in user_activities:

        with st.expander('{} details'.format(ACTIVITIES[act])):
            col1, col2 = st.columns(2)

            with col1:
                USER_DETAILS['DAYS_SINCE_LAST_{}'.format(ACTIVITIES[act]).upper()] = st.number_input(
                    label = 'How many days has it been since the user {}?'.format(act.lower()),
                    value = -1,
                    help = 'Please only input whole numbers.',
                    step = 1,
                    min_value = 0, 
                    key = 'DAYS_SINCE_LAST_{} input'.format(ACTIVITIES[act])
                )
                
                if act == "Invested through Chipper":
                    USER_DETAILS['INVESTMENTS_AMP_COUNT'] = st.number_input(
                    label = 'AMP count:',
                    value = 0,
                    help = 'Please only input whole numbers.',
                    step = 1,
                    min_value = 0, 
                    key = 'AMP_{} input'.format(ACTIVITIES[act])
                    )
            
            with col2:
                USER_DETAILS['{}_TRANSACTION_VALUE_IN_USD'.format(ACTIVITIES[act]).upper()] = st.number_input(
                    label = 'Total USD {}:'.format(act.lower()),
                    value = 1.0,
                    step = 1.0,
                    min_value = 0.00000001, 
                    key = '{}_TRANSACTION_VALUE_IN_USD input'.format(ACTIVITIES[act])
                )
                USER_DETAILS['{}_TRANSACTION_COUNT'.format(ACTIVITIES[act]).upper()] = st.number_input(
                    label = 'Number of Transactions of this type:',
                    value = 1,
                    help = 'Please only input whole numbers.',
                    step = 1,
                    min_value = 1, 
                    key = '{}_TRANSACTION_COUNT input'.format(ACTIVITIES[act])
                )
    
    DAYS_SINCE_LAST_TRANSFER = min([USER_DETAILS[x] if USER_DETAILS[x] > -1 else 100000 for x in utils.TRANSFER_TIME_COLUMNS])
    CASE_1 = DAYS_SINCE_LAST_TRANSFER > utils.MAX_HORIZON_DAYS and USER_DETAILS['INVESTMENTS_AMP_COUNT'] == 0
    CASE_2 = DAYS_SINCE_LAST_TRANSFER == 100000 and USER_DETAILS['INVESTMENTS_AMP_COUNT'] == 0
    IS_ACTIVE =  not CASE_1 and not CASE_2

    result = st.empty()

    if IS_ACTIVE:
        USER_CALCULATED_DETAILS, temp = utils.run_single_ues(USER_DETAILS)
        UES_INFO = [
            USER_CALCULATED_DETAILS["USER_ENGAGEMENT_SCORE"],
            USER_CALCULATED_DETAILS["USER_ENGAGEMENT_BUCKET"]
            ]

        details = st.expander("Details")
        with details:
            r_1, r_2 = st.empty(), st.empty()

            with r_1:
                base_ues, boost, dep_score = st.columns(3)
                
                base_ues.metric(
                    label = "Base UES:",
                    value = round(USER_CALCULATED_DETAILS["UES_BASE"], 4)
                )
                boost.metric(
                    label = "Boost Score:",
                    value = round(USER_CALCULATED_DETAILS["BOOST_SCORE"], 4)
                )
                dep_score.metric(
                    label = "Deposits Score:",
                    value = round(USER_CALCULATED_DETAILS["DEPOSITS_SCORE"], 4)
                )

            with r_2:
                p2p_score, inv_score, pur_score = st.columns(3)
                
                p2p_score.metric(
                    label = "P2P Score:",
                    value = round(USER_CALCULATED_DETAILS["P2P_SCORE"], 4)
                )
                inv_score.metric(
                    label = "Investments Score:",
                    value = round(USER_CALCULATED_DETAILS["INVESTMENTS_SCORE"], 4)
                )
                pur_score.metric(
                    label = "Deposits Score:",
                    value = round(USER_CALCULATED_DETAILS["PURCHASES_SCORE"], 4)
                )
        

    with result:
        score, bucket = st.columns(2)
        with score:
            st.metric(
                label = "User's UES:",
                value = round(UES_INFO[0], 4)
            )
        
        with bucket:
            st.metric(
                label = "User's UES Bucket:",
                value = UES_INFO[1]
            )
    
    
    
    
#### Transaction Scores to UES ####

# UES Score and Bucket Displays

"""
## Transaction Scores to UES
"""

scores_to_ues = st.expander('Scores to UES Explorer')

with scores_to_ues:
    ## Columns
    ues_display, ues_bucket_display = st.columns(2)

    ## Initial Container Setup 
    ues_cont = ues_display.empty() # Makes UES container
    bucket_cont = ues_bucket_display.empty() # Makes UES bucket container

    ues_cont.metric(label="User Engagement Score:", value = 0) # Populates Initial UES 
    bucket_cont.metric(label = "Bucket:", value = 'Inactive') # Populates Initial Bucket

    ## Numeric Inputs for Scores
    col_1, col_2, col_3, col_4 = st.columns(4) # Makes columns

    ### Score Prompts
    deposits_score = col_1.number_input('Enter Deposits Score', min_value = 0.00, max_value = 1.000, value = 0.0, step = 0.01) # Deposits Score
    investments_score = col_2.number_input('Enter Investments Score', min_value = 0.00, max_value = 1.00, value = 0.0, step = 0.01) # Investments Score
    purchases_score = col_3.number_input('Enter Purchases Score', min_value = 0.00, max_value = 1.00, value = 0.0, step = 0.01) # Purchases Score
    p2p_score = col_4.number_input('Enter P2P Score', min_value = 0.00, max_value = 1.00, value = 0.0, step = 0.01) # P2P Score

    ## UES Calculations
    ues_base = max(deposits_score, investments_score, purchases_score, p2p_score) # Base UES Score
    interaction_term = deposits_score * investments_score + deposits_score * purchases_score + deposits_score * p2p_score + investments_score * purchases_score + investments_score * p2p_score + purchases_score * p2p_score # Interaction term
    boost_multiplier = 0.5 # Boost multiplier
    boost_score = (interaction_term/6) * boost_multiplier # Boost score

    ues = ues_base + boost_score # User Engagement Score

    ## Updating Displays
    if ues <= 1:
        ues_cont.metric(label="User Engagement Score:", value = ues)
    else:
        ues_cont.metric(label="User Engagement Score:", value = 1.00) # Updates UES display

    ### Logic for updating bucket display
    if (ues > 0 and ues <= 0.3):
        bucket_cont.metric(label = "Bucket:", value = 'Low')
    elif (ues > 0.3 and ues < 0.7):
        bucket_cont.metric(label = "Bucket", value = 'Medium')
    elif (ues >= 0.7):
        bucket_cont.metric(label = "Bucket", value = 'High')
