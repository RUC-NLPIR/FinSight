import React, { useState, useEffect } from 'react'
import {
    Form,
    Input,
    Button,
    Card,
    Space,
    Divider,
    Typography,
    message,
    Row,
    Col,
    Collapse,
    Modal,
    List,
    Tag,
    Popconfirm
} from 'antd'
import {
    SaveOutlined,
    FolderOpenOutlined,
    ApiOutlined,
    DatabaseOutlined,
    DeleteOutlined,
    ClockCircleOutlined
} from '@ant-design/icons'
import { getConfig, updateConfig, saveConfig, loadConfig, listConfigs, deleteConfig } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'

const { Title, Text } = Typography
const { Panel } = Collapse

function ConfigPage() {
    const [form] = Form.useForm()
    const [loading, setLoading] = useState(false)
    const { t, language } = useLanguage()

    const llmConfigs = [
        { key: 'ds', label: t('config.llmLabels.ds'), prefix: 'DS' },
        { key: 'vlm', label: t('config.llmLabels.vlm'), prefix: 'VLM' },
        { key: 'embedding', label: t('config.llmLabels.embedding'), prefix: 'EMBEDDING' }
    ]

    const [saveModalVisible, setSaveModalVisible] = useState(false)
    const [loadModalVisible, setLoadModalVisible] = useState(false)
    const [configName, setConfigName] = useState('')
    const [savedConfigs, setSavedConfigs] = useState([])

    useEffect(() => {
        loadExistingConfig()
        loadSavedConfigsList()
    }, [])

    const loadSavedConfigsList = async () => {
        try {
            const response = await listConfigs()
            setSavedConfigs(response.data.configs || [])
        } catch (error) {
            console.error('Failed to load configs list:', error)
        }
    }

    const loadExistingConfig = async () => {
        try {
            const response = await getConfig()
            if (response.data.config) {
                const config = response.data.config

                // Set basic config
                form.setFieldsValue({
                    target_name: config.target_name,
                    stock_code: config.stock_code,
                    output_dir: config.output_dir,
                    reference_doc_path: config.reference_doc_path,
                    outline_template_path: config.outline_template_path,
                })

                // Set LLM configs
                if (config.llm_configs && config.llm_configs.length > 0) {
                    config.llm_configs.forEach((llm, index) => {
                        const prefix = llmConfigs[index]?.prefix
                        if (prefix) {
                            form.setFieldsValue({
                                [`${prefix}_model_name`]: llm.model_name,
                                [`${prefix}_api_key`]: llm.api_key,
                                [`${prefix}_base_url`]: llm.base_url,
                            })
                        }
                    })
                }

                // Set model names
                form.setFieldsValue({
                    ds_model_name: config.ds_model_name,
                    vlm_model_name: config.vlm_model_name,
                    embedding_model_name: config.embedding_model_name,
                })
            }
        } catch (error) {
            console.error('Failed to load config:', error)
        }
    }

    const handleShowLoadModal = () => {
        loadSavedConfigsList()
        setLoadModalVisible(true)
    }

    const handleLoadConfig = async (name) => {
        setLoading(true)
        try {
            const response = await loadConfig(name)
            if (response.data.status === 'success') {
                await loadExistingConfig()
                setLoadModalVisible(false)
                message.success(t('config.messages.loadSuccess').replace('{name}', name))
            }
        } catch (error) {
            message.error(t('config.messages.loadFailed') + ': ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    const handleDeleteConfig = async (name) => {
        try {
            const response = await deleteConfig(name)
            if (response.data.status === 'success') {
                message.success(t('config.messages.deleteSuccess').replace('{name}', name))
                loadSavedConfigsList()
            }
        } catch (error) {
            message.error(t('config.messages.deleteFailed') + ': ' + (error.response?.data?.detail || error.message))
        }
    }

    const handleUpdateConfig = async () => {
        try {
            const values = await form.validateFields()
            setLoading(true)

            // Build LLM configs array
            const llm_configs = llmConfigs.map(config => ({
                model_name: values[`${config.prefix}_model_name`],
                api_key: values[`${config.prefix}_api_key`],
                base_url: values[`${config.prefix}_base_url`],
                generation_params: {}
            }))

            const configData = {
                target_name: values.target_name,
                stock_code: values.stock_code,
                output_dir: values.output_dir || 'outputs/demo',
                reference_doc_path: values.reference_doc_path || 'src/config/report_template.docx',
                outline_template_path: values.outline_template_path || 'src/template/company_outline.md',
                llm_configs: llm_configs,
                ds_model_name: values.ds_model_name,
                vlm_model_name: values.vlm_model_name,
                embedding_model_name: values.embedding_model_name,
            }

            const response = await updateConfig(configData)

            if (response.data.status === 'success') {
                setSaveModalVisible(true)
            }
        } catch (error) {
            message.error(t('config.messages.updateFailed') + ': ' + (error.message || t('config.messages.checkForm')))
            console.error('Update config error:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleSaveConfig = async () => {
        if (!configName.trim()) {
            message.warning(t('config.messages.enterConfigName'))
            return
        }

        setLoading(true)
        try {
            const response = await saveConfig(configName.trim())
            if (response.data.status === 'success') {
                message.success(t('config.messages.saveSuccess').replace('{name}', configName))
                setSaveModalVisible(false)
                setConfigName('')
                loadSavedConfigsList()
            }
        } catch (error) {
            message.error(t('config.messages.saveFailed') + ': ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <Title level={2} style={{ margin: 0 }}>
                            <ApiOutlined /> {t('config.title')}
                        </Title>
                        <Text type="secondary">{t('config.description')}</Text>
                    </div>
                    <Space>
                        <Button
                            icon={<FolderOpenOutlined />}
                            onClick={handleShowLoadModal}
                            loading={loading}
                        >
                            {t('config.loadConfig')}
                        </Button>
                        <Button
                            type="primary"
                            icon={<SaveOutlined />}
                            onClick={handleUpdateConfig}
                            loading={loading}
                            style={{
                                background: '#dc2626',
                                borderColor: '#dc2626'
                            }}
                        >
                            {t('config.saveConfig')}
                        </Button>
                    </Space>
                </div>

                <Form
                    form={form}
                    layout="vertical"
                    initialValues={{
                        output_dir: 'outputs/demo',
                        reference_doc_path: 'src/config/report_template.docx',
                        outline_template_path: 'src/template/company_outline.md',
                    }}
                >
                    {/* Basic Configuration */}
                    <Card
                        title={
                            <Space>
                                <DatabaseOutlined />
                                <span>{t('config.basicConfig')}</span>
                            </Space>
                        }
                        style={{ marginBottom: 16 }}
                    >
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    label={t('config.targetCompany')}
                                    name="target_name"
                                    rules={[{ required: true, message: t('config.targetCompanyRequired') }]}
                                >
                                    <Input placeholder={t('config.targetCompanyPlaceholder')} size="large" />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    label={t('config.stockCode')}
                                    name="stock_code"
                                    rules={[{ required: true, message: t('config.stockCodeRequired') }]}
                                >
                                    <Input placeholder={t('config.stockCodePlaceholder')} size="large" />
                                </Form.Item>
                            </Col>
                        </Row>

                        <Form.Item
                            label={t('config.outputDir')}
                            name="output_dir"
                        >
                            <Input placeholder="outputs/demo" size="large" />
                        </Form.Item>

                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    label={t('config.reportTemplatePath')}
                                    name="reference_doc_path"
                                >
                                    <Input placeholder="src/config/report_template.docx" />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    label={t('config.outlineTemplatePath')}
                                    name="outline_template_path"
                                >
                                    <Input placeholder="src/template/company_outline.md" />
                                </Form.Item>
                            </Col>
                        </Row>
                    </Card>

                    {/* LLM Configurations */}
                    <Card
                        title={
                            <Space>
                                <ApiOutlined />
                                <span>{t('config.modelConfig')}</span>
                            </Space>
                        }
                        style={{ marginBottom: 16 }}
                    >
                        <Collapse defaultActiveKey={['0']} ghost>
                            {llmConfigs.map((config, index) => (
                                <Panel
                                    header={
                                        <Text strong style={{ fontSize: '16px' }}>
                                            {config.label}
                                        </Text>
                                    }
                                    key={index}
                                >
                                    <Form.Item
                                        label={t('config.modelName')}
                                        name={`${config.prefix}_model_name`}
                                        rules={[{ required: true, message: t('config.modelNameRequired') }]}
                                    >
                                        <Input placeholder="e.g., deepseek-chat" />
                                    </Form.Item>

                                    <Form.Item
                                        label={t('config.apiKey')}
                                        name={`${config.prefix}_api_key`}
                                        rules={[{ required: true, message: t('config.apiKeyRequired') }]}
                                    >
                                        <Input.Password placeholder={language === 'zh' ? '输入API密钥' : 'Enter API key'} />
                                    </Form.Item>

                                    <Form.Item
                                        label={t('config.baseUrl')}
                                        name={`${config.prefix}_base_url`}
                                        rules={[{ required: true, message: t('config.baseUrlRequired') }]}
                                    >
                                        <Input placeholder="https://api.deepseek.com" />
                                    </Form.Item>
                                </Panel>
                            ))}
                        </Collapse>

                        <Divider />

                        <Title level={5}>{t('config.usedModelNames')}</Title>
                        <Row gutter={16}>
                            <Col span={8}>
                                <Form.Item
                                    label={t('config.mainLLM')}
                                    name="ds_model_name"
                                    rules={[{ required: true }]}
                                >
                                    <Input
                                        placeholder="deepseek-chat"
                                        style={{ borderColor: '#fecaca' }}
                                    />
                                </Form.Item>
                            </Col>
                            <Col span={8}>
                                <Form.Item
                                    label={t('config.visionModel')}
                                    name="vlm_model_name"
                                    rules={[{ required: true }]}
                                >
                                    <Input
                                        placeholder="gpt-4-vision"
                                        style={{ borderColor: '#fecaca' }}
                                    />
                                </Form.Item>
                            </Col>
                            <Col span={8}>
                                <Form.Item
                                    label={t('config.embeddingModel')}
                                    name="embedding_model_name"
                                    rules={[{ required: true }]}
                                >
                                    <Input
                                        placeholder="text-embedding-ada-002"
                                        style={{ borderColor: '#fecaca' }}
                                    />
                                </Form.Item>
                            </Col>
                        </Row>
                    </Card>
                </Form>
            </Space>

            {/* Save Config Modal */}
            <Modal
                title={t('config.saveConfigModal.title')}
                open={saveModalVisible}
                onOk={handleSaveConfig}
                onCancel={() => {
                    setSaveModalVisible(false)
                    setConfigName('')
                }}
                okText={t('common.save')}
                cancelText={t('common.cancel')}
                confirmLoading={loading}
            >
                <Space direction="vertical" style={{ width: '100%' }}>
                    <Text>{t('config.saveConfigModal.prompt')}</Text>
                    <Input
                        placeholder={t('config.saveConfigModal.placeholder')}
                        value={configName}
                        onChange={(e) => setConfigName(e.target.value)}
                        onPressEnter={handleSaveConfig}
                        autoFocus
                    />
                </Space>
            </Modal>

            {/* Load Config Modal */}
            <Modal
                title={t('config.loadConfigModal.title')}
                open={loadModalVisible}
                onCancel={() => setLoadModalVisible(false)}
                footer={null}
                width={700}
            >
                <List
                    dataSource={savedConfigs}
                    locale={{ emptyText: t('config.loadConfigModal.empty') }}
                    renderItem={(config) => (
                        <List.Item
                            actions={[
                                <Button
                                    type="link"
                                    onClick={() => handleLoadConfig(config.name)}
                                    loading={loading}
                                >
                                    {t('common.load')}
                                </Button>,
                                <Popconfirm
                                    title={t('config.loadConfigModal.confirmDelete')}
                                    description={t('config.loadConfigModal.confirmDeleteDesc').replace('{name}', config.name)}
                                    onConfirm={() => handleDeleteConfig(config.name)}
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
                                        <Tag color="blue">{config.target_name}</Tag>
                                        <Tag color="green">{config.stock_code}</Tag>
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

export default ConfigPage
