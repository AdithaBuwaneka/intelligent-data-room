/**
 * ChartDisplay Component
 *
 * Renders various chart types using Recharts based on configuration.
 * Supports: bar, line, pie, scatter, area charts.
 */

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { ChartConfig } from '../types';

interface ChartDisplayProps {
  config: ChartConfig;
}

// Default color palette
const DEFAULT_COLORS = [
  '#3B82F6', // blue-500
  '#10B981', // emerald-500
  '#F59E0B', // amber-500
  '#EF4444', // red-500
  '#8B5CF6', // violet-500
  '#EC4899', // pink-500
  '#06B6D4', // cyan-500
  '#84CC16', // lime-500
];

export function ChartDisplay({ config }: ChartDisplayProps) {
  const { type, data, xKey, yKey, title, colors: configColors } = config;
  const colors = configColors && configColors.length > 0 ? configColors : DEFAULT_COLORS;

  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
        No data available for chart
      </div>
    );
  }

  const renderChart = () => {
    switch (type) {
      case 'bar':
        return renderBarChart();
      case 'line':
        return renderLineChart();
      case 'pie':
        return renderPieChart();
      case 'scatter':
        return renderScatterChart();
      case 'area':
        return renderAreaChart();
      default:
        return renderBarChart();
    }
  };

  const renderBarChart = () => {
    const yKeys = Array.isArray(yKey) ? yKey.filter(k => k) : (yKey ? [yKey] : []);
    
    if (yKeys.length === 0) {
      return (
        <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
          No data key specified for chart
        </div>
      );
    }

    const isHorizontalBars = config.layout === 'vertical';

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart 
          data={data} 
          layout={isHorizontalBars ? 'vertical' : 'horizontal'}
          margin={{ top: 20, right: 30, left: isHorizontalBars ? 100 : 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          
          {isHorizontalBars ? (
             // Horizontal Bars: Y axis is categories, X axis is numbers
             <>
               <XAxis type="number" tick={{ fontSize: 12 }} />
               <YAxis 
                 dataKey={xKey} 
                 type="category" 
                 width={90}
                 tick={{ fontSize: 12 }} 
               />
             </>
          ) : (
             // Vertical Bars (Default): X axis is categories, Y axis is numbers
             <>
               <XAxis
                dataKey={xKey}
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fontSize: 12 }} />
             </>
          )}

          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
            }}
          />
          <Legend />
          {yKeys.map((key, index) => (
            <Bar
              key={key}
              dataKey={key}
              fill={colors[index % colors.length]}
              radius={isHorizontalBars ? [0, 4, 4, 0] : [4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderLineChart = () => {
    const yKeys = Array.isArray(yKey) ? yKey.filter(k => k) : (yKey ? [yKey] : []);
    
    if (yKeys.length === 0) {
      return (
        <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
          No data key specified for chart
        </div>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
            }}
          />
          <Legend />
          {yKeys.map((key, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ fill: colors[index % colors.length], strokeWidth: 2 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const renderPieChart = () => {
    const dataKey = Array.isArray(yKey) ? yKey[0] : yKey;
    
    if (!dataKey) {
      return (
        <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
          No data key specified for chart
        </div>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey={dataKey}
            nameKey={xKey}
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={({ name, percent }) =>
              `${name}: ${(percent * 100).toFixed(1)}%`
            }
            labelLine={{ stroke: '#9CA3AF' }}
          >
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderScatterChart = () => {
    const yDataKey = Array.isArray(yKey) ? yKey[0] : yKey;
    
    if (!yDataKey) {
      return (
        <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
          No data key specified for chart
        </div>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey={xKey} tick={{ fontSize: 12 }} name={xKey} />
          <YAxis dataKey={yDataKey} tick={{ fontSize: 12 }} name={yDataKey} />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
            }}
          />
          <Scatter name="Data" data={data} fill={colors[0]}>
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    );
  };

  const renderAreaChart = () => {
    const yKeys = Array.isArray(yKey) ? yKey.filter(k => k) : (yKey ? [yKey] : []);
    
    if (yKeys.length === 0) {
      return (
        <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
          No data key specified for chart
        </div>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
            }}
          />
          <Legend />
          {yKeys.map((key, index) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[index % colors.length]}
              fill={colors[index % colors.length]}
              fillOpacity={0.3}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mt-2">
      {title && (
        <h3 className="text-sm font-medium text-gray-700 mb-4 text-center">
          {title}
        </h3>
      )}
      {renderChart()}
    </div>
  );
}

export default ChartDisplay;
