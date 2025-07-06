'use client';

import { useState } from 'react';
import { fetchSurfaceData } from '../lib/api';
import SurfacePlot3D from './(components)/SurfacePlot3D';

interface AnalysisResult {
  ticker: string;
  underlying_price: number;
  risk_free_rate: number;
  surface_data: {
    x: number[][];
    y: number[][];
    z: number[][];
  };
  market_data_points: Array<{ log_moneyness: number; T: number; implied_volatility: number }>;
  butterfly_arbitrage_signals: any[];
  calendar_arbitrage_signals: any[];
  profitable_butterfly_trades: any[];
  profitable_calendar_trades: any[];
}

export default function Home() {
  const [ticker, setTicker] = useState('');
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await fetchSurfaceData(ticker);
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold mb-8">Options Surface Analyzer</h1>
      </div>

      <div className="relative z-[-1] flex place-items-center before:absolute before:h-[300px] before:w-full before:-translate-x-1/2 before:rounded-full before:bg-gradient-radial before:from-white before:to-transparent before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-[180px] after:w-full after:translate-x-1/3 after:bg-gradient-conic after:from-sky-200 after:via-blue-200 after:blur-2xl after:content-[''] before:dark:bg-gradient-to-br before:dark:from-transparent before:dark:to-blue-700 before:dark:opacity-10 after:dark:from-sky-900 after:dark:via-[#0141ff] after:dark:opacity-40 before:lg:h-[360px] w-full">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-md">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Enter stock ticker (e.g., SPY)"
            className="p-3 border border-gray-300 rounded-md text-black focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="p-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </form>
      </div>

      <div className="mt-8 w-full max-w-5xl">
        {error && <p className="text-red-500">Error: {error}</p>}

        {data && (
          <div className="bg-gray-100 dark:bg-gray-800 p-6 rounded-md shadow-md overflow-auto">
            <h2 className="text-xl font-semibold mb-4">Analysis Result for {data.ticker}:</h2>
            <p><strong>Underlying Price:</strong> ${data.underlying_price.toFixed(2)}</p>
            <p><strong>Risk-Free Rate:</strong> {(data.risk_free_rate * 100).toFixed(2)}%</p>

            <h3 className="text-lg font-semibold mt-6 mb-2">Implied Volatility Surface:</h3>
            <SurfacePlot3D
              surfaceData={data.surface_data}
              marketDataPoints={data.market_data_points}
              ticker={data.ticker}
            />

            <h3 className="text-lg font-semibold mt-6 mb-2">Arbitrage Signals:</h3>
            {data.butterfly_arbitrage_signals.length > 0 || data.calendar_arbitrage_signals.length > 0 ? (
              <>
                {data.butterfly_arbitrage_signals.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium">Butterfly Arbitrage:</h4>
                    <ul className="list-disc pl-5">
                      {data.butterfly_arbitrage_signals.map((signal, index) => (
                        <li key={index}>
                          Expiry: {new Date(signal.expiry).toLocaleDateString()},
                          Log-Moneyness Range: [{signal.k_min.toFixed(3)}, {signal.k_max.toFixed(3)}]
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {data.calendar_arbitrage_signals.length > 0 && (
                  <div>
                    <h4 className="font-medium">Calendar Arbitrage:</h4>
                    <ul className="list-disc pl-5">
                      {data.calendar_arbitrage_signals.map((signal, index) => (
                        <li key={index}>
                          Expiries: {new Date(signal.expiry1).toLocaleDateString()} / {new Date(signal.expiry2).toLocaleDateString()},
                          Log-Moneyness Range: [{signal.k_min.toFixed(3)}, {signal.k_max.toFixed(3)}]
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <p>No arbitrage signals detected.</p>
            )}

            <h3 className="text-lg font-semibold mt-6 mb-2">Profitable Trades:</h3>
            {data.profitable_butterfly_trades.length > 0 || data.profitable_calendar_trades.length > 0 ? (
              <>
                {data.profitable_butterfly_trades.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium">Butterfly Spreads:</h4>
                    <ul className="list-disc pl-5">
                      {data.profitable_butterfly_trades.map((trade, index) => (
                        <li key={index}>
                          Expiry: {trade.expiry}, Strikes: {trade.strikes}, Profit: {trade.initial_profit_per_spread}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {data.profitable_calendar_trades.length > 0 && (
                  <div>
                    <h4 className="font-medium">Calendar Spreads:</h4>
                    <ul className="list-disc pl-5">
                      {data.profitable_calendar_trades.map((trade, index) => (
                        <li key={index}>
                          Expiries: {trade.expiries}, Strike: {trade.strike}, Credit: {trade.initial_credit_per_spread}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <p>No profitable trades found.</p>
            )}
          </div>
        )}
      </div>
    </main>
  );
}