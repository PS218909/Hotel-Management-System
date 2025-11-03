from .util import *

def get_time_range(start_time = None, end_time = None):
    if start_time is None:
        cnt = datetime.datetime.now()
        start_month = cnt.replace(day=1)
        day = 31
        while True:
            try:
                end_month = cnt.replace(day=day)
                break
            except Exception as err:
                day -= 1
        return start_month, end_month
    elif end_time is None:
        cnt = datetime.datetime.now()
        start_month = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        end_month = cnt.replace(month=(cnt.month+1 if cnt.month != 12 else 1))
        end_month = end_month - datetime.timedelta(days=1)
        return start_month, end_month
    else:
        start_month = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        end_month = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
        return start_month, end_month

def get_time_based_df(df, col, start_time, end_time):
    end_str_time = end_time.strftime('%Y-%m-%dT%H:%M')
    df[col] = df[col].fillna(end_str_time)
    df[col] = pd.to_datetime(df[col], format='%Y-%m-%dT%H:%M')
    mask = (df[col] > start_time) & (df[col] < end_time)
    return df[mask]

def revenue_based_on_purpose(start_time = None, end_time = None):
    start_time, end_time = get_time_range(start_time, end_time)
    register_df = read_csv(REGISTER_DB)
    transaction_df = read_csv(TRANSACTIONS_DB)
    register_df = get_time_based_df(register_df, 'cin', start_time, end_time)
    transaction_df = get_time_based_df(transaction_df, 't', start_time, end_time)
    group_rid = transaction_df.groupby(by='rid')['a'].sum()
    register_df['amount_paid'] = register_df.apply(lambda x: group_rid[x['id']] if x['id'] in group_rid else 0, axis=1) # type: ignore
    group_pov = register_df.groupby('pov')['amount_paid'].sum()
    pov_similar = {
        'OFFICIAL': ['300', '448', 'OFFICE', 'OFFICIAL', 'AAM EXAM', 'JOB', 'OFFICE WORK', 'OFFICIAL VISIT', 'OFFICILA', 'EXAM', 'GOVT WORK', 'SACUT INSTRUCTION', 'SALUTE INSTRUCTION', 'SERVICE', 'SEVICE', 'COURT', 'SURVICE', 'JIO', 'JIO TOWER'],
        'BANK': ['BANK', 'BANK WORK', 'SBI', 'BANK OFFICIAL'],
        'BUSINESS': ['BIRI PATTA', 'KLAVA', 'BUSSINESS', 'PATTA', 'RICE', 'TOWER ELECTRICAL', 'VIDEO DOCUMENT SHOOT', 'CAR SALE', 'RICEMIL', 'SOLAR', 'SPEEKER SALES', 'TOWER AIRTEL', 'GARBA'],
        'HOSPITAL': ['HOSPITAL', 'MEDICAL', 'MEDICAL WORK', 'MEDICINE', 'MR MEDICINE'],
        'VISIT': ['SCHOOL VISIT', 'VIST', 'MEET', 'MEETING', 'HYDERABAD VISIT', 'REST', 'COLLEGE', 'BRANCH VISIT SFL', 'FIELD VISIT', 'HEALD VISI', 'STAT TOUR', 'VISIT MEET', 'A/C MECANIC'],
        'PERSONAL': ['PERSONAL', 'PORSANAL', '19.COMPUTER', 'GADI LENE', 'HOME WORK', 'PENTER', 'TRAINING', 'CLC'],
        'MARKETING': ['MARKETING', 'MKT', 'SURVEY', 'SERVEY'],
        'OTHER': []
    }
    for pov, amount in group_pov.items():
        if "BANK" in pov:
            pov_similar['BANK'].append(pov)
        elif "OFFI" in pov:
            pov_similar['OFFICIAL'].append(pov)
        elif "MED" in pov or "HOSP" in pov:
            pov_similar['HOSPITAL'].append(pov)
        elif "VISIT" in pov:
            pov_similar['VISIT'].append(pov)
        elif 'BUS' in pov:
            pov_similar['BUSINESS'].append(pov)
        else:
            pov_similar['OTHER'].append(pov)
    revenue = {}
    for pov, amount in group_pov.items():
        for spov in pov_similar:
            if pov.strip() in pov_similar[spov]: # type: ignore
                revenue[spov] = revenue.get(spov, 0) + amount
                break
        else:
            revenue[pov] = revenue.get(pov, 0) + amount
    return revenue

def stay_duration(start_time = None, end_time = None):
    start_time, end_time = get_time_range(start_time, end_time)
    register_df = read_csv(REGISTER_DB)
    cin = get_time_based_df(register_df, 'cin', start_time, end_time)
    cout = get_time_based_df(register_df, 'cout', start_time, end_time)
    cout = cout[~cout['id'].isin(cin['id'])]
    register_df = pd.concat([cin, cout], ignore_index=True)
    register_df['cout'] = register_df['cout'].fillna(end_time)
    register_df['cout'] = pd.to_datetime(register_df['cout'])
    register_df['stayed_for'] = register_df.apply(lambda x: (x['cout'] - x['cin']).seconds, axis=1)
    duration = register_df['stayed_for'].sum()//3600
    return duration

def customer_retention(start_time = None, end_time=None):
    start_time, end_time = get_time_range(start_time, end_time)
    register_df = read_csv(REGISTER_DB)
    register_df_cnt = set(get_time_based_df(register_df, 'cin', start_time, end_time)['cid'])
    register_df['cin'] = pd.to_datetime(register_df['cin'])
    register_df_prev = set(register_df[register_df['cin'] < start_time]['cid'])
    count = len(register_df_cnt.intersection(register_df_prev))
    return count

def new_customer(start_time = None, end_time = None):
    start_time, end_time = get_time_range(start_time, end_time)
    register_df = read_csv(REGISTER_DB)
    register_df_cnt = set(get_time_based_df(register_df, 'cin', start_time, end_time)['cid'])
    register_df['cin'] = pd.to_datetime(register_df['cin'])
    register_df_prev = set(register_df[register_df['cin'] < start_time]['cid'])
    count = len(register_df_cnt.difference(register_df_prev))
    return count

def payment_mode_breakdown(start_time = None, end_time = None):
    start_time, end_time = get_time_range(start_time, end_time)
    transaction_df = read_csv(TRANSACTIONS_DB)
    transaction_df = transaction_df[transaction_df['rid'] != -1]
    transaction_df = get_time_based_df(transaction_df, 't', start_time, end_time)
    grouped = transaction_df.groupby('m')['a'].sum()
    break_down = {}
    for mode, amount in grouped.items():
        mode = mode.lower()
        if mode.startswith('ca') or mode.startswith('cs'):
            break_down['CASH'] = break_down.get('CASH', 0) + amount
        elif mode.startswith('u'):
            break_down['UPI'] = break_down.get('UPI', 0) + amount
        else:
            break_down['OTHER'] = grouped.get('OTHER', 0) + amount
    return break_down

def revenue_generated(start_time = None, end_time = None):
    start_time, end_time = get_time_range(start_time, end_time)
    transaction_df = read_csv(TRANSACTIONS_DB)
    transaction_df = get_time_based_df(transaction_df, 't', start_time, end_time)
    transaction_df = transaction_df[transaction_df['rid'] != -1]
    return transaction_df['a'].sum()

def get_analysis(start_time = None, end_time = None, **kwargs):
    st, et = get_time_range(start_time, end_time)
    if kwargs.get('all', False):
        return {
            'start_time': st.strftime('%Y-%m-%dT00:00'),
            'end_time': et.strftime('%Y-%m-%dT00:00'),
            'revenue_based_on_purpose': revenue_based_on_purpose(start_time, end_time),
            'stay_duration': stay_duration(start_time, end_time),
            'customer_retention': customer_retention(start_time, end_time),
            'new_customer': new_customer(start_time, end_time),
            'payment_mode_breakdown': payment_mode_breakdown(start_time, end_time),
            'revenue_generated': revenue_generated(start_time, end_time)
        }