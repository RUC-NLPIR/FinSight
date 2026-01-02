import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from matplotlib import font_manager
import matplotlib
matplotlib.use('Agg')
import os

def draw_kline_chart(kline_data: pd.DataFrame, working_dir: str):
    font_path = "./fonts/kt_font.ttf"
    font = font_manager.FontProperties(fname=font_path, size=16)
    plt.rcParams['axes.unicode_minus'] = False

    sns.set_style("whitegrid", {
        'axes.unicode_minus': False
    })

    # Custom palette
    custom_palette = [
        "#2E86AB",  # deep blue
        "#F18F01",  # orange
        "#C73E1D",  # red-brown
        "#3B1F2B",  # deep purple
        "#6B8F71",  # muted green
    ]
    sns.set_palette(custom_palette)

    # Prepare data
    df = kline_data
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    end_date = df.index.max()
    start_date = end_date - pd.DateOffset(years=2)
    df = df.loc[start_date:end_date]

    # Create figure
    plt.figure(figsize=(14, 7), dpi=100)

    # Plot closing price series
    ax = sns.lineplot(
        data=df,
        x=df.index,
        y='close',
        linewidth=2.5,
        color=custom_palette[0],
        label='Close price',
    )

    # Title and labels
    ax.set_title(
        'Share Price Trend (Past 2 Years)',
        fontsize=16,
        pad=20,
        font=font,
        fontweight='bold'
    )
    ax.set_ylabel('Price', fontsize=12, labelpad=10, font=font)
    ax.set_xlabel('Date', fontsize=12, labelpad=10, font=font)

    # Configure x-axis format
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45, ha='right')

    # Grid/legend styling
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(
        loc='upper left',
        frameon=True,
        framealpha=0.9,
        edgecolor='white',
        prop=font
    )

    # Background and borders
    ax.set_facecolor('#F5F5F5')
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['bottom', 'left']:
        ax.spines[spine].set_color('#888888')

    # Highlight the highest and lowest points
    max_point = df['close'].idxmax()
    min_point = df['close'].idxmin()
    ax.scatter(
        x=[max_point, min_point],
        y=[df.loc[max_point, 'close'], df.loc[min_point, 'close']],
        color=[custom_palette[1], custom_palette[2]],
        s=100,
        zorder=5,
        label=['High', 'Low'],
    )

    # Annotate extremes
    ax.annotate(
        f'High: {df.loc[max_point, "close"]:.2f}',
        xy=(max_point, df.loc[max_point, 'close']),
        xytext=(10, 10),
        textcoords='offset points',
        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
        arrowprops=dict(arrowstyle='->'),
        font=font
    )

    ax.annotate(
        f'Low: {df.loc[min_point, "close"]:.2f}',
        xy=(min_point, df.loc[min_point, 'close']),
        xytext=(10, -30),
        textcoords='offset points',
        bbox=dict(boxstyle='round,pad=0.5', fc='lightblue', alpha=0.5),
        arrowprops=dict(arrowstyle='->'),
        font=font
    )

    # Layout adjustments
    plt.tight_layout()
    plt.savefig(os.path.join(working_dir, 'kline_chart.png'))
    return os.path.join(working_dir, 'kline_chart.png')