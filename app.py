import bs4
import requests
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import plotly.express as px
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go


# 수익률 = (당월말 종가 - 전월말 종가) / 전월말 종가

def get_beautiful_soup(url, params):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    headers = {
                'Host': 'data.krx.co.kr',
                'Connection': 'keep-alive',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8',
    }
    return bs4.BeautifulSoup(requests.get(url, headers=headers, params=params).text, "lxml")
 
def post_beautiful_soup(url, payload):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    return bs4.BeautifulSoup(requests.post(url, headers=headers, data=payload).text, "lxml")

def maxworkdt_command():
 
    url = 'http://data.krx.co.kr/comm/bldAttendant/executeForResourceBundle.cmd'
    params = {'baseName': 'krx.mdc.i18n.component',
              'key': 'B128.bld',
              'menuId': 'MDC0201030108'}

    MktData = get_beautiful_soup(url, params=params)
    #print(MktData)

    data = json.loads(MktData.text)
    df_result = data['result']['output'][0]['max_work_dt']
 
    return df_result

# 주가지수 조회
def idx_prc(mktType):
 
    url = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
 
    end_dd = datetime.today().strftime("%Y%m%d")
    strt_dd = (datetime.now() - relativedelta(years=20)).strftime("%Y%m%d")

    if mktType == 'KOSPI':
        param = ['코스피', '1']
    elif mktType == 'KOSDAQ':
        param = ['코스닥', '2']
    else:
        param = ['코스피', '1']
 
    payload = {
               'bld': 'dbms/MDC/STAT/standard/MDCSTAT00301',
               'tboxindIdx_finder_equidx0_7': param[0],
               'indIdx': param[1],
               'indIdx2': '001',
               'codeNmindIdx_finder_equidx0_7': param[0],
               'param1indIdx_finder_equidx0_7':'',
               'strtDd': strt_dd,
               'endDd': end_dd,
               'share': '2',
               'money': '3',
               'csvxls_isNo':'false'
    }
    MktData = post_beautiful_soup(url, payload)
    #print(MktData)
    data = json.loads(MktData.text)
 
    elevations = json.dumps(data['output'])
    day_one = pd.read_json(elevations)
    org_df = pd.DataFrame(day_one)
 
    return org_df

max_work_dt = maxworkdt_command()
#display(max_work_dt)
df_idx_prc = idx_prc(max_work_dt)
#display(df_idx_prc)

df_idx_prc['TRD_DD'] = pd.to_datetime(df_idx_prc['TRD_DD'], format="%Y/%m/%d")
df_idx_prc.sort_values('TRD_DD', inplace=True)


# 모든 row 에 대해서 월말에 해당하는 레코드만 추출
# dataframe 이 내림차순으로 정렬되어있으면 head
# 반대로 올림차순으로 정렬되어있으면 tail
df_idx_prc_eom = df_idx_prc.groupby(df_idx_prc['TRD_DD'].dt.strftime('%Y-%m')).tail(1)

df_idx_prc_eom = df_idx_prc_eom[['TRD_DD', 'CLSPRC_IDX']]

df_idx_prc_eom['YEAR'] = df_idx_prc_eom['TRD_DD'].dt.strftime('%Y')
df_idx_prc_eom['MONTH'] = df_idx_prc_eom['TRD_DD'].dt.strftime('%m')
df_idx_prc_eom['MONTH'] = df_idx_prc_eom['MONTH'].astype(int)

df_idx_prc_eom['CLSPRC_IDX'] = df_idx_prc_eom['CLSPRC_IDX'].str.replace(',', '')
df_idx_prc_eom['CLSPRC_IDX'] = df_idx_prc_eom['CLSPRC_IDX'].astype(float)
df_idx_prc_eom['CLSPRC_IDX_CHG'] = df_idx_prc_eom['CLSPRC_IDX'].pct_change()

df_idx_prc_eom['FLAG'] = np.where(df_idx_prc_eom['CLSPRC_IDX_CHG']>0, 1, -1)



fig1 = px.bar(df_idx_prc_eom,
             x="MONTH",
             y="CLSPRC_IDX_CHG",
             color='MONTH',
             barmode='stack',
             height=400)
fig2 = px.bar(df_idx_prc_eom,
             x="MONTH",
             y="FLAG",
             color='MONTH',
             barmode='group',
             height=400)


fig = make_subplots(rows=2, cols=1, shared_xaxes=False)
fig.add_trace(fig1['data'][0], row=1, col=1)
fig.add_trace(fig2['data'][0], row=2, col=1)

fig.update_layout(shapes=[dict(type='line',
                x0=0.5,
                y0=0,
                x1=12.5,
                y1=0,
                line=dict(color='Red',width=1),
                xref='x',
                yref='y'),
              dict(type='line',
                x0=0.5,
                y0=0,
                x1=12.5,
                y1=0,
                line=dict(color='Red',width=1),
                xref='x2',
                yref='y2'),]
)

fig.update_traces(width=0.3)
fig.update_layout(xaxis=dict(tickmode='linear', dtick=1),
                  xaxis2=dict(tickmode='linear', dtick=1),
                  width=800,
                  height=800)

fig.show()

st.write(df_idx_prc_eom)

