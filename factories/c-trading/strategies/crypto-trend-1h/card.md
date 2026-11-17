# crypto-trend-1h

Written 17 November 2026, before the first test. The first strategy taken through the factory by hand.

## Idea

Hold each coin only while its price trend is up, sized so that calmer coins get more weight. Go to cash otherwise.

## Why someone would pay for this

Trend following is the best-evidenced edge in the research: prices under-react to news and investors herd, so moves persist for a while. In crypto the buyers who arrive late in a rally pay the trend follower. The known weakness is that crypto trends are concentrated in bull markets and the coins move together, so this may be little more than a cheaper way to hold the market.

## Rules

- Trend is up when the fast exponential average of the hourly close is above the slow one.
- Each coin in an uptrend gets weight in inverse proportion to its recent volatility, scaled so the weights of all ten coins sum to at most 1.
- Long only, no leverage. Decided at each hourly close, traded at the next open.

## Parameters and ranges

| Parameter | Range | Meaning |
|---|---|---|
| `fast` | 12 to 120 hours | fast average length |
| `slow` | 168 to 1000 hours | slow average length |
| `vol_window` | 72 to 720 hours | window for volatility |

## What would kill it

- It fails any of the four coded checks.
- It only works in a narrow corner of the parameter ranges.
- Its returns come from one year or one coin.

## Expected behaviour if real

Low hit rate, a few large winning runs, long flat or losing stretches in sideways markets, and far smaller drawdowns than buy and hold. Fees are high on this venue (0.25% a side), so it should trade rarely.
