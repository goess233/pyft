import numpy as np
import pandas as pd
# import matplotlib as mpl
# import matplotlib.pyplot as plt
import akshare as ak
import datetime
import time
from itertools import product

# shfe_text = ak.match_main_contract(exchange="shfe")
TRADE_IF_LAST_WIN = True
ENTRY_FAILSAFE_BREAKOUT = 55
ENTRY_BREAKOUT = 20
ENTRY_OFFSET_ATR = 0
ADD_ATR = 0.5
STOP_ATR = 2
EXIT_BREAKOUT = 10
EXIT_OFFSET_ATR = 0
MAX_UNITS = 4
ATR_WIN = 14


# 海龟交易法，顺势交易，逆鞅方法的应用
def turtle():
    # ag_df = ak.futures_zh_minute_sina(symbol="AG0",period='60')  # 37 frames a day if period equals 15
    # end_date = datetime.datetime.today().strftime('%Y%m%d')
    # shfe_df = ak.get_futures_daily(start_date='20200101', end_date='20210115', market='shfe')
    ag_df = ak.futures_foreign_hist(symbol="XAG")
    ag_df = ag_df.iloc[-365:]
    # ag_df = shfe_df[shfe_df['symbol'] == 'AG2102']
    # ag_current_price = ak.futures_zh_spot("AG2102", market="CF").loc[0, 'current_price']
    # if ag_df['close'].iloc[-1] == '':
    #     ag_df['close'].iloc[-1] = ag_current_price
    ag_df[['open', 'high', 'low', 'close']] = ag_df[['open', 'high', 'low', 'close']].astype(float, "ignore")
    atr(ag_df)
    donchian(ag_df)
    parameters = {'long_exit1': ag_df['exit_low'].iloc[-1], 'short_exit1': ag_df['exit_high'].iloc[-1]}
    # parameters.append ag_df['entry_high']+ag_df['ATR']*ADD_ATR
    print(parameters)
    return ag_df


def atr(df):
    temp = pd.DataFrame()
    temp['tr1'] = df['high'] - df['low']
    temp['tr2'] = df['high'] - df['close'].shift(1)
    temp['tr3'] = df['low'] - df['close'].shift(1)
    df['TR'] = temp[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=ATR_WIN).mean()


def donchian(df):
    df['entry_high'] = df['high'].rolling(window=ENTRY_BREAKOUT).max()
    df['entry_low'] = df['low'].rolling(window=ENTRY_BREAKOUT).min()
    df['entry_mid'] = (df['entry_high'] + df['entry_low']) / 2
    df['exit_high'] = df['high'].rolling(window=EXIT_BREAKOUT).max()
    df['exit_low'] = df['low'].rolling(window=EXIT_BREAKOUT).min()
    # long_open,short_open


# 网格，左侧交易，适用于震荡行情，或者波动较大，同时又有上下界的品种，没有止损
def grid():
    """
    需要确定元素：
    1、网格间隔
    2、每次操作仓位
    3、止盈策略
    :return:
    """
    end_date = datetime.datetime.today()
    start_date = datetime.datetime.today() - datetime.timedelta(days=30)
    future_df = ak.get_futures_daily()
    # future_df = ak.futures_zh_minute_sina
    # todo


def get_agm():
    fdata = ak.futures_zh_spot("AG2102", market="CF")
    # subscribe_list = ak.hf_subscribe_exchange_symbol()
    # futures_hf_spot_df = ak.futures_hf_spot(subscribe_list)
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

    if int(nowdatetime.strftime("%H%M")) > 1630:
        pass
    else:
        nowdatetime = nowdatetime - datetime.timedelta(days=1)

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
    ag_rank_table_df = ak.get_shfe_rank_table(date=tradedate, vars_list=[future])
    ag = {long: 0, short: 0, long_chg: 0, short_chg: 0, vol: 0}
    for df in ag_rank_table_df.values():
        ag[vol] += df.loc[20, vol]
        ag[long] += df.loc[20, long]
        ag[short] += df.loc[20, short]
        ag[long_chg] += df.loc[20, long_chg]
        ag[short_chg] += df.loc[20, short_chg]
        stat = (ag[long] + ag[short]) / ag[vol]
        ts = (ag[long_chg] - ag[short_chg]) / np.abs(ag[long_chg] + ag[short_chg])
        # how to use TS?
        print(stat, ts)
    return ag


if __name__ == "__main__":
    # rank = spider(['AG'])
    # print("------------------------------------------------")
    # aurank = time.time_ns()
    # raw_index_df = ak.stock_zh_index_daily(symbol="sz399300")
    # sma1 = range(20, 61, 4)
    # sma2 = range(180, 281, 10)
    # results = pd.DataFrame()
    # for SMA1, SMA2 in product(sma1, sma2):
    #     data: DataFrame = pd.DataFrame(raw_index_df['close'])
    #     data.dropna(inplace=True)
    #     data['returns'] = np.log(data['close'] / data['close'].shift(1))
    #     data['sma1'] = data['close'].rolling(SMA1).mean()
    #     data['sma2'] = data['close'].rolling(SMA2).mean()
    #     data.dropna(inplace=True)
    #     data['position'] = np.where(data['sma1'] > data['sma2'], 1, 0)
    #     data['strategy'] = data['position'].shift(1) * data['returns']
    #     data.dropna(inplace=True)
    #     perf = np.exp(data[['returns', 'strategy']].sum())
    #     results = results.append(
    #         pd.DataFrame({'SMA1': SMA1, 'SMA2': SMA2, 'market': perf['returns'], 'strategy': perf['strategy']},
    #                      index=[0]), ignore_index=True)
    # print(results.info())
    # print(results.sort_values('strategy', ascending=False))
    # results.shift()
    test = turtle()
    # print(df.iloc[-1])
