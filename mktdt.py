
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
# import baostock as bs
import akshare as ak
import datetime
import time
from itertools import product


# shfe_text = ak.match_main_contract(exchange="shfe")
from pandas import DataFrame


def get_agm():
    fdata = ak.futures_zh_spot("AG2102", market="CF")
    subscribe_list = ak.hf_subscribe_exchange_symbol()
    futures_hf_spot_df = ak.futures_hf_spot(subscribe_list)
    return fdata


def get_tick(inst):
    str_inst = str(inst)
    stock_zh_a_tick_df = ak.stock_zh_a_tick_tx_js(code="sh" + str_inst)
    return stock_zh_a_tick_df


def get_candle(inst):
    str_inst = str(inst)
    stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol="sh" + str_inst, period='1', adjust="qfq")
    return stock_zh_a_minute_df


def get_returns(sma1, sma2, index_df):
    index_df['sma1'] = index_df['close'].rolling(sma1).mean()
    index_df['sma2'] = index_df['close'].rolling(sma2).mean()
    index_p = index_df.iloc[-1500:][['close', 'sma1', 'sma2']]
    index_p['returns'] = np.log(index_p['close'] / index_p['close'].shift(1))
    index_p['position'] = np.where(index_p['sma1'] > index_p['sma2'], 1, 0)
    index_p['strategy'] = index_p['returns'] * index_p['position'].shift(1)
    index_p.dropna(inplace=True)
    print(np.exp(index_p[['returns', 'strategy']].sum()))


def spider(future):
    vol = 'vol'
    long = 'long_open_interest'
    long_chg = 'long_open_interest_chg'
    short = 'short_open_interest'
    short_chg = 'short_open_interest_chg'
    trade_calendar = ak.tool_trade_date_hist_sina()
    nowdatetime = datetime.datetime.now()

    if int(nowdatetime.strftime("%H%M"))>1630:
        pass
    else:
        nowdatetime = nowdatetime-datetime.timedelta(days=1)

    for counts in range(30):
        if nowdatetime.strftime("%Y-%m-%d") in trade_calendar['trade_date'].values:
            tradedate = nowdatetime.strftime("%Y%m%d")
            break
        else:
            nowdatetime -= datetime.timedelta(days=1)
    if counts == 29:
        print("no trade day found!")
        return

    # get_ag_sum_daily_df = ak.get_rank_sum_daily(start_day='20201209',end_day='20201210',vars_list=['AG'])
    # get_au_sum_daily_df = ak.get_rank_sum_daily(start_day='20201209',end_day='20201210',vars_list=['AU'])
    ag_rank_table_df = ak.get_shfe_rank_table(date=tradedate,vars_list=[future])
    ag = {long:0,short:0,long_chg:0,short_chg:0,vol:0}
    for df in ag_rank_table_df.values():
        ag[vol] += df.loc[20,vol]
        ag[long] += df.loc[20,long]
        ag[short] += df.loc[20,short]
        ag[long_chg] += df.loc[20,long_chg]
        ag[short_chg] += df.loc[20,short_chg]
        stat = (ag[long]+ag[short])/ag[vol]
        ts = (ag[long_chg]-ag[short_chg])/np.abs(ag[long_chg]+ag[short_chg])
    # how to use TS?
        print(stat,ts)
    return ag


if __name__ == "__main__":
    rank = spider(['AG'])
    print("------------------------------------------------")
    aurank = time.time_ns()
    raw_index_df = ak.stock_zh_index_daily(symbol="sz399300")
    sma1 = range(20,61,4)
    sma2 = range(180,281,10)
    results = pd.DataFrame()
    for SMA1, SMA2 in product(sma1, sma2):
        data: DataFrame = pd.DataFrame(raw_index_df['close'])
        data.dropna(inplace=True)
        data['returns'] = np.log(data['close'] / data['close'].shift(1))
        data['sma1'] = data['close'].rolling(SMA1).mean()
        data['sma2'] = data['close'].rolling(SMA2).mean()
        data.dropna(inplace=True)
        data['position'] = np.where(data['sma1'] > data['sma2'], 1, 0)
        data['strategy'] = data['position'].shift(1) * data['returns']
        data.dropna(inplace=True)
        perf = np.exp(data[['returns', 'strategy']].sum())
        results = results.append(
            pd.DataFrame({'SMA1': SMA1, 'SMA2': SMA2, 'market': perf['returns'], 'strategy': perf['strategy']},
                         index=[0]), ignore_index=True)
    print(results.info())
    print(results.sort_values('strategy',ascending=False))
    results.shift()
