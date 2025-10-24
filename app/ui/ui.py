import streamlit as st
import datetime as dt
import time

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from dateutil.relativedelta import relativedelta

from scipy import stats
import numpy as np
import pandas as pd
import calplot

import psycopg2
import subprocess

def to_date(date_string):
    return dt.datetime.strptime(date_string, "%Y-%m-%d").date()

def from_date(date_object):
    return dt.datetime.strftime(date_object, "%Y-%m-%d")

def create_rolling_28D_average(values):
    base_average = np.nanmean(values)
    trailing_twenty_eight = []
    average = []
    for el in values:
        if np.isnan(el):
            el = base_average
        trailing_twenty_eight.append(el)
        base_average = np.mean(trailing_twenty_eight)
        if len(trailing_twenty_eight) < 28:
            numbers = trailing_twenty_eight
        else:
            numbers = trailing_twenty_eight[-28:]
        average.append(np.mean(numbers))
    return average

def plot_minutes_to_target(plot_this, target, experiment_start, ax, limit):
    plot_this = (plot_this - target) * 60
    ax.plot(plot_this.index
      , plot_this
      , color='black'
      , linewidth=.5)
    ax.fill_between(
        plot_this.index
      , [0.0] * plot_this.shape[0]
      , np.minimum([0.0] * plot_this.shape[0], plot_this)
      , color='red'
      , alpha=0.2)
    ax.fill_between(
        plot_this.index
      , [0.0] * plot_this.shape[0]
      , np.maximum([0.0] * plot_this.shape[0], plot_this)
      , color='green'
      , alpha=0.2)
    ax.vlines(
        experiment_start
      , ymin=0
      , ymax=9 * 60
      , color='lightgreen'
      , linestyle='dashed')

    ax.set_ylim(-1 * limit, limit)
    ax.yaxis.set_label_position("right")
    ax.set_facecolor('whitesmoke')
    ax.yaxis.tick_right()
    myFmt = mdates.DateFormatter('%b')
    ax.xaxis.set_major_formatter(myFmt)
    ax.tick_params(
        axis='both',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        right=False,
        labelbottom=True,
        labelsize=7)
    ax.set_title(
        'Minutes to Target (Trailing 28 Days)'
      , loc='left'
      , size=7)
    return ax

USER_NAME = 'rubicon'
DB = 'sleepdb'
CONNECTION_STRING = f'postgresql+psycopg2://{USER_NAME}@localhost:5432/{DB}'

def create_conn(db):
    # Connect and Collect
    conn = psycopg2.connect(
        host="localhost"
        , user="rubicon"
        , connect_timeout=1
        , password=""
        , database=db)

    return conn

def table_exists(db, table_name, schema_name='public'):
    """
    Checks if a table exists in the specified schema of the PostgreSQL database.

    Args:
        conn: A psycopg2 connection object.
        table_name: The name of the table to check.
        schema_name: The name of the schema where the table is expected (default is 'public').

    Returns:
        True if the table exists, False otherwise.
    """
    conn = create_conn(db)
    with conn.cursor() as cur:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            );
        """
        cur.execute(query, (schema_name, table_name))
        return cur.fetchone()[0]

def retrieve_query(query):
    conn = create_conn(DB)
    cursor = conn.cursor()
    cursor.execute(query)
    try:
        data = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]
        df = pd.DataFrame(data, columns=column_names)
        conn.close()

        # decode binary data
        for el in df:
            if type(df[el][0]) == bytearray:
                df[el] = df[el].apply(lambda el: el.decode('utf-8') if el is not None else el)

        return df

    except KeyError:
        return None



def dashboard(config):
    st.title("Project Kiwi")
    st.text("We have set up an 'AB' test to determine if Kiwi's do in fact increase the duration and quality of sleep")

    # set up the date basis for all of the plots
    date_idx = pd.date_range(start='2024-01-01', end='2026-12-31', freq='D')
    base_df = pd.DataFrame({
        'date': date_idx.date
      , 'idx': range(len(date_idx))}).set_index('date')
    plot_df = base_df[base_df.index >= dt.date(2025,1,1)]

    st.subheader("Kiwi Treatment Days")
    # Check if experiments date table exist
    if not table_exists(DB, 'experiment'):

        # Generate random days if they don't exist (run experiment over the next three months)
        days = pd.date_range(dt.date.today(), periods = 91, freq = 'D')
        df = pd.DataFrame({'values': np.random.choice([1, 2], size=len(days)), 'date': days})
        df = df.set_index('date')

        # Save experiments date table to database
        df.to_sql('experiment', CONNECTION_STRING, index=True)

    # retrieve the experiments dates
    kiwi_df = retrieve_query("SELECT * FROM experiment;").set_index('date')
    kiwi_df = plot_df.join(kiwi_df)[['values']]

    if table_exists(DB, 'treatment'):
        treatment = retrieve_query("SELECT * FROM treatment;").set_index('date')
        kiwi_df = kiwi_df.join(treatment)
        kiwi_df.loc[~kiwi_df['treatment'].isnull(),'values'] = 4

    # All future experiment days should be a different color
    kiwi_df.loc[(kiwi_df.index.date >= dt.date.today()) & (kiwi_df['values'] > 1), 'values'] = 3
    kiwi_df['values'] = kiwi_df['values'].astype('float64')
    values = kiwi_df['values']

    # Apply random days to calendar
    # --- Grey if prior to or after the experiment
    # --- Light Green if Kiwi taken (past)
    # --- Dark Green if Kiwi Supposed to be taken (future)
    # --- White if Kiwi Not Taken
    # --- Red for days missed
    colors = [
        'whitesmoke'
      , 'darkgreen'
      , 'lightgreen'
      , 'red']
    labels = [
        'No Kiwi'
      , 'Kiwi Eaten'
      , 'Planned Kiwi'
      , 'Forgot Kiwi']
    custom_cmap = ListedColormap(colors, N=len(colors))
    fig, ax = calplot.calplot(
        values
      , fillcolor='lightgrey'
      , linecolor='lightgrey'
      , dropzero=False
      , edgecolor='black'
      , cmap=custom_cmap
      , vmin=1
      , vmax=4
      , colorbar=False)

    legend = plt.legend()
    legend.set_visible(False)

    for i in range(len(colors)):
        plt.plot([], [], c=custom_cmap.colors[i], label=labels[i])

    plt.legend(bbox_to_anchor=(0,2.75), loc='upper left', ncols=4)
    st.pyplot(fig=fig)

    # input kiwi data
    # choose model
    # visualize errors
    # visualize features

    with st.form(key='my_form'):

        left_col, right_col = st.columns(
            [0.7, 0.3]
          , vertical_alignment='bottom')

        with left_col:
            forgot_date = st.selectbox(
                "Did you forget to eat a kiwi for any of these days?"
                , (kiwi_df.index[kiwi_df['values'] == 2]).date
                , index=None
                , placeholder="Forgotten Date")

        with right_col:
            submitted = st.form_submit_button(label="Submit Information")

        if submitted:
            st.write(f"{forgot_date} is being removed from the database.")
            kiwi_df.loc[kiwi_df.index.date==forgot_date, 'values'] = 4
            treatment = kiwi_df[kiwi_df['values'] == 4]
            treatment['treatment'] = True
            treatment[['treatment']].to_sql('treatment', CONNECTION_STRING, index=True, if_exists='replace')
            time.sleep(3)
            st.rerun()



    # Generate Data For Sleep Duration Visualizations
    query = """
    select
        date::date date
      , deep_sleep_duration / 60.0 / 60.0 deep_sleep_duration
      , light_sleep_duration / 60.0 / 60.0  light_sleep_duration
      , rem_sleep_duration / 60.0 / 60.0 rem_sleep_duration
      , total_sleep_duration / 60.0 / 60.0  total_sleep_duration
      , row_number() over (partition by date order by total_sleep_duration desc) rn
    from sleep
    where type = 'long_sleep'
    """

    total_sleep_df = retrieve_query(query)
    total_sleep_df['date'] = pd.to_datetime(total_sleep_df['date'])
    total_sleep_df = total_sleep_df.set_index('date')
    total_sleep_df = total_sleep_df.astype({el: float for el in total_sleep_df.columns})
    total_sleep_df = total_sleep_df[total_sleep_df['rn'] == 1]
    total_sleep_df = base_df.join(total_sleep_df)
    kiwi_df_tmp = kiwi_df.copy().reset_index()
    kiwi_df_tmp.index = kiwi_df_tmp['date'].apply(lambda el: el + relativedelta(days=1))
    kiwi_df_tmp = kiwi_df_tmp.drop('date', axis=1)
    total_sleep_df = total_sleep_df.join(kiwi_df_tmp)
    total_sleep_df = total_sleep_df.drop('idx', axis=1)

    total_sleep_df['total_sleep_duration_28d'] = create_rolling_28D_average(total_sleep_df['total_sleep_duration'].values)
    total_sleep_df['deep_sleep_duration_28d'] = create_rolling_28D_average(total_sleep_df['deep_sleep_duration'].values)
    total_sleep_df['rem_sleep_duration_28d'] = create_rolling_28D_average(total_sleep_df['rem_sleep_duration'].values)

    total_sleep_df = plot_df.join(total_sleep_df)
    total_sleep_df = total_sleep_df[total_sleep_df.index.date <= dt.date.today()]

    st.subheader("Last Night's Sleep Statistics")
    yesterday = dt.date.today() + relativedelta(days= -1)
    todays_sleep = total_sleep_df[total_sleep_df.index.date == dt.date.today()]
    total_sleep = todays_sleep['total_sleep_duration'].iloc[0]
    deep_sleep = todays_sleep['deep_sleep_duration'].iloc[0]
    rem_sleep = todays_sleep['rem_sleep_duration'].iloc[0]

    def time_convert(time_float):
        hours = int(np.floor(time_float))
        minutes = int(np.floor((time_float - hours) * 60))
        return hours, minutes

    st.text(f"""
    Last Night's Summary Statistics ({dt.date.today()}):
      - Total Sleep Duration: {time_convert(total_sleep)[0]} hrs and {time_convert(total_sleep)[1]} minutes
      - REM Sleep Duration: {time_convert(rem_sleep)[0]} hrs and {time_convert(rem_sleep)[1]} minutes
      - Deep Sleep Duration: {time_convert(deep_sleep)[0]} hrs and {time_convert(deep_sleep)[1]} minutes
    """)

    st.subheader("Sleep Duration and Quality Visualizations")

    sleep_dimension = st.selectbox(
        "Choose Sleep Dimension"
      , options = [
            'Total Sleep'
          , 'Deep Sleep'
          , 'REM Sleep'
        ])

    params = {
        'Total Sleep': {
            'label': 'total_sleep'
          , 'good': 8
          , 'bad': 6
        }
      , 'Deep Sleep': {
            'label': 'deep_sleep'
          , 'good': 1.5
          , 'bad': 1
        }
      , 'REM Sleep': {
            'label': 'rem_sleep'
          , 'good': 2
          , 'bad': 1.5
        }
    }

    label = params[sleep_dimension]['label']
    good = params[sleep_dimension]['good']
    bad = params[sleep_dimension]['bad']

    # Generate total sleep data summary and plots
    st.markdown(f"##### {sleep_dimension}")

    mean_sleep = total_sleep_df[f'{label}_duration'][-91:].mean()
    current_hours = np.floor(mean_sleep)
    current_minutes = np.floor((mean_sleep - current_hours) * 60)

    target_hours = np.floor(good)
    target_minutes = np.floor((good - target_hours) * 60)

    st.write(f"The average hours of {sleep_dimension} in the last 91 days is {current_hours:.0f} hours and {current_minutes:.0f} minutes. "
             f"The {sleep_dimension} goal is {target_hours:.0f} hours and {target_minutes:.0f} minutes")

    fig, ax = calplot.calplot(
        data=total_sleep_df[f'{label}_duration']
      , fillcolor='whitesmoke'
      , linecolor='lightgrey'
      , dropzero=True
      , edgecolor='black'
      , cmap='RdYlGn'
      , vmin=bad
      , vmax=good)
    st.pyplot(fig=fig)

    fig, ax = plt.subplots(1, figsize=(8, 1.25))
    ax = plot_minutes_to_target(
        total_sleep_df[f'{label}_duration_28d']
      , good
      , kiwi_df[~kiwi_df['values'].isna()].index.min()
      , ax
      , 120)
    st.pyplot(fig=fig, width='content')

    st.subheader("T-Test Visualizations")

    fig, ax = plt.subplots(1, figsize=(8, 4))
    tmp = total_sleep_df[~total_sleep_df[f'{label}_duration'].isna()]
    control = tmp[f'{label}_duration'][tmp['values'] != 2].values
    experiment = tmp[f'{label}_duration'][tmp['values'] == 2].values

    # Perform independent samples t-test
    t_statistic, p_value = stats.ttest_ind(control, experiment)
    st.write(f"T-statistic: {t_statistic:.2f}")
    st.write(f"P-value: {p_value:.4f}")

    bins = ax.hist(control
      , bins=20
      , color='grey'
      , edgecolor='grey'
      , density=True
      , alpha=.4)

    ax.hist(experiment
      , bins=bins[1]
      , color='lightgreen'
      , edgecolor='green'
      , density=True
      , alpha=.4)

    ax.yaxis.set_label_position("right")
    ax.set_facecolor('whitesmoke')
    ax.yaxis.tick_right()
    ax.tick_params(
        axis='both',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        right=False,
        labelbottom=True,
        labelsize=7)
    ax.set_title(
        f'Distribution of {sleep_dimension} Duration [hours]'
      , loc='left'
      , size=7)
    st.pyplot(fig=fig, width='content')

    st.subheader("Modelling Visualizations")

def create_kpi_plot():
    q = f"""
    with payment_schedule as (
        select *
        from expenses_metadata
        where status = 'payback')

      , tbl as (
        select
            rd.report_date
          , sum(1) transactions
          , sum(payback_amount) payback_amount
        from report_dates rd
        left join payment_schedule ps
          on rd.report_date between ps.date and ps.final_payment_date
        where period_name = '01 Day'
        group by 1)

    select
        report_date
      , sum(1) over (order by report_date) days
      , {ALLOWANCE} allowance
      , {ALLOWANCE} * sum(1) over (order by report_date) total_allowances
      , -1 * payback_amount expenses
      , -1 * sum(payback_amount) over (order by report_date) total_expenses
    from tbl
    """

    df = retrieve_query(q)
    df['total_allowances'] = df['total_allowances'].astype('float')

    # declare working variables
    today = dt.datetime.today().date()
    dates = df['report_date'].array
    today_idx = np.where(dates == today)[0][0]
    allowances = df['total_allowances'].array
    expenses = df['total_expenses'].array
    current_allowance = allowances[today_idx]
    current_expenses = expenses[today_idx]
    overbudget = current_allowance - current_expenses

    fig, ax = plt.subplots(figsize=(10, 6))
    # plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    ax.plot(dates
             , allowances
             , color='green'
             , linewidth=1
             , linestyle='--')
    # plt.plot(df['report_date'], df['total_expenses'],)
    ax.fill_between(dates, np.minimum(expenses, allowances), color='green', alpha=0.2)
    ax.fill_between(dates, allowances, np.maximum(expenses, allowances), color='red', alpha=0.2)

    plt.title(f'2025 Expenses vs. ${YEARLY_ALLOCATION / 1000:.0f}K Budget\n'
              , loc='Left'
              , fontsize=15
              , fontweight='bold')

    plt.ylabel('Spend Amount\n', fontsize=12)

    # Add grid with custom style
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    # Customize ticks
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.ylim(0, YEARLY_ALLOCATION)
    plt.xlim(dates[0], dates[-1])

    # Format as percentage with one decimal place
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, ylabel: '' if y == 0 else f'${y / 1000:.0f}K'))

    plt.axvline(x=today, ymin=0, ymax=expenses[today_idx] / YEARLY_ALLOCATION, color='grey', linestyle='--',
                label=f"Spend vs. Budget: ${overbudget:,.0f}")
    plt.legend()

    return fig, ax


def create_over_under_plot():
    q = f"""
    with payment_schedule as (
        select *
        from expenses_metadata
        where status = 'payback')

    select
        rd.report_date
      , sum(1) transactions
      , sum(payback_amount) payback_amount
    from report_dates rd
    left join payment_schedule ps
      on rd.report_date between ps.date and ps.final_payment_date
    where period_name = '01 Day'
    group by 1
    """

    df = retrieve_query(q)
    # df = df.head(100)
    df['payback_amount'] = df['payback_amount'].astype('float')
    df['allowance'] = ALLOWANCE
    df['balance'] = df['allowance'] + df['payback_amount']

    # declare working variables
    today = dt.datetime.today().date()
    df = df[df['report_date'] <= today]
    dates = df['report_date'].array
    balances = df['balance'].array
    total = df['balance'].cumsum().array

    fig, ax1 = plt.subplots(figsize=(10, 6))
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    plt.bar(dates
            , [el if el < 0 else 0 for el in balances]
            , color='red'
            , alpha=.5
            , edgecolor='black'
            , linewidth=1)

    plt.bar(dates
            , [el if el > 0 else 0 for el in balances]
            , color='green'
            , alpha=.5
            , edgecolor='black'
            , linewidth=1)

    ax2 = ax1.twinx()
    ax2.plot(dates
             , total
             , color='black'
             , linewidth=.5)

    origin = [0 for el in total]
    ax2.fill_between(dates, origin, total, where=total >= origin, color='green', alpha=0.2, interpolate=True)
    ax2.fill_between(dates, origin, total, where=total <= origin, color='red', alpha=0.2, interpolate=True)

    plt.title(f'2025 Expenses over / under Daily Allowance (${ALLOWANCE:.0f})\n'
              , loc='Left'
              , fontsize=15
              , fontweight='bold')

    plt.ylabel('Spend Amount\n', fontsize=12)

    # Add grid with custom style
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    # Customize ticks
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.xlim(dates[0], dates[-1])

    # Format as percentage with one decimal place
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, ylabel: '' if y == 0 else f'${y:.0f}'))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, ylabel: '' if y == 0 else f'${y:.0f}'))

    plt.tight_layout()
    plt.show()
    return fig, ax1, ax2

def create_over_under_plot_short():
    q = f"""
    with payment_schedule as (
        select *
        from expenses_metadata
        where status = 'payback')

    select
        rd.report_date
      , sum(1) transactions
      , sum(payback_amount) payback_amount
    from report_dates rd
    left join payment_schedule ps
      on rd.report_date::date between ps.date::date and ps.final_payment_date::date
    where period_name = '01 Day'
    group by 1
    """

    df = retrieve_query(q)
    # df = df.head(100)
    df['payback_amount'] = df['payback_amount'].astype('float')
    df['allowance'] = ALLOWANCE
    df['balance'] = df['allowance'] + df['payback_amount']

    # declare working variables
    today = dt.datetime.today().date()
    df = df[df['report_date'] <= today]
    df = df.tail(15)
    dates = df['report_date'].array
    balances = df['balance'].array
    total = df['balance'].cumsum().array

    fig, ax1 = plt.subplots(figsize=(10, 6))
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    plt.bar(dates
            , [el if el < 0 else 0 for el in balances]
            , color='red'
            , alpha=.5
            , edgecolor='black'
            , linewidth=1)

    plt.bar(dates
            , [el if el > 0 else 0 for el in balances]
            , color='green'
            , alpha=.5
            , edgecolor='black'
            , linewidth=1)

    ax1.plot(dates
             , total
             , color='black'
             , linewidth=.5)

    origin = [0 for el in total]
    ax1.fill_between(dates, origin, total, where=total >= origin, color='green', alpha=0.2, interpolate=True)
    ax1.fill_between(dates, origin, total, where=total <= origin, color='red', alpha=0.2, interpolate=True)

    plt.title(f'2025 Expenses over / under Daily Allowance (${ALLOWANCE:.0f})\n'
              , loc='Left'
              , fontsize=15
              , fontweight='bold')

    plt.ylabel('Spend Amount\n', fontsize=12)

    # Add grid with custom style
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    # Customize ticks
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.xlim(dates[0], dates[-1])

    # Format as percentage with one decimal place
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, ylabel: '' if y == 0 else f'${y:.0f}'))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, ylabel: '' if y == 0 else f'${y:.0f}'))

    plt.tight_layout()
    return fig, ax1, ax2

def summary_statistics():
    q = f"""
    select
        description
      , payback_period
      , ('{TODAY}' - date) + 1 days_paid
      , payback_amount
      , ('{TODAY}' - date + 1) * payback_amount amount_paid
      , amount - ('{TODAY}' - date + 1) * payback_amount amount_due
      , amount
      , date
      , final_payment_date
    from expenses_metadata
    where status = 'payback'
      and '{TODAY}' between date and final_payment_date
    """

    ongoing_expenses = retrieve_query(q)

    total_expenses = ongoing_expenses.shape[0]
    remaining_expenses = ongoing_expenses['amount_due'].sum()
    daily_allotment = ongoing_expenses['payback_amount'].sum()

    q = f"""
    with payment_schedule as (
        select *
        from expenses_metadata
        where status = 'payback')

      , tbl as (
        select
            rd.report_date
          , sum(1) transactions
          , sum(payback_amount) payback_amount
        from report_dates rd
        left join payment_schedule ps
          on rd.report_date between ps.date and ps.final_payment_date
        where period_name = '01 Day'
        group by 1)

      , agg as (
        select
            report_date
          , sum(1) over (order by report_date) days
          , {ALLOWANCE} allowance
          , {ALLOWANCE} * sum(1) over (order by report_date) total_allowances
          , -1 * payback_amount expenses
          , -1 * sum(payback_amount) over (order by report_date) total_expenses
        from tbl)

      , first_positive_date as (
        select min(days) days
        from agg
        where report_date >= '{TODAY}'
          and total_allowances > total_expenses)

    select 
        report_date
      , 'today' dim
      , days
      , allowance
      , total_allowances
      , expenses
      , total_expenses
    from agg
    where report_date = '{TODAY}'
    union
    select
        a.report_date
      , 'balanced' dim
      , a.days
      , a.allowance
      , a.total_allowances
      , a.expenses
      , a.total_expenses
    from agg a
    inner join first_positive_date fpd
      on a.days = fpd.days
    ;
    """

    days_to_balance = retrieve_query(q)
    current_date = days_to_balance['days'].iloc[0]
    balanced_date = days_to_balance['days'].iloc[1]

    st.text(
    f"""
    There are {total_expenses} expenses being paid off
    There is ${remaining_expenses:,.0f} in total expenses outstanding
    ${-1 * daily_allotment:.2f} is paid to outstanding expenses daily
    """)

def daily_expense_breakdown():
    # declare working variables

    query_date = from_date(dt.datetime.today().date())  # today
    # query_date = from_date(dt.today().date() + relativedelta(days=-1)) # yesterday
    # query_date = '2025-08-15' # fixed date

    q = f"""
    select
        description
      , payback_period
      , ('{query_date}' - date) + 1 days_paid
      , payback_amount
      , ('{query_date}' - date + 1) * payback_amount amount_paid
      , amount - ('{query_date}' - date + 1) * payback_amount amount_due
      , amount
      , date
      , final_payment_date
    from expenses_metadata
    where status = 'payback'
      and '{query_date}' between date and final_payment_date
    """

    ongoing_expenses = retrieve_query(q)

    # Set plot variables
    date = to_date(query_date)
    remaining_spend = ALLOWANCE + ongoing_expenses['payback_amount'].sum()
    remaining_spend_legend = remaining_spend
    remaining_spend = remaining_spend if remaining_spend > 0 else 0
    plot_df = ongoing_expenses[['date', 'description', 'payback_amount']]
    plot_df['payback_amount'] = plot_df['payback_amount'] * -1
    plot_df['color'] = ['grey' if el != date else 'red' for el in plot_df['date'].values.flatten()]
    plot_df['rank'] = [3 if el != date else 2 for el in plot_df['date'].values.flatten()]
    new_row_values = [date, 'remaining_spend', remaining_spend, 'green', 1]
    plot_df.loc[len(plot_df)] = new_row_values

    plot_df = plot_df.sort_values(['rank', 'payback_amount'], ascending=[False, True])
    payback_amount = plot_df['payback_amount'].values.flatten()
    payback_amount_sum = payback_amount.cumsum()
    color = plot_df['color'].values.flatten()

    fig, ax = plt.subplots(figsize=(10, 6))
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    # plot
    ax.barh([.5 for _ in range(len(payback_amount))]
            , width=payback_amount
            , height=1
            , left=payback_amount_sum - payback_amount
            , color=color
            , alpha=.2
            , edgecolor='black'
            , linewidth=1)

    # Add title
    plt.title(f'Daily Expense Breakdown: {query_date}\n'
              , loc='Left'
              , fontsize=15
              , fontweight='bold')

    # Remove Grid Lines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # Customize ticks
    ax.set_yticks([])

    # Format as percentage with one decimal place
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda y, ylabel: '' if y == 0 else f'${y:.0f}'))

    plt.axvline(x=ALLOWANCE, ymin=0, ymax=1, color='grey', linestyle='--',
                label=f"Remaining to Spend ${remaining_spend_legend:,.0f}")
    plt.legend()

    plt.tight_layout()
    return fig, ax

def top_50_expenses():
    q = """
        select
            date
                , description
                , amount
        from expenses_metadata
        where status = 'payback'
        order by abs(amount) desc
            limit 50 \
        """

    df = retrieve_query(q)
    st.write(df)

def expenses_being_paid_off():
    query_date = from_date(dt.datetime.today().date())  # today
    # query_date = from_date(dt.today().date() + relativedelta(days=-1)) # yesterday
    # query_date = '2025-08-15' # fixed date

    q = f"""
    select
        description
      , payback_period
      , ('{query_date}' - date) + 1 days_paid
      , payback_amount
      , ('{query_date}' - date + 1) * payback_amount amount_paid
      , amount - ('{query_date}' - date + 1) * payback_amount amount_due
      , amount
      , date
      , final_payment_date
    from expenses_metadata
    where status = 'payback'
      and '{query_date}' between date and final_payment_date
    """

    ongoing_expenses = retrieve_query(q)
    display_df = ongoing_expenses[['date', 'description', 'amount', 'amount_due', 'final_payment_date']].sort_values(
        'amount_due')
    display_df['amount_due'] = display_df['amount_due'].apply(lambda el: f'${-1 * el:,.0f}')
    display_df['amount'] = display_df['amount'].apply(lambda el: f'${-1 * el:,.0f}')
    st.write(display_df)

def expenses_in_last_week():
    today = dt.datetime.today().date()
    q = f"""
    select
        date
      , description
      , amount
    from expenses_metadata
    where status = 'payback'
      and date between '{today - relativedelta(days=14)}' and '{today}'
    order by date
    limit 50
    """
    st.write(retrieve_query(q))

def pending_expenses():
    q = """
        select
            date
                , description
                , amount
        from expenses_metadata
        where status = 'pending'
            limit 10 \
        """

    pending_expenses = retrieve_query(q)
    total_pending_amount = pending_expenses['amount'].sum()
    total_pending_expenses = pending_expenses['amount'].count()

    st.write(f"There are {total_pending_expenses} expenses pending. These expenses represent ${-1 * total_pending_amount:,.0f}")
    st.write(pending_expenses.sort_values('amount'))

def launch_dashboard(pth):
    subprocess.run(['streamlit', 'run',pth])

def new_dashboard():
    print('test')

def current_date_total_spend(date):
    q = f"""
    select 
        sum(days_paid_back * payback_amount) payback_amount
    from (
    select 
        case when final_payment_date::date < '{date}'::date 
             then final_payment_date::date
             else '{date}'::date end - date + 1 days_paid_back
      , payback_amount
    from expenses_metadata
    where status = 'payback'
      and date <= '{date}') ali
    """
    df = retrieve_query(q)
    return df['payback_amount'].iloc[0]

def amount_allocated_to_payback(date):
    q = f"""
    select sum(payback_amount) payback_amount
    from expenses_metadata
    where status = 'payback'
      and '{date}' between date and final_payment_date
    """
    df = retrieve_query(q)
    return -1 * df['payback_amount'].sum()

def total_historical_spend(date):
    return total_historical_spend

if __name__ == '__main__':
    USER_NAME = 'rubicon'
    DB = 'kpi'
    CONNECTION_STRING = f'postgresql+psycopg2://{USER_NAME}@localhost:5432/{DB}'

    # Allowance Figures
    YEARLY_ALLOCATION = 72000
    ALLOWANCE = 72000 / 365
    TODAY = dt.datetime.now().date()

    st.header("KPI")
    st.write("""
    tldr; We are trying to influence daily spending habits to meet yearly spending goals.
    
    After failing to meet spending goals since 2012, I resist all forms of financial self control. 
    Instead of focusing on will-power I have built yet another budgeting app. This app works with the allowance system. Yearly spending goals are broken down into
    daily spend amounts and large expenses are amortized over varying periods of time. This allows the user a
    better understanding of how daily spending patterns impact yearly spending goals. 
    """)

    YESTERDAY = TODAY - dt.timedelta(days=1)
    payback_amount = np.array([amount_allocated_to_payback(TODAY), amount_allocated_to_payback(YESTERDAY)])
    total_spend = np.array([current_date_total_spend(TODAY), current_date_total_spend(YESTERDAY)])
    day_of_year = ((TODAY - dt.datetime(TODAY.year, 1, 1).date()).days + 1)
    expected_spend = np.array([day_of_year * ALLOWANCE, day_of_year * ALLOWANCE - ALLOWANCE])
    difference_to_expected_spend = expected_spend + total_spend
    available_to_spend = ALLOWANCE - payback_amount

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Available For Spend Today:"
          , value=f'${round(available_to_spend[0], 2):.2f}')
    with col2:
        st.metric("Contribution to Payback Expenses:"
          , value=f'${round(payback_amount[0], 2):.2f}'
          , delta=f'${round(payback_amount[0] - payback_amount[1], 2):.2f}'
          , delta_color='inverse')
    with col3:
        st.metric("Difference to Spending Goal:"
          , value=f'${round(difference_to_expected_spend[0], 2):,.2f}'
          , delta=f'${round(difference_to_expected_spend[0] - difference_to_expected_spend[1], 2):,.2f}'
          , delta_color='normal')

    st.subheader("Today's Expenses")
    fig, ax = daily_expense_breakdown()
    st.pyplot(fig=fig)

    st.subheader('Recent Expenses')
    expenses_in_last_week()

    st.subheader('Expenses Being Paid Off')
    summary_statistics()
    expenses_being_paid_off()

    st.subheader('Largest Expenses')
    top_50_expenses()

    st.subheader('Pending Expenses')
    pending_expenses()

    st.subheader('Progress Against Spending Goals')
    tab1, tab2 = st.tabs(['Cumulative', 'Local'])
    with tab1:
        fig, ax = create_kpi_plot()
        st.pyplot(fig=fig)
    with tab2:
        fig, ax1, ax2 = create_over_under_plot()
        st.pyplot(fig=fig)

