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
import streamlit as st
from pykrx import stock


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


st.set_page_config(
    page_title="Korea Stock Market Information",
    page_icon=":shark:",
    layout="wide",
    initial_sidebar_state="expanded"
    )

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

#fig.show()
st.plotly_chart(fig)




df_idx_prc_eom['diff'] = df_idx_prc_eom['CLSPRC_IDX'].diff()
#df_sample = df_idx_prc_eom[(df_idx_prc_eom['TRD_DD']>='2018-01-01')&(df_idx_prc_eom['TRD_DD']<='2021-12-31')].reset_index(drop=True)
df_sample = df_idx_prc_eom[(df_idx_prc_eom['TRD_DD']>='2008-01-01')].reset_index(drop=True)
#df_sample['diff'] = np.where(df_sample['diff'].isnull(), df_sample['CLSPRC_IDX'], df_sample['diff'])
#display(df_sample)
fig11 = go.Figure(go.Waterfall(
    name = "KOSPI", orientation = "v",
    measure = ["relative", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "relative", ],
    x = df_sample['TRD_DD'],
    textposition = "outside",
    text = df_sample['CLSPRC_IDX'],
    y = df_sample['diff'],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
))

fig11.update_layout(
        title = "KOSPI 2021",
        showlegend = True,
)
fig11.update_xaxes(dtick="M1")

st.plotly_chart(fig11, use_container_width=True)


df_test = df_idx_prc_eom.copy()
st.write(df_test.sort_values(['CLSPRC_IDX_CHG']).head(10))





today = datetime.today().strftime('%Y%m%d')

df_idx = stock.get_index_fundamental("20190101", today, "1001").reset_index()
df_mkt = stock.get_market_fundamental("20190101", today, "005930").reset_index()
df_mg = df_mkt.merge(df_idx, on='날짜') 
df_mg['ratio'] = df_mg['PBR_x'] / df_mg['PBR_y'] / (df_mg['PBR_x'].head(1).values[0] / df_mg['PBR_y'].head(1).values[0])
# 리노공업 058470
# 한미반도체 042700
# SKC 011790
# 유한양행 000100
# 셀트리온 068270
# 삼성전자 005930
# 한국금융지주 071050

#df_mg = df_mg.melt(id_vars='날짜', value_vars=['PBR_x', 'PBR_y'])
#display(df_mg)


today = datetime.today().strftime('%Y%m%d')


df_idx = stock.get_index_fundamental("20100101", today, "1001").reset_index()
df_idx['1/PER'] = 1 / df_idx['PER'] * 100

avgDays = 30

df_idx['1/PER_MA'] = df_idx['1/PER'].rolling(window=avgDays).mean()
df_idx['종가_MA'] = df_idx['종가'].rolling(window=avgDays).mean()
df_idx['PBR_MA'] = df_idx['PBR'].rolling(window=avgDays).mean()

# Create figure with secondary y-axis
#fig = make_subplots(specs=[[{"secondary_y": True}]])
fig = go.Figure()

# Add traces
fig.add_trace(
    go.Scatter(x=df_idx['날짜'], y=df_idx['1/PER_MA'], name="PER Earn Rate"),
)

fig.add_trace(
    go.Scatter(x=df_idx['날짜'], y=df_idx['종가_MA'], name="KOSPI", yaxis="y2"),
)

fig.add_trace(
    go.Scatter(x=df_idx['날짜'], y=df_idx['PBR_MA'], name="PBR", yaxis="y3"),
)

# Create axis objects
fig.update_layout(
    xaxis=dict(
        domain=[0.05, 1]
    ),
    yaxis=dict(
        title="PER Earn Rate",
        titlefont=dict(
            color="#1f77b4"
        ),
        tickfont=dict(
            color="#1f77b4"
        )
    ),
    yaxis2=dict(
        title="KOSPI Index",
        titlefont=dict(
            color="#ff7f0e"
        ),
        tickfont=dict(
            color="#ff7f0e"
        ),
        anchor="free",
        overlaying="y",
        side="left",
        position=0.02
    ),
    yaxis3=dict(
        title="PBR",
        titlefont=dict(
            color="#d62728"
        ),
        tickfont=dict(
            color="#d62728"
        ),
        anchor="x",
        overlaying="y",
        side="right"
    ),
)

# Set x-axis title
fig.update_xaxes(title_text="Date")


fig.update_xaxes(dtick='M3')

#fig.show()
#display(df_idx)

st.plotly_chart(fig, use_container_width=True)
st.write(df_idx)
