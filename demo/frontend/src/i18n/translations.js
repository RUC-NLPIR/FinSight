export const translations = {
    zh: {
        // Common
        common: {
            save: '保存',
            cancel: '取消',
            delete: '删除',
            load: '加载',
            confirm: '确认',
            close: '关闭',
            refresh: '刷新',
            add: '添加',
            loading: '加载中...',
            success: '成功',
            error: '错误',
            warning: '警告',
            preview: '预览',
            download: '下载',
            underDevelopment: 'Under Development'
        },

        // Landing Page
        landing: {
            title: '玉兰·融观',
            subtitle: 'AI 驱动的金融研究系统',
            description1: '以代码智能体和深度推理突破 AI 的局限',
            description2: '从数据到洞察 — 全自动生成专业级金融研究报告',
            enterButton: '进入系统',
            slogan: 'AI 驱动的专业金融研究',
            features: {
                codeAgent: {
                    title: '可编程代码智能体',
                    subtitle: 'CAVM 架构',
                    desc: '代码驱动执行，配合变量内存机制，精准控制异构数据流'
                },
                vision: {
                    title: '视觉增强',
                    subtitle: 'VLM 驱动',
                    desc: '迭代反馈循环，自动优化图表至出版级品质'
                },
                reasoning: {
                    title: '长文本推理',
                    subtitle: '分析链',
                    desc: '先分析后写作的框架，生成严谨、连贯的深度研究报告'
                },
                research: {
                    title: '深度研究',
                    subtitle: '循证驱动',
                    desc: '多轮验证机制，确保每个结论都有可追溯的事实依据'
                }
            }
        },

        // Header
        header: {
            title: '玉兰·融观',
            subtitle: 'Yulan-FinSight AI System',
            controlPanel: '控制面板'
        },

        // Menu
        menu: {
            config: '系统配置',
            tasks: '任务配置',
            execution: '执行监控',
            reports: '报告列表'
        },

        // Config Page
        config: {
            title: '系统配置',
            description: '配置系统参数和API密钥',
            loadConfig: '加载配置',
            saveConfig: '保存配置',
            basicConfig: '基础配置',
            targetCompany: '目标公司名称',
            targetCompanyPlaceholder: '例如：浪潮信息',
            targetCompanyRequired: '请输入目标公司名称',
            stockCode: '股票代码',
            stockCodePlaceholder: '例如：000977',
            stockCodeRequired: '请输入股票代码',
            outputDir: '输出目录',
            reportTemplatePath: '报告模板路径',
            outlineTemplatePath: '大纲模板路径',
            modelConfig: '模型配置',
            modelName: 'Model Name',
            modelNameRequired: '请输入模型名称',
            apiKey: 'API Key',
            apiKeyRequired: '请输入API Key',
            baseUrl: 'Base URL',
            baseUrlRequired: '请输入Base URL',
            usedModelNames: '使用的模型名称',
            mainLLM: '主要LLM模型',
            visionModel: '视觉模型',
            embeddingModel: 'Embedding模型',
            saveConfigModal: {
                title: '保存配置',
                prompt: '请输入配置名称：',
                placeholder: '例如: 浪潮信息_配置1'
            },
            loadConfigModal: {
                title: '加载配置',
                empty: '暂无保存的配置',
                confirmDelete: '确认删除',
                confirmDeleteDesc: '确定要删除配置 "{name}" 吗？'
            },
            messages: {
                loadSuccess: '配置 "{name}" 加载成功',
                loadFailed: '加载配置失败',
                saveSuccess: '配置 "{name}" 保存成功',
                saveFailed: '保存配置失败',
                updateFailed: '更新配置失败',
                deleteSuccess: '配置 "{name}" 已删除',
                deleteFailed: '删除配置失败',
                enterConfigName: '请输入配置名称',
                checkForm: '请检查表单'
            },
            llmLabels: {
                ds: 'DeepSeek LLM',
                vlm: 'Vision LLM',
                embedding: 'Embedding Model'
            }
        },

        // Tasks Page
        tasks: {
            title: '任务配置',
            description: '配置数据收集和分析任务',
            loadTasks: '加载任务',
            saveTasks: '保存任务',
            collectTasks: '数据收集任务',
            analysisTasks: '数据分析任务',
            addTask: '添加任务',
            dataCollect: '数据收集',
            dataAnalysis: '数据分析',
            noCollectTasks: '暂无数据收集任务',
            noAnalysisTasks: '暂无数据分析任务',
            addTaskModal: {
                collectTitle: '添加数据收集任务',
                analysisTitle: '添加数据分析任务',
                collectPlaceholder: '例如：Latest share price\n或：Sample company balance sheet',
                analysisPlaceholder: '例如：Company history and business review\n或：Ownership structure analysis'
            },
            saveTasksModal: {
                title: '保存任务配置',
                prompt: '请输入任务配置名称：',
                placeholder: '例如: 浪潮信息_任务配置1'
            },
            loadTasksModal: {
                title: '加载任务配置',
                empty: '暂无保存的任务配置',
                confirmDelete: '确认删除',
                confirmDeleteDesc: '确定要删除任务配置 "{name}" 吗？',
                collectCount: '收集',
                analysisCount: '分析'
            },
            messages: {
                loadSuccess: '任务配置 "{name}" 加载成功',
                loadFailed: '加载任务失败',
                saveSuccess: '任务配置 "{name}" 保存成功',
                saveFailed: '保存任务配置失败',
                updateFailed: '更新任务失败',
                deleteSuccess: '任务配置 "{name}" 已删除',
                deleteFailed: '删除任务配置失败',
                enterTaskName: '请输入任务配置名称',
                addSuccess: '任务添加成功',
                deleteTaskSuccess: '任务删除成功',
                enterTaskContent: '请输入任务内容'
            }
        },

        // Execution Page
        execution: {
            title: '执行监控',
            description: '实时监控Agent执行状态和日志',
            start: '开始执行',
            resume: '恢复执行',
            stop: '停止执行',
            noResumableExecution: '没有可恢复的执行记录',
            resumeTooltip: '恢复: {name} ({time})',
            lastExecution: '上次执行',
            collectTaskCount: '{count} 个收集任务',
            analysisTaskCount: '{count} 个分析任务',
            executing: '执行中',
            executingDesc: '系统正在执行任务，请耐心等待...',
            overview: '总览',
            overallProgress: '整体进度',
            currentPhase: '当前阶段',
            agentType: 'Agent类型',
            taskContent: '任务内容',
            currentStatus: '当前状态',
            priority: '优先级',
            agentId: 'Agent ID',
            executionLogs: '执行日志',
            noLogs: '暂无日志',
            showingLogs: '显示最近 {visible} 条日志（共 {total} 条）',
            noExecutionTasks: '暂无执行任务，请先配置任务并启动执行',
            taskCount: '{count} 个任务',
            status: {
                pending: '等待中',
                running: '运行中',
                completed: '已完成',
                error: '错误'
            },
            phases: {
                1: '数据收集阶段',
                2: '数据分析阶段',
                3: '报告生成阶段'
            },
            agentTypes: {
                data_collector: '数据收集',
                data_analyzer: '数据分析',
                report_generator: '报告生成',
                'deepsearch agent': '深度搜索'
            },
            messages: {
                startSuccess: '执行已开始',
                stopSent: '停止请求已发送',
                completeSuccess: '执行已完成',
                executionError: '执行出错',
                startFailed: '启动失败',
                stopFailed: '停止失败'
            }
        },

        // Reports Page
        reports: {
            title: '报告列表',
            description: '查看和下载已生成的分析报告',
            refresh: '刷新',
            totalReports: '总报告数',
            targetCompanies: '目标公司',
            wordDocs: 'Word 文档',
            markdown: 'Markdown',
            noReports: '暂无报告，请先执行任务生成报告',
            totalCount: '共 {count} 个报告',
            columns: {
                file: '文件',
                type: '类型',
                targetCompany: '目标公司',
                size: '大小',
                modifiedTime: '修改时间',
                actions: '操作'
            },
            fileTypes: {
                docx: 'Word 文档',
                pdf: 'PDF 文档',
                md: 'Markdown'
            },
            messages: {
                loadFailed: '加载报告列表失败',
                previewMdOnly: '只有 Markdown 文件支持预览，其他格式请下载后查看',
                previewFailed: '加载预览失败'
            }
        },

        // Language Switcher
        language: {
            switchTo: '切换到英文',
            current: '中文'
        }
    },

    en: {
        // Common
        common: {
            save: 'Save',
            cancel: 'Cancel',
            delete: 'Delete',
            load: 'Load',
            confirm: 'Confirm',
            close: 'Close',
            refresh: 'Refresh',
            add: 'Add',
            loading: 'Loading...',
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            preview: 'Preview',
            download: 'Download',
            underDevelopment: 'Under Development'
        },

        // Landing Page
        landing: {
            title: 'Yulan-FinSight',
            subtitle: 'AI-Powered Financial Research System',
            description1: 'Breaking AI limitations with code agents and deep reasoning',
            description2: 'From data to insights — fully automated, publication-ready financial reports',
            enterButton: 'Enter System',
            slogan: 'AI-Driven Professional Financial Research',
            features: {
                codeAgent: {
                    title: 'Programmable Code Agent',
                    subtitle: 'CAVM Architecture',
                    desc: 'Code-driven execution with variable memory for precise control of heterogeneous data flows'
                },
                vision: {
                    title: 'Vision Enhancement',
                    subtitle: 'VLM-Powered',
                    desc: 'Iterative feedback loops that automatically refine charts to publication-grade quality'
                },
                reasoning: {
                    title: 'Long-Form Reasoning',
                    subtitle: 'Chain-of-Analysis',
                    desc: 'Analyze-then-write framework producing rigorous, coherent in-depth reports'
                },
                research: {
                    title: 'Deep Research',
                    subtitle: 'Evidence-Based',
                    desc: 'Multi-round verification ensuring factual traceability for every conclusion'
                }
            }
        },

        // Header
        header: {
            title: 'Yulan-FinSight',
            subtitle: 'AI Financial Research System',
            controlPanel: 'Control Panel'
        },

        // Menu
        menu: {
            config: 'System Config',
            tasks: 'Task Config',
            execution: 'Execution Monitor',
            reports: 'Reports'
        },

        // Config Page
        config: {
            title: 'System Configuration',
            description: 'Configure system parameters and API keys',
            loadConfig: 'Load Config',
            saveConfig: 'Save Config',
            basicConfig: 'Basic Configuration',
            targetCompany: 'Target Company Name',
            targetCompanyPlaceholder: 'e.g., Apple Inc.',
            targetCompanyRequired: 'Please enter target company name',
            stockCode: 'Stock Code',
            stockCodePlaceholder: 'e.g., AAPL',
            stockCodeRequired: 'Please enter stock code',
            outputDir: 'Output Directory',
            reportTemplatePath: 'Report Template Path',
            outlineTemplatePath: 'Outline Template Path',
            modelConfig: 'Model Configuration',
            modelName: 'Model Name',
            modelNameRequired: 'Please enter model name',
            apiKey: 'API Key',
            apiKeyRequired: 'Please enter API Key',
            baseUrl: 'Base URL',
            baseUrlRequired: 'Please enter Base URL',
            usedModelNames: 'Model Names in Use',
            mainLLM: 'Main LLM Model',
            visionModel: 'Vision Model',
            embeddingModel: 'Embedding Model',
            saveConfigModal: {
                title: 'Save Configuration',
                prompt: 'Enter configuration name:',
                placeholder: 'e.g., Company_Config1'
            },
            loadConfigModal: {
                title: 'Load Configuration',
                empty: 'No saved configurations',
                confirmDelete: 'Confirm Delete',
                confirmDeleteDesc: 'Are you sure you want to delete configuration "{name}"?'
            },
            messages: {
                loadSuccess: 'Configuration "{name}" loaded successfully',
                loadFailed: 'Failed to load configuration',
                saveSuccess: 'Configuration "{name}" saved successfully',
                saveFailed: 'Failed to save configuration',
                updateFailed: 'Failed to update configuration',
                deleteSuccess: 'Configuration "{name}" deleted',
                deleteFailed: 'Failed to delete configuration',
                enterConfigName: 'Please enter configuration name',
                checkForm: 'Please check the form'
            },
            llmLabels: {
                ds: 'DeepSeek LLM',
                vlm: 'Vision LLM',
                embedding: 'Embedding Model'
            }
        },

        // Tasks Page
        tasks: {
            title: 'Task Configuration',
            description: 'Configure data collection and analysis tasks',
            loadTasks: 'Load Tasks',
            saveTasks: 'Save Tasks',
            collectTasks: 'Data Collection Tasks',
            analysisTasks: 'Data Analysis Tasks',
            addTask: 'Add Task',
            dataCollect: 'Collection',
            dataAnalysis: 'Analysis',
            noCollectTasks: 'No data collection tasks',
            noAnalysisTasks: 'No data analysis tasks',
            addTaskModal: {
                collectTitle: 'Add Data Collection Task',
                analysisTitle: 'Add Data Analysis Task',
                collectPlaceholder: 'e.g., Latest share price\nor: Sample company balance sheet',
                analysisPlaceholder: 'e.g., Company history and business review\nor: Ownership structure analysis'
            },
            saveTasksModal: {
                title: 'Save Task Configuration',
                prompt: 'Enter task configuration name:',
                placeholder: 'e.g., Company_TaskConfig1'
            },
            loadTasksModal: {
                title: 'Load Task Configuration',
                empty: 'No saved task configurations',
                confirmDelete: 'Confirm Delete',
                confirmDeleteDesc: 'Are you sure you want to delete task configuration "{name}"?',
                collectCount: 'Collect',
                analysisCount: 'Analyze'
            },
            messages: {
                loadSuccess: 'Task configuration "{name}" loaded successfully',
                loadFailed: 'Failed to load tasks',
                saveSuccess: 'Task configuration "{name}" saved successfully',
                saveFailed: 'Failed to save task configuration',
                updateFailed: 'Failed to update tasks',
                deleteSuccess: 'Task configuration "{name}" deleted',
                deleteFailed: 'Failed to delete task configuration',
                enterTaskName: 'Please enter task configuration name',
                addSuccess: 'Task added successfully',
                deleteTaskSuccess: 'Task deleted successfully',
                enterTaskContent: 'Please enter task content'
            }
        },

        // Execution Page
        execution: {
            title: 'Execution Monitor',
            description: 'Real-time monitoring of Agent execution status and logs',
            start: 'Start Execution',
            resume: 'Resume',
            stop: 'Stop Execution',
            noResumableExecution: 'No resumable execution record',
            resumeTooltip: 'Resume: {name} ({time})',
            lastExecution: 'Last Execution',
            collectTaskCount: '{count} collection tasks',
            analysisTaskCount: '{count} analysis tasks',
            executing: 'Executing',
            executingDesc: 'System is executing tasks, please wait...',
            overview: 'Overview',
            overallProgress: 'Overall Progress',
            currentPhase: 'Current Phase',
            agentType: 'Agent Type',
            taskContent: 'Task Content',
            currentStatus: 'Current Status',
            priority: 'Priority',
            agentId: 'Agent ID',
            executionLogs: 'Execution Logs',
            noLogs: 'No logs',
            showingLogs: 'Showing latest {visible} logs (total {total})',
            noExecutionTasks: 'No execution tasks. Please configure tasks and start execution.',
            taskCount: '{count} tasks',
            status: {
                pending: 'Pending',
                running: 'Running',
                completed: 'Completed',
                error: 'Error'
            },
            phases: {
                1: 'Data Collection Phase',
                2: 'Data Analysis Phase',
                3: 'Report Generation Phase'
            },
            agentTypes: {
                data_collector: 'Data Collector',
                data_analyzer: 'Data Analyzer',
                report_generator: 'Report Generator',
                'deepsearch agent': 'Deep Search'
            },
            messages: {
                startSuccess: 'Execution started',
                stopSent: 'Stop request sent',
                completeSuccess: 'Execution completed',
                executionError: 'Execution error',
                startFailed: 'Failed to start',
                stopFailed: 'Failed to stop'
            }
        },

        // Reports Page
        reports: {
            title: 'Reports',
            description: 'View and download generated analysis reports',
            refresh: 'Refresh',
            totalReports: 'Total Reports',
            targetCompanies: 'Target Companies',
            wordDocs: 'Word Documents',
            markdown: 'Markdown',
            noReports: 'No reports. Please execute tasks to generate reports.',
            totalCount: '{count} reports in total',
            columns: {
                file: 'File',
                type: 'Type',
                targetCompany: 'Target Company',
                size: 'Size',
                modifiedTime: 'Modified Time',
                actions: 'Actions'
            },
            fileTypes: {
                docx: 'Word Document',
                pdf: 'PDF Document',
                md: 'Markdown'
            },
            messages: {
                loadFailed: 'Failed to load reports',
                previewMdOnly: 'Only Markdown files support preview. Please download other formats to view.',
                previewFailed: 'Failed to load preview'
            }
        },

        // Language Switcher
        language: {
            switchTo: 'Switch to Chinese',
            current: 'English'
        }
    }
}

