# TODO: Function which gets ask price at x time ago.
from datetime import date, datetime
import requests
import time
import json
import oandapyV20
#from oandapyV20 import API
import oandapyV20.endpoints.trades as trades
from oandapyV20.contrib.requests import MarketOrderRequest
#from oandapyV20.contrib.requests import LimitOrderRequest
#from oandapyV20.contrib.requests import StopOrderRequest
from oandapyV20.contrib.requests import TakeProfitDetails, StopLossDetails
from oandapyV20.contrib.requests import TrailingStopLossOrderRequest
from oandapyV20.contrib.requests import TradeCloseRequest
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.instruments as instruments
from oandapyV20.exceptions import V20Error, StreamTerminated
from oandapyV20.endpoints.pricing import PricingStream
from oandapyV20.endpoints.pricing import PricingInfo
import oandapyV20.endpoints.pricing as pricing 
#import oandapyV20.endpoints.forexlabs as labs


isaac_token = ""
client = oandapyV20.API(access_token=isaac_token)
accountID = ""  # Isaac Oanda AccountID


class Order:
    def __init__(self, cur_pair):
        self.cur_pair = cur_pair

    @staticmethod
    def get_all_trades():
        """Returns all open trades"""
        r = trades.TradesList(accountID)
        rv = client.request(r)
        return rv


    def get_trades(self):
        """
        Get tradeID and unit information on a trade 
        with the given cur_pair/instrument.
        Returns a list of dicts of the form:
        {'tradeID' : tradeID, 'units' : units} 
        """
        trade_list = []
        trade_response = self.get_all_trades()
        all_trades = trade_response['trades']
        for trade in all_trades:
            trade_info = {}
            tradeID, instrument, current_units = trade['id'], trade['instrument'], trade['currentUnits']
            if instrument == self.cur_pair:
                trade_info['tradeID'] = tradeID
                trade_info['units'] = current_units
            trade_list.append(trade_info)

        if not bool(trade_list):
            print("No open {} trades found!".format(self.cur_pair))
            return trade_list
        else:
            return trade_list


    def trade_exists(self, order_units):
        """
        Check if a trade with the cur_pair and order_units already exists.
        Returns True if trade exists and False if matching trade does not exist.
        """
        trade_response = self.get_trades() # List of all trades 
        for trade_dict in trade_response:
            if int(trade_dict['units']) == int(order_units):
                print("{} {} Trade already exists!".format(self.cur_pair, order_units))
                return True

        return False # if no trades in the trade_response list match the corresponding order units

    def create_market_order(self, units, take_profit, stop_loss):
        """ 
        Create a market order.
        A market order is an order that is filled immediately upon creation using the current market price.
        """
        # Create the order body
        ordr = MarketOrderRequest(
            instrument = self.cur_pair,
            units = units,
            takeProfitOnFill=TakeProfitDetails(price=take_profit).data,
            stopLossOnFill=StopLossDetails(price=stop_loss).data)
        # create the OrderCreate request
        r = orders.OrderCreate(accountID, data=ordr.data)
        try:
            # create the OrderCreate request
            rv = client.request(r)
        except oandapyV20.exceptions.V20Error as err:
            print(r.status_code, err)
        else:
            print(json.dumps(rv, indent=2))

    def get_orderID(self):
        """Get the ID for the order."""
        trades = self.get_trades()
        if trades: # Returns true if trades is non-empty
            return self.get_trades()[0]['tradeID']
        else:
            return False


    def close_order(self, tradeID, units):
        """ Close an order """
        ordr = TradeCloseRequest(units=units)
        # Create TradeClose order request
        r = trades.TradeClose(accountID, tradeID=tradeID, data=ordr.data)
        # Perform the request
        try:
            rv = client.request(r)
        except oandapyV20.exceptions.V20Error as err:
            print(r.status_code, err)
        else:
            print(json.dumps(rv, indent=2))



            

class PricingData:
    def __init__(self, cur_pair):
        self.cur_pair = cur_pair

    def get_pricing_stream(self):
        """
        Start pricing information stream for given
        currency pair.
        """
        params = {
            "instruments": self.cur_pair
        }
        r = pricing.PricingStream(accountID=accountID, params=params)
        rv = client.request(r)
        for x in rv:
            #ask_price = x['asks']
            if x['type'] == 'PRICE':
                print(x['asks'][0]['price'])
                print(x['time'])

    def get_pricing_info(self):
        """
        Returns pricing information for instant time
        function is called
        """
        params = {
            "instruments": self.cur_pair,
        }
        r = pricing.PricingInfo(accountID=accountID, params=params)
        rv = client.request(r)
        return r.response

    def get_candlestick_data(self, granularity, time_from, time_to):
        """ 
        Get candlestick data with a specified granularity (time per candle),
        from the start to end time.
        Granularity Note: S5 = 5 second candlesticks, M4 = 4 minute candlesticks, 
        H2 = 2 hour candlesticks e.t.c
        More info at: 
        https://developer.oanda.com/rest-live-v20/instrument-df/#CandlestickGranularity
        Time Note: Either uses the "RFC 3339" representation or the "Unix representation"
        E.g If today is 5th May 2020 and time is 18:05 BST then the RFC time: 
        "2020-05-23T17:05:30.457847836Z" (UTC is 1hr behind BST)
        """
        options = {
            "granularity" : granularity,
            "from" : time_from,
            "to" : time_to}
        r = instruments.InstrumentsCandles(instrument=self.cur_pair, params=options)
        client.request(r)
        response = r.response
        return response

    def get_ask_price(self):
        """Returns current ask price for cur_pair"""
        pricing_info = self.get_pricing_info()
        ask = pricing_info['prices'][0]['asks'][0]['price']
        return ask
        
    def get_bid_price(self):
        """Returns current bid price for cur_pair"""
        pricing_info = self.get_pricing_info()
        bid = pricing_info['prices'][0]['bids'][0]['price']
        return bid

    def pip_to_price(self, pips):
        """
        Returns the current ask price plus 
        or minus a given number of pips.
        """
        ask = self.get_ask_price()
        pip_price = int(pips) * 0.0001
        return round(float(ask) + pip_price, 5)



    
def main():
    cur_pair = "AUD_CAD"
    order = Order(cur_pair)
    data = PricingData(cur_pair)
    #order.create_market_order('80')
    #order.close_order('272', '80')
    #current_price = data.get_pricing_info()
    #order.create_market_order(100, data.pip_to_price(10), data.pip_to_price(-10))
    #order.close_order(orderID, '50')
    #print(data.pip_to_price(11))
    data.get_pricing_stream()


if __name__ == "__main__":
    main()
