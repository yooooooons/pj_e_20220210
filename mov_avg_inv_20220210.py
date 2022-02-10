#!/usr/bin/env python
# coding: utf-8

# In[1]:


import time
import pyupbit
import datetime
import pandas as pd
import numpy as np
import warnings

import matplotlib.pyplot as plt


# In[2]:


pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)


# In[3]:


check_currency = 'KRW'

candle_count = 77
candle_type = '30min'

avg_duration_1 = 5
avg_duration_2 = 15

LIST_coin_candi = ['KRW-BTC', 'KRW-LSK', 'KRW-STEEM', 'KRW-GRS', 'KRW-QKC', 'KRW-TFUEL', 'KRW-STPT', 'KRW-HIVE', 'KRW-BORA', 'KRW-JST', 'KRW-META', 'KRW-SAND']

ratio_close_cri = 1.01
now_m_prior_ratio_close_cri = 1.01
ma_ratio_1_cri = 1.001
ma_ratio_2_cri = 1.001
ma1_m_ma2_cri = 0
multiple_cri = 1
vol_ratio_cri = 2


invest_ratio = 0.015   # 보유 금액의 최대 몇 % 를 투자할것인가 (예> 0.1 <-- 보유금액 10% 투자)
coin_interest_profit_ratio = 1.01   # 시뮬레이션 결과, 최근 이익율이 얼마 이상인것 대상으로 투자 검토할지 설정
dramatic_rise = 0.01   # 최근 n개 candle 기준, 한 candle에 (dramatic_rise * 100) % 이상 상승한 이력이 있으며, 매수 진행 안함
cut_off_open_price = 200   # open 가격이 얼마 이하인 것은 투자 대상에서 제외 (가격이 낮은것은 한 가격단위만 비싸게 구매해도 비율면에서 크게 올라감)

buy_margin = 0   # 몇 '거래단위' 가격 상승까지 매수가격으로 수용하여 매수하겠는가?   (예> 1 <-- BTC 거래단위인 5000원 x 1 단위까지 높은 가격으로 매수, 즉 현재가 75,000,000이면 75,005,000까지 매수)

sell_auto = 0.005   # 매수가 대비 몇 % 이상 하락했을때, candle 추이와 관계없이 자동 매도 하겠는가? (예> 0.02 <--- 2% 이상 상승시 자동 매도
sell_force = 0.01   # 매수가 대비 몇 % 이상 하락했을때, candle 추이와 관계없이 강제 매도 하겠는가? (예> 0.03 <--- 3% 이상 하락시 강제 매도
sell_one_candle_force = 0.01   # 한 candle 안에서 하락폭이 해당 candle의 open 가격 대비 일정 비율 보다 클때 강제 매도

transaction_fee_ratio = 0.0005   # 거래 수수료 비율

time_factor = 9   # 클라우드 서버 시차보정 (구글 클라우드 : time_factor = 9)

# ------------------------------------------------------------------------------------------------------------------------

transaction_fee_ratio = 0.0005   # 매수 수수료 설정 (0.0005 <-- 수수료 0.05%)

if candle_type == '1min' :
    candle_adapt = 'minute1'
    time_unit = 1
elif candle_type == '3min' :
    candle_adapt = 'minute3'
    time_unit = 3
elif candle_type == '5min' :
    candle_adapt = 'minute5'
    time_unit = 5
elif candle_type == '10min' :
    candle_adapt = 'minute10'
    time_unit = 10
elif candle_type == '15min' :
    candle_adapt = 'minute15'
    time_unit = 15
elif candle_type == '30min' :
    candle_adapt = 'minute30'
    time_unit = 30
elif candle_type == '60min' :
    candle_adapt = 'minute60'
    time_unit = 60
elif candle_type == '240min' :
    candle_adapt = 'minute240'
    time_unit = 240


# In[4]:


access_key = "eziU49y9cSYp6BFEu8Vu8yEwk0AAZIxn1o0ya7Bp"
secret_key = "mjkWq13cmg1XE38l9xK7x80XhcIsyChHrmyx3IVe"

upbit = pyupbit.Upbit(access_key, secret_key)


# In[5]:


'''
tickers = pyupbit.get_tickers()

LIST_coin_KRW = []

for i in range (0, len(tickers), 1):
    if tickers[i][0:3] == 'KRW':
        LIST_coin_KRW.append(tickers[i])
        
LIST_check_coin_currency = []

for i in range (0, len(LIST_coin_KRW), 1):
    LIST_check_coin_currency.append(LIST_coin_KRW[i][4:])


    
LIST_check_coin_currency_2 = []

for i in range (0, len(LIST_check_coin_currency), 1) :
    temp = 'KRW-' + LIST_check_coin_currency[i]
    LIST_check_coin_currency_2.append(temp)
'''


# In[6]:


# 이동평균선 구하기 + 후보 DF filter용 파라미터 설정
def moving_avg_trend (DF_input) :
    Series_moving_avg_1 = DF_input['close'].rolling(window = avg_duration_1).mean()
    Series_moving_avg_2 = DF_input['close'].rolling(window = avg_duration_2).mean()
    
    DF_moving_avg_1 = Series_moving_avg_1.to_frame(name='close_avg_1')
    DF_moving_avg_2 = Series_moving_avg_2.to_frame(name='close_avg_2')
    
    DF_moving_avg_1['prior_close_avg_1'] = DF_moving_avg_1['close_avg_1'].shift(1)
    DF_moving_avg_1['ma_ratio_1'] = DF_moving_avg_1['close_avg_1'] / DF_moving_avg_1['prior_close_avg_1']
    
    DF_moving_avg_2['prior_close_avg_2'] =  DF_moving_avg_2['close_avg_2'].shift(1)
    DF_moving_avg_2['ma_ratio_2'] = DF_moving_avg_2['close_avg_2'] / DF_moving_avg_2['prior_close_avg_2']
    
    DF_input['prior_close'] = DF_input['close'].shift(1)
    DF_input['ratio_close'] = DF_input['close'] / DF_input['prior_close']
    DF_input['prior_ratio_close'] = DF_input['ratio_close'].shift(1)
    DF_input['now_m_prior_ratio_close'] = DF_input['ratio_close'] / DF_input['prior_ratio_close']
    
    DF_input['day_after_ratio'] = DF_input['ratio_close'].shift(-1)
    
    DF_input['high_m_open'] = DF_input['high'] - DF_input['open']
    DF_input['high_m_open2'] = DF_input['high'] / DF_input['open']
    DF_input['high_m_open_ratio'] = (DF_input['high'] - DF_input['open']) / DF_input['high_m_open'].mean()
    DF_input['day_after_high_m_open2'] = DF_input['high_m_open2'].shift(-1)
    DF_input['day_after_high_m_open_ratio'] = DF_input['high_m_open_ratio'].shift(-1)
    
    DF_input['vol_ratio'] = DF_input['volume'] / DF_input['volume'].mean()
    
    DF_concat = pd.concat([DF_input,DF_moving_avg_1],axis=1)
    DF_concat = pd.concat([DF_concat,DF_moving_avg_2],axis=1)
    
    DF_concat['ma1_m_ma2'] = DF_concat['close_avg_1'] - DF_concat['close_avg_2']
    DF_concat['multiple'] = DF_concat['ratio_close'] * DF_concat['ma_ratio_1'] * DF_concat['ma_ratio_2']
    
    return DF_concat


# In[7]:


# 잔고 조회, 현재가 조회 함수 정의

def get_balance(target_currency):   # 현급 잔고 조회
    """잔고 조회"""
    balances = upbit.get_balances()   # 통화단위, 잔고 등이 Dictionary 형태로 balance에 저장
    for b in balances:
        if b['currency'] == target_currency:   # 화폐단위('KRW', 'KRW-BTC' 등)에 해당하는 잔고 출력
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_balance_locked(target_currency):   # 거래가 예약되어 있는 잔고 조회
    """잔고 조회"""
    balances = upbit.get_balances()   # 통화단위, 잔고 등이 Dictionary 형태로 balance에 저장
    for b in balances:
        if b['currency'] == target_currency:   # 화폐단위('KRW', 'KRW-BTC' 등)에 해당하는 잔고 출력
            if b['locked'] is not None:
                return float(b['locked'])
            else:
                return 0
    return 0

def get_avg_buy_price(target_currency):   # 거래가 예약되어 있는 잔고 조회
    """평균 매수가 조회"""
    balances = upbit.get_balances()   # 통화단위, 잔고 등이 Dictionary 형태로 balance에 저장
    for b in balances:
        if b['currency'] == target_currency:   # 화폐단위('KRW', 'KRW-BTC' 등)에 해당하는 잔고 출력
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0
    return 0


def get_current_price(invest_coin):
    """현재가 조회"""
    #return pyupbit.get_orderbook(tickers=invest_coin)[0]["orderbook_units"][0]["ask_price"]
    return pyupbit.get_current_price(invest_coin)

#price = pyupbit.get_current_price("KRW-BTC")


# In[8]:


#upbit.get_balances()


# In[9]:


#int(upbit.get_balances()[1]['avg_buy_price'])


# In[10]:


investable_budget = get_balance(check_currency) * invest_ratio
(investable_budget * (1 - transaction_fee_ratio)) / get_current_price('KRW-TFUEL')


# In[11]:


bought_state = 0
bought_volume = 0
avg_bought_price = 0


# In[12]:


while True :
    
    now = datetime.datetime.now() + datetime.timedelta(seconds = (time_factor * 3600))   # 클라우드 서버와 한국과의 시간차이 보정 (9시간)
    print ('now :', now)
    
    # 매수 영역
    if (bought_state == 0) & ((now.minute % time_unit == 0) & (52 < (now.second % 60) <= 57)) :   # N시 : time_unit : 52초 ~ N시 : time_unit : 57초 사이 시각이면
        
        print ('current_aseet_status\n', upbit.get_balances())
        
        for coin_i in LIST_coin_candi :
            print ('\n [[[[[[[[[[[[ coin ]]]]]]]]]] :', coin_i)
            DF_inform = pyupbit.get_ohlcv(coin_i, count = candle_count, interval = candle_adapt)
            print ('DF_target :\n', DF_inform)
            DF_mov_avg = moving_avg_trend (DF_inform)
            print ('DF_mov_avg :\n', DF_mov_avg)
                        
            if ((DF_mov_avg['ratio_close'][-2] >= ratio_close_cri) &             (DF_mov_avg['now_m_prior_ratio_close'][-2] >= now_m_prior_ratio_close_cri) &             (DF_mov_avg['ma_ratio_1'][-2] >= ma_ratio_1_cri) &             (DF_mov_avg['ma_ratio_2'][-2] >= ma_ratio_2_cri) &             (DF_mov_avg['ma1_m_ma2'][-2] >= ma1_m_ma2_cri) &             (DF_mov_avg['multiple'][-2] >= multiple_cri) &             (DF_mov_avg['vol_ratio'][-2] >= vol_ratio_cri)) :
                
                print ('$$$$$ [{0}] buying_transaction is coducting $$$$$'.format(coin_i))
                
                investable_budget = get_balance(check_currency) * invest_ratio
                #bought_volume = (investable_budget * (1 - transaction_fee_ratio)) / get_current_price(coin_i)
                
                transaction_buy = upbit.buy_market_order(coin_i, investable_budget)   # 시장가로 매수
                # transaction_buy = upbit.buy_limit_order(bought_coin, bought_price, bought_volume)
                time.sleep(10)
                print ('buy_transaction_result :', transaction_buy)
                print ('time : {0}  /  bought_target_volume : {1}  /  bought_volume_until_now : {2}'.format((datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))), bought_volume, get_balance(coin_i[4:])))
                
                #bought_price = get_balance(coin_i[4:])['avg_buy_price']
                for k in range(0, len(upbit.get_balances()), 1) :
                    if upbit.get_balances()[k]['currency'] == coin_i[4:] :
                        bought_price =  int(upbit.get_balances()[k]['avg_buy_price'])
                print ('bought_price : ', bought_price)
                bought_state = 1
                
                # 매도 영역
                while ((datetime.datetime.now().minute % time_unit) < (time_unit -1)) :
                    if get_current_price(coin_i) >= (bought_price * (1 + sell_auto + transaction_fee_ratio)) :   # 자동 매도 가격보다 현재가격이 상승하게되면 
                        transaction_sell = upbit.sell_market_order(coin_i, get_balance(coin_i[4:]))   # 시장가에 매도
                        print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
                        print ('sell_transaction_result :', transaction_sell)
                        bought_state = 0
                        
                        break   # 자동 매도 완료시 while 문 탈출
                                                     
                                                     
                    if get_current_price(coin_i) <= bought_price * (1-sell_one_candle_force) :   # 강제 매도 가격 이하로 현재가격이 하락하게 되면
                            transaction_sell = upbit.sell_market_order(coin_i, get_balance(coin_i[4:0]))   # 시장가에 매도
                            print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
                            print ('sell_transaction_result :', transaction_sell)
                            bought_state = 0
                            
                            break   # 강제 매도시 while 문 탈출
                    
                    time.sleep(5)
                
                transaction_sell = upbit.sell_market_order(coin_i, get_balance(coin_i[4:0]))   # 한 time_unit내에 자동 또는 강제 매도가 안되어, 시장가에 매도
                print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
                print ('sell_transaction_result :', transaction_sell)
                bought_state = 0
                
            time.sleep(1)
            
    time.sleep(1)
                


# In[ ]:


DF_test = pyupbit.get_ohlcv('KRW-BTC', count = candle_count, interval = candle_adapt)

DF_test2 = moving_avg_trend (DF_test)


# In[ ]:


DF_test2.iloc[-2:-1]['ratio_close'].values


# In[ ]:


DF_test2['ratio_close'][-2]


# In[ ]:


'''

while True:
    
    try:
        
        now = datetime.datetime.now() + datetime.timedelta(seconds = (time_factor * 3600))   # 클라우드 서버와 한국과의 시간차이 보정 (9시간)
        print ('bought_state : {0}   / now : {1}'.format(bought_state, now))
        
        
        if (now.minute % time_unit == 0) & (52 < (now.second % 60) <= 57) :   # N시:00:02초 ~ N시:00:07초 사이 시각이면
            balances2 = upbit.get_balances()
            print ('current_aseet_status\n', balances2)
 
         
        # 매수 영역
        if (bought_state == 0) & ((now.minute % time_unit == 0) & (52 < (now.second % 60) <= 57)) :   # N시:00:02초 ~ N시:00:07초 사이 시각이면
            
            DF_preliminary_target_coin, LIST_preliminary_target_coin = target_coin_with_rise_No ()
            #print ('LIST_preliminary_target_coin\n :', LIST_preliminary_target_coin)
            
            investing_trial_No = 0
            while (investing_trial_No < len(LIST_preliminary_target_coin)) :
                
                DF_last = pyupbit.get_ohlcv(LIST_preliminary_target_coin[investing_trial_No][0], count = candle_count, interval = candle_adapt)
                DF_check, buying_inter = rise_tagging(DF_last, LIST_preliminary_target_coin[investing_trial_No][1])
                #print ('DF_check\n' , DF_check)
                last_succesive_rise_No = DF_check['successive_rise'][-2]
                print ('investing_trial_No : {0}_____coin : {1}  / successive_rise_No : {2}  / dec_acept_No : {3}  ==> last_succesive_rise_No : {4} '.format(investing_trial_No, LIST_preliminary_target_coin[investing_trial_No][0], LIST_preliminary_target_coin[investing_trial_No][1], LIST_preliminary_target_coin[investing_trial_No][2], last_succesive_rise_No))
             
                if ((last_succesive_rise_No == LIST_preliminary_target_coin[investing_trial_No][1]) & (buying_inter != 2)):
                    
                    print ('$$$$$ buying_transaction is coducting $$$$$')
                    bought_coin = LIST_preliminary_target_coin[investing_trial_No][0]
                    bought_opt_successive_rise_No = LIST_preliminary_target_coin[investing_trial_No][1]
                    bought_dec_acept_No = LIST_preliminary_target_coin[investing_trial_No][2]
                    check_coin_currency = LIST_preliminary_target_coin[investing_trial_No][0][4:]
                    #target_coin = LIST_preliminary_target_coin[investing_trial_No][0]
                    #opt_succesive_rise_No = LIST_preliminary_target_coin[investing_trial_No][1]
                
                    investing_trial_No = investing_trial_No + len(LIST_preliminary_target_coin)   # 매수 조건을 만족하므로, 더이상 다른 코인 / rise_NO / dec_No 만족여부 확인이 불필요 하므로, 이번 턴만 하고 빠져나감
                    
                    temp_current_price = get_current_price(bought_coin)
                    
                    if temp_current_price >= 1000000 :  # 200만원 이상은 거래단위가 1000원, 100~200만원은 거래단위가 500원이지만 편의상 200만원 이상과 함께 처리
                        unit_factor = -3
                        unit_value = 1000
                    elif temp_current_price >= 100000 :
                        unit_factor = -2
                        unit_value = 50
                    elif temp_current_price >= 10000 :
                        unit_factor = -1
                        unit_value = 10
                    elif temp_current_price >= 1000 :
                        unit_factor = -1
                        unit_value = 5
                    elif temp_current_price >= 100 :
                        unit_factor = 0
                        unit_value = 1
                    else :
                        temp_current_price <= 100   # 100원 미만은 별도로 code에서 int형이 아닌 float형으로 형변환 해줘야함
                        unit_factor = 1
                        unit_value = 0.1
                    
                    
                    bought_price = temp_current_price + ((buy_margin -1) * unit_value)
                    investable_budget = get_balance(check_currency) * invest_ratio
                    bought_volume = (investable_budget * (1 - transaction_fee_ratio)) / bought_price
                    transaction_buy = upbit.buy_limit_order(bought_coin, bought_price, bought_volume)
                    time.sleep(5)
                    print ('buy_transaction_result :', transaction_buy)
                    print ('time : {0}  /  bought_target_volume : {1}  /  bought_volume_until_now : {2}'.format((datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))), bought_volume, get_balance(check_coin_currency)))
                    buy_time = datetime.datetime.now().hour
                    time.sleep(10)
            
                    while ((datetime.datetime.now().minute % time_unit) < (time_unit -1)) :   # 한번에 매수 물량 전체가 매수가 안될것을 고려하여, 1 time unit 동안은 매수 시도 유지
                        print ('time : {0}  /  bought_target_volume : {1}  /  bought_volume_until_now : {2}'.format((datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))), bought_volume, get_balance(check_coin_currency)))
                        #print ('bought_state : {0}  /  now_in buiyng_loop : {1}'.format(bought_state, (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600)))))
                        
                        time.sleep(5)   # 너무 많은 요청이 발생하면 Error 발생, 시간차를 두어 error 방지
                        
                        if get_balance(check_coin_currency) >= (0.9 * bought_volume) :
                            print ('bought_target_volume is (almost) bought')
                            bought_state = 1
                            break   # 매수 계획 물량이 실제 매수 되었으면 while 문 탈출
                        
                        if get_current_price(bought_coin) <= bought_price * (1-sell_one_candle_force) :   # 만약 매수 시도 시간(1 time_unit) 중간에, 하락 수용 가능 수준 이상으로 하락하게 되면
                            transaction_sell = upbit.sell_market_order(bought_coin, get_balance(check_coin_currency))   # 시장가에 매도
                            print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
                            print ('sell_transaction_result :', transaction_sell)
                            bought_state = 0
                            
                            break   # 강제 매도시 while 문 탈출
                            
                
                    time.sleep(3)
            
                    print ('transaction_buy_cancel is considering')
                    transaction_buy_cancel = upbit.cancel_order(transaction_buy['uuid'])   # 1시간 매수 시간 동안에도 매수가 미수에 그치면 매수 중단
                    time.sleep(10)
                    print ('transaction_buy_cancel is considering')
                    transaction_buy_cancel = upbit.cancel_order(transaction_buy['uuid'])   # 1시간 매수 시간 동안에도 매수가 미수에 그치면 매수 중단
                
                else :
                    investing_trial_No = investing_trial_No + 1   # 다른 코인 / rise_NO / dec_No 만족여부 확인을 위해 숫자 1 증가
                    
    
        if ((get_balance(check_coin_currency) == 0) & (get_balance_locked(check_coin_currency) == 0)) :
            bought_state = 0
            print ('Last tried coin : {0} ___ bought_state is 0'.format(check_coin_currency))
        
        else :
            bought_state = 1
            print ('Last tried coin : {0} ___ bought_state is 1'.format(check_coin_currency))

 
    
        # 일반 매도 영역

        if (bought_state == 1) :
            if (now.minute % time_unit == 0) & (52 < (now.second % 60) <= 57) :
                #DF_last = pyupbit.get_ohlcv(bought_coin, count = candle_count, interval = candle_adapt)
                DF_last = pyupbit.get_ohlcv(bought_coin, count = candle_count, interval = candle_adapt)
                DF_check, buying_inter2 = rise_tagging(DF_last, bought_opt_successive_rise_No)
                last_succesive_rise_No = DF_check['successive_rise'][-2]
                print ('last_succesive_rise_No : ', last_succesive_rise_No)
            
                if last_succesive_rise_No == (bought_opt_successive_rise_No - bought_dec_acept_No) :   # 기준 수준 이상으로 하락이 연속되면
                    transaction_sell = upbit.sell_market_order(bought_coin, get_balance(check_coin_currency))   # 시장가에 매도
                    print ('bought_state : {0}  / now_in selling_check mode : {1}'.format(bought_state, (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor * 3600)))))
                    print ('sell_transaction_result\n :', transaction_sell)
                    time.sleep(time_unit * 60)
                    bought_state = 0
                
                
        # 특이 매도 영역
        # 1) 매수가 대비 하락폭이 일정 비율 보다 클때 강제 매도     
        if (bought_state == 1) :
            if (get_current_price(bought_coin) <= bought_price * (1-sell_force)) :   # 하락폭이 기준수준보다 크다면
                transaction_sell = upbit.sell_market_order(bought_coin, get_balance(check_coin_currency))   # 시장가에 매도
                print ('bought_state : {0}  / now_in FORCED selling_check mode : {1}'.format(bought_state, (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor * 3600)))))
                print ('sell_transaction_result :', transaction_sell)
                time.sleep(time_unit * 60)
                bought_state = 0
            
        # 2) 한 candle 안에서 하락폭이 해당 candle의 open 가격 대비 일정 비율 보다 클때 강제 매도
        if (bought_state == 1) :
            DF_one_candle_check = pyupbit.get_ohlcv(bought_coin, count = 5, interval = candle_adapt)
            if (get_current_price(bought_coin) <= ((1 - sell_one_candle_force) * DF_one_candle_check.iloc[-1]['open'])) :
                transaction_sell = upbit.sell_market_order(bought_coin, get_balance(check_coin_currency))   # 시장가에 매도
                print ('bought_state : {0}  / now_in one_candle FORCED selling_check mode : {1}'.format(bought_state, (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor * 3600)))))
                print ('sell_transaction_result :', transaction_sell)
                time.sleep(time_unit * 60)
                bought_state = 0
            
        # 3) 매수가 대비 상승폭이 일정 비율 보다 클때 자동 매도       
        if (bought_state == 1) :
            if (get_current_price(bought_coin) >= bought_price * (1 + sell_auto)) :   # 상승폭이 기준수준보다 크다면
                transaction_sell = upbit.sell_market_order(bought_coin, get_balance(check_coin_currency))   # 시장가에 매도
                print ('bought_state : {0}  / now_in AUTO selling_check mode : {1}'.format(bought_state, (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor * 3600)))))
                print ('sell_transaction_result :', transaction_sell)
                time.sleep(time_unit * 60)
                bought_state = 0
    
        time.sleep(1)
    
    
    
    except Exception as e:
        print('ERROR')
        time.sleep(1)
'''


# In[ ]:





# In[ ]:





# In[ ]:




