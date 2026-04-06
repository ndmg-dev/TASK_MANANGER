import { useState, useEffect } from 'react'
import { metricsApi } from '../lib/api'

export function useMetrics() {
  const [throughput, setThroughput] = useState([])
  const [cycleTime, setCycleTime] = useState(null)
  const [leadTime, setLeadTime] = useState(null)
  const [bottlenecks, setBottlenecks] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchAll = async () => {
    try {
      setLoading(true)
      const [tp, ct, lt, bn] = await Promise.all([
        metricsApi.getThroughput(),
        metricsApi.getCycleTime(),
        metricsApi.getLeadTime(),
        metricsApi.getBottlenecks(),
      ])
      setThroughput(tp.data)
      setCycleTime(ct.data)
      setLeadTime(lt.data)
      setBottlenecks(bn.data)
    } catch (err) {
      console.error('Erro ao carregar métricas:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAll()
  }, [])

  return {
    throughput,
    cycleTime,
    leadTime,
    bottlenecks,
    loading,
    refresh: fetchAll,
  }
}
