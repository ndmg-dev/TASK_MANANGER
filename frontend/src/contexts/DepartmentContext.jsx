import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { departmentsApi } from '../lib/api'
import { useAuth } from './AuthContext'

const DepartmentContext = createContext(null)
const STORAGE_KEY = 'ndmg:department'

export function DepartmentProvider({ children }) {
  const { user } = useAuth()
  const [departments, setDepartments] = useState([])
  const [currentId, setCurrentId] = useState(() => localStorage.getItem(STORAGE_KEY) || null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchDepartments = useCallback(async () => {
    if (!user) {
      setDepartments([])
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      const { data } = await departmentsApi.getMine()
      setDepartments(data || [])
      setError(null)

      // Mantém o último setor escolhido se ele ainda for acessível
      const saved = localStorage.getItem(STORAGE_KEY)
      const valid = (data || []).some((d) => d.id === saved)
      setCurrentId(valid ? saved : data?.[0]?.id ?? null)
    } catch (err) {
      setError(err?.response?.data?.error || err.message)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    fetchDepartments()
  }, [fetchDepartments])

  const selectDepartment = useCallback((id) => {
    setCurrentId(id)
    if (id) localStorage.setItem(STORAGE_KEY, id)
    else localStorage.removeItem(STORAGE_KEY)
  }, [])

  const current = useMemo(
    () => departments.find((d) => d.id === currentId) || null,
    [departments, currentId]
  )

  const value = {
    departments,
    current,
    currentId,
    loading,
    error,
    selectDepartment,
    refresh: fetchDepartments,
    // Sem setor vinculado o usuário não consegue criar nem ver tickets
    hasDepartment: departments.length > 0,
  }

  return <DepartmentContext.Provider value={value}>{children}</DepartmentContext.Provider>
}

export function useDepartments() {
  const context = useContext(DepartmentContext)
  if (!context) {
    throw new Error('useDepartments deve ser usado dentro de DepartmentProvider')
  }
  return context
}
