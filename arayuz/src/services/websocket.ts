import { useCallback, useEffect, useState } from 'react';
import { nabizTahmini, solunumTahmini } from './sinyalisleme';
import type { Ornek } from './sinyalisleme';

export interface OlcumData {
  timestamp: number;
  heartRate: number;
  gsr: number;
  respiration: number;
  temperature?: number;
  movement?: number;
}

export type BaglantiDurumu = 'baglaniyor' | 'bagli' | 'kapali';

const WS_URL = 'ws://localhost:8765';
const MAX_NOKTA = 120;
const PENCERE_SN = 40;
const BAYAT_MS = 3000;

/**
 * C Grubu Veri Hattı WebSocket Servisi (React Hook)
 * Canlı sensör ölçümlerini (olcum) ve kalp atımlarını (atim) dinleyerek 
 * A Grubu sinyal işleme algoritmalarından geçirir ve grafiğe besler.
 */
export function useOlcumStream(active: boolean = true) {
  const [data, setData] = useState<OlcumData[]>([]);
  const [status, setStatus] = useState<BaglantiDurumu>('kapali');

  useEffect(() => {
    if (!active) return;

    let kapali = false;
    let yeniden: ReturnType<typeof setTimeout> | undefined;
    let ws: WebSocket | null = null;

    const az: Ornek[] = [];
    const atimlar: number[] = [];
    let sonGsr: number | null = null;
    let sonT = 0;
    let sonGelis = 0;

    const baglan = () => {
      setStatus('baglaniyor');
      ws = new WebSocket(WS_URL);
      
      ws.onopen = () => setStatus('bagli');
      
      ws.onmessage = (e) => {
        let m: any;
        try {
          m = JSON.parse(e.data);
        } catch {
          return;
        }

        if (m.tur === 'olcum') {
          sonT = m.t;
          sonGsr = m.gsr_mv;
          sonGelis = Date.now();
          az.push({ t: m.t, v: m.az_g });
          while (az.length > 0 && m.t - az[0].t > PENCERE_SN) az.shift();
        } else if (m.tur === 'atim') {
          atimlar.push(m.t);
          if (atimlar.length > 20) atimlar.shift();
        }
      };

      ws.onclose = () => {
        setStatus('kapali');
        if (!kapali) yeniden = setTimeout(baglan, 2000);
      };

      ws.onerror = () => ws?.close();
    };

    baglan();

    const zamanlayici = setInterval(() => {
      if (sonGsr === null || Date.now() - sonGelis > BAYAT_MS) return;
      const hr = nabizTahmini(atimlar, sonT);
      const resp = solunumTahmini(az);
      if (hr === null || resp === null) return;

      const nokta: OlcumData = { 
        timestamp: sonT, 
        heartRate: hr, 
        gsr: sonGsr, 
        respiration: resp 
      };
      
      setData((prev) => [...prev.slice(-(MAX_NOKTA - 1)), nokta]);
    }, 1000);

    return () => {
      kapali = true;
      clearTimeout(yeniden);
      clearInterval(zamanlayici);
      ws?.close();
    };
  }, [active]);

  const clear = useCallback(() => setData([]), []);
  return { data, status, clear };
}

/**
 * Geriye Dönük Uyumluluk Sınıfı (DataStreamService)
 * Eski bileşenlerin kırılmasını önlemek için hazırlanmıştır.
 */
export class DataStreamService {
  private ws: WebSocket | null = null;

  connect(url: string = WS_URL, onDataReceived: (data: OlcumData) => void) {
    this.ws = new WebSocket(url);

    this.ws.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        if (parsedData.heartRate !== undefined || parsedData.gsr !== undefined) {
          onDataReceived(parsedData);
        }
      } catch (err) {
        console.error("Veri ayrıştırma hatası:", err);
      }
    };

    this.ws.onerror = (error) => {
      console.warn("WebSocket bağlantı uyarısı:", error);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}