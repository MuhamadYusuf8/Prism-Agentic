import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import axios from "axios";

export function TrendsChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    axios.get("/api/analytics/trends").then((r) => {
      setData(
        r.data.map((d) => ({
          week: d.week,
          count: d.count,
        }))
      );
    });
  }, []);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <XAxis dataKey="week" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
