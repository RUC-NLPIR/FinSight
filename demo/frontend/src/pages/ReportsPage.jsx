import React, { useState, useEffect, useCallback } from 'react'
import {
    Card,
    Button,
    Space,
    Typography,
    Table,
    Tag,
    Empty,
    message,
    Modal,
    Spin,
    Tooltip,
    Divider
} from 'antd'
import {
    FileTextOutlined,
    DownloadOutlined,
    EyeOutlined,
    FileWordOutlined,
    FilePdfOutlined,
    FileMarkdownOutlined,
    ReloadOutlined,
    FolderOpenOutlined
} from '@ant-design/icons'
import { listReports, getReportPreview, getReportDownloadUrl } from '../api/client'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useLanguage } from '../contexts/LanguageContext'

const { Title, Text, Paragraph } = Typography

function ReportsPage() {
    const [reports, setReports] = useState([])
    const [loading, setLoading] = useState(false)
    const [previewVisible, setPreviewVisible] = useState(false)
    const [previewContent, setPreviewContent] = useState('')
    const [previewTitle, setPreviewTitle] = useState('')
    const [previewLoading, setPreviewLoading] = useState(false)
    const { t, language } = useLanguage()

    useEffect(() => {
        loadReports()
    }, [])

    const loadReports = async () => {
        setLoading(true)
        try {
            const response = await listReports()
            setReports(response.data.reports || [])
        } catch (error) {
            console.error('Failed to load reports:', error)
            message.error(t('reports.messages.loadFailed'))
        } finally {
            setLoading(false)
        }
    }

    const handleDownload = useCallback((record) => {
        const url = getReportDownloadUrl(record.target_name, record.filename)
        window.open(url, '_blank')
    }, [])

    const handlePreview = useCallback(async (record) => {
        if (record.type !== 'md') {
            message.info(t('reports.messages.previewMdOnly'))
            return
        }

        setPreviewLoading(true)
        setPreviewVisible(true)
        setPreviewTitle(record.filename)

        try {
            const response = await getReportPreview(record.target_name, record.filename)
            setPreviewContent(response.data.content)
        } catch (error) {
            console.error('Failed to load preview:', error)
            message.error(t('reports.messages.previewFailed'))
            setPreviewContent(t('reports.messages.previewFailed'))
        } finally {
            setPreviewLoading(false)
        }
    }, [t])

    const getFileIcon = useCallback((type) => {
        switch (type) {
            case 'docx':
                return <FileWordOutlined style={{ color: '#2b579a', fontSize: '20px' }} />
            case 'pdf':
                return <FilePdfOutlined style={{ color: '#dc2626', fontSize: '20px' }} />
            case 'md':
                return <FileMarkdownOutlined style={{ color: '#083d77', fontSize: '20px' }} />
            default:
                return <FileTextOutlined style={{ fontSize: '20px' }} />
        }
    }, [])

    const formatFileSize = useCallback((bytes) => {
        if (bytes === 0) return '0 B'
        const k = 1024
        const sizes = ['B', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }, [])

    const getTypeLabel = useCallback((type) => {
        const typeKey = `reports.fileTypes.${type}`
        const translated = t(typeKey)
        return translated !== typeKey ? translated : type.toUpperCase()
    }, [t])

    const getTypeColor = useCallback((type) => {
        const colors = {
            'docx': 'blue',
            'pdf': 'red',
            'md': 'green'
        }
        return colors[type] || 'default'
    }, [])

    const columns = [
        {
            title: t('reports.columns.file'),
            dataIndex: 'filename',
            key: 'filename',
            render: (text, record) => (
                <Space>
                    {getFileIcon(record.type)}
                    <div>
                        <div>
                            <Text strong style={{ fontSize: '14px' }}>{text}</Text>
                        </div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                            <FolderOpenOutlined /> {record.target_name}
                        </Text>
                    </div>
                </Space>
            ),
            sorter: (a, b) => a.filename.localeCompare(b.filename)
        },
        {
            title: t('reports.columns.type'),
            dataIndex: 'type',
            key: 'type',
            width: 120,
            render: (type) => (
                <Tag color={getTypeColor(type)}>
                    {getTypeLabel(type)}
                </Tag>
            ),
            filters: [
                { text: t('reports.fileTypes.docx'), value: 'docx' },
                { text: t('reports.fileTypes.pdf'), value: 'pdf' },
                { text: t('reports.fileTypes.md'), value: 'md' }
            ],
            onFilter: (value, record) => record.type === value
        },
        {
            title: t('reports.columns.targetCompany'),
            dataIndex: 'target_name',
            key: 'target_name',
            width: 150,
            render: (text) => (
                <Tag color="orange">{text}</Tag>
            ),
            sorter: (a, b) => a.target_name.localeCompare(b.target_name)
        },
        {
            title: t('reports.columns.size'),
            dataIndex: 'size',
            key: 'size',
            width: 100,
            render: (size) => formatFileSize(size),
            sorter: (a, b) => a.size - b.size
        },
        {
            title: t('reports.columns.modifiedTime'),
            dataIndex: 'modified_time',
            key: 'modified_time',
            width: 180,
            render: (time) => new Date(time).toLocaleString(language === 'zh' ? 'zh-CN' : 'en-US'),
            sorter: (a, b) => new Date(a.modified_time) - new Date(b.modified_time),
            defaultSortOrder: 'descend'
        },
        {
            title: t('reports.columns.actions'),
            key: 'actions',
            width: 150,
            render: (_, record) => (
                <Space>
                    {record.type === 'md' && (
                        <Tooltip title={t('common.preview')}>
                            <Button
                                type="text"
                                icon={<EyeOutlined />}
                                onClick={() => handlePreview(record)}
                            />
                        </Tooltip>
                    )}
                    <Tooltip title={t('common.download')}>
                        <Button
                            type="text"
                            icon={<DownloadOutlined />}
                            onClick={() => handleDownload(record)}
                            style={{ color: '#dc2626' }}
                        />
                    </Tooltip>
                </Space>
            )
        }
    ]

    // Group reports by target
    const reportsByTarget = reports.reduce((acc, report) => {
        if (!acc[report.target_name]) {
            acc[report.target_name] = []
        }
        acc[report.target_name].push(report)
        return acc
    }, {})

    return (
        <div>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <Title level={2} style={{ margin: 0 }}>
                            <FileTextOutlined /> {t('reports.title')}
                        </Title>
                        <Text type="secondary">{t('reports.description')}</Text>
                    </div>
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={loadReports}
                        loading={loading}
                    >
                        {t('common.refresh')}
                    </Button>
                </div>

                {/* Summary Cards */}
                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                    <Card size="small" style={{ minWidth: '150px' }}>
                        <Space direction="vertical" align="center" style={{ width: '100%' }}>
                            <Text type="secondary">{t('reports.totalReports')}</Text>
                            <Title level={2} style={{ margin: 0, color: '#dc2626' }}>
                                {reports.length}
                            </Title>
                        </Space>
                    </Card>
                    <Card size="small" style={{ minWidth: '150px' }}>
                        <Space direction="vertical" align="center" style={{ width: '100%' }}>
                            <Text type="secondary">{t('reports.targetCompanies')}</Text>
                            <Title level={2} style={{ margin: 0, color: '#f59e0b' }}>
                                {Object.keys(reportsByTarget).length}
                            </Title>
                        </Space>
                    </Card>
                    <Card size="small" style={{ minWidth: '150px' }}>
                        <Space direction="vertical" align="center" style={{ width: '100%' }}>
                            <Text type="secondary">{t('reports.wordDocs')}</Text>
                            <Title level={2} style={{ margin: 0, color: '#2b579a' }}>
                                {reports.filter(r => r.type === 'docx').length}
                            </Title>
                        </Space>
                    </Card>
                    <Card size="small" style={{ minWidth: '150px' }}>
                        <Space direction="vertical" align="center" style={{ width: '100%' }}>
                            <Text type="secondary">{t('reports.markdown')}</Text>
                            <Title level={2} style={{ margin: 0, color: '#16a34a' }}>
                                {reports.filter(r => r.type === 'md').length}
                            </Title>
                        </Space>
                    </Card>
                </div>

                {/* Reports Table */}
                <Card>
                    {reports.length === 0 && !loading ? (
                        <Empty
                            description={t('reports.noReports')}
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                    ) : (
                        <Table
                            columns={columns}
                            dataSource={reports}
                            rowKey="id"
                            loading={loading}
                            pagination={{
                                pageSize: 10,
                                showSizeChanger: true,
                                showTotal: (total) => t('reports.totalCount').replace('{count}', total)
                            }}
                        />
                    )}
                </Card>
            </Space>

            {/* Preview Modal */}
            <Modal
                title={
                    <Space>
                        <FileMarkdownOutlined />
                        <span>{previewTitle}</span>
                    </Space>
                }
                open={previewVisible}
                onCancel={() => setPreviewVisible(false)}
                footer={[
                    <Button key="close" onClick={() => setPreviewVisible(false)}>
                        {t('common.close')}
                    </Button>
                ]}
                width={900}
                style={{ top: 20 }}
                styles={{
                    body: {
                        maxHeight: 'calc(100vh - 200px)',
                        overflow: 'auto',
                        padding: '24px'
                    }
                }}
            >
                {previewLoading ? (
                    <div style={{ textAlign: 'center', padding: '50px' }}>
                        <Spin size="large" />
                        <div style={{ marginTop: '16px' }}>
                            <Text type="secondary">{t('common.loading')}</Text>
                        </div>
                    </div>
                ) : (
                    <div className="markdown-preview" style={{
                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif',
                        lineHeight: 1.8,
                        color: '#333'
                    }}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {previewContent}
                        </ReactMarkdown>
                    </div>
                )}
            </Modal>

            <style>{`
                .markdown-preview h1 {
                    font-size: 28px;
                    font-weight: 700;
                    border-bottom: 2px solid #dc2626;
                    padding-bottom: 8px;
                    margin-top: 24px;
                    margin-bottom: 16px;
                    color: #1a1a1a;
                }
                .markdown-preview h2 {
                    font-size: 22px;
                    font-weight: 600;
                    margin-top: 20px;
                    margin-bottom: 12px;
                    color: #dc2626;
                }
                .markdown-preview h3 {
                    font-size: 18px;
                    font-weight: 600;
                    margin-top: 16px;
                    margin-bottom: 8px;
                    color: #333;
                }
                .markdown-preview p {
                    margin-bottom: 12px;
                    text-align: justify;
                }
                .markdown-preview ul, .markdown-preview ol {
                    margin-bottom: 12px;
                    padding-left: 24px;
                }
                .markdown-preview li {
                    margin-bottom: 6px;
                }
                .markdown-preview table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 16px 0;
                }
                .markdown-preview th, .markdown-preview td {
                    border: 1px solid #e5e5e5;
                    padding: 10px 12px;
                    text-align: left;
                }
                .markdown-preview th {
                    background: linear-gradient(135deg, #fef2f2 0%, #fff 100%);
                    font-weight: 600;
                    color: #dc2626;
                }
                .markdown-preview tr:nth-child(even) {
                    background: #fafafa;
                }
                .markdown-preview blockquote {
                    border-left: 4px solid #dc2626;
                    padding-left: 16px;
                    margin: 16px 0;
                    color: #666;
                    font-style: italic;
                    background: #fef2f2;
                    padding: 12px 16px;
                    border-radius: 0 8px 8px 0;
                }
                .markdown-preview code {
                    background: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: 'Consolas', monospace;
                    font-size: 14px;
                }
                .markdown-preview pre {
                    background: #1e1e1e;
                    padding: 16px;
                    border-radius: 8px;
                    overflow-x: auto;
                }
                .markdown-preview pre code {
                    background: none;
                    color: #d4d4d4;
                    padding: 0;
                }
            `}</style>
        </div>
    )
}

export default ReportsPage
