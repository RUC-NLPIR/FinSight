import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import {
    Card,
    Button,
    Space,
    Typography,
    Tabs,
    Progress,
    Tag,
    Alert,
    Timeline,
    message,
    Badge,
    Empty,
    Tooltip
} from 'antd'
import {
    PlayCircleOutlined,
    PauseCircleOutlined,
    ReloadOutlined,
    ThunderboltOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    SyncOutlined,
    CloseCircleOutlined,
    HistoryOutlined
} from '@ant-design/icons'
import {
    getExecutionStatus,
    startExecution,
    stopExecution,
    getLastExecution,
    createWebSocketConnection
} from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'

const { Title, Text, Paragraph } = Typography

// Maximum number of logs to keep per agent to prevent memory issues
const MAX_LOGS_PER_AGENT = 5000
// Batch update interval for logs (ms)
const LOG_BATCH_INTERVAL = 500

function ExecutionPage() {
    const [isRunning, setIsRunning] = useState(false)
    const [agents, setAgents] = useState([])
    const [agentLogs, setAgentLogs] = useState({})
    const [currentPriority, setCurrentPriority] = useState(null)
    const [loading, setLoading] = useState(false)
    const [activeTab, setActiveTab] = useState('overview')
    const [lastExecution, setLastExecution] = useState(null)
    const { t, language } = useLanguage()

    const wsRef = useRef(null)
    const logEndRef = useRef({})
    const logBatchRef = useRef({})
    const batchTimerRef = useRef(null)
    const scrollTimerRef = useRef(null)

    useEffect(() => {
        loadExecutionStatus()
        loadLastExecution()
        connectWebSocket()

        return () => {
            if (wsRef.current) {
                wsRef.current.close()
            }
            if (batchTimerRef.current) {
                clearInterval(batchTimerRef.current)
            }
            if (scrollTimerRef.current) {
                clearTimeout(scrollTimerRef.current)
            }
        }
    }, [])

    // Throttled auto-scroll - only scroll every 500ms max
    useEffect(() => {
        if (activeTab !== 'overview' && logEndRef.current[activeTab]) {
            if (scrollTimerRef.current) {
                clearTimeout(scrollTimerRef.current)
            }
            scrollTimerRef.current = setTimeout(() => {
                logEndRef.current[activeTab]?.scrollIntoView({ behavior: 'smooth' })
            }, 500)
        }
    }, [agentLogs, activeTab])

    // Setup batch log processing
    useEffect(() => {
        batchTimerRef.current = setInterval(() => {
            const batch = logBatchRef.current
            if (Object.keys(batch).length > 0) {
                setAgentLogs(prev => {
                    const updated = { ...prev }
                    for (const [agentId, logs] of Object.entries(batch)) {
                        const existing = updated[agentId] || []
                        const combined = [...existing, ...logs]
                        // Keep only the last MAX_LOGS_PER_AGENT logs
                        updated[agentId] = combined.slice(-MAX_LOGS_PER_AGENT)
                    }
                    return updated
                })
                logBatchRef.current = {}
            }
        }, LOG_BATCH_INTERVAL)

        return () => {
            if (batchTimerRef.current) {
                clearInterval(batchTimerRef.current)
            }
        }
    }, [])

    const loadLastExecution = async () => {
        try {
            const response = await getLastExecution()
            setLastExecution(response.data)
        } catch (error) {
            console.error('Failed to load last execution:', error)
        }
    }

    const loadExecutionStatus = async () => {
        try {
            const response = await getExecutionStatus()
            setIsRunning(response.data.is_running)
            setAgents(response.data.agents || [])
            setCurrentPriority(response.data.current_priority)
        } catch (error) {
            console.error('Failed to load execution status:', error)
        }
    }

    const connectWebSocket = useCallback(() => {
        wsRef.current = createWebSocketConnection(
            handleWebSocketMessage,
            (error) => console.error('WebSocket error:', error),
            () => {
                console.log('WebSocket disconnected, attempting to reconnect...')
                setTimeout(connectWebSocket, 3000)
            }
        )
    }, [])

    const handleWebSocketMessage = useCallback((data) => {
        switch (data.type) {
            case 'log':
                // Add to batch instead of updating state directly
                if (!logBatchRef.current[data.agent_id]) {
                    logBatchRef.current[data.agent_id] = []
                }
                logBatchRef.current[data.agent_id].push({
                    message: data.message,
                    timestamp: data.timestamp,
                    level: data.level
                })
                break

            case 'agent_status_update':
                setAgents(prev => prev.map(agent =>
                    agent.agent_id === data.agent.agent_id ? data.agent : agent
                ))
                break

            case 'agents_initialized':
                setAgents(data.agents)
                break

            case 'priority_start':
                setCurrentPriority(data.priority)
                break

            case 'execution_start':
                setIsRunning(true)
                setAgentLogs({})
                logBatchRef.current = {}
                message.success(t('execution.messages.startSuccess'))
                break

            case 'execution_complete':
                setIsRunning(false)
                setCurrentPriority(null)
                message.success(t('execution.messages.completeSuccess'))
                loadExecutionStatus()
                loadLastExecution()
                break

            case 'execution_error':
                setIsRunning(false)
                message.error(t('execution.messages.executionError') + ': ' + data.error)
                break

            default:
                break
        }
    }, [t])

    const handleStart = async (resume = false) => {
        setLoading(true)
        try {
            await startExecution(resume)
        } catch (error) {
            message.error(t('execution.messages.startFailed') + ': ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    const handleStop = async () => {
        setLoading(true)
        try {
            await stopExecution()
            message.success(t('execution.messages.stopSent'))
        } catch (error) {
            message.error(t('execution.messages.stopFailed') + ': ' + error.message)
        } finally {
            setLoading(false)
        }
    }

    const getStatusIcon = useCallback((status) => {
        switch (status) {
            case 'running':
                return <SyncOutlined spin style={{ color: '#dc2626' }} />
            case 'completed':
                return <CheckCircleOutlined style={{ color: '#16a34a' }} />
            case 'pending':
                return <ClockCircleOutlined style={{ color: '#f59e0b' }} />
            case 'error':
                return <CloseCircleOutlined style={{ color: '#dc2626' }} />
            default:
                return <ClockCircleOutlined />
        }
    }, [])

    const getStatusColor = useCallback((status) => {
        switch (status) {
            case 'running':
                return 'processing'
            case 'completed':
                return 'success'
            case 'pending':
                return 'default'
            case 'error':
                return 'error'
            default:
                return 'default'
        }
    }, [])

    const getAgentTypeLabel = useCallback((agentType) => {
        const typeKey = `execution.agentTypes.${agentType}`
        const translated = t(typeKey)
        return translated !== typeKey ? translated : agentType
    }, [t])

    const getPriorityLabel = useCallback((priority) => {
        const phaseKey = `execution.phases.${priority}`
        const translated = t(phaseKey)
        return translated !== phaseKey ? translated : `Phase ${priority}`
    }, [t])

    const getStatusLabel = useCallback((status) => {
        const statusKey = `execution.status.${status}`
        const translated = t(statusKey)
        return translated !== statusKey ? translated : status
    }, [t])

    const progress = useMemo(() => {
        if (agents.length === 0) return 0
        const completed = agents.filter(a => a.status === 'completed').length
        return Math.round((completed / agents.length) * 100)
    }, [agents])

    const agentsByPriority = useMemo(() => {
        const grouped = {}
        agents.forEach(agent => {
            if (!grouped[agent.priority]) {
                grouped[agent.priority] = []
            }
            grouped[agent.priority].push(agent)
        })
        return grouped
    }, [agents])

    const statusCounts = useMemo(() => ({
        pending: agents.filter(a => a.status === 'pending').length,
        running: agents.filter(a => a.status === 'running').length,
        completed: agents.filter(a => a.status === 'completed').length,
        error: agents.filter(a => a.status === 'error').length
    }), [agents])

    const renderOverview = () => (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* Overall Progress */}
            <Card>
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Title level={4}>{t('execution.overallProgress')}</Title>
                        <Text strong style={{ fontSize: '24px' }}>{progress}%</Text>
                    </div>
                    <Progress
                        percent={progress}
                        status={isRunning ? 'active' : progress === 100 ? 'success' : 'normal'}
                        strokeColor="#dc2626"
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-around' }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>
                                {statusCounts.pending}
                            </div>
                            <Text type="secondary">{t('execution.status.pending')}</Text>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc2626' }}>
                                {statusCounts.running}
                            </div>
                            <Text type="secondary">{t('execution.status.running')}</Text>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#16a34a' }}>
                                {statusCounts.completed}
                            </div>
                            <Text type="secondary">{t('execution.status.completed')}</Text>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc2626' }}>
                                {statusCounts.error}
                            </div>
                            <Text type="secondary">{t('execution.status.error')}</Text>
                        </div>
                    </div>
                </Space>
            </Card>

            {/* Current Phase */}
            {currentPriority !== null && (
                <Alert
                    message={`${t('execution.currentPhase')}: ${getPriorityLabel(currentPriority)}`}
                    type="info"
                    icon={<ThunderboltOutlined />}
                    showIcon
                />
            )}

            {/* Agents by Priority */}
            {Object.keys(agentsByPriority).sort().map(priority => (
                <Card
                    key={priority}
                    title={
                        <Space>
                            <Badge
                                status={parseInt(priority) === currentPriority ? 'processing' : 'default'}
                            />
                            <span>{getPriorityLabel(parseInt(priority))}</span>
                            <Tag>{t('execution.taskCount').replace('{count}', agentsByPriority[priority].length)}</Tag>
                        </Space>
                    }
                    size="small"
                >
                    <Timeline>
                        {agentsByPriority[priority].map(agent => (
                            <Timeline.Item
                                key={agent.agent_id}
                                dot={getStatusIcon(agent.status)}
                                color={agent.status === 'completed' ? 'green' : agent.status === 'running' ? 'blue' : 'gray'}
                            >
                                <Space direction="vertical" size="small">
                                    <Space>
                                        <Tag color={getStatusColor(agent.status)}>
                                            {getStatusLabel(agent.status)}
                                        </Tag>
                                        <Tag color="blue">{getAgentTypeLabel(agent.agent_type)}</Tag>
                                        <Text strong>{agent.task_content}</Text>
                                    </Space>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                        Agent ID: {agent.agent_id}
                                    </Text>
                                    {agent.progress && (
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                            {agent.progress}
                                        </Text>
                                    )}
                                </Space>
                            </Timeline.Item>
                        ))}
                    </Timeline>
                </Card>
            ))}

            {agents.length === 0 && (
                <Empty
                    description={t('execution.noExecutionTasks')}
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
            )}
        </Space>
    )

    const renderAgentLogs = useCallback((agentId) => {
        const logs = agentLogs[agentId] || []
        // Only render last 200 logs for performance
        const visibleLogs = logs.slice(-200)

        return (
            <Card
                style={{
                    height: '600px',
                    overflow: 'auto',
                    background: '#1e1e1e',
                    color: '#d4d4d4'
                }}
                bodyStyle={{ padding: '16px' }}
            >
                {visibleLogs.length === 0 ? (
                    <Empty
                        description={t('execution.noLogs')}
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        style={{ color: '#d4d4d4' }}
                    />
                ) : (
                    <div>
                        {logs.length > 200 && (
                            <div style={{
                                padding: '8px',
                                marginBottom: '8px',
                                background: 'rgba(255,255,255,0.1)',
                                borderRadius: '4px',
                                textAlign: 'center'
                            }}>
                                <Text style={{ color: '#888' }}>
                                    {t('execution.showingLogs').replace('{visible}', '200').replace('{total}', logs.length.toString())}
                                </Text>
                            </div>
                        )}
                        {visibleLogs.map((log, index) => (
                            <div
                                key={index}
                                style={{
                                    marginBottom: '8px',
                                    padding: '8px',
                                    background: log.level === 'ERROR' ? '#3d1e1e' : 'transparent',
                                    borderLeft: log.level === 'ERROR' ? '3px solid #ff4d4f' :
                                        log.level === 'WARNING' ? '3px solid #faad14' :
                                            '3px solid #1890ff',
                                    borderRadius: '4px'
                                }}
                            >
                                <Space size="small">
                                    <Text
                                        style={{
                                            color: '#858585',
                                            fontSize: '12px',
                                            fontFamily: 'monospace'
                                        }}
                                    >
                                        {new Date(log.timestamp).toLocaleTimeString()}
                                    </Text>
                                    <Tag
                                        color={
                                            log.level === 'ERROR' ? 'red' :
                                                log.level === 'WARNING' ? 'orange' :
                                                    'blue'
                                        }
                                        style={{ fontSize: '10px' }}
                                    >
                                        {log.level}
                                    </Tag>
                                </Space>
                                <Paragraph
                                    style={{
                                        color: '#d4d4d4',
                                        fontFamily: 'monospace',
                                        fontSize: '13px',
                                        marginBottom: 0,
                                        marginTop: '4px',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word'
                                    }}
                                >
                                    {log.message}
                                </Paragraph>
                            </div>
                        ))}
                        <div ref={el => logEndRef.current[agentId] = el} />
                    </div>
                )}
            </Card>
        )
    }, [agentLogs, t])

    // Memoize tab items to prevent re-creation
    const tabItems = useMemo(() => {
        const items = [
            {
                key: 'overview',
                label: (
                    <Space>
                        <ThunderboltOutlined />
                        <span>{t('execution.overview')}</span>
                    </Space>
                ),
                children: renderOverview()
            }
        ]

        agents.forEach(agent => {
            items.push({
                key: agent.agent_id,
                label: (
                    <Space size="small">
                        {getStatusIcon(agent.status)}
                        <Tooltip title={agent.task_content}>
                            <span style={{
                                maxWidth: '120px',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                display: 'inline-block'
                            }}>
                                {agent.task_content}
                            </span>
                        </Tooltip>
                        <Badge
                            count={agentLogs[agent.agent_id]?.length || 0}
                            style={{ backgroundColor: '#52c41a' }}
                            overflowCount={999}
                        />
                    </Space>
                ),
                children: (
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Card size="small">
                            <Space direction="vertical" style={{ width: '100%' }}>
                                <Space>
                                    <Text strong>{t('execution.agentType')}:</Text>
                                    <Tag color="blue">{getAgentTypeLabel(agent.agent_type)}</Tag>
                                </Space>
                                <Space>
                                    <Text strong>{t('execution.taskContent')}:</Text>
                                    <Text>{agent.task_content}</Text>
                                </Space>
                                <Space>
                                    <Text strong>{t('execution.currentStatus')}:</Text>
                                    <Tag color={getStatusColor(agent.status)} icon={getStatusIcon(agent.status)}>
                                        {getStatusLabel(agent.status)}
                                    </Tag>
                                </Space>
                                <Space>
                                    <Text strong>{t('execution.priority')}:</Text>
                                    <Text>{getPriorityLabel(agent.priority)}</Text>
                                </Space>
                                <Space>
                                    <Text strong>{t('execution.agentId')}:</Text>
                                    <Text code>{agent.agent_id}</Text>
                                </Space>
                            </Space>
                        </Card>

                        <Title level={5}>{t('execution.executionLogs')}</Title>
                        {renderAgentLogs(agent.agent_id)}
                    </Space>
                )
            })
        })

        return items
    }, [agents, agentLogs, currentPriority, progress, statusCounts, isRunning, renderAgentLogs, getStatusIcon, getStatusColor, getAgentTypeLabel, getPriorityLabel, getStatusLabel, agentsByPriority, t])

    return (
        <div>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <Title level={2} style={{ margin: 0 }}>
                            <ThunderboltOutlined /> {t('execution.title')}
                        </Title>
                        <Text type="secondary">{t('execution.description')}</Text>
                    </div>
                    <Space>
                        {!isRunning ? (
                            <>
                                <Button
                                    type="primary"
                                    size="large"
                                    icon={<PlayCircleOutlined />}
                                    onClick={() => handleStart(false)}
                                    loading={loading}
                                    style={{
                                        background: '#dc2626',
                                        borderColor: '#dc2626'
                                    }}
                                >
                                    {t('execution.start')}
                                </Button>
                                <Tooltip
                                    title={lastExecution?.has_last_execution
                                        ? t('execution.resumeTooltip')
                                            .replace('{name}', lastExecution.target_name)
                                            .replace('{time}', new Date(lastExecution.timestamp).toLocaleString(language === 'zh' ? 'zh-CN' : 'en-US'))
                                        : t('execution.noResumableExecution')}
                                >
                                    <Button
                                        size="large"
                                        icon={<ReloadOutlined />}
                                        onClick={() => handleStart(true)}
                                        loading={loading}
                                        disabled={!lastExecution?.has_last_execution}
                                    >
                                        {t('execution.resume')}
                                    </Button>
                                </Tooltip>
                            </>
                        ) : (
                            <Button
                                danger
                                size="large"
                                icon={<PauseCircleOutlined />}
                                onClick={handleStop}
                                loading={loading}
                            >
                                {t('execution.stop')}
                            </Button>
                        )}
                    </Space>
                </div>

                {/* Last Execution Info */}
                {!isRunning && lastExecution?.has_last_execution && (
                    <Alert
                        message={
                            <Space>
                                <HistoryOutlined />
                                <span>{t('execution.lastExecution')}: {lastExecution.target_name}</span>
                                <Tag color="blue">{t('execution.collectTaskCount').replace('{count}', lastExecution.collect_count)}</Tag>
                                <Tag color="green">{t('execution.analysisTaskCount').replace('{count}', lastExecution.analysis_count)}</Tag>
                                <Text type="secondary">
                                    {new Date(lastExecution.timestamp).toLocaleString(language === 'zh' ? 'zh-CN' : 'en-US')}
                                </Text>
                            </Space>
                        }
                        type="info"
                        showIcon={false}
                    />
                )}

                {isRunning && (
                    <Alert
                        message={t('execution.executing')}
                        description={t('execution.executingDesc')}
                        type="info"
                        icon={<SyncOutlined spin />}
                        showIcon
                    />
                )}

                <Card>
                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        type="card"
                        size="large"
                        items={tabItems}
                    />
                </Card>
            </Space>
        </div>
    )
}

export default ExecutionPage
