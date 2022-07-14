## Packages ##
import streamlit as st


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
"""

#### UES Bucket and Metric Playground ####

# UES Score and Bucket Displays

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