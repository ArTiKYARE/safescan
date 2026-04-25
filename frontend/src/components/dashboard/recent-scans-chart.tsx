'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface RecentScansChartProps {
  data: number[];
}

export function RecentScansChart({ data }: RecentScansChartProps) {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const chartData = days.slice(0, Math.max(data.length, 7)).map((day, index) => ({
    day,
    scans: data[index] || 0,
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="day"
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={{ stroke: '#1e293b' }}
          />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={{ stroke: '#1e293b' }}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111827',
              border: '1px solid #1e293b',
              borderRadius: '8px',
              color: '#fff',
            }}
            labelStyle={{ color: '#9ca3af' }}
            formatter={(value: number) => [`${value} scans`, 'Scans']}
          />
          <Bar
            dataKey="scans"
            fill="#6366f1"
            radius={[4, 4, 0, 0]}
            maxBarSize={40}
          />
        </BarChart>
      </ResponsiveContainer>
      {data.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-gray-500 text-sm">No scan data available</p>
        </div>
      )}
    </div>
  );
}
