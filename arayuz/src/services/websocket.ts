import { useCallback, useEffect, useState } from 'react';

export interface OlcumData {
  timestamp: number;
  heartRate: number;
  gsr: number;
  respiration: number;
}

export type BaglantiDurumu = 'baglaniyor' | 'bagli' | 'kapali';

const WS_URL = 'ws://localhost:8000/ws';
const MAX_NOKTA = 120;

export function useOlcumStream(active: boolean = true) {
  const [data, setData] = useState<OlcumData[]>([]);
  const [status, setStatus] = useState<BaglantiDurumu>('kapali');

  useEffect(() => {
    if (!active) return;
    let kapali = false;
    let yeniden: ReturnType<typeof setTimeout> | undefined;
    let ws: WebSocket | null = null;

    const baglan = () => {
      setStatus('baglaniyor');
      ws = new WebSocket(WS_URL);
      ws.onmessage = (e) => {
        try {
          const m = JSON.parse(e.data);
          if (m.durum === 'veri_yok') {
            setStatus('baglaniyor');
            return;
          }
          setStatus('bagli');
          if (typeof m.heartRate !== 'number') return;
          const nokta: OlcumData = {
            timestamp: m.timestamp,
            heartRate: m.heartRate,
            gsr: m.gsr,
            respiration: m.respiration,
          };
          setData((prev) => [...prev.slice(-(MAX_NOKTA - 1)), nokta]);
        } catch {
          return;
        }
      };
      ws.onclose = () => {
        setStatus('kapali');
        if (!kapali) yeniden = setTimeout(baglan, 2000);
      };
      ws.onerror = () => ws?.close();
    };

    baglan();
    return () => {
      kapali = true;
      clearTimeout(yeniden);
      ws?.close();
    };
  }, [active]);

  const clear = useCallback(() => setData([]), []);
  return { data, status, clear };
}