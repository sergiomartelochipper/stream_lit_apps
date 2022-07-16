## Packages ##
import streamlit as st
import time 



ACTIVITIES = {
    "Deposited into Chipper": "Deposits", 
    "Purchased through Chipper": "Purchases",
    "Transfered funds P2P": "P2P Transfers",
    "Invested through Chipper": "Investments"
}

def progress_bar(s: int) -> None:
    bar = st.progress(0)
    step = s/100

    for percent_complete in range(100):
        time.sleep(step)
        bar.progress(percent_complete + 1)

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
    user_details = {}
    user_activities = []

    user_details['ACCOUNT_AGE_IN_DAYS'] = st.number_input(
        label = "How old is the user's account in days?",
        value = 0,
        help = 'Please only input whole numbers.',
        step = 1,
        min_value = 0
        )
    

    if user_details['ACCOUNT_AGE_IN_DAYS'] != 0:
        transacted = st.radio(
            label = "Has the user transacted in the last 90 days?",
            options = ["No", "Yes"],
            horizontal = True
        )

    if user_details['ACCOUNT_AGE_IN_DAYS'] != 0 and transacted == "Yes":
        user_activities = st.multiselect(
            label = 'What actions has the user taken in the past 90 days?',
            options = ACTIVITIES.keys()
        )
    elif user_details['ACCOUNT_AGE_IN_DAYS'] != 0 and transacted == "No":
        result = st.empty()
        ues_info = [0.00, 'INACTIVE']

        with result:
            progress_bar(2)
            score, bucket = st.columns(2)
         
            with score:
                st.metric(
                    label = "User's UES:",
                    value = ues_info[0]
                )
            
            with bucket:
                st.metric(
                    label = "User's UES Bucket:",
                    value = ues_info[1]
                )

        
    if len(user_activities) > 0:
        """
        Fill in the details on user activity below.
        """
    
    for act in user_activities:

        with st.expander('{} details'.format(ACTIVITIES[act])):
            col1, col2 = st.columns(2)

            with col1:
                user_details['DAYS_SINCE_LAST_{}'.format(ACTIVITIES[act])] = st.number_input(
                    label = 'How many days has it been since the user {}?'.format(act.lower()),
                    value = 0,
                    help = 'Please only input whole numbers.',
                    step = 1,
                    min_value = 0, 
                    key = 'DAYS_SINCE_LAST_{} input'.format(ACTIVITIES[act])
                )
            with col2:
                user_details['TOTAL_USD_{}'.format(ACTIVITIES[act])] = st.number_input(
                    label = 'Total USD {}:'.format(act.lower()),
                    value = 0.0,
                    step = 1.0,
                    min_value = 0.0, 
                    key = 'TOTAL_USD_{} input'.format(ACTIVITIES[act])
                )
                user_details['TOTAL_TRANSACTIONS_{}'.format(ACTIVITIES[act])] = st.number_input(
                    label = 'Number of Transactions of this type:',
                    value = 0,
                    help = 'Please only input whole numbers.',
                    step = 1,
                    min_value = 0, 
                    key = 'TOTAL_TRANSACTIONS_{} input'.format(ACTIVITIES[act])
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
