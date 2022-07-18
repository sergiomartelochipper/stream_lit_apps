import pandas as pd
import numpy as n
import snowflake.connector
import streamlit as st

# Time horizon considered in the calculation of UES
MAX_HORIZON_DAYS = 90
# Min time horizon to scale newly created accounts
MIN_HORIZON_DAYS = 10
# Amplitude feature multiplier to control the ceiling of amplitude score
AMP_FEATURE_MULTIPLIER = 0.7
# Diversity boost multiplier to control the magnitude of boost
DIVERSITY_SCORE_MULTIPLIER = 0.5

TRANSACTION_COLUMNS = [
    "PURCHASES_TRANSACTION_COUNT",
    "PURCHASES_TRANSACTION_VALUE_IN_USD",
    "P2P_TRANSACTION_COUNT",
    "P2P_TRANSACTION_VALUE_IN_USD",
    "INVESTMENTS_TRANSACTION_COUNT",
    "INVESTMENTS_TRANSACTION_VALUE_IN_USD",
    "INVESTMENTS_AMP_COUNT",
    "DEPOSITS_TRANSACTION_COUNT",
    "DEPOSITS_TRANSACTION_VALUE_IN_USD",
]

TRANSFER_TIME_COLUMNS = [
    "DAYS_SINCE_LAST_PURCHASES",
    "DAYS_SINCE_LAST_P2P",
    "DAYS_SINCE_LAST_INVESTMENTS",
    "DAYS_SINCE_LAST_DEPOSITS",
]

# Product lines
PRODUCT_LINES = ["PURCHASES_SCORE", "P2P_SCORE", "INVESTMENTS_SCORE", "DEPOSITS_SCORE"]

# Get the adjusted frequncy based on account age in days
def get_scaled_acct_age(user: dict):
    # scaled acct age is always between [MIN_HORIZON_DAYS, MAX_HORIZON_DAYS]
    account_age = user["ACCOUNT_AGE_IN_DAYS"]
    if account_age > MAX_HORIZON_DAYS:
        return MAX_HORIZON_DAYS
    if account_age < MIN_HORIZON_DAYS:
        return MIN_HORIZON_DAYS

    return account_age

# Get the transaction scores by adjusting with account age and scaling by the sigmoid function
def get_age_adjusted_transaction_scores(user_data):

    user_data["SCALED_ACCT_AGE"] = get_scaled_acct_age(user_data) # 10

    # get the density of ransaction cols by scaled account age in days
    for col in TRANSACTION_COLUMNS:
        user_data[col] = user_data[col] / user_data["SCALED_ACCT_AGE"] # 1
        user_data[col] = 1 / (1 + n.exp(-user_data[col])) # Sigmoid (1/1+e^-1) 0.73
        

    del user_data["SCALED_ACCT_AGE"]
    return user_data

# Get a dictionary for each transaction columns to store column min and column max values
@st.cache
def get_transaction_min_max_dict():
    min_max_dict = {}

    query = """
    SELECT *
    FROM "CHIPPER"."DBT_TRANSFORMATIONS"."UES_V3_ALL_FEATURES"
    WHERE IS_ACTIVE AND DAYS_SINCE_LAST_TRANSFER <= 90;
    """

    ctx = snowflake.connector.connect( # Connection
        user = "sergiomartelo",
        password = "Cojowa214356.",
        account = 'eia16549.us-east-1',
        database = 'CHIPPER',
        warehouse = 'CHIPPER_DATA'
        )

    ddf_user_data = pd.read_sql(query, ctx)
    ddf_user_data = ddf_user_data.apply(get_age_adjusted_transaction_scores, axis = 1)

    for col in TRANSACTION_COLUMNS:
        min_val = ddf_user_data[col].min()
        max_val = ddf_user_data[col].max()
        min_max_dict[col] = (float(min_val), float(max_val))
    return min_max_dict

# Perform min max scaling for each entry of the given column
def min_max_scaler(
    row,
    col_name,
    input_min_val,
    input_max_val,
    output_lower_bound=0,
    output_upper_bound=1,
):
    # avoid zero division issue - this occurs in Dask cold run
    if input_max_val == input_min_val:
        return output_lower_bound

    val_original = row[col_name]

    val_scaled = output_lower_bound + (
        (val_original - input_min_val) * (output_upper_bound - output_lower_bound) 
    ) / (input_max_val - input_min_val)
    return val_scaled



# Apply min_max scaler to the transaction scores, result in range [0, 1]
def get_minmax_scaled_transaction_scores(user, min_max_dict):

    for col, (min_val, max_val) in min_max_dict.items():
        user[col] = min_max_scaler(user, col, min_val, max_val)
    return user

# Helper function fo freshness scores
# Base 20 in the exp function havles the score when the days since last transfer
# is 21 (3 weeks), then slowly decay as the value grows
def get_freshness_decay(row, col_name):
    days_since_last_transfer = row[col_name]
    # column value is -1 when the user made 0 settled transaction during the time window
    # for users who is active based on amplitude data but made 0 settled transactions in the ues horizon window
    if days_since_last_transfer == -1 or days_since_last_transfer > MAX_HORIZON_DAYS:
        return 0
    if days_since_last_transfer <= 7:
        return 1
    return n.exp(((7 - days_since_last_transfer) / 20))

def get_transfer_days_freshness_dacay(user_data):
    for col in TRANSFER_TIME_COLUMNS:
        user_data[col] = get_freshness_decay(user_data, col_name=col)
    return user_data

def compute_product_score(ddf, product_line, amp_feature=False):

    product_line_score_name = "{}_SCORE".format(product_line)
    ddf[product_line_score_name] = ddf["DAYS_SINCE_LAST_{}".format(product_line)] * max(
        ddf["{}_TRANSACTION_VALUE_IN_USD".format(product_line)],
        ddf["{}_TRANSACTION_COUNT".format(product_line)]
    )

    # if amp feature is included for a product line, compare the max of scaled
    # transactional scores with the scaled amp score
    if amp_feature:
        # get scaled amp feature score
        ddf["{}_AMP_COUNT".format(product_line)] *= AMP_FEATURE_MULTIPLIER
        ddf[product_line_score_name] = max(
            ddf[product_line_score_name], 
            ddf["{}_AMP_COUNT".format(product_line)]
        )

    return ddf

# get the final base UES according to each product line score
def compute_base_ues_scores(ddf_user_data):

    # product line without amp feature
    product_line_without_amp = ["PURCHASES", "P2P", "DEPOSITS"]
    for product_line in product_line_without_amp:
        ddf_user_data = compute_product_score(
            ddf_user_data, product_line, amp_feature=False
        )

    # product line with amp feature
    ddf_user_data = compute_product_score(
        ddf_user_data, "INVESTMENTS", amp_feature=True
    )

    # Get the max across all 4 product line scores as the base UES
    ddf_user_data["UES_BASE"] = max(
        ddf_user_data[PRODUCT_LINES[0]], 
        ddf_user_data[PRODUCT_LINES[1]], 
        ddf_user_data[PRODUCT_LINES[2]], 
        ddf_user_data[PRODUCT_LINES[3]]
        )

    return ddf_user_data

# compute diversity boost score
def get_diversity_boost_score(row):
    scores = [
        row[PRODUCT_LINES[0]], 
        row[PRODUCT_LINES[1]], 
        row[PRODUCT_LINES[2]], 
        row[PRODUCT_LINES[3]]
    ]
    # get sum of pairwise product
    sum_pairwise_prod = (sum(scores) ** 2 - n.dot(scores,scores)) / 2
    # flatten out by taking average of scores, then adjusted by the multiplier
    n_pairs = n.size(scores) * (n.size(scores) - 1) / 2
    boost_score = (sum_pairwise_prod / n_pairs) * DIVERSITY_SCORE_MULTIPLIER
    return boost_score

# get adjusted final score by combining base and diversity boost scores with clipping at 1
def get_adjusted_ues(row):
    # if boosted ues >= 1, clip it to 1
    ues_boosted = row["UES_BASE"] + row["BOOST_SCORE"]
    return min(ues_boosted, 1)

# get final engagement score with base + diversity boost
def get_boosted_ues(ddf_user_data):
    # diversity boost score
    ddf_user_data["BOOST_SCORE"] = get_diversity_boost_score(ddf_user_data)
    # get final score
    ddf_user_data["USER_ENGAGEMENT_SCORE"] = get_adjusted_ues(ddf_user_data)

    return ddf_user_data

#get user engagement bucket based on the engagement score
def ues_to_bucket(row):
    score = row["USER_ENGAGEMENT_SCORE"]
    if score == 0:
        bucket = "INACTIVE"
    elif score > 0 and score <= 0.3:
        bucket = "LOW"
    elif score > 0.3 and score <= 0.7:
        bucket = "MEDIUM"
    elif score > 0.7 and score <= 1:
        bucket = "HIGH"
    return bucket


def run_single_ues(user: dict) -> dict:
    # Step 1: Get age adjusted scores for transaction features
    user = get_age_adjusted_transaction_scores(user)

    # Step 2: Get the min max values for each transaction feature, and scale the raw scores
    transaction_min_max_dict = get_transaction_min_max_dict()
    user_data = get_minmax_scaled_transaction_scores(user, min_max_dict=transaction_min_max_dict)

    # Step 3: Get freshness decay on last transfer of each product line
    user_data = get_transfer_days_freshness_dacay(user_data)
    
    # Step 4: Compute product line based scores as well as base UES
    user_data = compute_base_ues_scores(user_data)
    
    # Step 5: Get diversity boosted UES
    user_data = get_boosted_ues(user_data)
    
    # Step 6: Get user engagement bucket based on User Engagement Score
    user_data["USER_ENGAGEMENT_BUCKET"] = ues_to_bucket(user_data)

    return [user_data, transaction_min_max_dict]

# p2p = 0.2736034579
