import { useState, useEffect, useCallback } from 'react'
import { metricsApi } from '../lib/api'

export function useMetrics(departmentId) {
  const [throughput, setThroughput] = useState([])
  const [cycleTime, setCycleTime] = useState(null)
  const [leadTime, setLeadTime] = useState(null)
  const [bottlenecks, setBottlenecks] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchAll = useCallback(async () => {
    const params = departmentId ? { department_id: departmentId } : undefined
    try {
      setLoading(true)
      const [tp, ct, lt, bn] = await Promise.all([
        metricsApi.getThroughput(params),
        metricsApi.getCycleTime(params),
        metricsApi.getLeadTime(params),
        metricsApi.getBottlenecks(params),
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
  }, [departmentId])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  return {
    throughput,
    cycleTime,
    leadTime,
    bottlenecks,
    loading,
    refresh: fetchAll,
  }
}
