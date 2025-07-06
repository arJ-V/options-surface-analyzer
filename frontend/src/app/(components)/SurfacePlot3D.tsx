import React from 'react';
import Plot from 'react-plotly.js';

interface SurfacePlot3DProps {
  surfaceData: {
    x: number[][];
    y: number[][];
    z: number[][];
  };
  marketDataPoints: Array<{ log_moneyness: number; T: number; implied_volatility: number }>;
  ticker: string;
}

const SurfacePlot3D: React.FC<SurfacePlot3DProps> = ({ surfaceData, marketDataPoints, ticker }) => {
  const plotData: Plotly.Data[] = [
    {
      type: 'surface',
      x: surfaceData.x,
      y: surfaceData.y,
      z: surfaceData.z,
      colorscale: 'Viridis',
      opacity: 0.8,
      showscale: false,
    },
    {
      type: 'scatter3d',
      mode: 'markers',
      x: marketDataPoints.map(p => p.log_moneyness),
      y: marketDataPoints.map(p => p.T),
      z: marketDataPoints.map(p => p.implied_volatility),
      marker: {
        size: 3,
        color: 'red',
        opacity: 0.8,
      },
      name: 'Market Data Points',
    },
  ];

  const layout: Partial<Plotly.Layout> = {
    title: `Fitted SVI Implied Volatility Surface for ${ticker}`,
    scene: {
      xaxis: { title: 'Log-Moneyness (k)' },
      yaxis: { title: 'Time to Expiration (T)' },
      zaxis: { title: 'Implied Volatility (σ)' },
    },
    autosize: true,
    margin: { l: 0, r: 0, b: 0, t: 40 },
  };

  return (
    <Plot
      data={plotData}
      layout={layout}
      style={{ width: '100%', height: '600px' }}
      useResizeHandler={true}
    />
  );
};

export default SurfacePlot3D;
