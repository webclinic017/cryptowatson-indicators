from logging import exception
from typing import Dict, Tuple, Union
from datetime import datetime, date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cryptowatson_indicators.datas import FngDataSource
from cryptowatson_indicators import utils
from .band_indicator_base import BandIndicatorBase, BandDetails

# 0-25: Extreme Fear
# 26-46: Fear
# 47-54: Neutral
# 55-75: Greed
# 76-100: Extreme Greed
# _FNG_THRESHOLDS = [25,             46,        54,        75,        100]
# _FNG_NAMES = ["Extreme Fear", "Fear",    "Neutral", "Greed",   "Extreme Greed"]
# https://colordesigner.io/gradient-generator/?mode=rgb#DE2121-21DE21
# _FNG_COLORS = ["#C05840",      "#FC9A24", "#E5C769", "#B4E168", "#5CBC3C"]
# _FNG_MULTIPLIERS = [1.5,            1.25,      1,         0.75,      0.5]


class FngBandIndicator(BandIndicatorBase):
    _band_thresholds= [25,             46,        54,        75,        100]
    _band_names=      ["Extreme Fear", "Fear",    "Neutral", "Greed",   "Extreme Greed"]
    _band_colors=     ["#C05840",      "#FC9A24", "#E5C769", "#B4E168", "#5CBC3C"]
    _band_multipliers=[1.5,            1.25,      1,         0.75,      0.5]
    def __init__(self, data: Union[pd.DataFrame, None] = None, data_column: str = 'close', indicator_start_date: Union[str, date, datetime, None] = None, ticker_symbol: str = 'BTCUSDT', binance_api_key: str = '', binance_secret_key: str = ''):
        self.ticker_symbol = ticker_symbol
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key
        self.data_column = data_column

        # load indicator data
        if isinstance(data, pd.DataFrame):
            self.indicator_data = data
        else:
            self.indicator_data = FngDataSource().load().to_dataframe(start=indicator_start_date)

        if not isinstance(self.indicator_data, pd.DataFrame) or self.indicator_data.empty:
            error_message = f"FngBandIndicator.constructor: No indicator data available"
            print(f"[error] {error_message}")
            raise exception(error_message)

    def get_band_at(self, at_date: Union[str, date, datetime, None] = None, **kvargs) -> Union[int, None]:
        value_at = self.get_value_at(at_date=at_date)

        if (value_at is None or value_at < 0 or value_at > 100):
            return None

        # Get index
        band_index_at = 0
        if (0 <= value_at < self._band_thresholds[0]):
            band_index_at = 0
        elif (self._band_thresholds[0] <= value_at < self._band_thresholds[1]):
            band_index_at = 1
        elif (self._band_thresholds[1] <= value_at <= self._band_thresholds[2]):
            band_index_at = 2
        elif (self._band_thresholds[2] < value_at <= self._band_thresholds[3]):
            band_index_at = 3
        elif (self._band_thresholds[3] < value_at <= self._band_thresholds[4]):
            band_index_at = 4

        return band_index_at

    def get_band_details_at(self, at_date: Union[str, date, datetime, None] = None, **kvargs) -> Union[BandDetails, None]:
        band_index = self.get_band_at(at_date=at_date)
        
        if (band_index is None or band_index < 0 or band_index > len(self._band_names) -1):
            return None
        
        band_details_at = BandDetails()
        band_details_at.band_index=band_index
        band_details_at.band_ordinal=f"{band_index + 1}/{len(self._band_names)}",
        band_details_at.name=self._band_names[band_index]
        band_details_at.color=self._band_colors[band_index]
        band_details_at.multiplier=self._band_multipliers[band_index]

        return band_details_at

    def get_value_at(self, at_date: Union[str, date, datetime, None] = None, **kvargs) -> Union[int, None]:
        if not isinstance(self.indicator_data, pd.DataFrame) or self.indicator_data.empty:
            print(f"[warn] FngBandIndicator.get_value_at: No indicator data available")
            return None

        at_date = utils.parse_any_date(at_date)
        if not at_date:
            at_date = self.indicator_data.index.max().date()

        value_serie_at = self.indicator_data[self.indicator_data.index == pd.to_datetime(
            at_date)]
        if (value_serie_at.empty):
            print(
                f"[warn] FngBandIndicator.get_value_at: Data not found at date {at_date}")
            return None

        value_at = int(value_serie_at[self.data_column])

        return value_at


    def plot_axes(self, axes, start=None, end=None):
        plot_data = self.indicator_data
        # Filter start and end
        if start is not None:
            plot_data = plot_data[plot_data.index >= start]
        if end is not None:
            plot_data = plot_data[plot_data.index <= end]

        axes.set_ylabel('FnG Index', fontsize='medium')

        range1 = plot_data[plot_data[self.data_column].between(
            0, 25, inclusive='left')]
        range2 = plot_data[plot_data[self.data_column].between(
            25, 46, inclusive='left')]
        range3 = plot_data[plot_data[self.data_column].between(
            46, 54, inclusive='both')]
        range4 = plot_data[plot_data[self.data_column].between(
            54, 75, inclusive='right')]
        range5 = plot_data[plot_data[self.data_column].between(
            75, 100, inclusive='right')]

        axes.bar(range1.index, range1[self.data_column],
                 color='#C05840')  # , width, yerr=menStd
        axes.bar(range2.index, range2[self.data_column],
                 color='#FC9A24')  # , width, yerr=menStd
        axes.bar(range3.index, range3[self.data_column],
                 color='#E5C769')  # , width, yerr=menStd
        axes.bar(range4.index, range4[self.data_column],
                 color='#B4E168')  # , width, yerr=menStd
        axes.bar(range5.index, range5[self.data_column],
                 color='#5CBC3C')  # , width, yerr=menStd

        # Plot MA line
        # if ma_data_column is not None:
        #     axes.plot(plot_data.index, plot_data[ma_data_column],
        #             color='#000000', alpha=0.5, linewidth=1, label='FnG MA')

        # yticks
        axes.set_yticks(self._band_thresholds)
        axes.tick_params(axis='y', labelsize='x-small')

        # Grid
        axes.grid(axis = 'y', linestyle = '--', linewidth = 0.5)

        # axes.legend()

        return axes

    def __str__(self):
        return 'Fear and Greed'

    # @classmethod
    # def _get_fng_value_details(cls, value: int = -1) -> dict:
    #     if (value is None or value < 0 or value > 100):
    #         return dict()

    #     # Get index
    #     index = 0
    #     if (0 <= value < self._band_thresholds[0]):
    #         index = 0
    #     elif (self._band_thresholds[0] <= value < self._band_thresholds[1]):
    #         index = 1
    #     elif (self._band_thresholds[1] <= value <= self._band_thresholds[2]):
    #         index = 2
    #     elif (self._band_thresholds[2] < value <= self._band_thresholds[3]):
    #         index = 3
    #     elif (self._band_thresholds[3] < value <= self._band_thresholds[4]):
    #         index = 4

    #     return {
    #         'fng_index': index,
    #         'fng_ordinal': f"{index + 1}/5",
    #         'name': _FNG_NAMES[index],
    #         'color': _FNG_COLORS[index],
    #         'multiplier': _FNG_MULTIPLIERS[index],
    #     }
    
    def plot_fng(self):
        if not isinstance(self.indicator_data, pd.DataFrame) or self.indicator_data.empty:
            print(f"[warn] FngBandIndicator.plot_fng: No indicator data available")
            return None

        fig, axes = plt.subplots()

        # Consider using pivot(): https://pandas.pydata.org/pandas-docs/dev/getting_started/intro_tutorials/09_timeseries.html#datetime-as-index
        range1 = self.indicator_data[self.indicator_data[self.data_column].between(
            0, 25, inclusive='left')]
        range2 = self.indicator_data[self.indicator_data[self.data_column].between(
            25, 46, inclusive='left')]
        range3 = self.indicator_data[self.indicator_data[self.data_column].between(
            46, 54, inclusive='both')]
        range4 = self.indicator_data[self.indicator_data[self.data_column].between(
            54, 75, inclusive='right')]
        range5 = self.indicator_data[self.indicator_data[self.data_column].between(
            75, 100, inclusive='right')]

        axes.bar(range1.index, range1[self.data_column],
                 color='#C05840')  # , width, yerr=menStd
        axes.bar(range2.index, range2[self.data_column],
                 color='#FC9A24')  # , width, yerr=menStd
        axes.bar(range3.index, range3[self.data_column],
                 color='#E5C769')  # , width, yerr=menStd
        axes.bar(range4.index, range4[self.data_column],
                 color='#B4E168')  # , width, yerr=menStd
        axes.bar(range5.index, range5[self.data_column],
                 color='#5CBC3C')  # , width, yerr=menStd

        # ax.axhline(0, color='grey', linewidth=0.8)
        # axes.set_xlabel('Date')
        axes.set_ylabel('FnG')
        axes.set_title('Fear and Greed history')

        axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        # Set xticks
        fng_data_length = len(self.indicator_data)
        fng_xticks = self.indicator_data.iloc[::int(
            fng_data_length/20)].index.to_list()
        fng_xticks[0] = self.indicator_data.index.min()
        fng_xticks[-1] = self.indicator_data.index.max()

        axes.set_xticks(fng_xticks)
        plt.xticks(fontsize=8, rotation=45, ha='right')

        # Label with label_type 'center' instead of the default 'edge'
        # ax.bar_label(p1, label_type='center')
        # ax.bar_label(p2, label_type='center')
        # ax.bar_label(p2)

        plt.show()

    def plot_fng_and_ticker_price(self, ticker_data: pd.DataFrame):
        if not isinstance(self.indicator_data, pd.DataFrame) or self.indicator_data.empty:
            print(
                f"[warn] FngBandIndicator.plot_fng_and_ticker_price: No indicator data available")
            return None

        if not isinstance(ticker_data, pd.DataFrame) or ticker_data.empty:
            print(
                f"[warn] plot_fng_and_ticker_price: No data available in ticker_data")
            return None

        fig, axes = plt.subplots()
        fig.suptitle('Fear and Greed Index / BTCUSDT Price', fontsize='large')
        # fig.set_tight_layout(True)
        axes.set_ylabel('FnG Index', fontsize='medium')
        plt.xticks(fontsize='small', rotation=45, ha='right')
        plt.yticks(fontsize='small')

        # fng chart ########
        range1 = self.indicator_data[self.indicator_data[self.data_column].between(
            0, 25, inclusive='left')]
        range2 = self.indicator_data[self.indicator_data[self.data_column].between(
            25, 46, inclusive='left')]
        range3 = self.indicator_data[self.indicator_data[self.data_column].between(
            46, 54, inclusive='both')]
        range4 = self.indicator_data[self.indicator_data[self.data_column].between(
            54, 75, inclusive='right')]
        range5 = self.indicator_data[self.indicator_data[self.data_column].between(
            75, 100, inclusive='right')]

        axes.bar(range1.index, range1[self.data_column],
                 color='#C05840')  # , width, yerr=menStd
        axes.bar(range2.index, range2[self.data_column],
                 color='#FC9A24')  # , width, yerr=menStd
        axes.bar(range3.index, range3[self.data_column],
                 color='#E5C769')  # , width, yerr=menStd
        axes.bar(range4.index, range4[self.data_column],
                 color='#B4E168')  # , width, yerr=menStd
        axes.bar(range5.index, range5[self.data_column],
                 color='#5CBC3C')  # , width, yerr=menStd

        # fng ticks
        axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        # Get index positions for xticks
        fng_data_length = len(self.indicator_data)
        fng_xticks = self.indicator_data.iloc[::int(
            fng_data_length/20)].index.to_list()
        fng_xticks[0] = self.indicator_data.index.min()
        fng_xticks[-1] = self.indicator_data.index.max()

        axes.set_xticks(fng_xticks)
        axes.set_yticks([0, 25, 46, 54, 75, 100])

        # ticker chart ##########
        axes2 = axes.twinx()
        axes2.set_ylabel('Price', fontsize='medium')
        axes2.plot(ticker_data.index, ticker_data[self.data_column],
                   color='#333333', linewidth=0.75)

        # ticker ticks
        ticker_max_value = ticker_data[self.data_column].max()
        ticker_yticks = np.arange(
            0, int(ticker_max_value), int(ticker_max_value / 10))
        ticker_yticks[0] = 0
        ticker_yticks[-1] = ticker_max_value
        axes2.set_yticks(ticker_yticks)

        # horizontal line with latest ticker value
        # ticker_latest_value = ticker_data.iloc[-1, 1]
        # axes2.axhline(y=ticker_latest_value, color='#dedede', linewidth=0.5, linestyle='--', zorder=-1)

        plt.show()

    def plot_fng_and_ticker_price_2(self, ticker_data: pd.DataFrame):
        if not isinstance(self.indicator_data, pd.DataFrame) or self.indicator_data.empty:
            print(
                f"[warn] FngBandIndicator.plot_fng_and_ticker_price_2: No indicator data available")
            return None

        if not isinstance(ticker_data, pd.DataFrame) or ticker_data.empty:
            print(
                f"[warn] plot_fng_and_ticker_price: No data available in ticker_data")
            return None

        # fig, axes = plt.subplots()
        fig, (fng_axes, ticker_axes) = plt.subplots(
            nrows=2, sharex=True, subplot_kw=dict(frameon=True))
        ticker_axes2 = ticker_axes.secondary_yaxis('right')
        fig.suptitle('Fear and Greed Index / BTCUSDT Price', fontsize='large')
        # fig.set_tight_layout(True)
        fng_axes.set_ylabel('FnG Index', fontsize='medium')
        ticker_axes.set_ylabel('Price', fontsize='medium')
        plt.xticks(fontsize='small', rotation=45, ha='right')
        plt.yticks(fontsize='small')

        # fng chart ########
        merged_data = pd.merge(self.indicator_data, ticker_data,
                               how='inner', on='Date', suffixes=('FngBandIndicator', 'Ticker'))

        range1 = merged_data[merged_data['ValueFng'].between(
            0, 25, inclusive='left')]
        range2 = merged_data[merged_data['ValueFng'].between(
            25, 46, inclusive='left')]
        range3 = merged_data[merged_data['ValueFng'].between(
            46, 54, inclusive='both')]
        range4 = merged_data[merged_data['ValueFng'].between(
            54, 75, inclusive='right')]
        range5 = merged_data[merged_data['ValueFng'].between(
            75, 100, inclusive='right')]

        fng_axes.bar(range1.index, range1['ValueFng'],
                     color='#C05840')  # , width, yerr=menStd
        fng_axes.bar(range2.index, range2['ValueFng'],
                     color='#FC9A24')  # , width, yerr=menStd
        fng_axes.bar(range3.index, range3['ValueFng'],
                     color='#E5C769')  # , width, yerr=menStd
        fng_axes.bar(range4.index, range4['ValueFng'],
                     color='#B4E168')  # , width, yerr=menStd
        fng_axes.bar(range5.index, range5['ValueFng'],
                     color='#5CBC3C')  # , width, yerr=menStd

        # fng ticks
        fng_axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fng_data_length = len(self.indicator_data)
        fng_xticks = self.indicator_data.iloc[::int(
            fng_data_length/20)].index.to_list()
        fng_xticks[0] = self.indicator_data.index.min()
        fng_xticks[-1] = self.indicator_data.index.max()
        fng_axes.set_xticks(fng_xticks)
        fng_axes.set_yticks([0, 25, 46, 54, 75, 100])

        # ticker chart ##########
        ticker_axes.bar(range1.index, range1['ValueTicker'],
                        color='#C05840')  # , width, yerr=menStd
        ticker_axes.bar(range2.index, range2['ValueTicker'],
                        color='#FC9A24')  # , width, yerr=menStd
        ticker_axes.bar(range3.index, range3['ValueTicker'],
                        color='#E5C769')  # , width, yerr=menStd
        ticker_axes.bar(range4.index, range4['ValueTicker'],
                        color='#B4E168')  # , width, yerr=menStd
        ticker_axes.bar(range5.index, range5['ValueTicker'],
                        color='#5CBC3C')  # , width, yerr=menStd

        # ticker ticks
        ticker_max_value = ticker_data[self.data_column].max()
        ticker_yticks = np.arange(
            0, int(ticker_max_value), int(ticker_max_value / 10))
        ticker_yticks[0] = 0
        ticker_yticks[-1] = ticker_max_value
        ticker_axes.set_yticks(ticker_yticks)

        # ticker ticks 2
        ticker_latest_value = ticker_data.iloc[-1, 1]
        ticker_axes2.set_yticks(
            [ticker_latest_value, ticker_max_value],
            [f"today:\n{ticker_latest_value}", f"max:\n{ticker_max_value}"],
            fontsize='small'
        )

        # horizontal lines in today and max
        ticker_axes.axhline(y=ticker_latest_value, color='#dedede',
                            linewidth=0.5, linestyle='--', zorder=-1)
        ticker_axes.axhline(y=ticker_max_value, color='#dedede',
                            linewidth=0.5, linestyle='--', zorder=-1)

        plt.show()
