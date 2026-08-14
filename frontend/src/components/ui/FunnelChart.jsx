import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import axios from "axios";

const COLORS = ["#3b82f6", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444"];

export function FunnelChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    axios.get("/api/analytics/funnel").then((r) => {
      setData(
        Object.entries(r.data).map(([stage, value]) => ({
          stage,
          value,
        }))
      );
    });
  }, []);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical">
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="stage" width={90} tick={{ fontSize: 12 }} />
        <Tooltip />
        <Bar dataKey="value" radius={4}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
