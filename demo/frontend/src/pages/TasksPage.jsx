import React, { useState, useEffect } from 'react'
import {
    Card,
    Button,
    Space,
    Typography,
    Input,
    List,
    Tag,
    Modal,
    message,
    Row,
    Col,
    Empty,
    Popconfirm
} from 'antd'
import {
    PlusOutlined,
    DeleteOutlined,
    SaveOutlined,
    FolderOpenOutlined,
    DatabaseOutlined,
    BarChartOutlined,
    EditOutlined,
    ClockCircleOutlined
} from '@ant-design/icons'
import { getTasks, updateTasks, saveTasks, loadTasks, listTaskConfigs, deleteTaskConfig } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'

const { Title, Text } = Typography
const { TextArea } = Input

function TasksPage() {
    const [collectTasks, setCollectTasks] = useState([])
    const [analysisTasks, setAnalysisTasks] = useState([])
    const [isModalVisible, setIsModalVisible] = useState(false)
    const [modalType, setModalType] = useState('collect')
    const [newTaskContent, setNewTaskContent] = useState('')
    const [loading, setLoading] = useState(false)
    const [saveModalVisible, setSaveModalVisible] = useState(false)
    const [loadModalVisible, setLoadModalVisible] = useState(false)
    const [taskConfigName, setTaskConfigName] = useState('')
    const [savedTaskConfigs, setSavedTaskConfigs] = useState([])
    const { t, language } = useLanguage()

    useEffect(() => {
        loadExistingTasks()
        loadSavedTaskConfigsList()
    }, [])

    const loadSavedTaskConfigsList = async () => {
        try {
            const response = await listTaskConfigs()
            setSavedTaskConfigs(response.data.tasks_list || [])
        } catch (error) {
            console.error('Failed to load task configs list:', error)
        }
    }

    const loadExistingTasks = async () => {
        try {
            const response = await getTasks()
            if (response.data.tasks) {
                setCollectTasks(response.data.tasks.collect_tasks || [])
                setAnalysisTasks(response.data.tasks.analysis_tasks || [])
            }
        } catch (error) {
            console.error('Failed to load tasks:', error)
        }
    }

    const handleShowLoadModal = () => {
        loadSavedTaskConfigsList()
        setLoadModalVisible(true)
    }

    const handleLoadTasks = async (name) => {
        setLoading(true)
        try {
            const response = await loadTasks(name)
            if (response.data.status === 'success') {
                await loadExistingTasks()
                setLoadModalVisible(false)
                message.success(t('tasks.messages.loadSuccess').replace('{name}', name))
            }
        } catch (error) {
            message.error(t('tasks.messages.loadFailed') + ': ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    const handleDeleteTaskConfig = async (name) => {
        try {
            const response = await deleteTaskConfig(name)
            if (response.data.status === 'success') {
                message.success(t('tasks.messages.deleteSuccess').replace('{name}', name))
                loadSavedTaskConfigsList()
            }
        } catch (error) {
            message.error(t('tasks.messages.deleteFailed') + ': ' + (error.response?.data?.detail || error.message))
        }
    }

    const handleUpdateTasks = async () => {
        setLoading(true)
        try {
            const tasksData = {
                collect_tasks: collectTasks,
                analysis_tasks: analysisTasks
            }

            const response = await updateTasks(tasksData)

            if (response.data.status === 'success') {
                setSaveModalVisible(true)
            }
        } catch (error) {
            message.error(t('tasks.messages.updateFailed') + ': ' + error.message)
        } finally {
            setLoading(false)
        }
    }

    const handleSaveTasks = async () => {
        if (!taskConfigName.trim()) {
            message.warning(t('tasks.messages.enterTaskName'))
            return
        }

        setLoading(true)
        try {
            const response = await saveTasks(taskConfigName.trim())
            if (response.data.status === 'success') {
                message.success(t('tasks.messages.saveSuccess').replace('{name}', taskConfigName))
                setSaveModalVisible(false)
                setTaskConfigName('')
                loadSavedTaskConfigsList()
            }
        } catch (error) {
            message.error(t('tasks.messages.saveFailed') + ': ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    const showAddTaskModal = (type) => {
        setModalType(type)
        setNewTaskContent('')
        setIsModalVisible(true)
    }

    const handleAddTask = () => {
        if (!newTaskContent.trim()) {
            message.warning(t('tasks.messages.enterTaskContent'))
            return
        }

        const newTask = {
            id: `task_${Date.now()}`,
            type: modalType,
            content: newTaskContent.trim()
        }

        if (modalType === 'collect') {
            setCollectTasks([...collectTasks, newTask])
        } else {
            setAnalysisTasks([...analysisTasks, newTask])
        }

        setIsModalVisible(false)
        setNewTaskContent('')
        message.success(t('tasks.messages.addSuccess'))
    }

    const handleDeleteTask = (taskId, type) => {
        if (type === 'collect') {
            setCollectTasks(collectTasks.filter(task => task.id !== taskId))
        } else {
            setAnalysisTasks(analysisTasks.filter(task => task.id !== taskId))
        }
        message.success(t('tasks.messages.deleteTaskSuccess'))
    }

    const renderTaskCard = (task, type) => (
        <Card
            size="small"
            style={{
                marginBottom: 12,
                borderRadius: 12,
                boxShadow: '0 2px 12px rgba(220, 38, 38, 0.08)',
                transition: 'all 0.3s',
                cursor: 'pointer',
                border: `1px solid ${type === 'collect' ? 'rgba(220, 38, 38, 0.2)' : 'rgba(234, 88, 12, 0.2)'}`,
                background: type === 'collect' ? 'rgba(254, 226, 226, 0.3)' : 'rgba(255, 237, 213, 0.3)'
            }}
            hoverable
        >
            <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Space>
                        <Tag color={type === 'collect' ? 'red' : 'orange'}>
                            {type === 'collect' ? t('tasks.dataCollect') : t('tasks.dataAnalysis')}
                        </Tag>
                        <Text code>{task.id}</Text>
                    </Space>
                    <Button
                        type="text"
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={() => handleDeleteTask(task.id, type)}
                    />
                </div>
                <Text>{task.content}</Text>
            </Space>
        </Card>
    )

    return (
        <div>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <Title level={2} style={{ margin: 0 }}>
                            <EditOutlined /> {t('tasks.title')}
                        </Title>
                        <Text type="secondary">{t('tasks.description')}</Text>
                    </div>
                    <Space>
                        <Button
                            icon={<FolderOpenOutlined />}
                            onClick={handleShowLoadModal}
                            loading={loading}
                        >
                            {t('tasks.loadTasks')}
                        </Button>
                        <Button
                            type="primary"
                            icon={<SaveOutlined />}
                            onClick={handleUpdateTasks}
                            loading={loading}
                            style={{
                                background: '#dc2626',
                                borderColor: '#dc2626'
                            }}
                        >
                            {t('tasks.saveTasks')}
                        </Button>
                    </Space>
                </div>

                <Row gutter={24}>
                    {/* Data Collection Tasks */}
                    <Col span={12}>
                        <Card
                            title={
                                <Space>
                                    <DatabaseOutlined style={{ color: '#dc2626' }} />
                                    <span>{t('tasks.collectTasks')}</span>
                                    <Tag color="red">{collectTasks.length}</Tag>
                                </Space>
                            }
                            extra={
                                <Button
                                    type="primary"
                                    size="small"
                                    icon={<PlusOutlined />}
                                    onClick={() => showAddTaskModal('collect')}
                                    style={{
                                        background: '#dc2626',
                                        borderColor: '#dc2626'
                                    }}
                                >
                                    {t('tasks.addTask')}
                                </Button>
                            }
                            style={{ height: '600px', overflow: 'auto' }}
                        >
                            {collectTasks.length === 0 ? (
                                <Empty
                                    description={t('tasks.noCollectTasks')}
                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                />
                            ) : (
                                <div>
                                    {collectTasks.map(task => renderTaskCard(task, 'collect'))}
                                </div>
                            )}
                        </Card>
                    </Col>

                    {/* Data Analysis Tasks */}
                    <Col span={12}>
                        <Card
                            title={
                                <Space>
                                    <BarChartOutlined style={{ color: '#ea580c' }} />
                                    <span>{t('tasks.analysisTasks')}</span>
                                    <Tag color="orange">{analysisTasks.length}</Tag>
                                </Space>
                            }
                            extra={
                                <Button
                                    type="primary"
                                    size="small"
                                    icon={<PlusOutlined />}
                                    onClick={() => showAddTaskModal('analyze')}
                                    style={{
                                        background: '#ea580c',
                                        borderColor: '#ea580c'
                                    }}
                                >
                                    {t('tasks.addTask')}
                                </Button>
                            }
                            style={{ height: '600px', overflow: 'auto' }}
                        >
                            {analysisTasks.length === 0 ? (
                                <Empty
                                    description={t('tasks.noAnalysisTasks')}
                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                />
                            ) : (
                                <div>
                                    {analysisTasks.map(task => renderTaskCard(task, 'analyze'))}
                                </div>
                            )}
                        </Card>
                    </Col>
                </Row>
            </Space>

            {/* Add Task Modal */}
            <Modal
                title={modalType === 'collect' ? t('tasks.addTaskModal.collectTitle') : t('tasks.addTaskModal.analysisTitle')}
                open={isModalVisible}
                onOk={handleAddTask}
                onCancel={() => setIsModalVisible(false)}
                okText={t('common.add')}
                cancelText={t('common.cancel')}
            >
                <TextArea
                    rows={4}
                    placeholder={
                        modalType === 'collect'
                            ? t('tasks.addTaskModal.collectPlaceholder')
                            : t('tasks.addTaskModal.analysisPlaceholder')
                    }
                    value={newTaskContent}
                    onChange={(e) => setNewTaskContent(e.target.value)}
                />
            </Modal>

            {/* Save Tasks Modal */}
            <Modal
                title={t('tasks.saveTasksModal.title')}
                open={saveModalVisible}
                onOk={handleSaveTasks}
                onCancel={() => {
                    setSaveModalVisible(false)
                    setTaskConfigName('')
                }}
                okText={t('common.save')}
                cancelText={t('common.cancel')}
                confirmLoading={loading}
            >
                <Space direction="vertical" style={{ width: '100%' }}>
                    <Text>{t('tasks.saveTasksModal.prompt')}</Text>
                    <Input
                        placeholder={t('tasks.saveTasksModal.placeholder')}
                        value={taskConfigName}
                        onChange={(e) => setTaskConfigName(e.target.value)}
                        onPressEnter={handleSaveTasks}
                        autoFocus
                    />
                </Space>
            </Modal>

            {/* Load Tasks Modal */}
            <Modal
                title={t('tasks.loadTasksModal.title')}
                open={loadModalVisible}
                onCancel={() => setLoadModalVisible(false)}
                footer={null}
                width={700}
            >
                <List
                    dataSource={savedTaskConfigs}
                    locale={{ emptyText: t('tasks.loadTasksModal.empty') }}
                    renderItem={(config) => (
                        <List.Item
                            actions={[
                                <Button
                                    type="link"
                                    onClick={() => handleLoadTasks(config.name)}
                                    loading={loading}
                                >
                                    {t('common.load')}
                                </Button>,
                                <Popconfirm
                                    title={t('tasks.loadTasksModal.confirmDelete')}
                                    description={t('tasks.loadTasksModal.confirmDeleteDesc').replace('{name}', config.name)}
                                    onConfirm={() => handleDeleteTaskConfig(config.name)}
                                    okText={t('common.delete')}
                                    cancelText={t('common.cancel')}
                                >
                                    <Button type="link" danger icon={<DeleteOutlined />}>
                                        {t('common.delete')}
                                    </Button>
                                </Popconfirm>
                            ]}
                        >
                            <List.Item.Meta
                                title={
                                    <Space>
                                        <Text strong>{config.name}</Text>
                                        <Tag color="red">{t('tasks.loadTasksModal.collectCount')}: {config.collect_count}</Tag>
                                        <Tag color="orange">{t('tasks.loadTasksModal.analysisCount')}: {config.analysis_count}</Tag>
                                    </Space>
                                }
                                description={
                                    <Space>
                                        <ClockCircleOutlined />
                                        <Text type="secondary">
                                            {new Date(config.modified_time).toLocaleString(language === 'zh' ? 'zh-CN' : 'en-US')}
                                        </Text>
                                    </Space>
                                }
                            />
                        </List.Item>
                    )}
                />
            </Modal>
        </div>
    )
}

export default TasksPage
