import os, requests, threading, json
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

DATASET = 'dataset'
TEMP_DOCX = os.path.join(DATASET, 'TEMP.docx')
TEMP_DOCX = os.path.abspath(TEMP_DOCX)
if not os.path.exists(DATASET):
    os.mkdir(DATASET)

ROOMS_DB = os.path.join(DATASET, 'room.csv')
if not os.path.exists(ROOMS_DB):
    with open(ROOMS_DB, 'w') as writer:
        writer.write('Room No.,Floor,Status')

CUSTOMER_DB = os.path.join(DATASET, 'customer.csv')
if not os.path.exists(CUSTOMER_DB):
    with open(CUSTOMER_DB, 'w') as writer:
        writer.write('id,Name,Address,Phone,Id Type,Id Detail')

REGISTER_DB = os.path.join(DATASET, 'register.csv')
if not os.path.exists(REGISTER_DB):
    with open(REGISTER_DB, 'w') as writer:
        writer.write('id,customer_id,room,ac,checkin,checkout,rpd')

TRANSACTION_DB = os.path.join(DATASET, 'transaction.csv')
if not os.path.exists(TRANSACTION_DB):
    with open(TRANSACTION_DB, 'w') as writer:
        writer.write('register_id,datetime,amount,mode,description')

PENDING_DB = os.path.join(DATASET, 'pending.json')
if not os.path.exists(PENDING_DB):
    with open(PENDING_DB, 'w') as writer:
        writer.write('[]')
def get_rooms():
    df = pd.read_csv(ROOMS_DB, index_col=False)
    df.sort_values(by='Floor', axis=0, ascending=True, inplace=True, na_position='first')
    return df.to_dict(orient='records')

def get_room_details(room_no):
    df = pd.read_csv(REGISTER_DB, index_col=False)
    df['checkout'] = df['checkout'].fillna('')
    df = df[(df["room"] == room_no) & (df['checkout'] == '')]
    if not df.empty:
        df.reset_index(drop=True, inplace=True)
        customer_id = df.loc[0, 'customer_id']
        df2 = pd.read_csv(CUSTOMER_DB, index_col=False)
        df2 = df2[df2['id'] == customer_id]
        df2.reset_index(drop=True, inplace=True)
        return {
            'id': df.loc[0, 'id'],
            'name': df2.loc[0, 'Name'],
            'phone': df2.loc[0, 'Phone'],
            'address': df2.loc[0, 'Address'].replace('||', '\n').replace('|', ','),
            'id_type': df2.loc[0, 'Id Type'],
            'id_detail': df2.loc[0, 'Id Detail'],
            'rpd': df.loc[0, 'rpd'],
            'check_in': df.loc[0, 'checkin'],
            'ac': df.loc[0, 'ac'],
        }
    else:
        return {}


def floor_wise():
    df = pd.read_csv(ROOMS_DB, index_col=False)
    x = len(df['Floor'].unique())
    floor = [[] for i in range(x)]
    for idx, val in df.iterrows():
        floor[val['Floor']].append(val.values)
    return floor

def update_room(room_no, status):
    df = pd.read_csv(ROOMS_DB, index_col=False)
    df['Room No.'] = df['Room No.'].astype(str)
    room_match = df[(df['Room No.']) == str(room_no)]
    if room_match.empty:
        print(f"No room with number {room_no} found.")
    df.loc[df['Room No.'] == str(room_no), 'Status'] = status
    df.to_csv(ROOMS_DB, index=False)

def add_data(file, data):
    df = pd.read_csv(file, index_col=False)
    df.loc[len(df)] = data
    df.to_csv(file, index=False)

def update_data(file, query, data):
    df = pd.read_csv(file, index_col=False)
    df = df.fillna('')
    idx = df.query(query).index
    for i in idx:
        df.loc[i] = data
    df.to_csv(file, index=False)

def update_checkout(room_no, time):
    df = pd.read_csv(REGISTER_DB, index_col=False)
    df['checkout'] = df['checkout'].fillna('')
    df.loc[(df['checkout'].str.strip() == '') & (df['room'] == room_no), 'checkout'] = time
    df.to_csv(REGISTER_DB, index=False)

def search_query(file, query):
    df = pd.read_csv(file, index_col=False)
    df = df.fillna('')
    df = df.astype(str)
    temp = df.columns
    df.columns = [col.replace(' ', '_').replace('.', '_') for col in df.columns]
    df.query(query, inplace=True, engine='python')
    df.columns = temp
    return df.to_dict(orient='records')

def search_customer_(name='', phone='', id_type='', id_details=''):
    df = pd.read_csv(CUSTOMER_DB, index_col=False)
    df = df.astype(str)
    df = df[(df['Name'].str.lower().str.startswith(name.lower())) & (df['Phone'].str.lower().str.startswith(phone.lower())) & (df['Id Type'].str.lower().str.contains(id_type.lower())) & (df['Id Detail'].str.lower().str.contains(id_details.lower()))]
    return df.to_dict(orient='records')

def get_next_id(file, id_col = 'id'):
    df = pd.read_csv(file, index_col=False)
    if not df.empty:
        return df[id_col].max() + 1
    else:
        return 1

def get_data(file):
    df = pd.read_csv(file, index_col=False)
    return df.to_dict(orient='records')

def total_balance(mode):
    df = pd.read_csv(TRANSACTION_DB, index_col=False)
    df['amount'] = df['amount'].astype(int)
    if mode != '':
        return pd.Series(df.loc[(df['mode'].str.lower() == mode.lower()) & (df['register_id'] != -1), 'amount']).sum() - pd.Series(df.loc[(df['mode'].str.lower() == mode.lower()) & (df['register_id'] == -1), 'amount']).sum()
    return pd.Series(df['amount']).sum()

def payment_info():
    # Load the data
    df = pd.read_csv(REGISTER_DB, index_col=False)
    df2 = pd.read_csv(CUSTOMER_DB, index_col=False)
    df3 = pd.read_csv(TRANSACTION_DB, index_col=False)
    
    # Step 1: Join register with customer
    register_customer = df.merge(df2, left_on='customer_id', right_on='id', suffixes=('_register', '_customer'))

    # Step 2: Join the result with transaction
    final_df = df3.merge(register_customer, left_on='register_id', right_on='id_register', how='left')
    final_df['Name'] = final_df['Name'].fillna('Credit')
    final_df['room'] = final_df['room'].fillna('-1')

    # Step 3: Select the desired columns
    result = final_df[['Name', 'room', 'amount', 'datetime', 'mode']]
    result['room'] = result['room'].astype(int)
    return result.to_dict(orient='records')
    
def get_amount_paid(reg_id):
    df = pd.read_csv(TRANSACTION_DB, index_col=False)
    return pd.Series(df.loc[df['register_id'] == reg_id, 'amount']).sum()

def add_to_pending(data):
    db = json.load(open(PENDING_DB, 'r'))
    db.append(data)
    json.dump(db, open(PENDING_DB, 'w'))

def generate_report(date):
    df = pd.read_csv(REGISTER_DB, index_col=False)
    df = df[(df['checkin'].str.contains(date)) | (df['checkout'].isna())]

    df2 = pd.read_csv(CUSTOMER_DB, index_col=False)
    df2['Address'] = df2['Address'].str.replace('|', ',')

    final_df = df.merge(df2, how='left', left_on='customer_id', right_on='id', suffixes=('_register', '_customer'))
    docx = Document()
    header1 = docx.add_heading('Hotel Maheswari Inn')
    header1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header1.style.font.size = Pt(36) # type: ignore
    header2 = docx.add_heading('Behind Bus Stand, Malkangiri, Odisha', level=3)
    header2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header2.style.font.size = Pt(24) # type: ignore
    docx.add_paragraph(f'Date: {date}', ).paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    table = docx.add_table(rows=len(final_df) + 1, cols=6)
    table.style = 'Table Grid'
    table.rows[0].cells[0].text = 'Sl. No.'
    table.rows[0].cells[1].text = 'Name & Address'
    table.rows[0].cells[2].text = 'Check In'
    table.rows[0].cells[3].text = 'Phone'
    table.rows[0].cells[4].text = 'Id Type'
    table.rows[0].cells[5].text = 'Id Detail'
    for idx, row in final_df.iterrows():
        idx_int = int(idx) # type: ignore
        table.rows[idx_int + 1].cells[0].text = str(idx_int + 1) # pyright: ignore[reportOperatorIssue]
        table.rows[idx_int + 1].cells[1].text = row['Name'] + '\n' + row['Address']
        table.rows[idx_int + 1].cells[2].text = '-'.join(row['checkin'].split('T')[0].split('-')[::-1]) + '\n' + row['checkin'].split('T')[1]
        table.rows[idx_int + 1].cells[3].text = str(row['Phone'])
        table.rows[idx_int + 1].cells[4].text = row['Id Type']
        table.rows[idx_int + 1].cells[5].text = str(row['Id Detail'])
        table.rows[idx_int + 1].cells[0].width = Inches(0.5)
        table.rows[idx_int + 1].cells[1].width = Inches(3)
        table.rows[idx_int + 1].cells[2].width = Inches(2.5)
        table.rows[idx_int + 1].cells[3].width = Inches(0.5)
        table.rows[idx_int + 1].cells[4].width = Inches(0.5)
        table.rows[idx_int + 1].cells[5].width = Inches(0.5)
    docx.save(TEMP_DOCX)


def _discord_post(json):
    try:
        res = requests.post('https://discord.com/api/webhooks/1395845186579337346/dO0YR0eM1ApLnQqdUyDn1-W1tx2Rqsa89BO2leZD8uL3l1zOEYhNdwOCZ1eohkl6UD23', json=json, timeout=5)
        if res.status_code == 204:
            return 'Success'
        else:
            add_to_pending(json)
            return 'Error'
    except requests.exceptions.Timeout as err:
        add_to_pending(json)
        return 'No Internet Connection / Link not found'
    except Exception as err:
        add_to_pending(json)
        return 'error'

def discord_post(json):
    threading.Thread(None, _discord_post, '', (json, )).start()

if __name__ == '__main__':
    pass