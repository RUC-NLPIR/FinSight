import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Config APIs
export const getConfig = () => client.get('/api/config')
export const listConfigs = () => client.get('/api/config/list')
export const updateConfig = (config) => client.post('/api/config', config)
export const saveConfig = (name) => client.post('/api/config/save', { name })
export const loadConfig = (name) => client.post('/api/config/load', { name })
export const deleteConfig = (name) => client.delete(`/api/config/${name}`)

// Tasks APIs
export const getTasks = () => client.get('/api/tasks')
export const listTaskConfigs = () => client.get('/api/tasks/list')
export const updateTasks = (tasks) => client.post('/api/tasks', tasks)
export const saveTasks = (name) => client.post('/api/tasks/save', { name })
export const loadTasks = (name) => client.post('/api/tasks/load', { name })
export const deleteTaskConfig = (name) => client.delete(`/api/tasks/${name}`)

// Execution APIs
export const getExecutionStatus = () => client.get('/api/execution/status')
export const startExecution = (resume = false) =>
    client.post('/api/execution/start', { resume })
export const stopExecution = () => client.post('/api/execution/stop')
export const getLastExecution = () => client.get('/api/execution/last')

// Reports APIs
export const listReports = () => client.get('/api/reports')
export const getReportPreview = (targetName, filename) =>
    client.get(`/api/reports/preview/${encodeURIComponent(targetName)}/${encodeURIComponent(filename)}`)
export const getReportDownloadUrl = (targetName, filename) =>
    `${API_BASE_URL}/api/reports/download/${encodeURIComponent(targetName)}/${encodeURIComponent(filename)}`

// WebSocket connection
export const createWebSocketConnection = (onMessage, onError, onClose) => {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws/logs'
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
        console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (onMessage) onMessage(data)
    }

    ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (onError) onError(error)
    }

    ws.onclose = () => {
        console.log('WebSocket disconnected')
        if (onClose) onClose()
    }

    return ws
}

export default client

